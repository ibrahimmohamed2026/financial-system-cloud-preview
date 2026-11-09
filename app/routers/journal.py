from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import exists, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..common import money
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import (Account, Company, Contract, ContractSettlement, ContractSettlementSchedule, TechnicalSettlementEstimate, FiscalYear, JournalEntry, JournalEntryDetail, Project, User, utcnow)

SCREEN = "JournalBook"
router = APIRouter(prefix="/journal", tags=["JournalBook"])
Amt = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class LineIn(BaseModel):
    account_id: int
    project_id: int | None = None
    debit_amount: Decimal = Amt
    credit_amount: Decimal = Amt
    description: str | None = None

    @model_validator(mode="after")
    def _one_side(self):
        if (self.debit_amount > 0) == (self.credit_amount > 0):
            raise ValueError("كل سطر لازم يكون مدين أو دائن (مش الاتنين ومش صفر)")
        return self


class EntryIn(BaseModel):
    entry_date: date
    description: str | None = Field(default=None, max_length=500)
    source_settlement_id: int | None = Field(default=None, gt=0)
    lines: list[LineIn] = Field(min_length=2)

    @model_validator(mode="after")
    def _line_descriptions_required(self):
        missing = [str(i) for i, line in enumerate(self.lines, 1) if not (line.description or "").strip()]
        if missing:
            raise ValueError("اكتب بيانًا لكل سطر في القيد — السطور الناقصة: " + ", ".join(missing))
        return self


class FiscalYearIn(BaseModel):
    start_date: date
    end_date: date
    company_name: str = "الشركة"


def _fy_for(db: Session, d: date) -> FiscalYear:
    fy = db.scalar(select(FiscalYear).where(FiscalYear.start_date <= d, FiscalYear.end_date >= d))
    if fy is None:
        raise HTTPException(409, f"مفيش سنة مالية تشمل تاريخ {d} — أضف سنة مالية الأول")
    if fy.is_closed:
        raise HTTPException(409, "السنة المالية مقفولة")
    return fy


def _validate_lines(db: Session, lines: list[LineIn]) -> tuple[Decimal, Decimal]:
    ids = {l.account_id for l in lines}
    accs = {a.account_id: a for a in db.scalars(select(Account).where(Account.account_id.in_(ids)))}
    parents = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.in_(ids))))
    for l in lines:
        a = accs.get(l.account_id)
        if a is None:
            raise HTTPException(400, f"الحساب رقم {l.account_id} غير موجود")
        if not a.is_active:
            raise HTTPException(400, f"الحساب {a.account_code} غير نشط")
        if a.account_id in parents:
            raise HTTPException(400, f"الحساب {a.account_code} حساب رئيسي — اختار حساب فرعي")
    pids = {l.project_id for l in lines if l.project_id}
    if pids and len(set(db.scalars(select(Project.project_id).where(Project.project_id.in_(pids))))) != len(pids):
        raise HTTPException(400, "مركز تكلفة غير موجود")
    d = sum((l.debit_amount for l in lines), Decimal("0"))
    c = sum((l.credit_amount for l in lines), Decimal("0"))
    if d != c:
        raise HTTPException(422, f"القيد غير متوازن: المدين {money(d)} ≠ الدائن {money(c)}")
    return d, c


def _next_no(db: Session, fy: FiscalYear) -> str:
    # Serialize numbering per fiscal year on PostgreSQL to avoid duplicate EntryNo
    # values when multiple transactions post journals concurrently.
    bind = db.get_bind()
    if getattr(getattr(bind, "dialect", None), "name", None) == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:k)"),
                   {"k": 4_200_000 + fy.start_date.year})
    prefix = f"JE-{fy.start_date.year}-"
    last = db.scalar(select(func.max(JournalEntry.entry_no)).where(JournalEntry.entry_no.like(prefix + "%")))
    n = int(last[len(prefix):]) + 1 if last and last[len(prefix):].isdigit() else 1
    return f"{prefix}{n:06d}"


