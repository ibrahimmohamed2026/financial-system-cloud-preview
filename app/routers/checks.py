import io
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..arabic_money import MAX_AMOUNT, amount_in_words
from ..common import money, require_any, require_dynamic
from ..database import get_db
from ..deps import get_current_user, has_permission, write_audit
from ..models import (Account, Beneficiary, Check, CheckPrintTemplate, CheckStatusHistory, Company, FiscalYear,
                      AccountClassification, JournalEntry, JournalEntryDetail, Project, TreasuryAccount,
                      TreasuryTransaction, User, utcnow, ContractSettlement, Contract, Counterparty)

CHECK_SCREENS = {"ChecksCib", "ChecksCairoEgp", "ChecksCairoUsd"}
CHECK_CURRENCY = {"ChecksCib": "EGP", "ChecksCairoEgp": "EGP", "ChecksCairoUsd": "USD"}
STATUSES = ["جديد", "مطبوع", "تم التسليم", "تم الصرف", "ملغي", "مرتد"]
# الانتقالات المسموحة
NEXT = {"جديد": {"مطبوع", "تم التسليم", "ملغي"}, "مطبوع": {"تم التسليم", "ملغي"},
        "تم التسليم": {"تم الصرف", "مرتد", "ملغي"}, "تم الصرف": set(), "ملغي": set(), "مرتد": {"تم التسليم", "ملغي"}}
router = APIRouter(prefix="/checks", tags=["Checks"])


class BeneficiaryIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str | None = Field(default=None, max_length=30)
    name_ar: str = Field(min_length=1, max_length=200)
    bank_account_number: str | None = Field(default=None, max_length=50)


class CheckIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    check_book_no: str = Field(min_length=1, max_length=20)
    sequence_no: int = Field(ge=1)
    check_no: str | None = Field(default=None, max_length=30)
    check_date: date | None = None
    beneficiary_id: int
    amount: Decimal | None = Field(default=None, ge=0, le=MAX_AMOUNT, max_digits=18, decimal_places=2)
    purchase_order_no: str | None = Field(default=None, max_length=50)
    project_id: int | None = None
    settlement_id: int | None = None
    description: str | None = Field(default=None, max_length=500)


class StatusIn(BaseModel):
    status: str


class LinkIn(BaseModel):
    treasury_account_id: int


@router.get("/beneficiaries")
def beneficiaries(q: str | None = None, _: User = Depends(require_any(CHECK_SCREENS, "View")),
                  db: Session = Depends(get_db)):
    stmt = select(Beneficiary).where(Beneficiary.is_active == True)
    if q and q.strip():
        stmt = stmt.where(or_(Beneficiary.name_ar.ilike(f"%{q.strip()}%"), Beneficiary.code.ilike(f"%{q.strip()}%")))
    result = []
    for b in db.scalars(stmt.order_by(Beneficiary.name_ar).limit(500)):
        linked = db.get(Account, b.linked_account_id) if b.linked_account_id else None
        result.append({"beneficiary_id": b.beneficiary_id, "code": b.code, "name_ar": b.name_ar,
                       "linked_account_id": linked.account_id if linked else None,
                       "linked_account_label": (f"{linked.account_code} — {linked.account_name_ar}"
                                                if linked else "غير مربوط بحساب في شجرة الحسابات")})
    return result


@router.post("/beneficiaries", status_code=201)
def add_beneficiary(body: BeneficiaryIn, user: User = Depends(require_any(CHECK_SCREENS, "Add")),
                    db: Session = Depends(get_db)):
    code = body.code
    if not code:
        n = (db.scalar(select(func.max(Beneficiary.beneficiary_id))) or 0) + 1
        code = f"B{n:05d}"
    b = Beneficiary(code=code, name_ar=body.name_ar, bank_account_number=body.bank_account_number)
    db.add(b)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "كود المستفيد مستخدم قبل كده")
    write_audit(db, user.user_id, "Create", "Beneficiaries", b.beneficiary_id, None, body.model_dump())
    db.commit()
    return {"beneficiary_id": b.beneficiary_id, "code": b.code, "name_ar": b.name_ar}


@router.get("/projects")
def projects(_: User = Depends(require_any(CHECK_SCREENS, "View")), db: Session = Depends(get_db)):
    return [{"project_id": p.project_id, "name_ar": p.name_ar}
            for p in db.scalars(select(Project).where(Project.is_active == True).order_by(Project.name_ar))]


