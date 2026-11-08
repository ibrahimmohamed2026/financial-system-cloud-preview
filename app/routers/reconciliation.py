from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..common import money
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import (
    Account, BankReconciliation, BankReconciliationLine, JournalEntry,
    JournalEntryDetail, TreasuryAccount, User,
)

SCREEN = "BankReconciliation"
router = APIRouter(prefix="/reconciliations", tags=["BankReconciliation"])
Amt = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class RecIn(BaseModel):
    treasury_account_id: int
    reconciliation_date: date
    statement_balance: Decimal = Field(max_digits=18, decimal_places=2)
    notes: str | None = Field(default=None, max_length=500)


class LineIn(BaseModel):
    transaction_date: date | None = None
    inflow: Decimal = Amt
    outflow: Decimal = Amt
    description: str | None = Field(default=None, max_length=500)
    check_no: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)
    recipient: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def _one(self):
        if (self.inflow > 0) == (self.outflow > 0):
            raise ValueError("البند إما وارد أو منصرف")
        return self


class MatchIn(BaseModel):
    is_matched: bool


def posted_book_balance(db: Session, treasury: TreasuryAccount, upto: date | None = None) -> Decimal:
    """Return the linked GL balance from Posted entries only, in the bank account currency.

    EGP accounts use the functional-currency debit/credit amounts plus the GL opening
    balance. Foreign-currency accounts use JournalEntryDetail.FcyAmount and deliberately
    do not mix EGP opening balances into the foreign-currency statement balance.
    """
    detail = JournalEntryDetail
    entry = JournalEntry
    filters = [
        detail.account_id == treasury.gl_account_id,
        entry.status == "Posted",
    ]
    if upto is not None:
        filters.append(entry.entry_date <= upto)

    if treasury.currency_code == "EGP":
        amount = func.coalesce(func.sum(detail.debit_amount - detail.credit_amount), 0)
    else:
        signed_fcy = case(
            (detail.debit_amount > 0, func.coalesce(detail.fcy_amount, 0)),
            (detail.credit_amount > 0, -func.coalesce(detail.fcy_amount, 0)),
            else_=0,
        )
        amount = func.coalesce(func.sum(signed_fcy), 0)

    posted = db.scalar(
        select(amount)
        .select_from(detail)
        .join(entry, entry.journal_entry_id == detail.journal_entry_id)
        .where(*filters)
    )
    balance = Decimal(posted or 0)
    if treasury.currency_code == "EGP":
        gl = db.get(Account, treasury.gl_account_id)
        if gl is not None:
            balance += Decimal(gl.opening_debit or 0) - Decimal(gl.opening_credit or 0)
    return balance


def _rec(db: Session, rid: int) -> BankReconciliation:
    r = db.get(BankReconciliation, rid)
    if r is None:
        raise HTTPException(404, "المذكرة غير موجودة")
    return r


def _out(db: Session, r: BankReconciliation, lines: bool = False) -> dict:
    a = db.get(TreasuryAccount, r.treasury_account_id)
    out = {"reconciliation_id": r.reconciliation_id, "treasury_account_id": r.treasury_account_id,
           "account_name": a.name_ar if a else None, "currency_code": a.currency_code if a else None,
           "reconciliation_date": r.reconciliation_date, "book_balance": money(r.book_balance),
           "statement_balance": money(r.statement_balance),
           "difference": money(Decimal(r.statement_balance) - Decimal(r.book_balance)), "notes": r.notes}
    if lines:
        ls = db.scalars(select(BankReconciliationLine).where(BankReconciliationLine.reconciliation_id == r.reconciliation_id)
                        .order_by(BankReconciliationLine.transaction_date, BankReconciliationLine.line_id)).all()
        unmatched = sum((l.inflow - l.outflow for l in ls if not l.is_matched), Decimal("0"))
        out["unmatched_net"] = money(unmatched)
        out["lines"] = [{"line_id": l.line_id, "transaction_date": l.transaction_date, "inflow": money(l.inflow),
                         "outflow": money(l.outflow), "description": l.description, "check_no": l.check_no,
                         "status": l.status, "recipient": l.recipient, "is_matched": l.is_matched} for l in ls]
    return out


