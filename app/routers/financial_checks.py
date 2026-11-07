import csv, io
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..common import require_any
from ..database import get_db
from ..deps import write_audit
from ..models import (Account, Company, FiscalYear, FinancialCheck, JournalEntry,
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

class ProjectLinkIn(BaseModel):
    project_id: int | None = Field(default=None, gt=0)

class AllocationIn(BaseModel):
    settlement_id: int = Field(gt=0)
    allocated_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)




def out(c):
    return {"check_id": c.check_id, "check_number": c.check_number, "check_type": c.check_type,
            "amount": str(c.amount), "due_date": str(c.due_date), "drawee_bank": c.drawee_bank,
            "status": c.status, "project_id": c.project_id, "party_account_id": c.party_account_id,
            "treasury_account_id": c.treasury_account_id, "journal_entry_id": c.journal_entry_id,
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
    return [out(c) for c in db.scalars(q.limit(2000))]

@router.post("", status_code=201)
def create(body: CheckIn, user: User = Depends(require_any(SCREENS, "Add")), db: Session = Depends(get_db)):
    if body.check_type not in ("INCOMING", "OUTGOING"): raise HTTPException(422, "نوع الشيك غير صحيح")
    party = db.get(Account, body.party_account_id); bank = db.get(TreasuryAccount, body.treasury_account_id)
    if not party or not party.is_active: raise HTTPException(422, "حساب العميل/المورد غير صحيح")
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
    if not c: raise HTTPException(404, "الشيك غير موجود")
    allowed = {"مسودة": {"معتمد", "ملغي"}, "معتمد": {"صادر", "ملغي"}, "صادر": {"تم التسليم", "ملغي", "موقوف"}, "تم التسليم": {"منصرف", "موقوف", "مرتد"}, "موقوف": {"صادر", "ملغي"}, "تحت التحصيل": {"تم التحصيل", "مرتد"}, "تم التحصيل": set(), "منصرف": set(), "مرتد": set(), "ملغي": set()}
    legacy_allowed = {"مسودة": {"تحت التحصيل", "مُحصّل", "منصرف", "مُرتجع"}, "تحت التحصيل": {"مُحصّل", "مُرتجع"}}
    if body.status not in set().union(*allowed.values(), *legacy_allowed.values()): raise HTTPException(422, "الحالة غير صحيحة")
    transitions = allowed if c.status in allowed else legacy_allowed
    if body.status not in transitions.get(c.status, set()):
        raise HTTPException(409, f"انتقال الحالة من {c.status} إلى {body.status} غير مسموح")
    target = "مُحصّل" if c.check_type == "INCOMING" else "منصرف"
    if c.journal_entry_id and body.status != c.status:
        raise HTTPException(409, "الشيك له قيد مرحّل؛ لا تغيّر حالته قبل إجراء عكس محاسبي معتمد")
    if (c.check_type == "INCOMING" and body.status == "منصرف") or (c.check_type == "OUTGOING" and body.status == "مُحصّل"):
        raise HTTPException(422, "الحالة لا تتوافق مع نوع الشيك")
    if body.status == target and c.status not in (("تحت التحصيل",) if c.check_type == "INCOMING" else ("مسودة", "تحت التحصيل")):
        raise HTTPException(409, "انتقال الحالة غير مسموح؛ راجع حالة الشيك الحالية")
    if body.status == target:
        if c.journal_entry_id: raise HTTPException(409, "تم إنشاء القيد لهذا الشيك مسبقاً")
        today = date.today(); fy = db.scalar(select(FiscalYear).where(FiscalYear.start_date <= today, FiscalYear.end_date >= today))
        if not fy or fy.is_closed: raise HTTPException(409, "لا توجد سنة مالية مفتوحة للتاريخ الحالي")
        bank = db.get(TreasuryAccount, c.treasury_account_id); party = db.get(Account, c.party_account_id)
        bank_gl = db.get(Account, bank.gl_account_id) if bank else None
        if not party or not party.is_active or not bank_gl or not bank_gl.is_active: raise HTTPException(409, "حساب العميل/المورد أو حساب البنك غير نشط")
        if not bank or bank.account_type != "Bank" or bank.currency_code != "EGP":
            raise HTTPException(409, "لا يمكن ترحيل شيك بالجنيه على حساب بنك بعملة مختلفة")
        if party.account_id == bank_gl.account_id:
            raise HTTPException(422, "حساب الطرف لا يمكن أن يكون نفس حساب البنك")
        voucher_no = f"FCHK-{c.check_id}"
        if db.scalar(select(TreasuryTransaction.transaction_id).where(TreasuryTransaction.voucher_no == voucher_no)):
            raise HTTPException(409, "حركة البنك مسجلة لهذا الشيك بالفعل؛ تم إيقاف الترحيل لمنع التكرار")
        prefix = f"JE-{fy.start_date.year}-"
        last = db.scalar(select(func.max(JournalEntry.entry_no)).where(JournalEntry.entry_no.like(prefix + "%")))
        seq = int(last[len(prefix):]) + 1 if last and last[len(prefix):].isdigit() else 1
        entry = JournalEntry(entry_no=f"{prefix}{seq:06d}", entry_date=today, company_id=fy.company_id,
            fiscal_year_id=fy.fiscal_year_id, description=f"تسوية شيك {c.check_number}", status="Posted",
            created_by=user.user_id, posted_by=user.user_id, posted_at=utcnow())
        db.add(entry); db.flush(); amount = Decimal(c.amount)
        # وارد: البنك مدين والعميل دائن. صادر: المورد مدين والبنك دائن.
        lines = [(bank_gl.account_id, amount, Decimal("0")), (party.account_id, Decimal("0"), amount)] if c.check_type == "INCOMING" else [(party.account_id, amount, Decimal("0")), (bank_gl.account_id, Decimal("0"), amount)]
        for n, (aid, debit, credit) in enumerate(lines, 1): db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id, line_no=n, account_id=aid, debit_amount=debit, credit_amount=credit, description=f"شيك {c.check_number}"))
        db.flush(); c.journal_entry_id = entry.journal_entry_id
        db.add(TreasuryTransaction(treasury_account_id=c.treasury_account_id, transaction_date=today,
            inflow=amount if c.check_type == "INCOMING" else Decimal("0"), outflow=amount if c.check_type == "OUTGOING" else Decimal("0"),
            description=f"تسوية شيك {c.check_number}", voucher_no=voucher_no, status=target, journal_entry_id=entry.journal_entry_id))
    old_status = c.status
    c.status = body.status
    db.add(FinancialCheckStatusHistory(check_id=cid, old_status=old_status, new_status=body.status, changed_by=user.user_id))
    write_audit(db, user.user_id, "Update", "FinancialChecks", cid, {"status": old_status}, {"status": body.status})
    db.commit(); return out(c)

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
            if body.project_id is not None:
                project = db.get(Project, body.project_id)
                if not project or not project.is_active: raise ValueError("المشروع غير صحيح أو غير نشط")
            db.add(FinancialCheck(**body.model_dump(), status="مسودة", created_by=user.user_id)); made += 1
        db.commit()
    except Exception as e:
        db.rollback(); raise HTTPException(422, f"فشل الاستيراد بالكامل دون حفظ جزئي: {str(e)[:180]}")
    return {"imported": made}


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


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
    reserved = db.scalar(select(func.coalesce(func.sum(FinancialCheckSettlementAllocation.allocated_amount), 0)).where(
        FinancialCheckSettlementAllocation.settlement_id == settlement.settlement_id)) or 0
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