@router.get("/payable-settlements")
def payable_settlements(_: User = Depends(require_any(CHECK_SCREENS, "Add")), db: Session = Depends(get_db)):
    """Posted subcontractor settlements, with only their unpaid balances offered for cheque linking."""
    rows = db.scalars(select(ContractSettlement).where(
        ContractSettlement.settlement_side == "Subcontractor",
        ContractSettlement.status == "Posted",
        ContractSettlement.net_amount > 0
    ).order_by(ContractSettlement.settlement_date.desc(), ContractSettlement.settlement_id.desc()).limit(1000)).all()
    result = []
    for settlement in rows:
        paid = db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
            TreasuryTransaction.settlement_id == settlement.settlement_id,
            TreasuryTransaction.status == "تم الصرف")) or Decimal("0")
        remaining = max(Decimal("0"), Decimal(settlement.net_amount or 0) - Decimal(paid))
        if remaining <= 0:
            continue
        contract = db.get(Contract, settlement.contract_id)
        result.append({"settlement_id": settlement.settlement_id, "settlement_no": settlement.settlement_no,
                       "contract_no": contract.contract_no if contract else "", "counterparty_name": settlement.counterparty_name,
                       "net_amount": money(settlement.net_amount), "paid_amount": money(paid),
                       "remaining_amount": money(remaining)})
    return {"items": result}


def _acc(db: Session, sc: str) -> TreasuryAccount | None:
    return db.scalar(select(TreasuryAccount).where(TreasuryAccount.checks_screen_code == sc))


def _need(db: Session, sc: str) -> TreasuryAccount:
    a = _acc(db, sc)
    if a is None:
        raise HTTPException(404, "دفتر الشيكات ده لسه مش مربوط بحساب بنك")
    return a


@router.get("/{screen_code}/account")
def get_account(screen_code: str, _: User = Depends(require_dynamic("View", CHECK_SCREENS)),
                db: Session = Depends(get_db)):
    a = _acc(db, screen_code)
    cash_bank_classes = select(AccountClassification.classification_id).where(
        AccountClassification.name_ar == "نقدية بالصندوق و البنوك")
    bank_gl_accounts = select(Account.account_id).where(Account.is_active == True,
                                                         Account.classification_id.in_(cash_bank_classes))
    banks = [{"treasury_account_id": b.treasury_account_id, "name_ar": b.name_ar, "currency_code": b.currency_code}
             for b in db.scalars(select(TreasuryAccount).where(TreasuryAccount.account_type == "Bank",
                                                               TreasuryAccount.currency_code == CHECK_CURRENCY[screen_code],
                                                               TreasuryAccount.gl_account_id.in_(bank_gl_accounts),
                                                               TreasuryAccount.checks_screen_code.is_(None)))]
    return {"account": {"treasury_account_id": a.treasury_account_id, "name_ar": a.name_ar,
                        "currency_code": a.currency_code} if a else None, "available_banks": banks}


@router.post("/{screen_code}/account")
def link_account(screen_code: str, body: LinkIn, user: User = Depends(require_dynamic("Add", CHECK_SCREENS)),
                 db: Session = Depends(get_db)):
    if _acc(db, screen_code):
        raise HTTPException(409, "الدفتر مربوط بحساب قبل كده")
    a = db.get(TreasuryAccount, body.treasury_account_id)
    if a is None or a.account_type != "Bank":
        raise HTTPException(400, "حساب البنك غير صحيح")
    if a.currency_code != CHECK_CURRENCY[screen_code]:
        raise HTTPException(400, "عملة حساب البنك لا تطابق دفتر الشيكات")
    gl = db.get(Account, a.gl_account_id)
    cash_bank_class = db.scalar(select(AccountClassification.classification_id).where(
        AccountClassification.name_ar == "نقدية بالصندوق و البنوك"))
    if gl is None or not gl.is_active or gl.classification_id != cash_bank_class:
        raise HTTPException(400, "اربط حساب البنك أولًا بحساب من تصنيف نقدية الصندوق والبنوك")
    if a.checks_screen_code:
        raise HTTPException(409, "الحساب ده مربوط بدفتر شيكات تاني")
    a.checks_screen_code = screen_code
    write_audit(db, user.user_id, "Update", "TreasuryAccounts", a.treasury_account_id, None, {"checks": screen_code})
    db.commit()
    return {"treasury_account_id": a.treasury_account_id, "name_ar": a.name_ar}


def _words(amount, currency) -> str | None:
    if amount is None:
        return None
    try:
        # Match the cheque workbook's wording for the dual-million amount.
        return (amount_in_words(amount, currency)
                .replace("مليونا جنيه", "مليونان جنيه")
                .replace("مليونا دولار", "مليونان دولار"))
    except ValueError:
        return None


