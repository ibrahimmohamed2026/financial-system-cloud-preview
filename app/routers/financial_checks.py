import csv, io
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .journal import _next_no
from .treasury import USD_TRANSACTION_TYPES
from ..common import require_any
from ..database import get_db
from ..deps import write_audit
from ..models import (Account, AccountClassification, Company, FiscalYear, FinancialCheck, JournalEntry,
                      JournalEntryDetail, Project, TreasuryAccount, TreasuryTransaction, User, utcnow,
                      FinancialCheckStatusHistory, FinancialCheckSettlementAllocation, ContractSettlement,
                      Contract, Counterparty)

SCREENS = {"FinancialChecks", "ChecksCib", "ChecksCairoEgp", "ChecksCairoUsd"}
router = APIRouter(prefix="/checks-register", tags=["Financial Checks"])

class CheckIn(BaseModel):
    check_number: str = Field(min_length=1, max_length=50)
    check_type: str
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    due_date: date
    party_account_id: int
    treasury_account_id: int
    drawee_bank: str | None = Field(default=None, max_length=200)
    project_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)

class StatusIn(BaseModel):
    status: str
    # Actual clearing date. Defaults to today and may not be in the future.
    settlement_date: date | None = None


STATUS_ALIASES = {"مُرتجع": "مرتد", "مرتجع": "مرتد"}
KNOWN_STATUSES = {
    "مسودة", "معتمد", "صادر", "تم التسليم", "تحت التحصيل",
    "تم التحصيل", "مُحصّل", "منصرف", "موقوف", "مرتد", "ملغي",
}


def canon_status(status: str | None) -> str | None:
    return STATUS_ALIASES.get(status, status)


def _party_classifications(check_type: str) -> set[str]:
    direction = "inflow" if check_type == "INCOMING" else "outflow"
    names: set[str] = set()
    for transaction in USD_TRANSACTION_TYPES.values():
        if transaction["direction"] == direction:
            names.update(transaction["classifications"])
    return names


def _validate_party_account(db: Session, check_type: str, party: Account | None) -> None:
    if party is None or not party.is_active:
        raise HTTPException(422, "حساب العميل/المورد غير صحيح أو غير نشط")
    if db.scalar(
        select(Account.account_id)
        .where(Account.parent_account_id == party.account_id)
        .limit(1)
    ) is not None:
        raise HTTPException(422, "حساب الطرف حساب رئيسي؛ اختر حسابًا فرعيًا من شجرة الحسابات")
    classification = db.get(AccountClassification, party.classification_id)
    if classification is None or classification.name_ar not in _party_classifications(check_type):
        kind = "الوارد" if check_type == "INCOMING" else "الصادر"
        name = classification.name_ar if classification else "—"
        raise HTTPException(422, f"تصنيف حساب الطرف ({name}) لا يناسب الشيك {kind}")


class ProjectLinkIn(BaseModel):
    project_id: int | None = Field(default=None, gt=0)

class AllocationIn(BaseModel):
    settlement_id: int = Field(gt=0)
    allocated_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)




def _flow_account_ids(check_type: str, party_account_id: int, bank_gl_account_id: int) -> tuple[int, int]:
    """Return (source, destination) GL accounts for the cheque's actual settlement."""
    if check_type == "INCOMING":
        return party_account_id, bank_gl_account_id
    if check_type == "OUTGOING":
        return bank_gl_account_id, party_account_id
    raise HTTPException(422, "نوع الشيك غير صحيح")


def out(c, db=None):
    bank = db.get(TreasuryAccount, c.treasury_account_id) if db is not None else None
    party = db.get(Account, c.party_account_id) if db is not None else None
    bank_gl = db.get(Account, bank.gl_account_id) if bank is not None else None
    source_id, destination_id = _flow_account_ids(
        c.check_type, c.party_account_id, bank.gl_account_id if bank is not None else 0)
    def label(account):
        return (f"{account.account_code} — {account.account_name_ar}"
                if account is not None else "حساب غير مربوط")
    source_account = party if c.check_type == "INCOMING" else bank_gl
    destination_account = bank_gl if c.check_type == "INCOMING" else party
    return {"check_id": c.check_id, "check_number": c.check_number, "check_type": c.check_type,
            "amount": str(c.amount), "due_date": str(c.due_date), "drawee_bank": c.drawee_bank,
            "status": c.status, "project_id": c.project_id, "party_account_id": c.party_account_id,
            "treasury_account_id": c.treasury_account_id, "journal_entry_id": c.journal_entry_id,
            "from_account_id": source_id, "to_account_id": destination_id,
            "from_account_label": label(source_account), "to_account_label": label(destination_account),
            "description": c.description}