@router.get("/accounts")
def accounts(_: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    return [{"treasury_account_id": a.treasury_account_id, "name_ar": a.name_ar, "currency_code": a.currency_code}
            for a in db.scalars(select(TreasuryAccount).where(TreasuryAccount.account_type == "Bank",
                                                              TreasuryAccount.is_active == True).order_by(TreasuryAccount.name_ar))]


@router.get("")
def list_recs(treasury_account_id: int | None = None, _: User = Depends(require_permission(SCREEN, "View")),
              db: Session = Depends(get_db)):
    stmt = select(BankReconciliation)
    if treasury_account_id:
        stmt = stmt.where(BankReconciliation.treasury_account_id == treasury_account_id)
    return [_out(db, r) for r in db.scalars(stmt.order_by(BankReconciliation.reconciliation_date.desc(),
                                                          BankReconciliation.reconciliation_id.desc()))]


@router.get("/{rid}")
def get_rec(rid: int, _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    return _out(db, _rec(db, rid), True)


@router.post("", status_code=201)
def create(body: RecIn, user: User = Depends(require_permission(SCREEN, "Add")), db: Session = Depends(get_db)):
    a = db.get(TreasuryAccount, body.treasury_account_id)
    if a is None or a.account_type != "Bank":
        raise HTTPException(400, "حساب البنك غير صحيح")
    r = BankReconciliation(treasury_account_id=a.treasury_account_id, reconciliation_date=body.reconciliation_date,
                           book_balance=posted_book_balance(db, a, body.reconciliation_date),
                           statement_balance=body.statement_balance, prepared_by=user.user_id, notes=body.notes)
    db.add(r)
    db.flush()
    write_audit(db, user.user_id, "Create", "BankReconciliations", r.reconciliation_id, None,
                {"account": a.name_ar, "date": str(body.reconciliation_date)})
    db.commit()
    db.refresh(r)
    return _out(db, r, True)


@router.post("/{rid}/lines", status_code=201)
def add_line(rid: int, body: LineIn, user: User = Depends(require_permission(SCREEN, "Edit")),
             db: Session = Depends(get_db)):
    _rec(db, rid)
    l = BankReconciliationLine(reconciliation_id=rid, **body.model_dump())
    db.add(l)
    db.commit()
    return {"line_id": l.line_id}


@router.patch("/{rid}/lines/{lid}")
def match(rid: int, lid: int, body: MatchIn, user: User = Depends(require_permission(SCREEN, "Edit")),
          db: Session = Depends(get_db)):
    l = db.get(BankReconciliationLine, lid)
    if l is None or l.reconciliation_id != rid:
        raise HTTPException(404, "البند غير موجود")
    l.is_matched = body.is_matched
    db.commit()
    return {"line_id": lid, "is_matched": l.is_matched}


@router.delete("/{rid}/lines/{lid}", status_code=204)
def del_line(rid: int, lid: int, user: User = Depends(require_permission(SCREEN, "Edit")),
             db: Session = Depends(get_db)):
    l = db.get(BankReconciliationLine, lid)
    if l is None or l.reconciliation_id != rid:
        raise HTTPException(404, "البند غير موجود")
    db.delete(l)
    db.commit()


@router.delete("/{rid}", status_code=204)
def delete(rid: int, user: User = Depends(require_permission(SCREEN, "Delete")), db: Session = Depends(get_db)):
    r = _rec(db, rid)
    for l in db.scalars(select(BankReconciliationLine).where(BankReconciliationLine.reconciliation_id == rid)):
        db.delete(l)
    write_audit(db, user.user_id, "Delete", "BankReconciliations", rid, {"date": str(r.reconciliation_date)}, None)
    db.flush()
    db.delete(r)
    db.commit()