def _out(c: Check, bname: str | None, pname: str | None, t: TreasuryAccount | None = None,
         bacc: str | None = None, settlement_no: str | None = None, db: Session | None = None) -> dict:
    beneficiary = db.get(Beneficiary, c.beneficiary_id) if db is not None else None
    beneficiary_gl = db.get(Account, beneficiary.linked_account_id) if beneficiary and beneficiary.linked_account_id else None
    bank_gl = db.get(Account, t.gl_account_id) if db is not None and t is not None else None
    def account_label(account):
        return (f"{account.account_code} — {account.account_name_ar}"
                if account is not None else "حساب غير مربوط")
    from_account = account_label(bank_gl)
    to_account = account_label(beneficiary_gl)
    out = {"check_id": c.check_id, "check_book_no": c.check_book_no, "sequence_no": c.sequence_no,
           "check_no": c.check_no, "check_date": c.check_date, "beneficiary_id": c.beneficiary_id,
           "beneficiary": bname, "amount": money(c.amount) if c.amount is not None else None,
           "amount_words": _words(c.amount, t.currency_code if t else "EGP"),
           "purchase_order_no": c.purchase_order_no, "project_id": c.project_id, "project": pname,
           "settlement_id": c.settlement_id, "settlement_no": settlement_no,
           "description": c.description, "print_date": c.print_date, "delivery_date": c.delivery_date,
           "cash_date": c.cash_date, "status": c.status, "next_statuses": sorted(NEXT.get(c.status, set())),
           "from_account_id": bank_gl.account_id if bank_gl else None,
           "to_account_id": beneficiary_gl.account_id if beneficiary_gl else None,
           "from_account_label": from_account, "to_account_label": to_account,
           "flow_stage": "عند الصرف"}
    if t is not None:
        out.update({"bank": t.name_ar, "bank_account_no": t.bank_account_number, "currency_code": t.currency_code,
                    "beneficiary_account_no": bacc, "treasury_account_id": t.treasury_account_id})
    return out


_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _norm(v: str | None) -> str:
    """يشيل المسافات ويحوّل الأرقام الهندية (٠-٩) لأرقام عادية عشان البحث يطابق."""
    return (v or "").strip().translate(_DIGITS)


def _esc_like(v: str) -> str:
    return v.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class Filters(BaseModel):
    status: str | None = None
    q: str | None = None
    account_no: str | None = None   # تطابق كامل مع رقم حساب البنك أو رقم حساب المستفيد (مش جزء من الرقم)
    check_no: str | None = None     # تطابق كامل
    beneficiary: str | None = None  # جزء من الاسم
    bank_id: int | None = None


def _select_checks():
    return (select(Check, Beneficiary.name_ar.label("bname"), Project.name_ar.label("pname"),
                   TreasuryAccount, Beneficiary.bank_account_number.label("bacc"))
            .join(Beneficiary, Beneficiary.beneficiary_id == Check.beneficiary_id)
            .join(TreasuryAccount, TreasuryAccount.treasury_account_id == Check.treasury_account_id)
            .outerjoin(Project, Project.project_id == Check.project_id))


def _apply(stmt, account_ids: list[int], f: Filters):
    stmt = stmt.where(Check.treasury_account_id.in_(account_ids))
    if f.bank_id:
        stmt = stmt.where(Check.treasury_account_id == f.bank_id)
    if f.status:
        stmt = stmt.where(Check.status == f.status)
    if _norm(f.account_no):
        n = _norm(f.account_no)
        stmt = stmt.where(or_(TreasuryAccount.bank_account_number == n, Beneficiary.bank_account_number == n))
    if _norm(f.check_no):
        stmt = stmt.where(Check.check_no == _norm(f.check_no))
    if (f.beneficiary or "").strip():
        stmt = stmt.where(Beneficiary.name_ar.ilike(f"%{_esc_like(f.beneficiary.strip())}%", escape="\\"))
    if (f.q or "").strip():
        like = f"%{_esc_like(f.q.strip())}%"
        stmt = stmt.where(or_(Check.check_no.ilike(like, escape="\\"), Beneficiary.name_ar.ilike(like, escape="\\"),
                              Check.description.ilike(like, escape="\\"),
                              Check.purchase_order_no.ilike(like, escape="\\")))
    return stmt


def _run(db: Session, account_ids: list[int], f: Filters, skip: int, limit: int) -> dict:
    stmt = _apply(_select_checks(), account_ids, f)
    total = db.scalar(select(func.count()).select_from(stmt.with_only_columns(Check.check_id).subquery())) or 0
    rows = db.execute(stmt.order_by(TreasuryAccount.name_ar, Check.check_book_no, Check.sequence_no)
                      .offset(skip).limit(limit)).all()
    settlement_ids = {c.settlement_id for c, *_ in rows if c.settlement_id is not None}
    settlement_numbers = {x.settlement_id: x.settlement_no for x in db.scalars(
        select(ContractSettlement).where(ContractSettlement.settlement_id.in_(settlement_ids))).all()} if settlement_ids else {}
    sums = db.execute(_apply(select(Check.status, TreasuryAccount.currency_code, func.count(),
                                    func.coalesce(func.sum(Check.amount), 0))
                             .join(Beneficiary, Beneficiary.beneficiary_id == Check.beneficiary_id)
                             .join(TreasuryAccount, TreasuryAccount.treasury_account_id == Check.treasury_account_id),
                             account_ids, f).group_by(Check.status, TreasuryAccount.currency_code)).all()
    return {"total": total, "statuses": STATUSES,
            "summary": [{"status": s, "currency_code": cur, "count": n, "amount": money(v)} for s, cur, n, v in sums],
            "items": [_out(c, b, p, t, ba, settlement_numbers.get(c.settlement_id), db) for c, b, p, t, ba in rows]}