@router.get("/options")
def options(_: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    return {"accounts": [{"id": a.account_id, "code": a.account_code, "name": a.account_name_ar}
            for a in db.scalars(select(Account).where(Account.is_active == True).order_by(Account.account_code))],
            "banks": [{"id": b.treasury_account_id, "name": b.name_ar, "gl_account_id": b.gl_account_id}
            for b in db.scalars(select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.account_type == "Bank", TreasuryAccount.currency_code == "EGP"))],
            "projects": [{"id": p.project_id, "name": p.name_ar} for p in db.scalars(
                select(Project).where(Project.is_active == True).order_by(Project.name_ar))],
            "bank_binding": {"active_bank_accounts": db.scalar(select(func.count()).select_from(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.account_type == "Bank", TreasuryAccount.currency_code == "EGP")) or 0,
                             "cib_accounts": sum(1 for b in db.scalars(select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.account_type == "Bank")) if b.currency_code == "EGP" and ("cib" in (b.name_ar or "").lower() or "التجاري" in (b.name_ar or "")))}}

@router.get("")
def list_checks(status: str | None = None, check_type: str | None = None, project_id: int | None = None,
                qtext: str | None = None, _: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    q = select(FinancialCheck).order_by(FinancialCheck.due_date.desc(), FinancialCheck.check_id.desc())
    if status: q = q.where(FinancialCheck.status == status)
    if check_type: q = q.where(FinancialCheck.check_type == check_type)
    if project_id is not None: q = q.where(FinancialCheck.project_id == project_id)
    if qtext: q = q.where(FinancialCheck.check_number.ilike(f"%{qtext[:80]}%"))
    return [out(c, db) for c in db.scalars(q.limit(2000))]

@router.post("", status_code=201)
def create(body: CheckIn, user: User = Depends(require_any(SCREENS, "Add")), db: Session = Depends(get_db)):
    if body.check_type not in ("INCOMING", "OUTGOING"): raise HTTPException(422, "نوع الشيك غير صحيح")
    party = db.get(Account, body.party_account_id); bank = db.get(TreasuryAccount, body.treasury_account_id)
    if not party or not party.is_active: raise HTTPException(422, "حساب العميل/المورد غير صحيح")
    _validate_party_account(db, body.check_type, party)
    if not bank or not bank.is_active or bank.account_type != "Bank" or bank.currency_code != "EGP": raise HTTPException(422, "اختر حسابًا بنكيًا نشطًا بالجنيه المصري؛ سجل الشيكات الحالي مقوّم بالجنيه")
    if body.project_id is not None:
        project = db.get(Project, body.project_id)
        if not project or not project.is_active: raise HTTPException(422, "المشروع المحدد غير موجود أو غير نشط")
    c = FinancialCheck(**body.model_dump(), status="مسودة", created_by=user.user_id)
    db.add(c)
    try:
        db.flush()
        db.add(FinancialCheckStatusHistory(check_id=c.check_id, old_status=None, new_status="مسودة", changed_by=user.user_id, note="إنشاء الشيك"))
        write_audit(db, user.user_id, "Create", "FinancialChecks", c.check_id, None, body.model_dump(mode="json"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "رقم الشيك مستخدم بالفعل")
    return out(c)

@router.post("/{cid}/status")
def set_status(cid: int, body: StatusIn, user: User = Depends(require_any(SCREENS, "Edit")), db: Session = Depends(get_db)):
    c = db.scalar(select(FinancialCheck).where(FinancialCheck.check_id == cid).with_for_update())
    if not c:
        raise HTTPException(404, "الشيك غير موجود")

    new_status = canon_status(body.status)
    if new_status not in KNOWN_STATUSES:
        raise HTTPException(422, "الحالة غير صحيحة")
    if new_status == canon_status(c.status):
        raise HTTPException(409, "الشيك بالفعل في هذه الحالة")
    allowed_next = _allowed_next_statuses(c.check_type, c.status)
    if new_status not in allowed_next:
        raise HTTPException(409, f"انتقال الحالة من {c.status} إلى {new_status} غير مسموح")

    settlement_statuses = {"تم التحصيل", "مُحصّل"} if c.check_type == "INCOMING" else {"منصرف"}
    if new_status in settlement_statuses:
        required_sources = {"تحت التحصيل"} if c.check_type == "INCOMING" else {"تم التسليم"}
        legacy_incoming_direct = c.check_type == "INCOMING" and new_status == "مُحصّل" and c.status == "مسودة"
        if c.status not in required_sources and not legacy_incoming_direct:
            raise HTTPException(409, "لا يمكن تسوية الشيك قبل اكتمال دورة الاستلام أو التسليم")
    if c.journal_entry_id and new_status != c.status:
        raise HTTPException(409, "الشيك له قيد مرحّل؛ لا تغيّر حالته قبل إجراء عكس محاسبي معتمد")

    if new_status in settlement_statuses:
        if c.journal_entry_id:
            raise HTTPException(409, "تم إنشاء القيد لهذا الشيك مسبقاً")
        today = date.today()
        entry_date = body.settlement_date or today
        if entry_date > today:
            raise HTTPException(422, "تاريخ التسوية لا يمكن أن يكون في المستقبل")
        fy = db.scalar(select(FiscalYear).where(FiscalYear.start_date <= entry_date, FiscalYear.end_date >= entry_date))
        if not fy or fy.is_closed:
            raise HTTPException(409, "لا توجد سنة مالية مفتوحة لتاريخ التسوية")
        bank = db.get(TreasuryAccount, c.treasury_account_id)
        party = db.get(Account, c.party_account_id)
        bank_gl = db.get(Account, bank.gl_account_id) if bank else None
        if not party or not party.is_active or not bank_gl or not bank_gl.is_active:
            raise HTTPException(409, "حساب العميل/المورد أو حساب البنك غير نشط")
        if not bank or bank.account_type != "Bank" or bank.currency_code != "EGP":
            raise HTTPException(409, "لا يمكن ترحيل شيك بالجنيه على حساب بنك بعملة مختلفة")
        if party.account_id == bank_gl.account_id:
            raise HTTPException(422, "حساب الطرف لا يمكن أن يكون نفس حساب البنك")
        voucher_no = f"FCHK-{c.check_id}"
        if db.scalar(select(TreasuryTransaction.transaction_id).where(TreasuryTransaction.voucher_no == voucher_no)):
            raise HTTPException(409, "حركة البنك مسجلة لهذا الشيك بالفعل؛ تم إيقاف الترحيل لمنع التكرار")
        entry = JournalEntry(entry_no=_next_no(db, fy), entry_date=entry_date, company_id=fy.company_id,
            fiscal_year_id=fy.fiscal_year_id, description=f"تسوية شيك {c.check_number}", status="Posted",
            created_by=user.user_id, posted_by=user.user_id, posted_at=utcnow())
        db.add(entry)
        db.flush()
        amount = Decimal(c.amount)
        # لا يتأثر البنك عند التسجيل أو الاعتماد أو الإصدار؛ فقط عند التحصيل/الصرف الفعلي.
        lines = [(bank_gl.account_id, amount, Decimal("0")), (party.account_id, Decimal("0"), amount)] if c.check_type == "INCOMING" else [(party.account_id, amount, Decimal("0")), (bank_gl.account_id, Decimal("0"), amount)]
        for n, (aid, debit, credit) in enumerate(lines, 1):
            db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id, line_no=n,
                account_id=aid, debit_amount=debit, credit_amount=credit, description=f"شيك {c.check_number}"))
        db.flush()
        c.journal_entry_id = entry.journal_entry_id
        if c.check_type == "INCOMING":
            db.add(TreasuryTransaction(treasury_account_id=c.treasury_account_id, transaction_date=entry_date,
                inflow=amount, outflow=Decimal("0"), description=f"تحصيل شيك {c.check_number}",
                voucher_no=voucher_no, status="تم التحصيل", counterpart_account_id=party.account_id, journal_entry_id=entry.journal_entry_id))
        else:
            # Preserve the cheque's single balanced journal entry while distributing
            # its bank payment across the linked settlement balances.
            allocations = db.scalars(select(FinancialCheckSettlementAllocation).where(
                FinancialCheckSettlementAllocation.check_id == c.check_id).order_by(
                    FinancialCheckSettlementAllocation.allocation_id)).all()
            allocated_total = sum((_money(a.allocated_amount) for a in allocations), Decimal("0.00"))
            if allocated_total > amount:
                raise HTTPException(409, "إجمالي تخصيصات الشيك تجاوز قيمته؛ أوقفنا الصرف")
            for allocation in allocations:
                db.add(TreasuryTransaction(treasury_account_id=c.treasury_account_id, transaction_date=entry_date,
                    inflow=Decimal("0"), outflow=_money(allocation.allocated_amount),
                    description=f"صرف شيك {c.check_number} للمستخلص {allocation.settlement_id}",
                    voucher_no=f"{voucher_no}-A{allocation.allocation_id}", status="تم الصرف",
                    settlement_id=allocation.settlement_id, journal_entry_id=entry.journal_entry_id))
            unallocated = _money(amount - allocated_total)
            if unallocated > 0:
                db.add(TreasuryTransaction(treasury_account_id=c.treasury_account_id, transaction_date=entry_date,
                    inflow=Decimal("0"), outflow=unallocated,
                    description=f"صرف غير موزع من شيك {c.check_number}", voucher_no=voucher_no,
                    status="تم الصرف", journal_entry_id=entry.journal_entry_id))
    old_status = c.status
    c.status = new_status
    db.add(FinancialCheckStatusHistory(check_id=cid, old_status=old_status, new_status=new_status, changed_by=user.user_id))
    write_audit(db, user.user_id, "Update", "FinancialChecks", cid, {"status": old_status}, {"status": new_status})
    db.commit()
    return out(c)