def _out(db: Session, e: JournalEntry, with_lines: bool = False, lang: str = "ar") -> dict:
    rows = db.execute(
        select(JournalEntryDetail, Account.account_code, Account.account_name_ar, Account.account_name_en, Project.name_ar, Project.name_en)
        .join(Account, Account.account_id == JournalEntryDetail.account_id)
        .outerjoin(Project, Project.project_id == JournalEntryDetail.project_id)
        .where(JournalEntryDetail.journal_entry_id == e.journal_entry_id)
        .order_by(JournalEntryDetail.line_no)).all()
    out = {"journal_entry_id": e.journal_entry_id, "entry_no": e.entry_no, "entry_date": e.entry_date,
           "description": e.description, "status": e.status, "posted_at": e.posted_at,
           "source_settlement_id": e.source_settlement_id,
           "line_descriptions": [{"line_no": r[0].line_no, "description": r[0].description} for r in rows],
           "total_debit": money(sum((r[0].debit_amount for r in rows), Decimal("0"))),
           "total_credit": money(sum((r[0].credit_amount for r in rows), Decimal("0")))}
    if with_lines:
        out["lines"] = [{"line_no": d.line_no, "account_id": d.account_id, "account_code": code,
                         "account_name": (name_en if lang == "en" and name_en else name), "project_id": d.project_id, "project_name": (project_en if lang == "en" and project_en else pname),
                         "debit_amount": money(d.debit_amount), "credit_amount": money(d.credit_amount),
                         "fcy_amount": money(d.fcy_amount) if d.fcy_amount is not None else None,
                         "exchange_rate": str(d.exchange_rate) if d.exchange_rate is not None else None,
                         "description": d.description} for d, code, name, name_en, pname, project_en in rows]
    return out


def _get(db: Session, eid: int) -> JournalEntry:
    e = db.get(JournalEntry, eid)
    if e is None:
        raise HTTPException(404, "القيد غير موجود")
    return e


def _fill_lines(db: Session, e: JournalEntry, lines: list[LineIn]) -> None:
    for i, l in enumerate(lines, start=1):
        db.add(JournalEntryDetail(journal_entry_id=e.journal_entry_id, line_no=i, account_id=l.account_id,
                                  project_id=l.project_id, debit_amount=l.debit_amount,
                                  credit_amount=l.credit_amount, description=l.description))


def _validate_settlement_link(db: Session, settlement_id: int | None, *, journal_entry_id: int | None = None) -> None:
    if settlement_id is None:
        return
    settlement = db.scalar(select(ContractSettlement).where(
        ContractSettlement.settlement_id == settlement_id).with_for_update())
    if settlement is None:
        raise HTTPException(404, "المستخلص المرتبط بالقيد غير موجود")
    if settlement.status == "Posted":
        raise HTTPException(409, "المستخلص مرحّل بالفعل")
    if settlement.journal_entry_id not in (None, journal_entry_id):
        raise HTTPException(409, "المستخلص مرتبط بقيد آخر بالفعل")
    if journal_entry_id is not None and settlement.status != "JournalDraft":
        raise HTTPException(409, "حالة المستخلص لا تسمح بترحيل هذا القيد")
    existing = db.scalar(select(JournalEntry).where(
        JournalEntry.source_settlement_id == settlement_id,
        JournalEntry.status != "Reversed",
        JournalEntry.journal_entry_id != (journal_entry_id or 0),
    ).limit(1))
    if existing:
        raise HTTPException(409, f"يوجد قيد {existing.entry_no} مرتبط بهذا المستخلص؛ لا يمكن إنشاء قيد آخر له")


