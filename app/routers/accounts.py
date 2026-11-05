from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import require_permission, write_audit
from ..excel_import import ExistingAccount, ImportFileError, build_template, norm, parse_rows, read_rows
from ..models import (
    Account, AccountClassification, Beneficiary, JournalEntryDetail, TreasuryAccount, User,
)
from ..pdf_report import PdfSetupError, build_accounts_pdf
from ..schemas import (
    AccountCreate, AccountDetail, AccountList, AccountNode, AccountOut, AccountUpdate, ClassificationOut,
    ImportPreviewRow, ImportReport, ImportRowError,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PDF_ROWS = 20000
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

SCREEN = "ChartOfAccounts"
router = APIRouter(prefix="/accounts", tags=["ChartOfAccounts"])

_FIELDS = ("account_code", "account_name_ar", "account_name_en", "parent_account_id", "classification_id",
           "normal_balance", "opening_debit", "opening_credit", "is_active")


def _snapshot(acc: Account) -> dict:
    return {f: getattr(acc, f) for f in _FIELDS}


def _count(db: Session, stmt) -> int:
    return db.scalar(stmt) or 0


def _blockers(db: Session, acc: Account) -> dict[str, tuple[int, str]]:
    """الأسباب اللي بتمنع حذف الحساب: key → (العدد، الوصف)."""
    out: dict[str, tuple[int, str]] = {}
    n = _count(db, select(func.count()).select_from(JournalEntryDetail)
               .where(JournalEntryDetail.account_id == acc.account_id))
    if n:
        out["journal_lines"] = (n, f"عليه {n} حركة في قيود اليومية")
    n = _count(db, select(func.count()).select_from(Account).where(Account.parent_account_id == acc.account_id))
    if n:
        out["children"] = (n, f"له {n} حساب فرعي")
    if (acc.opening_debit or 0) != 0 or (acc.opening_credit or 0) != 0:
        out["opening_balance"] = (1, "له رصيد افتتاحي")
    n = _count(db, select(func.count()).select_from(TreasuryAccount).where(TreasuryAccount.gl_account_id == acc.account_id))
    if n:
        out["treasury"] = (n, f"مربوط بـ {n} خزينة/بنك")
    n = _count(db, select(func.count()).select_from(Beneficiary).where(Beneficiary.linked_account_id == acc.account_id))
    if n:
        out["beneficiaries"] = (n, f"مربوط بـ {n} مستفيد")
    return out


def _get_or_404(db: Session, account_id: int) -> Account:
    acc = db.get(Account, account_id)
    if acc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "الحساب غير موجود")
    return acc


def _check_classification(db: Session, classification_id: int) -> None:
    if db.get(AccountClassification, classification_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "التصنيف غير موجود")


def _check_parent(db: Session, parent_id: int, account_id: int | None = None) -> None:
    parent = db.get(Account, parent_id)
    if parent is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الحساب الأب غير موجود")
    if not parent.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الحساب الأب غير نشط")
    if _count(db, select(func.count()).select_from(JournalEntryDetail)
              .where(JournalEntryDetail.account_id == parent_id)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "الحساب الأب عليه حركات — مينفعش يبقى حساب رئيسي")
    cur = parent
    while cur is not None:  # منع الحلقات: الأب الجديد ما يبقاش الحساب نفسه أو أحد فروعه
        if account_id is not None and cur.account_id == account_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "مينفعش الحساب يبقى أب لنفسه أو لأحد فروعه")
        cur = db.get(Account, cur.parent_account_id) if cur.parent_account_id else None


def _code_taken(db: Session, code: str, exclude_id: int | None = None) -> bool:
    stmt = select(func.count()).select_from(Account).where(Account.account_code == code)
    if exclude_id is not None:
        stmt = stmt.where(Account.account_id != exclude_id)
    return _count(db, stmt) > 0


# ----------------------------- Read -----------------------------
@router.get("/classifications", response_model=list[ClassificationOut])
def list_classifications(_: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    return db.scalars(select(AccountClassification).order_by(AccountClassification.classification_id)).all()


@router.get("/tree", response_model=list[AccountNode])
def accounts_tree(_: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).order_by(Account.account_code)).all()
    nodes = {a.account_id: AccountNode.model_validate(a) for a in accounts}
    roots: list[AccountNode] = []
    for a in accounts:
        node = nodes[a.account_id]
        parent = nodes.get(a.parent_account_id) if a.parent_account_id else None
        (parent.children if parent else roots).append(node)
    return roots