@router.post("/{cid}/project")
def set_project(cid: int, body: ProjectLinkIn, user: User = Depends(require_any(SCREENS, "Edit")), db: Session = Depends(get_db)):
    c = db.get(FinancialCheck, cid)
    if not c: raise HTTPException(404, "الشيك غير موجود")
    if c.journal_entry_id: raise HTTPException(409, "لا يمكن تغيير مشروع شيك مرحّل؛ حافظ على ارتباطه المحاسبي")
    if body.project_id is not None:
        project = db.get(Project, body.project_id)
        if not project or not project.is_active: raise HTTPException(422, "المشروع المحدد غير موجود أو غير نشط")
    old = c.project_id
    c.project_id = body.project_id
    write_audit(db, user.user_id, "UpdateProject", "FinancialChecks", cid,
                {"project_id": old}, {"project_id": c.project_id})
    db.commit()
    return out(c)

@router.get("/export.csv")
def export_csv(_: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    buf = io.StringIO(); w = csv.writer(buf); w.writerow(["check_number","check_type","amount","due_date","party_account_id","treasury_account_id","drawee_bank","project_id","description","status"])
    for c in db.scalars(select(FinancialCheck).order_by(FinancialCheck.check_id)): w.writerow([c.check_number,c.check_type,c.amount,c.due_date,c.party_account_id,c.treasury_account_id,c.drawee_bank or "",c.project_id or "",c.description or "",c.status])
    data = "\ufeff" + buf.getvalue()
    return StreamingResponse(iter([data.encode("utf-8")]), media_type="text/csv; charset=utf-8", headers={"Content-Disposition":"attachment; filename=financial_checks.csv"})

@router.post("/import.csv")
def import_csv(file: UploadFile = File(...), user: User = Depends(require_any(SCREENS, "Add")), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(415, "ارفع ملف CSV فقط")
    raw = file.file.read(5_000_001)
    if len(raw) > 5_000_000: raise HTTPException(413, "الملف أكبر من 5MB")
    try: rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    except Exception: raise HTTPException(400, "تعذر قراءة CSV بترميز UTF-8")
    if len(rows) > 5000: raise HTTPException(413, "الحد الأقصى 5000 صف")
    made = 0
    try:
        for r in rows:
            body = CheckIn(check_number=r["check_number"], check_type=r["check_type"], amount=Decimal(r["amount"]), due_date=r["due_date"], party_account_id=int(r["party_account_id"]), treasury_account_id=int(r["treasury_account_id"]), drawee_bank=r.get("drawee_bank") or None, project_id=int(r["project_id"]) if r.get("project_id") else None, description=r.get("description") or None)
            party = db.get(Account, body.party_account_id)
            bank = db.get(TreasuryAccount, body.treasury_account_id)
            if body.check_type not in ("INCOMING", "OUTGOING") or not party or not party.is_active or not bank or not bank.is_active or bank.account_type != "Bank" or bank.currency_code != "EGP":
                raise ValueError("نوع الشيك أو حساب الطرف أو حساب البنك بالجنيه غير صحيح")
            _validate_party_account(db, body.check_type, party)
            if body.project_id is not None:
                project = db.get(Project, body.project_id)
                if not project or not project.is_active: raise ValueError("المشروع غير صحيح أو غير نشط")
            imported_check = FinancialCheck(**body.model_dump(), status="مسودة", created_by=user.user_id)
            db.add(imported_check)
            db.flush()
            db.add(FinancialCheckStatusHistory(
                check_id=imported_check.check_id, old_status=None, new_status="مسودة",
                changed_by=user.user_id, note="استيراد الشيك"
            ))
            made += 1
        db.commit()
    except Exception as e:
        db.rollback(); raise HTTPException(422, f"فشل الاستيراد بالكامل دون حفظ جزئي: {str(e)[:180]}")
    return {"imported": made}


def _allowed_next_statuses(check_type: str, current_status: str) -> set[str]:
    incoming = {
        "مسودة": {"تحت التحصيل", "ملغي"},
        "تحت التحصيل": {"تم التحصيل", "مرتد"},
        "تم التحصيل": set(), "مرتد": set(), "ملغي": set(),
    }
    outgoing = {
        "مسودة": {"معتمد", "ملغي"},
        "معتمد": {"صادر", "ملغي"},
        "صادر": {"تم التسليم", "موقوف", "ملغي"},
        "تم التسليم": {"منصرف", "موقوف", "مرتد"},
        "موقوف": {"صادر", "ملغي"},
        "منصرف": set(), "مرتد": set(), "ملغي": set(),
    }
    # Legacy labels remain readable without allowing a new outgoing cheque
    # to bypass approval, issuance, and delivery.
    legacy_incoming = {
        "مسودة": {"مُحصّل", "مرتد"},
        "تحت التحصيل": {"مُحصّل", "مرتد"},
    }
    current_status = canon_status(current_status)
    transitions = incoming if check_type == "INCOMING" else outgoing
    legacy = legacy_incoming.get(current_status, set()) if check_type == "INCOMING" else set()
    return set(transitions.get(current_status, set())) | set(legacy)


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _reserved_allocations_stmt(settlement_id: int):
    """Only unpaid, non-cancelled cheques reserve settlement balance."""
    return (
        select(func.coalesce(func.sum(FinancialCheckSettlementAllocation.allocated_amount), 0))
        .select_from(FinancialCheckSettlementAllocation)
        .join(FinancialCheck, FinancialCheck.check_id == FinancialCheckSettlementAllocation.check_id)
        .where(
            FinancialCheckSettlementAllocation.settlement_id == settlement_id,
            FinancialCheck.status.notin_(("منصرف", "مرتد", "مُرتجع", "مرتجع", "ملغي")),
        )
    )


def _allocations_out(db: Session, check_id: int):
    rows = db.execute(
        select(FinancialCheckSettlementAllocation, ContractSettlement)
        .join(ContractSettlement, ContractSettlement.settlement_id == FinancialCheckSettlementAllocation.settlement_id)
        .where(FinancialCheckSettlementAllocation.check_id == check_id)
        .order_by(FinancialCheckSettlementAllocation.allocation_id)
    ).all()
    return [{
        "allocation_id": a.allocation_id,
        "settlement_id": s.settlement_id,
        "settlement_no": s.settlement_no,
        "contract_id": s.contract_id,
        "allocated_amount": str(_money(a.allocated_amount)),
        "settlement_net_amount": str(_money(s.net_amount)),
    } for a, s in rows]


@router.get("/{cid}/allocations")
def list_allocations(cid: int, _: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    if not db.get(FinancialCheck, cid):
        raise HTTPException(404, "الشيك غير موجود")
    return {"items": _allocations_out(db, cid)}


@router.post("/{cid}/allocations", status_code=201)
def add_allocation(cid: int, body: AllocationIn,
                   user: User = Depends(require_any(SCREENS, "Edit")), db: Session = Depends(get_db)):
    check = db.scalar(select(FinancialCheck).where(FinancialCheck.check_id == cid).with_for_update())
    if not check:
        raise HTTPException(404, "الشيك غير موجود")
    if check.check_type != "OUTGOING":
        raise HTTPException(422, "تخصيص المستخلصات متاح للشيكات الصادرة فقط")
    if check.status not in ("مسودة", "معتمد", "صادر"):
        raise HTTPException(409, "لا يمكن تعديل تخصيصات الشيك بعد تسليمه أو تسويته")
    settlement = db.scalar(select(ContractSettlement).where(
        ContractSettlement.settlement_id == body.settlement_id).with_for_update())
    if not settlement:
        raise HTTPException(404, "المستخلص غير موجود")
    if settlement.settlement_side != "Subcontractor" or settlement.status not in ("Approved", "Posted"):
        raise HTTPException(409, "يجب اختيار مستخلص مقاول باطن معتمد نهائيًا")
    if not settlement.manager_approved_by or not settlement.manager_approved_at:
        raise HTTPException(409, "المستخلص لم يحصل على اعتماد المدير النهائي")
    contract = db.get(Contract, settlement.contract_id)
    if not contract or contract.status.lower() != "active":
        raise HTTPException(409, "عقد المستخلص غير موجود أو غير نشط")
    if settlement.counterparty_id is not None and contract.counterparty_id != settlement.counterparty_id:
        raise HTTPException(409, "المقاول المسجل في المستخلص لا يطابق المقاول المرتبط بالعقد")
    if check.project_id is not None and contract.project_id is not None and check.project_id != contract.project_id:
        raise HTTPException(422, "المستخلص لا يتبع مشروع الشيك")
    if contract.counterparty_id is None:
        raise HTTPException(409, "العقد غير مربوط بمقاول من سجل الأطراف؛ لا يمكن التحقق من المستفيد")
    party = db.get(Counterparty, contract.counterparty_id)
    if not party or not party.is_active:
        raise HTTPException(409, "المقاول المرتبط بالعقد غير نشط أو غير موجود")
    valid_accounts = {x for x in (party.account_id, party.linked_account_id) if x is not None}
    if check.party_account_id not in valid_accounts:
        raise HTTPException(422, "حساب مستفيد الشيك لا يطابق حساب المقاول المرتبط بالمستخلص")
    amount = _money(body.allocated_amount)
    if amount <= 0:
        raise HTTPException(422, "قيمة التخصيص يجب أن تكون أكبر من صفر")
    duplicate = db.scalar(select(FinancialCheckSettlementAllocation.allocation_id).where(
        FinancialCheckSettlementAllocation.check_id == cid,
        FinancialCheckSettlementAllocation.settlement_id == body.settlement_id))
    if duplicate:
        raise HTTPException(409, "هذا المستخلص مخصص للشيك بالفعل")
    check_allocated = db.scalar(select(func.coalesce(func.sum(FinancialCheckSettlementAllocation.allocated_amount), 0)).where(
        FinancialCheckSettlementAllocation.check_id == cid)) or 0
    if _money(check_allocated) + amount > _money(check.amount):
        raise HTTPException(409, "إجمالي تخصيصات المستخلصات سيتجاوز قيمة الشيك")
    paid = db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
        TreasuryTransaction.settlement_id == settlement.settlement_id,
        TreasuryTransaction.status == "تم الصرف")) or 0
    reserved = db.scalar(_reserved_allocations_stmt(settlement.settlement_id)) or 0
    remaining = max(Decimal("0.00"), _money(settlement.net_amount) - _money(paid) - _money(reserved))
    if amount > remaining:
        raise HTTPException(409, f"قيمة التخصيص تتجاوز المتبقي غير المدفوع من المستخلص: {remaining}")
    allocation = FinancialCheckSettlementAllocation(
        check_id=cid, settlement_id=body.settlement_id,
        allocated_amount=amount, created_by=user.user_id)
    db.add(allocation)
    write_audit(db, user.user_id, "AllocateSettlement", "FinancialChecks", cid, None, {
        "settlement_id": body.settlement_id, "allocated_amount": str(amount)})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "التخصيص موجود بالفعل أو تعارضت عملية تخصيص متزامنة")
    return {"items": _allocations_out(db, cid), "allocated_total": str(_money(_money(check_allocated) + amount))}