# ---------- السنوات المالية ----------
@router.get("/fiscal-years")
def fiscal_years(_: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    return [{"fiscal_year_id": f.fiscal_year_id, "start_date": f.start_date, "end_date": f.end_date,
             "is_closed": f.is_closed} for f in db.scalars(select(FiscalYear).order_by(FiscalYear.start_date))]


@router.post("/fiscal-years", status_code=201)
def add_fiscal_year(body: FiscalYearIn, user: User = Depends(require_permission(SCREEN, "Approve")),
                    db: Session = Depends(get_db)):
    if body.end_date <= body.start_date:
        raise HTTPException(422, "نهاية السنة لازم تبقى بعد بدايتها")
    if db.scalar(select(func.count()).select_from(FiscalYear).where(
            FiscalYear.start_date <= body.end_date, FiscalYear.end_date >= body.start_date)):
        raise HTTPException(409, "السنة المالية بتتداخل مع سنة موجودة")
    company = db.scalar(select(Company).order_by(Company.company_id))
    if company is None:
        company = Company(name_ar=body.company_name)
        db.add(company)
        db.flush()
    fy = FiscalYear(company_id=company.company_id, start_date=body.start_date, end_date=body.end_date)
    db.add(fy)
    db.flush()
    write_audit(db, user.user_id, "Create", "FiscalYears", fy.fiscal_year_id, None, body.model_dump())
    db.commit()
    return {"fiscal_year_id": fy.fiscal_year_id}


@router.get("/lookup/accounts")
def lookup_accounts(lang: str = Query("ar", pattern="^(ar|en)$"), _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    """الحسابات الفرعية النشطة (اللي يصح تتسجل عليها قيود)."""
    parents = select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))
    rows = db.scalars(select(Account).where(Account.is_active == True, Account.account_id.not_in(parents))
                      .order_by(Account.account_code)).all()
    return [{"account_id": a.account_id, "account_name_ar": a.account_name_ar, "account_name_en": a.account_name_en, "label": f"{a.account_code} — {(a.account_name_en if lang == 'en' and a.account_name_en else a.account_name_ar)}"} for a in rows]


