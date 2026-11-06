from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..common import money, require_dynamic
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import Account, AccountClassification, Project, TreasuryAccount, TreasuryTransaction, User

# شاشة → (نوع الحساب الافتراضي، العملة الافتراضية)
BANK_SCREENS = {
    "BankCibEgp": ("Bank", "EGP"), "CashUsd": ("Cash", "USD"), "CashEgp": ("Cash", "EGP"), "BankCairoEgp": ("Bank", "EGP"),
    "BankHdbUsd": ("Bank", "USD"), "BankHdbEgp": ("Bank", "EGP"), "BankCibUsd": ("Bank", "USD"),
}
router = APIRouter(prefix="/treasury", tags=["Treasury"])
D0 = Decimal("0")
Amt = Field(default=D0, ge=0, max_digits=18, decimal_places=2)


class AccountIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name_ar: str = Field(min_length=1, max_length=200)
    account_type: str = Field(pattern="^(Bank|Cash)$")
    currency_code: str = Field(min_length=3, max_length=3)
    bank_account_number: str | None = Field(default=None, max_length=50)
    gl_account_id: int


class GLAccountLinkIn(BaseModel):
    gl_account_id: int


class TxIn(BaseModel):
    transaction_date: date
    inflow: Decimal = Amt
    outflow: Decimal = Amt
    description: str | None = Field(default=None, max_length=500)
    voucher_no: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    recipient_name: str | None = Field(default=None, max_length=200)
    project_id: int | None = None

    @model_validator(mode="after")
    def _one(self):
        if (self.inflow > 0) == (self.outflow > 0):
            raise ValueError("الحركة إما وارد أو منصرف (مش الاتنين ومش صفر)")
        return self


def balance_of(db: Session, tid: int, upto: date | None = None) -> Decimal:
    stmt = select(func.coalesce(func.sum(TreasuryTransaction.inflow - TreasuryTransaction.outflow), 0)).where(
        TreasuryTransaction.treasury_account_id == tid)
    if upto:
        stmt = stmt.where(TreasuryTransaction.transaction_date <= upto)
    return Decimal(db.scalar(stmt) or 0)


def acc_out(db: Session, a: TreasuryAccount) -> dict:
    gl = db.get(Account, a.gl_account_id)
    return {"treasury_account_id": a.treasury_account_id, "name_ar": a.name_ar, "account_type": a.account_type,
            "currency_code": a.currency_code, "bank_account_number": a.bank_account_number,
            "gl_account_id": a.gl_account_id, "gl_account": f"{gl.account_code} — {gl.account_name_ar}" if gl else None,
            "is_active": a.is_active, "balance": money(balance_of(db, a.treasury_account_id))}


def _bound(db: Session, screen_code: str) -> TreasuryAccount:
    a = db.scalar(select(TreasuryAccount).where(TreasuryAccount.screen_code == screen_code))
    if a is None:
        raise HTTPException(404, "الحساب لسه مش متسجّل للشاشة دي")
    return a


def _validate_cash_bank_gl(db: Session, account_id: int) -> Account:
    gl = db.get(Account, account_id)
    cash_bank_class = db.scalar(select(AccountClassification.classification_id).where(
        AccountClassification.name_ar == "نقدية بالصندوق و البنوك"))
    if gl is None or not gl.is_active or gl.classification_id != cash_bank_class:
        raise HTTPException(400, "اختَر حسابًا نشطًا من تصنيف نقدية الصندوق والبنوك")
    if db.scalar(select(Account.account_id).where(Account.parent_account_id == gl.account_id).limit(1)):
        raise HTTPException(400, "اختَر حسابًا فرعيًا من شجرة الحسابات، وليس حسابًا رئيسيًا")
    return gl


@router.get("/analysis")
def analysis(_: User = Depends(require_permission("CashAnalysis", "View")), db: Session = Depends(get_db)):
    accs = db.scalars(select(TreasuryAccount).where(TreasuryAccount.is_active == True)
                      .order_by(TreasuryAccount.currency_code, TreasuryAccount.account_type, TreasuryAccount.name_ar)).all()
    items, by_cur = [], {}
    for a in accs:
        b = balance_of(db, a.treasury_account_id)
        by_cur[a.currency_code] = by_cur.get(a.currency_code, D0) + b
        items.append({"name_ar": a.name_ar, "account_type": a.account_type, "currency_code": a.currency_code,
                      "balance": money(b)})
    return {"items": items, "totals": [{"currency_code": k, "balance": money(v)} for k, v in by_cur.items()]}


@router.get("/{screen_code}/account")
def get_account(screen_code: str, _: User = Depends(require_dynamic("View", set(BANK_SCREENS))),
                db: Session = Depends(get_db)):
    a = db.scalar(select(TreasuryAccount).where(TreasuryAccount.screen_code == screen_code))
    t, cur = BANK_SCREENS[screen_code]
    return {"account": acc_out(db, a) if a else None, "default_type": t, "default_currency": cur}


@router.get("/{screen_code}/gl-accounts")
def gl_list(screen_code: str, q: str | None = None, _: User = Depends(require_dynamic("Add", set(BANK_SCREENS))),
            db: Session = Depends(get_db)):
    cash_bank_classes = select(AccountClassification.classification_id).where(
        AccountClassification.name_ar == "نقدية بالصندوق و البنوك")
    parent_ids = select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))
    stmt = select(Account).where(Account.is_active == True, Account.classification_id.in_(cash_bank_classes),
                                 Account.account_id.not_in(parent_ids))
    if q and q.strip():
        stmt = stmt.where(or_(Account.account_code.ilike(f"%{q.strip()}%"), Account.account_name_ar.ilike(f"%{q.strip()}%")))
    return [{"account_id": a.account_id, "label": f"{a.account_code} — {a.account_name_ar}"}
            for a in db.scalars(stmt.order_by(Account.account_code).limit(300))]