@router.get("/{cid}/allocation-options")
def allocation_options(cid: int, _: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    check = db.get(FinancialCheck, cid)
    if not check:
        raise HTTPException(404, "الشيك غير موجود")
    if check.check_type != "OUTGOING":
        raise HTTPException(422, "تخصيص المستخلصات متاح للشيكات الصادرة فقط")
    result = []
    rows = db.scalars(select(ContractSettlement).where(
        ContractSettlement.settlement_side == "Subcontractor",
        ContractSettlement.status.in_(("Approved", "Posted")),
        ContractSettlement.manager_approved_by.is_not(None),
        ContractSettlement.manager_approved_at.is_not(None)
    ).order_by(ContractSettlement.settlement_date, ContractSettlement.settlement_id)).all()
    for settlement in rows:
        contract = db.get(Contract, settlement.contract_id)
        if not contract or contract.status.lower() != "active":
            continue
        if check.project_id is not None and contract.project_id is not None and check.project_id != contract.project_id:
            continue
        party = db.get(Counterparty, contract.counterparty_id) if contract.counterparty_id else None
        if not party or not party.is_active:
            continue
        if check.party_account_id not in {x for x in (party.account_id, party.linked_account_id) if x is not None}:
            continue
        paid = db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
            TreasuryTransaction.settlement_id == settlement.settlement_id,
            TreasuryTransaction.status == "تم الصرف")) or 0
        reserved = db.scalar(_reserved_allocations_stmt(settlement.settlement_id)) or 0
        remaining = max(Decimal("0.00"), _money(settlement.net_amount) - _money(paid) - _money(reserved))
        duplicate = db.scalar(select(FinancialCheckSettlementAllocation.allocation_id).where(
            FinancialCheckSettlementAllocation.check_id == cid,
            FinancialCheckSettlementAllocation.settlement_id == settlement.settlement_id))
        if remaining <= 0 or duplicate:
            continue
        result.append({
            "settlement_id": settlement.settlement_id,
            "settlement_no": settlement.settlement_no,
            "contract_no": contract.contract_no,
            "counterparty_name": settlement.counterparty_name,
            "net_amount": str(_money(settlement.net_amount)),
            "paid_amount": str(_money(paid)),
            "allocated_amount": str(_money(reserved)),
            "remaining_amount": str(remaining),
            "project_id": contract.project_id,
        })
    return {"items": result}


@router.get("/{cid}/history")
def check_history(cid: int, _: User = Depends(require_any(SCREENS, "View")), db: Session = Depends(get_db)):
    if not db.get(FinancialCheck, cid):
        raise HTTPException(404, "الشيك غير موجود")
    rows = db.scalars(select(FinancialCheckStatusHistory).where(
        FinancialCheckStatusHistory.check_id == cid
    ).order_by(FinancialCheckStatusHistory.changed_at, FinancialCheckStatusHistory.history_id)).all()
    return {"items": [{
        "history_id": row.history_id,
        "old_status": row.old_status,
        "new_status": row.new_status,
        "changed_by": row.changed_by,
        "note": row.note,
        "changed_at": row.changed_at.isoformat() if row.changed_at else None,
    } for row in rows]}