@router.get("", response_model=AccountList)
def list_accounts(
    q: str | None = Query(None, description="بحث في الكود أو الاسم"),
    classification_id: int | None = None,
    parent_id: int | None = None,
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _: User = Depends(require_permission(SCREEN, "View")),
    db: Session = Depends(get_db),
):
    stmt = select(Account)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Account.account_code.ilike(like), Account.account_name_ar.ilike(like), Account.account_name_en.ilike(like)))
    if classification_id is not None:
        stmt = stmt.where(Account.classification_id == classification_id)
    if parent_id is not None:
        stmt = stmt.where(Account.parent_account_id == parent_id)
    if is_active is not None:
        stmt = stmt.where(Account.is_active.is_(is_active))
    total = _count(db, select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.order_by(Account.account_code).offset(skip).limit(limit)).all()
    return AccountList(total=total, items=[AccountOut.model_validate(i) for i in items])


@router.get("/{account_id}", response_model=AccountDetail)
def get_account(account_id: int, _: User = Depends(require_permission(SCREEN, "View")),
                db: Session = Depends(get_db)):
    acc = _get_or_404(db, account_id)
    blockers = _blockers(db, acc)
    return AccountDetail(
        **AccountOut.model_validate(acc).model_dump(),
        children_count=blockers.get("children", (0, ""))[0],
        journal_lines_count=blockers.get("journal_lines", (0, ""))[0],
        can_delete=not blockers,
        blockers=[msg for _, msg in blockers.values()],
    )


# ----------------------------- Print (PDF) -----------------------------
@router.get("/export/pdf")
def export_pdf(
    q: str | None = Query(None, description="بحث في الكود أو الاسم"),
    classification_id: int | None = None,
    is_active: bool | None = None,
    lang: str = Query("ar", pattern="^(ar|en)$"),
    user: User = Depends(require_permission(SCREEN, "Print")),
    db: Session = Depends(get_db),
):
    """طباعة شجرة الحسابات PDF بنفس فلاتر الشاشة (الحسابات مرتبة بالكود ومزاحة حسب المستوى)."""
    all_accounts = db.scalars(select(Account).order_by(Account.account_code)).all()
    by_id = {a.account_id: a for a in all_accounts}
    parents = {a.parent_account_id for a in all_accounts if a.parent_account_id}
    classes = {c.classification_id: (c.name_en if lang == "en" and c.name_en else c.name_ar) for c in db.scalars(select(AccountClassification))}

    def level(a: Account) -> int:
        n, cur, guard = 0, a, 0
        while cur.parent_account_id and cur.parent_account_id in by_id and guard < 50:
            cur, n, guard = by_id[cur.parent_account_id], n + 1, guard + 1
        return n

    needle = (q or "").strip().lower()
    rows = []
    for a in all_accounts:
        if needle and needle not in a.account_code.lower() and needle not in a.account_name_ar.lower() and needle not in (a.account_name_en or "").lower():
            continue
        if classification_id is not None and a.classification_id != classification_id:
            continue
        if is_active is not None and a.is_active != is_active:
            continue
        rows.append({
            "code": a.account_code, "name": (a.account_name_en if lang == "en" and a.account_name_en else a.account_name_ar), "level": level(a),
            "is_parent": a.account_id in parents, "classification": classes.get(a.classification_id, ""),
            "normal_balance": a.normal_balance, "debit": a.opening_debit, "credit": a.opening_credit,
            "is_active": a.is_active,
        })
    if len(rows) > MAX_PDF_ROWS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"عدد الحسابات أكبر من {MAX_PDF_ROWS} — ضيّق الفلتر")

    parts = []
    if classification_id is not None:
        parts.append(f"التصنيف: {classes.get(classification_id, classification_id)}")
    if needle:
        parts.append(f"بحث: {q.strip()}")
    if is_active is not None:
        parts.append("الحالة: نشط" if is_active else "الحالة: موقوف")
    try:
        pdf = build_accounts_pdf(
            rows, title="شجرة الحسابات", filters_text=" | ".join(parts), printed_by=user.full_name,
            font_path=settings.pdf_font_path, bold_font_path=settings.pdf_font_bold_path)
    except PdfSetupError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
    write_audit(db, user.user_id, "Print", "ChartOfAccounts", "list", None, {"rows": len(rows), "filters": parts})
    db.commit()
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="chart_of_accounts.pdf"'})