@router.post("/{screen_code}/account", status_code=201)
def create_account(screen_code: str, body: AccountIn,
                   user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    if db.scalar(select(TreasuryAccount).where(TreasuryAccount.screen_code == screen_code)):
        raise HTTPException(409, "الشاشة دي مربوطة بحساب قبل كده")
    _validate_cash_bank_gl(db, body.gl_account_id)
    expected_type, expected_currency = BANK_SCREENS[screen_code]
    if body.account_type != expected_type or body.currency_code.upper() != expected_currency:
        raise HTTPException(400, "نوع الحساب أو العملة لا يطابقان الشاشة المحددة")
    values = body.model_dump()
    values["currency_code"] = expected_currency
    if expected_type == "Cash":
        values["bank_account_number"] = None
    a = TreasuryAccount(**values, screen_code=screen_code)
    db.add(a)
    db.flush()
    write_audit(db, user.user_id, "Create", "TreasuryAccounts", a.treasury_account_id, None, body.model_dump())
    db.commit()
    return acc_out(db, a)


@router.put("/{screen_code}/account")
def update_account_gl(screen_code: str, body: GLAccountLinkIn,
                      user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    a = _bound(db, screen_code)
    gl = _validate_cash_bank_gl(db, body.gl_account_id)
    old = {"gl_account_id": a.gl_account_id}
    a.gl_account_id = gl.account_id
    write_audit(db, user.user_id, "Update", "TreasuryAccounts", a.treasury_account_id,
                old, {"gl_account_id": a.gl_account_id})
    db.commit()
    return acc_out(db, a)


@router.get("/{screen_code}/transactions")
def transactions(screen_code: str, date_from: date | None = None, date_to: date | None = None, q: str | None = None,
                 skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                 _: User = Depends(require_dynamic("View", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    a = _bound(db, screen_code)
    tid = a.treasury_account_id
    T = TreasuryTransaction
    opening = D0
    if date_from:
        opening = Decimal(db.scalar(select(func.coalesce(func.sum(T.inflow - T.outflow), 0)).where(
            T.treasury_account_id == tid, T.transaction_date < date_from)) or 0)
    stmt = select(T).where(T.treasury_account_id == tid)
    if date_from:
        stmt = stmt.where(T.transaction_date >= date_from)
    if date_to:
        stmt = stmt.where(T.transaction_date <= date_to)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(T.description.ilike(like), T.recipient_name.ilike(like), T.voucher_no.ilike(like)))
    rows = db.scalars(stmt.order_by(T.transaction_date, T.transaction_id)).all()
    run, out, tin, tout = opening, [], D0, D0
    for t in rows:
        run += t.inflow - t.outflow
        tin += t.inflow
        tout += t.outflow
        out.append({"transaction_id": t.transaction_id, "transaction_date": t.transaction_date,
                    "inflow": money(t.inflow), "outflow": money(t.outflow), "balance": money(run),
                    "description": t.description, "voucher_no": t.voucher_no, "status": t.status,
                    "recipient_name": t.recipient_name, "project_id": t.project_id,
                    "locked": t.journal_entry_id is not None})
    return {"total": len(out), "opening_balance": money(opening), "total_inflow": money(tin),
            "total_outflow": money(tout), "closing_balance": money(run), "items": out[skip:skip + limit]}


def _check_project(db: Session, pid: int | None):
    if pid is not None and db.get(Project, pid) is None:
        raise HTTPException(400, "مركز التكلفة غير موجود")


@router.post("/{screen_code}/transactions", status_code=201)
def add_tx(screen_code: str, body: TxIn, user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))),
           db: Session = Depends(get_db)):
    a = _bound(db, screen_code)
    _check_project(db, body.project_id)
    t = TreasuryTransaction(treasury_account_id=a.treasury_account_id, **body.model_dump())
    db.add(t)
    db.flush()
    write_audit(db, user.user_id, "Create", "TreasuryTransactions", t.transaction_id, None, body.model_dump())
    db.commit()
    return {"transaction_id": t.transaction_id}


def _tx(db: Session, screen_code: str, tid: int) -> TreasuryTransaction:
    a = _bound(db, screen_code)
    t = db.get(TreasuryTransaction, tid)
    if t is None or t.treasury_account_id != a.treasury_account_id:
        raise HTTPException(404, "الحركة غير موجودة")
    if t.journal_entry_id is not None:
        raise HTTPException(409, "الحركة مرتبطة بقيد يومية — مينفعش تتعدّل أو تتحذف")
    return t


@router.put("/{screen_code}/transactions/{tid}")
def edit_tx(screen_code: str, tid: int, body: TxIn,
            user: User = Depends(require_dynamic("Edit", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    t = _tx(db, screen_code, tid)
    _check_project(db, body.project_id)
    old = {"inflow": str(t.inflow), "outflow": str(t.outflow), "description": t.description}
    for k, v in body.model_dump().items():
        setattr(t, k, v)
    write_audit(db, user.user_id, "Update", "TreasuryTransactions", tid, old, body.model_dump())
    db.commit()
    return {"transaction_id": tid}


@router.delete("/{screen_code}/transactions/{tid}", status_code=204)
def del_tx(screen_code: str, tid: int, user: User = Depends(require_dynamic("Delete", set(BANK_SCREENS))),
           db: Session = Depends(get_db)):
    t = _tx(db, screen_code, tid)
    write_audit(db, user.user_id, "Delete", "TreasuryTransactions", tid,
                {"inflow": str(t.inflow), "outflow": str(t.outflow)}, None)
    db.delete(t)
    db.commit()