@router.get("/lookup/settlements")
def lookup_settlements(_: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    rows = db.scalars(select(ContractSettlement).order_by(ContractSettlement.settlement_date.desc(),
                             ContractSettlement.settlement_id.desc()).limit(1000)).all()
    result = []
    for settlement in rows:
        contract = db.get(Contract, settlement.contract_id)
        result.append({"settlement_id": settlement.settlement_id, "settlement_no": settlement.settlement_no,
                       "settlement_side": settlement.settlement_side, "status": settlement.status,
                       "journal_entry_id": settlement.journal_entry_id,
                       "contract_no": contract.contract_no if contract else "",
                       "contract_title": contract.title if contract else ""})
    return result


# ---------- القيود ----------
@router.get("")
def list_entries(q: str | None = None, status_: str | None = Query(None, alias="status"),
                 date_from: date | None = None, date_to: date | None = None,
                 account_ids: list[int] = Query(default=[]),
                 skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                 _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    stmt = select(JournalEntry)
    if q and q.strip():
        like = f"%{q.strip()}%"
        line_match = exists(select(JournalEntryDetail.detail_id).where(
            JournalEntryDetail.journal_entry_id == JournalEntry.journal_entry_id,
            JournalEntryDetail.description.ilike(like)))
        stmt = stmt.where(or_(JournalEntry.entry_no.ilike(like), JournalEntry.description.ilike(like), line_match))
    if status_:
        stmt = stmt.where(JournalEntry.status == status_)
    if date_from:
        stmt = stmt.where(JournalEntry.entry_date >= date_from)
    if date_to:
        stmt = stmt.where(JournalEntry.entry_date <= date_to)
    if account_ids:
        matching_account = exists(select(JournalEntryDetail.detail_id).where(
            JournalEntryDetail.journal_entry_id == JournalEntry.journal_entry_id,
            JournalEntryDetail.account_id.in_(set(account_ids))))
        stmt = stmt.where(matching_account)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(JournalEntry.entry_date.desc(), JournalEntry.journal_entry_id.desc())
                       .offset(skip).limit(limit)).all()
    return {"total": total, "items": [_out(db, e) for e in items]}


@router.get("/{eid}")
def get_entry(eid: int, lang: str = Query("ar", pattern="^(ar|en)$"), _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    return _out(db, _get(db, eid), True, lang)


@router.post("", status_code=201)
def create_entry(body: EntryIn, user: User = Depends(require_permission(SCREEN, "Add")),
                 db: Session = Depends(get_db)):
    fy = _fy_for(db, body.entry_date)
    _validate_settlement_link(db, body.source_settlement_id)
    _validate_lines(db, body.lines)
    for attempt in range(3):
        e = JournalEntry(entry_no=_next_no(db, fy), entry_date=body.entry_date, company_id=fy.company_id,
                         fiscal_year_id=fy.fiscal_year_id, description=body.description, status="Draft",
                         source_settlement_id=body.source_settlement_id, created_by=user.user_id)
        db.add(e)
        try:
            db.flush()
            break
        except IntegrityError:
            db.rollback()
            if attempt == 2:
                raise HTTPException(409, "تعارض في رقم القيد — حاول تاني")
    _fill_lines(db, e, body.lines)
    db.flush()
    write_audit(db, user.user_id, "Create", "JournalEntries", e.journal_entry_id, None, {"entry_no": e.entry_no})
    db.commit()
    return _out(db, e, True)


@router.put("/{eid}")
def update_entry(eid: int, body: EntryIn, user: User = Depends(require_permission(SCREEN, "Edit")),
                 db: Session = Depends(get_db)):
    e = _get(db, eid)
    if e.status != "Draft":
        raise HTTPException(409, "مينفعش تعدّل قيد مرحّل أو ملغي")
    fy = _fy_for(db, body.entry_date)
    _validate_settlement_link(db, body.source_settlement_id, journal_entry_id=e.journal_entry_id)
    _validate_lines(db, body.lines)
    old = _out(db, e, True)
    for d in db.scalars(select(JournalEntryDetail).where(JournalEntryDetail.journal_entry_id == eid)):
        db.delete(d)
    db.flush()
    e.entry_date, e.description = body.entry_date, body.description
    e.source_settlement_id = body.source_settlement_id
    e.company_id, e.fiscal_year_id = fy.company_id, fy.fiscal_year_id
    _fill_lines(db, e, body.lines)
    db.flush()
    write_audit(db, user.user_id, "Update", "JournalEntries", eid, old, _out(db, e, True))
    db.commit()
    return _out(db, e, True)


@router.post("/{eid}/post")
def post_entry(eid: int, user: User = Depends(require_permission(SCREEN, "Post")), db: Session = Depends(get_db)):
    e = _get(db, eid)
    if e.status != "Draft":
        raise HTTPException(409, "القيد مش مسودة")
    _validate_settlement_link(db, e.source_settlement_id, journal_entry_id=e.journal_entry_id)
    _fy_for(db, e.entry_date)
    lines = [LineIn(account_id=d.account_id, project_id=d.project_id, debit_amount=d.debit_amount,
                    credit_amount=d.credit_amount)
             for d in db.scalars(select(JournalEntryDetail).where(JournalEntryDetail.journal_entry_id == eid))]
    if len(lines) < 2:
        raise HTTPException(422, "القيد لازم فيه سطرين على الأقل")
    _validate_lines(db, lines)
    e.status, e.posted_by, e.posted_at = "Posted", user.user_id, utcnow()
    if e.source_settlement_id is not None:
        settlement = db.scalar(select(ContractSettlement).where(
            ContractSettlement.settlement_id == e.source_settlement_id).with_for_update())
        if settlement is None or settlement.journal_entry_id != e.journal_entry_id or settlement.status != "JournalDraft":
            raise HTTPException(409, "ربط المستخلص بالقيد غير متطابق أو أن حالة المستخلص تغيرت")
        contract = db.scalar(select(Contract).where(
            Contract.contract_id == settlement.contract_id).with_for_update())
        if contract is None or contract.status.lower() != "active":
            raise HTTPException(409, "لا يمكن ترحيل مستخلص لعقد غير فعّال")
        settlement.status = "Posted"
        linked_estimate = db.scalar(select(TechnicalSettlementEstimate).where(
            TechnicalSettlementEstimate.financial_settlement_id == settlement.settlement_id))
        if linked_estimate is not None:
            linked_schedule = db.scalar(select(ContractSettlementSchedule).where(
                ContractSettlementSchedule.technical_estimate_id == linked_estimate.estimate_id).with_for_update())
            if linked_schedule is not None:
                linked_schedule.status = "Completed"
        posted_final = db.scalar(select(ContractSettlement.settlement_id).where(
            ContractSettlement.contract_id == contract.contract_id,
            ContractSettlement.is_final.is_(True),
            ContractSettlement.status == "Posted").limit(1))
        if posted_final:
            unfinished = db.scalar(select(func.count()).select_from(ContractSettlement).where(
                ContractSettlement.contract_id == contract.contract_id,
                ContractSettlement.status != "Posted")) or 0
            if unfinished == 0:
                contract.status = "Closed"
                contract.closed_at = utcnow()
                contract.closed_by = user.user_id
                write_audit(db, user.user_id, "AutoClose", "Contracts", contract.contract_id,
                            old={"status": "Active"}, new={"status": "Closed",
                            "closed_at": contract.closed_at.isoformat(),
                            "reason": "Final settlement journal posted and all contract settlements completed"})
        write_audit(db, user.user_id, "Post", "ContractSettlements", settlement.settlement_id,
                    {"status": "JournalDraft", "journal_entry_id": eid},
                    {"status": "Posted", "journal_entry_id": eid})
    write_audit(db, user.user_id, "Post", "JournalEntries", eid, {"status": "Draft"}, {"status": "Posted"})
    db.commit()
    return _out(db, e)


@router.post("/{eid}/cancel")
def cancel_entry(eid: int, user: User = Depends(require_permission(SCREEN, "Approve")),
                 db: Session = Depends(get_db)):
    """إلغاء قيد مرحّل: بيتحوّل لـReversed وبيخرج من ميزان المراجعة (القيد نفسه بيفضل للمراجعة)."""
    e = _get(db, eid)
    if e.status != "Posted":
        raise HTTPException(409, "الإلغاء للقيود المرحّلة بس")
    _fy_for(db, e.entry_date)
    e.status = "Reversed"
    write_audit(db, user.user_id, "Cancel", "JournalEntries", eid, {"status": "Posted"}, {"status": "Reversed"})
    db.commit()
    return _out(db, e)


@router.delete("/{eid}", status_code=204)
def delete_entry(eid: int, user: User = Depends(require_permission(SCREEN, "Delete")),
                 db: Session = Depends(get_db)):
    e = _get(db, eid)
    if e.status not in ("Draft", "Reversed"):
        raise HTTPException(409, "الحذف للمسودات والقيود الملغاة فقط — القيد المرحّل لازم يتلغي الأول")
    linked_settlement = db.scalar(select(ContractSettlement).where(
        ContractSettlement.journal_entry_id == eid).limit(1))
    if linked_settlement is not None:
        raise HTTPException(409, "لا يمكن حذف القيد لأنه مرتبط بمستخلص مرحّل؛ احتفظ بسجل الربط المحاسبي")
    from ..models import TreasuryTransaction
    for t in db.scalars(select(TreasuryTransaction).where(TreasuryTransaction.journal_entry_id == eid)):
        t.journal_entry_id = None
    for d in db.scalars(select(JournalEntryDetail).where(JournalEntryDetail.journal_entry_id == eid)):
        db.delete(d)
    write_audit(db, user.user_id, "Delete", "JournalEntries", eid, {"entry_no": e.entry_no}, None)
    db.flush()
    db.delete(e)
    db.commit()