# ----------------------------- Import (Excel) -----------------------------
@router.get("/import/template")
def import_template(_: User = Depends(require_permission(SCREEN, "Add")), db: Session = Depends(get_db)):
    """قالب Excel جاهز (عناوين + مثال + قايمة التصنيفات + تعليمات)."""
    names = db.scalars(select(AccountClassification.name_ar).order_by(AccountClassification.classification_id)).all()
    return Response(build_template(list(names)), media_type=XLSX_MIME,
                    headers={"Content-Disposition": 'attachment; filename="accounts_import_template.xlsx"'})


@router.post("/import", response_model=ImportReport)
def import_accounts(
    file: UploadFile = File(..., description="ملف .xlsx"),
    dry_run: bool = Form(True, description="true = فحص بس من غير حفظ"),
    skip_existing: bool = Form(True, description="تخطّي الأكواد الموجودة دون تعديلها"),
    update_existing: bool = Form(False, description="تحديث الحساب الموجود بنفس الكود"),
    user: User = Depends(require_permission(SCREEN, "Add")),
    db: Session = Depends(get_db),
):
    """استيراد شجرة حسابات من Excel. الحفظ كله أو لا شيء: أي خطأ في أي صف = مفيش حاجة بتتحفظ."""
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "الملف لازم يبقى .xlsx")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "الملف أكبر من 5 ميجا")
    try:
        rows = read_rows(data)
    except ImportFileError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    classifications = {norm(c.name_ar): c.classification_id for c in db.scalars(select(AccountClassification))}
    with_lines = set(db.scalars(select(JournalEntryDetail.account_id).distinct()))
    existing = {
        a.account_code.casefold(): ExistingAccount(a.account_id, a.is_active, a.account_id in with_lines)
        for a in db.scalars(select(Account))
    }
    if update_existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "استيراد شجرة الحسابات مخصص لإضافة الحسابات الجديدة فقط؛ الحسابات الموجودة لا يتم تعديلها.")
    # الموجود بنفس الكود يتم تخطيه دائمًا.
    plan = parse_rows(rows, classifications, existing, skip_existing=True, update_existing=False)

    report = ImportReport(
        dry_run=dry_run, total_rows=plan.total_rows, valid_rows=len(plan.items),
        skipped_existing=plan.skipped_existing, created=0,
        errors=[ImportRowError(row=e.row, field=e.field, message=e.message) for e in plan.errors],
        preview=[ImportPreviewRow(row=i.row, account_code=i.code, account_name_ar=i.name, parent_code=i.parent_code)
                 for i in plan.items[:20]],
    )
    if dry_run:
        return report
    if plan.errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=report.model_dump())
    if not plan.items:
        return report

    by_code = {a.account_code.casefold(): a for a in db.scalars(select(Account)).all()}
    created: dict[str, Account] = {}
    try:
        # إضافة حسابات جديدة فقط؛ الحسابات الموجودة تم تخطيها أثناء الفحص.
        for item in plan.items:
            key = item.code.casefold()
            acc = Account(account_code=item.code, account_name_ar=item.name, classification_id=item.classification_id,
                          normal_balance=item.normal_balance, opening_debit=Decimal("0.00"),
                          opening_credit=Decimal("0.00"), is_active=True)
            db.add(acc)
            created[key] = acc
        db.flush()
        for item in plan.items:
            acc = created[item.code.casefold()]
            if item.parent_code:
                pkey = item.parent_code.casefold()
                parent = created.get(pkey) or by_code.get(pkey)
                if parent is None:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"الحساب الأب {item.parent_code} غير موجود")
                if parent.account_id == acc.account_id:
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"الحساب {item.code} لا يمكن أن يكون أبًا لنفسه")
                acc.parent_account_id = parent.account_id
            else:
                acc.parent_account_id = None
        write_audit(db, user.user_id, "Import", "ChartOfAccounts", "bulk", None,
                    {"file": file.filename, "created": len(plan.items),
                     "skipped_existing": plan.skipped_existing, "opening_balances_zero": True})
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "في كود مكرر اتضاف في نفس الوقت — جرّب تاني")
    report.created = len(plan.items)
    report.dry_run = False
    if hasattr(report, "message"):
        report.message = f"تمت إضافة {report.created} حساب جديد، وتخطي {plan.skipped_existing} حساب موجود"
    return report