def _filters(status: str | None = None, q: str | None = None, account_no: str | None = None,
             check_no: str | None = None, beneficiary: str | None = None, bank_id: int | None = None) -> Filters:
    return Filters(status=status, q=q, account_no=account_no, check_no=check_no, beneficiary=beneficiary,
                   bank_id=bank_id)


def _books(db: Session, user: User, actions: tuple[str, ...], screen: str | None = None) -> list[TreasuryAccount]:
    """دفاتر الشيكات المربوطة اللي المستخدم عنده عليها كل الصلاحيات المطلوبة (وممكن نحدد دفتر واحد)."""
    if screen is not None and screen not in CHECK_SCREENS:
        raise HTTPException(404, "الشاشة غير موجودة")
    books = [a for a in db.scalars(select(TreasuryAccount).where(TreasuryAccount.checks_screen_code.is_not(None)))
             if (screen is None or a.checks_screen_code == screen)
             and all(has_permission(db, user.user_id, a.checks_screen_code, act) for act in actions)]
    if screen is not None and not books:
        raise HTTPException(403, f"ليس لديك صلاحية ({screen}:{'/'.join(actions)}) أو الدفتر غير مربوط")
    return books


@router.get("/amount-words")
def amount_words(amount: str, currency: str = "EGP", _: User = Depends(require_any(CHECK_SCREENS, "View"))):
    """التفقيط التلقائي لقيمة الشيك (للمعاينة أثناء الكتابة)."""
    try:
        return {"amount_words": amount_in_words(amount, currency)}
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/search")
def search(screen: str | None = Query(None, description="كود دفتر الشيكات؛ بدونه يبحث في كل الدفاتر المسموحة"),
           f: Filters = Depends(_filters), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    books = _books(db, user, ("View",), screen)
    if not books:
        raise HTTPException(403, "ليس لديك صلاحية")
    r = _run(db, [b.treasury_account_id for b in books], f, skip, limit)
    r["banks"] = [{"treasury_account_id": b.treasury_account_id, "name_ar": b.name_ar,
                   "bank_account_number": b.bank_account_number, "currency_code": b.currency_code,
                   "screen_code": b.checks_screen_code} for b in books]
    return r


@router.get("/search/xlsx")
def search_xlsx(screen: str | None = None, f: Filters = Depends(_filters),
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """تصدير النتائج المفلترة فقط إلى Excel (يحتاج صلاحية Print + View على كل دفتر)."""
    books = _books(db, user, ("View", "Print"), screen)
    if not books:
        raise HTTPException(403, "ليس لديك صلاحية الطباعة/التصدير")
    r = _run(db, [b.treasury_account_id for b in books], f, 0, 5001)
    if len(r["items"]) > 5000:
        raise HTTPException(400, "النتائج أكتر من 5000 شيك — ضيّق الفلتر")
    data = _build_xlsx(r["items"], f)
    write_audit(db, user.user_id, "Print", "Checks", "export-xlsx", None,
                {"rows": len(r["items"]), "filters": f.model_dump(exclude_none=True), "screen": screen})
    db.commit()
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="checks.xlsx"'})


def _build_xlsx(items: list[dict], f: Filters) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "الشيكات"
    ws.sheet_view.rightToLeft = True
    heads = ["الدفتر", "م", "رقم الشيك", "التاريخ", "البنك", "رقم حساب البنك", "المستفيد", "رقم حساب المستفيد",
             "المبلغ", "العملة", "التفقيط", "أمر الشراء", "المشروع", "البيان", "الحالة"]
    ws.append(heads)
    for c in items:
        ws.append([c["check_book_no"], c["sequence_no"], c["check_no"], c["check_date"], c.get("bank"),
                   c.get("bank_account_no"), c["beneficiary"], c.get("beneficiary_account_no"),
                   float(c["amount"]) if c["amount"] is not None else None, c.get("currency_code"),
                   c["amount_words"], c["purchase_order_no"], c["project"], c["description"], c["status"]])
    fill = PatternFill("solid", fgColor="1F3A68")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = "s"  # نص صريح: يمنع تفسير أي قيمة تبدأ بـ = أو + كمعادلة
            if cell.column in (6, 8, 3):
                cell.number_format = "@"  # أرقام الحسابات والشيكات نصوص (أصفار البداية تفضل)
        row[8].number_format = "#,##0.00"
        row[3].number_format = "yyyy-mm-dd"
    for col, w in zip("ABCDEFGHIJKLMNO", (10, 6, 14, 12, 24, 20, 28, 20, 16, 8, 55, 16, 22, 34, 14)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:O{max(ws.max_row, 2)}"
    info = wb.create_sheet("الفلاتر")
    info.sheet_view.rightToLeft = True
    labels = {"account_no": "رقم الحساب", "check_no": "رقم الشيك", "beneficiary": "المستفيد", "status": "الحالة",
              "q": "بحث عام", "bank_id": "رقم البنك (داخلي)"}
    applied = [(labels[k], v) for k, v in f.model_dump(exclude_none=True).items() if str(v).strip()]
    info.append(["الفلتر", "القيمة"])
    for row in applied or [("بدون فلاتر", "كل الشيكات")]:
        info.append(list(row))
    info.append(["عدد الشيكات", len(items)])
    info.column_dimensions["A"].width = 24
    info.column_dimensions["B"].width = 30
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@router.get("/{screen_code}/items")
def items(screen_code: str, f: Filters = Depends(_filters),
          skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
          _: User = Depends(require_dynamic("View", CHECK_SCREENS)), db: Session = Depends(get_db)):
    a = _need(db, screen_code)
    return _run(db, [a.treasury_account_id], f, skip, limit)


# ----------------------------- قالب طباعة الشيك (مقاس + مواضع + إزاحة عامة) -----------------------------
# المقاس والإزاحة العامة بيتخزنوا كصفين خاصين في نفس الجدول: _page (X=العرض، Y=الطول) و _offset (X,Y بالمليمتر).
# ترتيب ومواضع ابتدائية مستوحاة من نموذج الشيك المرسل (تظل قابلة للمعايرة لكل حساب بنك).
PRINT_FIELDS = ("check_date", "payee_note", "beneficiary", "amount_words", "amount_number", "signatory_1", "signatory_2")
CORE_PRINT_FIELDS = ("check_date", "beneficiary", "amount_number", "amount_words")
_PRINT_DEFAULT = {"page_w": 184.2, "page_h": 76.2, "offset_x": 0.0, "offset_y": 0.0, "fields": [
    {"name": "check_date", "x": 170.0, "y": 10.0, "font_size": 11.0, "align": "Right"},
    {"name": "payee_note", "x": 125.0, "y": 21.0, "font_size": 12.0, "align": "Right"},
    {"name": "beneficiary", "x": 170.0, "y": 30.0, "font_size": 12.0, "align": "Right"},
    {"name": "amount_words", "x": 170.0, "y": 42.0, "font_size": 12.0, "align": "Right"},
    {"name": "amount_number", "x": 180.0, "y": 51.0, "font_size": 13.0, "align": "Right"},
    {"name": "signatory_1", "x": 170.0, "y": 68.0, "font_size": 9.0, "align": "Right"},
    {"name": "signatory_2", "x": 115.0, "y": 68.0, "font_size": 9.0, "align": "Center"}]}


class PrintFieldIn(BaseModel):
    name: Literal["check_date", "payee_note", "beneficiary", "amount_number", "amount_words", "signatory_1", "signatory_2"]
    x: float = Field(ge=-50, le=500)
    y: float = Field(ge=-50, le=500)
    font_size: float = Field(ge=6, le=48)
    align: Literal["Left", "Center", "Right"]
    text: str | None = Field(default=None, max_length=200)


class PrintTemplateIn(BaseModel):
    page_w: float = Field(ge=50, le=400)
    page_h: float = Field(ge=30, le=400)
    offset_x: float = Field(ge=-30, le=30)
    offset_y: float = Field(ge=-30, le=30)
    fields: list[PrintFieldIn]


def _template_out(db: Session, tid: int) -> dict:
    rows = {r.field_name: r for r in db.scalars(select(CheckPrintTemplate).where(CheckPrintTemplate.treasury_account_id == tid))}
    out = {**_PRINT_DEFAULT, "fields": [dict(f) for f in _PRINT_DEFAULT["fields"]], "saved": bool(rows)}
    if "_page" in rows:
        out["page_w"], out["page_h"] = float(rows["_page"].pos_x), float(rows["_page"].pos_y)
    if "_offset" in rows:
        out["offset_x"], out["offset_y"] = float(rows["_offset"].pos_x), float(rows["_offset"].pos_y)
    for f in out["fields"]:
        r = rows.get(f["name"])
        if r is not None:
            f.update(x=float(r.pos_x), y=float(r.pos_y), font_size=float(r.font_size), align=r.alignment)
            # Move templates still using the original left-side default to the cheque's right edge.
            if f["name"] == "amount_number" and float(r.pos_x) <= 50 and r.alignment == "Left":
                f.update(x=180.0, align="Right")
            if f["name"] in ("signatory_1", "signatory_2") and r.text_value:
                f["text"] = r.text_value
        if f["name"] in ("signatory_1", "signatory_2"):
            f.setdefault("text", "أسامه شوقت حافظ خليل" if f["name"] == "signatory_1" else "محمد احمد محمد مصطفى")
    return out


@router.get("/{screen_code}/print-template")
def get_print_template(screen_code: str, _: User = Depends(require_dynamic("View", CHECK_SCREENS)),
                       db: Session = Depends(get_db)):
    return _template_out(db, _need(db, screen_code).treasury_account_id)


@router.get("/{screen_code}/signatories")
def signatories(screen_code: str, _: User = Depends(require_dynamic("View", CHECK_SCREENS)),
                db: Session = Depends(get_db)):
    """Searchable list of active system users; custom signer names remain editable in the print dialog."""
    _need(db, screen_code)
    names = db.scalars(select(User.full_name).where(User.is_active == True).order_by(User.full_name)).all()
    return {"items": sorted({name.strip() for name in names if name and name.strip()}, key=str.casefold)}


@router.put("/{screen_code}/print-template")
def put_print_template(screen_code: str, body: PrintTemplateIn,
                       user: User = Depends(require_dynamic("Edit", CHECK_SCREENS)), db: Session = Depends(get_db)):
    a = _need(db, screen_code)
    names = [f.name for f in body.fields]
    # Keep compatibility with older clients that only send the original four
    # data fields; the workbook-inspired static fields retain their defaults.
    if len(names) != len(set(names)) or sorted(names) not in (sorted(CORE_PRINT_FIELDS), sorted(PRINT_FIELDS)):
        raise HTTPException(422, "أرسل حقول الشيك الأساسية أو الحقول السبعة كاملة")
    old = _template_out(db, a.treasury_account_id)
    D = lambda v: Decimal(str(round(v, 2)))  # noqa: E731
    wanted = {"_page": (D(body.page_w), D(body.page_h), Decimal("11"), "Left", None),
              "_offset": (D(body.offset_x), D(body.offset_y), Decimal("11"), "Left", None),
              **{f.name: (D(f.x), D(f.y), D(f.font_size), f.align, f.text if f.name in ("signatory_1", "signatory_2") else None) for f in body.fields}}
    existing = {r.field_name: r for r in db.scalars(
        select(CheckPrintTemplate).where(CheckPrintTemplate.treasury_account_id == a.treasury_account_id))}
    for name, (x, y, size, align, text_value) in wanted.items():
        r = existing.get(name)
        if r is None:
            db.add(CheckPrintTemplate(treasury_account_id=a.treasury_account_id, field_name=name,
                                      pos_x=x, pos_y=y, font_size=size, alignment=align, text_value=text_value))
        else:
            r.pos_x, r.pos_y, r.font_size, r.alignment = x, y, size, align
            r.text_value = text_value
    write_audit(db, user.user_id, "Update", "CheckPrintTemplates", a.treasury_account_id, old, body.model_dump())
    db.commit()
    return _template_out(db, a.treasury_account_id)


def _chk(db: Session, screen_code: str, cid: int, for_update: bool = False) -> Check:
    a = _need(db, screen_code)
    stmt = select(Check).where(Check.check_id == cid)
    if for_update:
        stmt = stmt.with_for_update()
    c = db.scalar(stmt)
    if c is None or c.treasury_account_id != a.treasury_account_id:
        raise HTTPException(404, "الشيك غير موجود")
    return c


def _refs(db: Session, body: CheckIn):
    if db.get(Beneficiary, body.beneficiary_id) is None:
        raise HTTPException(400, "المستفيد غير موجود")
    if body.project_id is not None and db.get(Project, body.project_id) is None:
        raise HTTPException(400, "مركز التكلفة غير موجود")
    if body.settlement_id is not None:
        settlement = db.get(ContractSettlement, body.settlement_id)
        if settlement is None or settlement.settlement_side != "Subcontractor" or settlement.status != "Posted":
            raise HTTPException(400, "اختر مستخلصًا ماليًا مرحّلًا لمقاول من الباطن")


@router.post("/{screen_code}/items", status_code=201)
def create(screen_code: str, body: CheckIn, user: User = Depends(require_dynamic("Add", CHECK_SCREENS)),
           db: Session = Depends(get_db)):
    a = _need(db, screen_code)
    _refs(db, body)
    c = Check(treasury_account_id=a.treasury_account_id, status="جديد", **body.model_dump())
    db.add(c)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "رقم الدفتر والتسلسل موجودين قبل كده")
    db.add(CheckStatusHistory(check_id=c.check_id, old_status=None, new_status="جديد", changed_by=user.user_id))
    write_audit(db, user.user_id, "Create", "Checks", c.check_id, None, body.model_dump())
    db.commit()
    return {"check_id": c.check_id}


@router.put("/{screen_code}/items/{cid}")
def update(screen_code: str, cid: int, body: CheckIn, user: User = Depends(require_dynamic("Edit", CHECK_SCREENS)),
           db: Session = Depends(get_db)):
    c = _chk(db, screen_code, cid)
    if c.status in ("تم الصرف", "ملغي"):
        raise HTTPException(409, "مينفعش تعدّل شيك مصروف أو ملغي")
    if c.status not in ("جديد", "مطبوع") and c.settlement_id != body.settlement_id:
        raise HTTPException(409, "مينفعش تغيير المستخلص المرتبط بعد تسليم الشيك")
    _refs(db, body)
    old = {"amount": str(c.amount), "beneficiary_id": c.beneficiary_id, "check_no": c.check_no}
    for k, v in body.model_dump().items():
        setattr(c, k, v)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "رقم الدفتر والتسلسل موجودين قبل كده")
    write_audit(db, user.user_id, "Update", "Checks", cid, old, body.model_dump())
    db.commit()
    return {"check_id": cid}


@router.post("/{screen_code}/items/{cid}/status")
def change_status(screen_code: str, cid: int, body: StatusIn,
                  user: User = Depends(require_dynamic("Edit", CHECK_SCREENS)), db: Session = Depends(get_db)):
    c = _chk(db, screen_code, cid, for_update=True)
    if body.status not in NEXT.get(c.status, set()):
        raise HTTPException(409, f"مينفعش الانتقال من «{c.status}» إلى «{body.status}»")
    if body.status in ("مطبوع", "تم التسليم", "تم الصرف") and not (c.amount and c.amount > 0):
        raise HTTPException(422, "لازم تحدد مبلغ الشيك الأول")
    today = date.today()
    old = c.status

    # الصرف ينشئ حركة بنك وقيد يومية مرة واحدة فقط، داخل نفس transaction.
    # المرجع الثابت يمنع تكرار الحركة عند إعادة الطلب أو تكرار تغيير الحالة.
    if body.status == "تم الصرف":
        if c.amount is None or c.amount <= 0:
            raise HTTPException(422, "لازم تحدد مبلغ الشيك الأول")
        voucher = f"CHK-{c.check_id}"
        existing = db.scalar(select(TreasuryTransaction).where(TreasuryTransaction.voucher_no == voucher))
        if existing is not None:
            raise HTTPException(409, "تم إنشاء حركة البنك لهذا الشيك بالفعل؛ لن يتم إنشاء قيد أو حركة مكررة")

        linked_settlement = None
        if c.settlement_id is not None:
            linked_settlement = db.scalar(select(ContractSettlement).where(
                ContractSettlement.settlement_id == c.settlement_id).with_for_update())
            if linked_settlement is None or linked_settlement.status != "Posted" or linked_settlement.settlement_side != "Subcontractor":
                raise HTTPException(409, "المستخلص المرتبط غير مرحّل أو لم يعد مستحقًا للصرف")
            contract = db.get(Contract, linked_settlement.contract_id)
            party = db.get(Counterparty, linked_settlement.counterparty_id) if linked_settlement.counterparty_id else (
                db.get(Counterparty, contract.counterparty_id) if contract and contract.counterparty_id else None)
            if party and (party.linked_account_id or party.account_id):
                if db.get(Beneficiary, c.beneficiary_id).linked_account_id != (party.linked_account_id or party.account_id):
                    raise HTTPException(409, "حساب المستفيد لا يطابق حساب المقاول المرتبط بالمستخلص")
            paid = db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
                TreasuryTransaction.settlement_id == linked_settlement.settlement_id,
                TreasuryTransaction.status == "تم الصرف")) or Decimal("0")
            remaining = Decimal(linked_settlement.net_amount or 0) - Decimal(paid)
            if Decimal(c.amount) > remaining:
                raise HTTPException(409, f"قيمة الشيك تتجاوز المتبقي من المستخلص ({money(max(Decimal('0'), remaining))})")

        beneficiary = db.get(Beneficiary, c.beneficiary_id)
        if beneficiary is None or beneficiary.linked_account_id is None:
            raise HTTPException(409, "اربط المستفيد بحسابه في دليل الحسابات قبل صرف الشيك")
        beneficiary_account = db.get(Account, beneficiary.linked_account_id)
        bank_account = db.get(Account, _need(db, screen_code).gl_account_id)
        if beneficiary_account is None or not beneficiary_account.is_active:
            raise HTTPException(409, "حساب المستفيد المحاسبي غير موجود أو غير نشط")
        if bank_account is None or not bank_account.is_active:
            raise HTTPException(409, "حساب الأستاذ المرتبط بالبنك غير موجود أو غير نشط")
        fy = db.scalar(select(FiscalYear).where(FiscalYear.start_date <= today, FiscalYear.end_date >= today))
        if fy is None:
            raise HTTPException(409, f"مفيش سنة مالية تشمل تاريخ {today} — أضف سنة مالية الأول")
        if fy.is_closed:
            raise HTTPException(409, "السنة المالية مقفولة")
        if beneficiary_account.account_id == bank_account.account_id:
            raise HTTPException(422, "حساب المستفيد لا يمكن أن يكون نفس حساب البنك")

        # رقم القيد متوافق مع تنسيق شاشة القيود.
        prefix = f"JE-{fy.start_date.year}-"
        last_no = db.scalar(select(func.max(JournalEntry.entry_no)).where(JournalEntry.entry_no.like(prefix + "%")))
        seq = int(last_no[len(prefix):]) + 1 if last_no and last_no[len(prefix):].isdigit() else 1
        entry_no = f"{prefix}{seq:06d}"
        # Debit beneficiary/payable account, credit bank account.
        entry = JournalEntry(entry_no=entry_no, entry_date=today, company_id=fy.company_id,
                             fiscal_year_id=fy.fiscal_year_id,
                             description=f"صرف شيك رقم {c.check_no or c.sequence_no} للمستفيد {beneficiary.name_ar}",
                             status="Posted", created_by=user.user_id, posted_by=user.user_id, posted_at=utcnow())
        db.add(entry)
        db.flush()
        amount = Decimal(c.amount)
        db.add_all([
            JournalEntryDetail(journal_entry_id=entry.journal_entry_id, line_no=1,
                               account_id=beneficiary_account.account_id, project_id=c.project_id,
                               debit_amount=amount, credit_amount=Decimal("0"),
                               description=f"صرف شيك {c.check_no or c.sequence_no}"),
            JournalEntryDetail(journal_entry_id=entry.journal_entry_id, line_no=2,
                               account_id=bank_account.account_id, project_id=c.project_id,
                               debit_amount=Decimal("0"), credit_amount=amount,
                               description=f"صرف شيك {c.check_no or c.sequence_no}")
        ])
        tx = TreasuryTransaction(treasury_account_id=c.treasury_account_id,
                                 transaction_date=today, inflow=Decimal("0"), outflow=amount,
                                 description=f"صرف شيك {c.check_no or c.sequence_no} للمستفيد {beneficiary.name_ar}",
                                 voucher_no=voucher, status="تم الصرف", recipient_name=beneficiary.name_ar,
                                 project_id=c.project_id or (contract.project_id if c.settlement_id and contract else None),
                                 settlement_id=c.settlement_id,
                                 counterparty_id=linked_settlement.counterparty_id if linked_settlement else None,
                                 counterpart_account_id=beneficiary_account.account_id,
                                 journal_entry_id=entry.journal_entry_id)
        db.add(tx)
        db.flush()

    c.status = body.status
    if body.status == "مطبوع":
        c.print_date = today
    elif body.status == "تم التسليم":
        c.delivery_date = c.delivery_date or today
    elif body.status == "تم الصرف":
        c.cash_date = today
    db.add(CheckStatusHistory(check_id=cid, old_status=old, new_status=body.status, changed_by=user.user_id))
    write_audit(db, user.user_id, "Update", "Checks", cid, {"status": old}, {"status": body.status})
    if body.status == "تم الصرف":
        write_audit(db, user.user_id, "Create", "TreasuryTransactions", tx.transaction_id,
                    None, {"voucher_no": voucher, "outflow": str(c.amount), "journal_entry_id": entry.journal_entry_id})
        write_audit(db, user.user_id, "Post", "JournalEntries", entry.journal_entry_id,
                    None, {"entry_no": entry.entry_no, "status": "Posted", "source_check_id": c.check_id})
    db.commit()
    result = {"check_id": cid, "status": c.status}
    if body.status == "تم الصرف":
        result.update({"transaction_id": tx.transaction_id, "journal_entry_id": entry.journal_entry_id,
                       "entry_no": entry.entry_no, "voucher_no": voucher})
    return result


@router.delete("/{screen_code}/items/{cid}", status_code=204)
def delete(screen_code: str, cid: int, user: User = Depends(require_dynamic("Delete", CHECK_SCREENS)),
           db: Session = Depends(get_db)):
    c = _chk(db, screen_code, cid)
    if c.status != "جديد":
        raise HTTPException(409, "الحذف للشيكات الجديدة بس — الباقي يتلغي")
    for h in db.scalars(select(CheckStatusHistory).where(CheckStatusHistory.check_id == cid)):
        db.delete(h)
    write_audit(db, user.user_id, "Delete", "Checks", cid, {"check_no": c.check_no}, None)
    db.flush()
    db.delete(c)
    db.commit()