# ----------------------------- Create -----------------------------
@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(body: AccountCreate, user: User = Depends(require_permission(SCREEN, "Add")),
                   db: Session = Depends(get_db)):
    if _code_taken(db, body.account_code):
        raise HTTPException(status.HTTP_409_CONFLICT, "كود الحساب مستخدم قبل كده")
    _check_classification(db, body.classification_id)
    if body.parent_account_id is not None:
        _check_parent(db, body.parent_account_id)

    acc = Account(**body.model_dump())
    db.add(acc)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "كود الحساب مستخدم قبل كده")
    write_audit(db, user.user_id, "Create", "ChartOfAccounts", acc.account_id, None, _snapshot(acc))
    db.commit()
    return acc


# ----------------------------- Update -----------------------------
@router.put("/{account_id}", response_model=AccountOut)
def update_account(account_id: int, body: AccountUpdate,
                   user: User = Depends(require_permission(SCREEN, "Edit")), db: Session = Depends(get_db)):
    acc = _get_or_404(db, account_id)
    data = body.model_dump(exclude_unset=True)
    for key in ("account_code", "account_name_ar", "classification_id", "normal_balance",
                "opening_debit", "opening_credit", "is_active"):
        if key in data and data[key] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"الحقل {key} مينفعش يبقى فاضي")

    old = _snapshot(acc)
    has_lines = _count(db, select(func.count()).select_from(JournalEntryDetail)
                       .where(JournalEntryDetail.account_id == account_id)) > 0

    changing_nature = (
        ("classification_id" in data and data["classification_id"] != acc.classification_id)
        or ("normal_balance" in data and data["normal_balance"] != acc.normal_balance)
    )
    if has_lines and changing_nature:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "الحساب عليه حركات — مينفعش تغيّر التصنيف أو طبيعة الرصيد")

    if "account_code" in data and data["account_code"] != acc.account_code \
            and _code_taken(db, data["account_code"], exclude_id=account_id):
        raise HTTPException(status.HTTP_409_CONFLICT, "كود الحساب مستخدم قبل كده")
    if "classification_id" in data:
        _check_classification(db, data["classification_id"])
    if "parent_account_id" in data and data["parent_account_id"] is not None \
            and data["parent_account_id"] != acc.parent_account_id:
        _check_parent(db, data["parent_account_id"], account_id)

    if data.get("is_active") is False and acc.is_active:
        active_children = _count(db, select(func.count()).select_from(Account).where(
            Account.parent_account_id == account_id, Account.is_active == True))
        if active_children:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"للحساب {active_children} حساب فرعي نشط — عطّلهم الأول")

    new_debit = Decimal(data.get("opening_debit", acc.opening_debit) or 0)
    new_credit = Decimal(data.get("opening_credit", acc.opening_credit) or 0)
    if new_debit > 0 and new_credit > 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "الرصيد الافتتاحي إما مدين أو دائن، مش الاتنين")

    for key, value in data.items():
        setattr(acc, key, value)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "كود الحساب مستخدم قبل كده")
    write_audit(db, user.user_id, "Update", "ChartOfAccounts", acc.account_id, old, _snapshot(acc))
    db.commit()
    return acc


# ----------------------------- Delete -----------------------------
@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, user: User = Depends(require_permission(SCREEN, "Delete")),
                   db: Session = Depends(get_db)):
    acc = _get_or_404(db, account_id)
    blockers = _blockers(db, acc)
    if blockers:
        raise HTTPException(status.HTTP_409_CONFLICT, detail={
            "message": "مينفعش تحذف الحساب ده",
            "reasons": [msg for _, msg in blockers.values()],
            "hint": "لو مش عايز تستخدمه تاني، عطّله (is_active=false) بدل الحذف",
        })
    old = _snapshot(acc)
    db.delete(acc)
    write_audit(db, user.user_id, "Delete", "ChartOfAccounts", account_id, old, None)
    db.commit()
