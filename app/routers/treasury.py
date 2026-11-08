from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..common import money, require_dynamic
from ..database import get_db
from ..deps import has_permission, require_permission, write_audit
from ..models import (Account, AccountClassification, Counterparty, JournalEntry, JournalEntryDetail, Project, TreasuryAccount, TreasuryTransaction, User)

# شاشة → (نوع الحساب الافتراضي، العملة الافتراضية)
BANK_SCREENS = {
    "BankCibEgp": ("Bank", "EGP"), "CashUsd": ("Cash", "USD"), "CashEgp": ("Cash", "EGP"), "BankCairoEgp": ("Bank", "EGP"),
    "BankHdbUsd": ("Bank", "USD"), "BankHdbEgp": ("Bank", "EGP"), "BankCibUsd": ("Bank", "USD"),
}
router = APIRouter(prefix="/treasury", tags=["Treasury"])
D0 = Decimal("0")
Amt = Field(default=D0, ge=0, max_digits=18, decimal_places=2)

# Transaction type determines the only valid counterpart classifications.
USD_TRANSACTION_TYPES = {
    "funding": {"label": "تمويل من المساهمين أو الأطراف ذات العلاقة", "direction": "inflow",
                "classifications": ("مستحق الى اطراف ذات علاقة", "راس المال المصدر و المدفوع")},
    "customer_collection": {"label": "تحصيل مستحقات من عميل", "direction": "inflow",
                "classifications": ("عملاء وأوراق قبض", "مدينون و ارصدة مدينة اخرى", "مدينون و ارصدة مدينة أخرى")},
    "customer_advance": {"label": "تحصيل دفعة مقدمة من عميل", "direction": "inflow",
                "classifications": ("عملاء دفعات مقدمه",)},
    "direct_income": {"label": "تحصيل إيراد مباشر", "direction": "inflow",
                "classifications": ("مبيعات / إيرادات", "فوائد دائنة")},
    "supplier_payment": {"label": "سداد مورد أو مقاول", "direction": "outflow",
                "classifications": ("موردون و اوراق دفع", "دائنون و ارصدة دائنة اخرى", "دائنون و ارصدة دائنة أخرى")},
    "supplier_advance": {"label": "دفعة مقدمة لمورد أو مقاول", "direction": "outflow",
                "classifications": ("دفعات مقدمه موردون و مقاولون",)},
    "expense_payment": {"label": "سداد مصروفات", "direction": "outflow",
                "classifications": ("مصروفات عمومية و ادارية", "مصروفات عمومية و إدارية", "تكلفة المبيعات", "فوائد التاجير التمويلى")},
    "asset_purchase": {"label": "شراء أصل أو مخزون أو أعمال تحت التنفيذ", "direction": "outflow",
                "classifications": ("اصول ثابتة بالصافي", "اصول غير ملموسه", "مخزون", "اعمال تحت التنفيذ")},
    "cash_transfer": {"label": "تحويل بين حسابات نقدية", "direction": "either",
                "classifications": ("نقدية بالصندوق و البنوك",)},
}


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
    exchange_rate: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=6)
    counterpart_account_id: int | None = Field(default=None, gt=0)
    treasury_account_id: int | None = Field(default=None, gt=0)
    counterparty_id: int | None = Field(default=None, gt=0)
    transaction_type: str | None = Field(default=None, max_length=40)

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

def _validate_treasury_gl_link(db: Session, account_id: int,
                               exclude_treasury_account_id: int | None = None) -> None:
    """A ledger cash/bank account must belong to one treasury record only."""
    stmt = select(TreasuryAccount.treasury_account_id).where(
        TreasuryAccount.gl_account_id == account_id)
    if exclude_treasury_account_id is not None:
        stmt = stmt.where(TreasuryAccount.treasury_account_id != exclude_treasury_account_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(409, "حساب الأستاذ مربوط بالفعل بخزينة أو بنك آخر؛ خصص حسابًا مستقلًا لكل حساب نقدي")


def _ensure_gl_relink_safe(db: Session, treasury: TreasuryAccount, new_gl_account_id: int) -> None:
    """Do not detach a ledger account after it has acquired opening or transaction history."""
    if treasury.gl_account_id == new_gl_account_id:
        return
    has_treasury_moves = db.scalar(select(TreasuryTransaction.transaction_id).where(
        TreasuryTransaction.treasury_account_id == treasury.treasury_account_id).limit(1))
    old_gl = db.get(Account, treasury.gl_account_id)
    has_opening_balance = bool(old_gl and (
        old_gl.opening_debit != 0 or old_gl.opening_credit != 0))
    has_ledger_history = db.scalar(select(JournalEntryDetail.detail_id).where(
        JournalEntryDetail.account_id == treasury.gl_account_id).limit(1))
    if has_treasury_moves or has_opening_balance or has_ledger_history:
        raise HTTPException(
            409,
            "لا يمكن تغيير ربط حساب الأستاذ بعد وجود رصيد افتتاحي أو حركات خزينة أو قيود عليه؛ "
            "يلزم إجراء تسوية وإعادة تصنيف محاسبية معتمدة أولًا",
        )


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
    current_treasury = db.scalar(select(TreasuryAccount).where(
        TreasuryAccount.screen_code == screen_code))
    used_by_other_treasuries = select(TreasuryAccount.gl_account_id)
    if current_treasury is not None:
        used_by_other_treasuries = used_by_other_treasuries.where(
            TreasuryAccount.treasury_account_id != current_treasury.treasury_account_id)
    stmt = select(Account).where(Account.is_active == True, Account.classification_id.in_(cash_bank_classes),
                                 Account.account_id.not_in(parent_ids),
                                 Account.account_id.not_in(used_by_other_treasuries))
    if screen_code == "CashUsd":
        stmt = stmt.where(Account.account_code == "15301002")
    if q and q.strip():
        stmt = stmt.where(or_(Account.account_code.ilike(f"%{q.strip()}%"), Account.account_name_ar.ilike(f"%{q.strip()}%")))
    return [{"account_id": a.account_id, "label": f"{a.account_code} — {a.account_name_ar}"}
            for a in db.scalars(stmt.order_by(Account.account_code).limit(300))]


@router.get("/{screen_code}/available-accounts")
def available_accounts(screen_code: str, _: User = Depends(require_dynamic("View", set(BANK_SCREENS))),
                       db: Session = Depends(get_db)):
    """List active cash/bank accounts in the screen currency for movement selection."""
    current = _bound(db, screen_code)
    rows = db.scalars(select(TreasuryAccount).where(
        TreasuryAccount.is_active == True,
        TreasuryAccount.currency_code == current.currency_code,
    ).order_by(TreasuryAccount.account_type, TreasuryAccount.name_ar)).all()
    rows = [row for row in rows if row.screen_code == current.screen_code or (
        has_permission(db, _.user_id, row.screen_code, "View")
        and has_permission(db, _.user_id, row.screen_code, "Add"))]
    return [{
        "treasury_account_id": row.treasury_account_id,
        "name_ar": row.name_ar,
        "account_type": row.account_type,
        "currency_code": row.currency_code,
        "label": f"{row.name_ar} — {'بنك' if row.account_type == 'Bank' else 'خزينة'} — {row.currency_code}",
        "is_current": row.treasury_account_id == current.treasury_account_id,
    } for row in rows]


@router.get("/{screen_code}/counterparties")
def treasury_counterparties(screen_code: str, transaction_type: str = Query(..., min_length=1, max_length=40),
                            _: User = Depends(require_dynamic("Add", set(BANK_SCREENS))),
                            db: Session = Depends(get_db)):
    """List active customer/supplier master records with a valid linked ledger account."""
    _bound(db, screen_code)
    if transaction_type in ("customer_collection", "customer_advance"):
        allowed_types = ("Customer", "Mixed")
    elif transaction_type in ("supplier_payment", "supplier_advance"):
        allowed_types = ("Supplier", "Contractor", "Mixed")
    else:
        return []
    config = USD_TRANSACTION_TYPES.get(transaction_type)
    if config is None:
        raise HTTPException(400, "نوع الحركة غير معروف")
    rows = db.execute(
        select(Counterparty, Account, AccountClassification)
        .join(Account, Account.account_id == func.coalesce(Counterparty.linked_account_id, Counterparty.account_id))
        .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
        .where(Counterparty.is_active == True, Counterparty.party_type.in_(allowed_types),
               Account.is_active == True, AccountClassification.name_ar.in_(config["classifications"]))
        .order_by(Counterparty.legal_name).limit(500)
    ).all()
    parents = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    return [{"counterparty_id": p.counterparty_id, "label": f"{p.code} — {p.legal_name}",
             "linked_account_id": a.account_id, "account_label": f"{a.account_code} — {a.account_name_ar}"}
            for p, a, _cl in rows if a.account_id not in parents]


@router.get("/{screen_code}/counterpart-accounts")
def counterpart_accounts(screen_code: str, direction: str = Query(..., pattern="^(inflow|outflow)$"),
                         transaction_type: str = Query(..., min_length=1, max_length=40),
                         treasury_account_id: int | None = Query(None, gt=0),
                         user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))),
                         db: Session = Depends(get_db)):
    """Return only accounts allowed for the selected transaction type and direction."""
    screen_account = _bound(db, screen_code)
    treasury = db.get(TreasuryAccount, treasury_account_id) if treasury_account_id else screen_account
    if treasury is None or not treasury.is_active or treasury.currency_code != screen_account.currency_code:
        raise HTTPException(400, "اختَر حساب بنك أو خزينة نشطًا بنفس عملة الشاشة")
    if not has_permission(db, user.user_id, treasury.screen_code, "Add"):
        raise HTTPException(403, "ليس لديك صلاحية إضافة حركة على حساب البنك أو الخزينة المحدد")
    config = USD_TRANSACTION_TYPES.get(transaction_type)
    if config is None or config["direction"] not in (direction, "either"):
        raise HTTPException(400, "نوع الحركة لا يتوافق مع اتجاه الوارد أو المنصرف")
    parents = select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))
    if transaction_type == "cash_transfer":
        # Transfers must target another configured USD treasury/bank account,
        # not an arbitrary ledger account that merely shares the cash classification.
        rows = db.execute(
            select(Account, AccountClassification)
            .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
            .join(TreasuryAccount, TreasuryAccount.gl_account_id == Account.account_id)
            .where(TreasuryAccount.is_active == True, TreasuryAccount.currency_code == treasury.currency_code,
                   TreasuryAccount.treasury_account_id != treasury.treasury_account_id,
                   Account.is_active == True, Account.account_id.not_in(parents))
            .order_by(Account.account_code).limit(500)
        ).all()
    else:
        rows = db.execute(
            select(Account, AccountClassification)
            .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
            .where(Account.is_active == True, Account.account_id != treasury.gl_account_id,
                   Account.account_id.not_in(parents),
                   Account.account_code.not_in(("32102001", "47101001")),
                   AccountClassification.name_ar.in_(config["classifications"]))
            .order_by(Account.account_code).limit(500)
        ).all()
    posting_side = "credit" if direction == "inflow" else "debit"
    side_ar = "دائن" if direction == "inflow" else "مدين"
    return [{"account_id": a.account_id, "label": f"{a.account_code} — {a.account_name_ar} ({side_ar})",
             "classification": cl.name_ar, "statement_type": cl.statement_type,
             "normal_balance": a.normal_balance, "posting_side": posting_side} for a, cl in rows]


@router.post("/{screen_code}/account", status_code=201)
def create_account(screen_code: str, body: AccountIn,
                   user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    if db.scalar(select(TreasuryAccount).where(TreasuryAccount.screen_code == screen_code)):
        raise HTTPException(409, "الشاشة دي مربوطة بحساب قبل كده")
    gl = _validate_cash_bank_gl(db, body.gl_account_id)
    _validate_treasury_gl_link(db, gl.account_id)
    if screen_code == "CashUsd" and gl.account_code != "15301002":
        raise HTTPException(400, "خزينة الدولار يجب ربطها بالحساب 15301002 — الصندوق - خزينة (دولار أمريكي)")
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
    _validate_treasury_gl_link(db, gl.account_id, exclude_treasury_account_id=a.treasury_account_id)
    if screen_code == "CashUsd" and gl.account_code != "15301002":
        raise HTTPException(400, "خزينة الدولار يجب ربطها بالحساب 15301002 — الصندوق - خزينة (دولار أمريكي)")
    _ensure_gl_relink_safe(db, a, gl.account_id)
    old = {"gl_account_id": a.gl_account_id}
    a.gl_account_id = gl.account_id
    write_audit(db, user.user_id, "Update", "TreasuryAccounts", a.treasury_account_id,
                old, {"gl_account_id": a.gl_account_id})
    db.commit()
    return acc_out(db, a)


@router.get("/{screen_code}/transactions")
def transactions(screen_code: str, date_from: date | None = None, date_to: date | None = None, q: str | None = None,
                 treasury_account_id: int | None = Query(None, gt=0),
                 skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                 user: User = Depends(require_dynamic("View", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    screen_account = _bound(db, screen_code)
    a = db.get(TreasuryAccount, treasury_account_id) if treasury_account_id else screen_account
    if a is None or not a.is_active or a.currency_code != screen_account.currency_code:
        raise HTTPException(400, "اختَر حساب بنك أو خزينة نشطًا بنفس عملة الشاشة")
    if not has_permission(db, user.user_id, a.screen_code, "View"):
        raise HTTPException(403, "ليس لديك صلاحية عرض حساب البنك أو الخزينة المحدد")
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
                    "treasury_account_id": a.treasury_account_id, "treasury_account_name": a.name_ar,
                    "treasury_account_type": a.account_type,
                    "inflow": money(t.inflow), "outflow": money(t.outflow), "balance": money(run),
                    "description": t.description, "voucher_no": t.voucher_no, "status": t.status,
                    "recipient_name": t.recipient_name, "project_id": t.project_id,
                    "transaction_type": t.transaction_type,
                    "exchange_rate": str(t.exchange_rate) if t.exchange_rate is not None else None,
                    "counterpart_account_id": t.counterpart_account_id,
                    "counterparty_id": t.counterparty_id,
                    "journal_entry_id": t.journal_entry_id,
                    "locked": t.journal_entry_id is not None})
    return {"total": len(out), "opening_balance": money(opening), "total_inflow": money(tin),
            "total_outflow": money(tout), "closing_balance": money(run), "items": out[skip:skip + limit]}


def _check_project(db: Session, pid: int | None):
    if pid is not None and db.get(Project, pid) is None:
        raise HTTPException(400, "مركز التكلفة غير موجود")


def _create_usd_journal(db: Session, a: TreasuryAccount, t: TreasuryTransaction,
                        body: TxIn, user: User, *, allow_legacy: bool = False) -> str:
    if body.exchange_rate is None or body.counterpart_account_id is None:
        raise HTTPException(422, "حركة الدولار تتطلب سعر الصرف وحساب الطرف المقابل")
    if body.counterpart_account_id == a.gl_account_id:
        raise HTTPException(422, "حساب الطرف المقابل لازم يختلف عن حساب الخزينة")
    counterpart = db.get(Account, body.counterpart_account_id)
    if counterpart is None or not counterpart.is_active:
        raise HTTPException(400, "حساب الطرف المقابل غير موجود أو غير نشط")
    if counterpart.account_id == a.gl_account_id or counterpart.account_code in ("32102001", "47101001"):
        raise HTTPException(400, "لا يمكن اختيار حساب الخزينة أو حساب فروق العملة المحققة كطرف مقابل يدوي")
    parents = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    if counterpart.account_id in parents:
        raise HTTPException(400, "حساب الطرف المقابل لازم يكون حسابًا فرعيًا")
    config = USD_TRANSACTION_TYPES.get(body.transaction_type or "")
    direction = "inflow" if body.inflow > 0 else "outflow"
    if config is None or config["direction"] not in (direction, "either"):
        raise HTTPException(422, "اختَر نوع حركة صحيحًا ومتوافقًا مع الوارد أو المنصرف")
    counterpart_class = db.get(AccountClassification, counterpart.classification_id)
    if body.transaction_type == "cash_transfer":
        target_treasury = db.scalar(select(TreasuryAccount).where(
            TreasuryAccount.gl_account_id == counterpart.account_id,
            TreasuryAccount.currency_code == "USD",
            TreasuryAccount.is_active == True,
            TreasuryAccount.treasury_account_id != a.treasury_account_id,
        ))
        if target_treasury is None:
            raise HTTPException(400, "التحويل لازم يكون إلى خزينة أو بنك آخر مُسجّل بالدولار")
    elif counterpart_class is None or counterpart_class.name_ar not in config["classifications"]:
        raise HTTPException(400, "الحساب المختار لا يتبع التصنيف المسموح لنوع الحركة")
    counterpart_posting_side = "credit" if direction == "inflow" else "debit"
    if counterpart_posting_side not in ("credit", "debit"):
        raise HTTPException(400, "اتجاه حركة الخزينة غير صحيح")

    # Prevent new movements while legacy movements or draft journals remain unprocessed.
    unlinked_stmt = select(func.count()).select_from(TreasuryTransaction).where(
        TreasuryTransaction.treasury_account_id == a.treasury_account_id,
        TreasuryTransaction.journal_entry_id.is_(None),
        TreasuryTransaction.transaction_id != t.transaction_id,
    )
    if allow_legacy:
        unlinked_stmt = unlinked_stmt.where(or_(
            TreasuryTransaction.transaction_date < t.transaction_date,
            (TreasuryTransaction.transaction_date == t.transaction_date)
            & (TreasuryTransaction.transaction_id < t.transaction_id),
        ))
    unlinked = db.scalar(unlinked_stmt) or 0
    if unlinked:
        raise HTTPException(409, "يوجد حركات دولار قديمة غير مرتبطة بقيود؛ راجعها واربطها أولًا")
    pending = db.scalar(select(func.count()).select_from(TreasuryTransaction).join(
        JournalEntry, JournalEntry.journal_entry_id == TreasuryTransaction.journal_entry_id
    ).where(TreasuryTransaction.treasury_account_id == a.treasury_account_id,
            JournalEntry.status == "Draft")) or 0
    if pending:
        raise HTTPException(409, "رحّل أو ألغِ مسودة القيد السابقة قبل تسجيل حركة دولار جديدة")

    from .journal import _fy_for, _next_no
    fy = _fy_for(db, body.transaction_date)
    amount_usd = body.inflow if body.inflow > 0 else body.outflow
    spot_egp = (amount_usd * body.exchange_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if spot_egp <= 0:
        raise HTTPException(422, "القيمة المقابلة بالجنيه لازم تكون أكبر من صفر")

    cash_egp = spot_egp
    cash_rate = body.exchange_rate
    fx_difference = Decimal("0")
    fx_account = None
    cash_is_debit = body.inflow > 0

    if not cash_is_debit:
        posted_rows = db.execute(
            select(JournalEntryDetail.fcy_amount, JournalEntryDetail.debit_amount,
                   JournalEntryDetail.credit_amount)
            .join(JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
            .where(JournalEntryDetail.account_id == a.gl_account_id,
                   JournalEntry.status == "Posted",
                   JournalEntryDetail.fcy_amount.is_not(None))
        ).all()
        usd_carrying = sum(
            (r.fcy_amount if r.debit_amount > 0 else -r.fcy_amount for r in posted_rows),
            Decimal("0"),
        )
        egp_carrying = sum(
            (r.debit_amount - r.credit_amount for r in posted_rows),
            Decimal("0"),
        )
        if usd_carrying < amount_usd or usd_carrying <= 0 or egp_carrying <= 0:
            raise HTTPException(409, "الرصيد الدولاري المرحّل غير كافٍ أو لا توجد تكلفة دفترية موثقة؛ راجع الرصيد الافتتاحي أولًا")
        carrying_rate = egp_carrying / usd_carrying
        cash_egp = (amount_usd * carrying_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cash_rate = (cash_egp / amount_usd).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        fx_difference = spot_egp - cash_egp
        if fx_difference > 0:
            fx_account = db.scalar(select(Account).where(Account.account_code == "32102001"))
        elif fx_difference < 0:
            fx_account = db.scalar(select(Account).where(Account.account_code == "47101001"))
        if fx_difference != 0:
            if fx_account is None or not fx_account.is_active or fx_account.account_id in parents:
                raise HTTPException(409, "حساب فروق العملة المعتمد غير موجود أو غير نشط في شجرة الحسابات")

    entry = JournalEntry(
        entry_no=_next_no(db, fy), entry_date=body.transaction_date,
        company_id=fy.company_id, fiscal_year_id=fy.fiscal_year_id,
        description=body.description or f"حركة خزينة {a.name_ar}",
        status="Draft", created_by=user.user_id,
    )
    db.add(entry)
    db.flush()
    db.add_all([
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=1,
            account_id=a.gl_account_id, project_id=body.project_id,
            debit_amount=cash_egp if cash_is_debit else Decimal("0"),
            credit_amount=Decimal("0") if cash_is_debit else cash_egp,
            fcy_amount=amount_usd, exchange_rate=cash_rate,
            description=f"{a.name_ar} — {amount_usd} USD",
        ),
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=2,
            account_id=counterpart.account_id, project_id=body.project_id,
            debit_amount=Decimal("0") if cash_is_debit else spot_egp,
            credit_amount=spot_egp if cash_is_debit else Decimal("0"),
            fcy_amount=amount_usd, exchange_rate=body.exchange_rate,
            description=body.description or "الطرف المقابل لحركة الخزينة",
        ),
    ])
    if fx_difference > 0:
        db.add(JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=3,
            account_id=fx_account.account_id, project_id=body.project_id,
            debit_amount=Decimal("0"), credit_amount=fx_difference,
            description="أرباح فروق عملة محققة",
        ))
    elif fx_difference < 0:
        db.add(JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=3,
            account_id=fx_account.account_id, project_id=body.project_id,
            debit_amount=abs(fx_difference), credit_amount=Decimal("0"),
            description="خسائر فروق عملة محققة",
        ))
    t.journal_entry_id = entry.journal_entry_id
    write_audit(db, user.user_id, "Create", "JournalEntries", entry.journal_entry_id, None,
                {"entry_no": entry.entry_no, "source": "TreasuryTransaction", "status": "Draft"})
    return entry.entry_no

def _egp_journal_sides(inflow: Decimal, outflow: Decimal) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Return treasury debit/credit and counterpart debit/credit for an EGP movement."""
    if (inflow > 0) == (outflow > 0):
        raise HTTPException(422, "الحركة إما وارد أو منصرف (مش الاتنين ومش صفر)")
    if inflow > 0:
        return inflow, D0, D0, inflow
    return D0, outflow, outflow, D0


def _create_egp_journal(db: Session, a: TreasuryAccount, t: TreasuryTransaction,
                        body: TxIn, user: User) -> str:
    """Create one draft GL journal for each newly-entered EGP treasury movement.

    Existing unlinked rows are intentionally not backfilled: they require a reviewed
    opening/migration reconciliation so historic entries are never duplicated.
    """
    if t.journal_entry_id is not None:
        raise HTTPException(409, "حركة الخزينة مرتبطة بقيد بالفعل؛ لا يمكن إنشاء قيد مكرر")
    if body.counterpart_account_id is None or not body.transaction_type:
        raise HTTPException(422, "حركة خزينة الجنيه تتطلب نوع الحركة وحساب الطرف المقابل")
    if body.counterpart_account_id == a.gl_account_id:
        raise HTTPException(422, "حساب الطرف المقابل لازم يختلف عن حساب الخزينة")
    counterpart = db.get(Account, body.counterpart_account_id)
    if counterpart is None or not counterpart.is_active:
        raise HTTPException(400, "حساب الطرف المقابل غير موجود أو غير نشط")
    parents = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    if counterpart.account_id in parents:
        raise HTTPException(400, "حساب الطرف المقابل لازم يكون حسابًا فرعيًا")
    config = USD_TRANSACTION_TYPES.get(body.transaction_type)
    direction = "inflow" if body.inflow > 0 else "outflow"
    if config is None or config["direction"] not in (direction, "either"):
        raise HTTPException(422, "اختَر نوع حركة صحيحًا ومتوافقًا مع الوارد أو المنصرف")
    if body.transaction_type == "cash_transfer":
        target = db.scalar(select(TreasuryAccount).where(
            TreasuryAccount.gl_account_id == counterpart.account_id,
            TreasuryAccount.currency_code == a.currency_code,
            TreasuryAccount.is_active == True,
            TreasuryAccount.treasury_account_id != a.treasury_account_id,
        ))
        if target is None:
            raise HTTPException(400, "التحويل لازم يكون إلى خزينة أو بنك آخر مسجل بنفس العملة")
    else:
        classification = db.get(AccountClassification, counterpart.classification_id)
        if classification is None or classification.name_ar not in config["classifications"]:
            raise HTTPException(400, "الحساب المختار لا يتبع التصنيف المسموح لنوع الحركة")

    from .journal import _fy_for, _next_no
    fy = _fy_for(db, body.transaction_date)
    entry = JournalEntry(
        entry_no=_next_no(db, fy), entry_date=body.transaction_date,
        company_id=fy.company_id, fiscal_year_id=fy.fiscal_year_id,
        description=body.description or f"حركة خزينة {a.name_ar}",
        status="Draft", created_by=user.user_id,
    )
    db.add(entry)
    db.flush()
    td, tc, cd, cc = _egp_journal_sides(body.inflow, body.outflow)
    db.add_all([
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=1,
            account_id=a.gl_account_id, project_id=body.project_id,
            debit_amount=td, credit_amount=tc,
            description=f"{a.name_ar} — حركة بالجنيه المصري",
        ),
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id, line_no=2,
            account_id=counterpart.account_id, project_id=body.project_id,
            debit_amount=cd, credit_amount=cc,
            description=body.description or "الطرف المقابل لحركة الخزينة",
        ),
    ])
    t.journal_entry_id = entry.journal_entry_id
    write_audit(db, user.user_id, "Create", "JournalEntries", entry.journal_entry_id, None,
                {"entry_no": entry.entry_no, "source": "TreasuryTransaction", "status": "Draft"})
    return entry.entry_no


def _create_egp_transfer_mirror(db: Session, source: TreasuryAccount, original: TreasuryTransaction,
                                  body: TxIn, user: User) -> TreasuryTransaction | None:
    """Create the opposite operational bank/cash movement for an EGP transfer.

    Both operational rows share the single balanced journal created for the
    original movement. This is intentionally applied only to new transfers;
    historical one-sided rows are never backfilled automatically.
    """
    if body.transaction_type != "cash_transfer":
        return None
    target = db.scalar(select(TreasuryAccount).where(
        TreasuryAccount.gl_account_id == body.counterpart_account_id,
        TreasuryAccount.currency_code == source.currency_code,
        TreasuryAccount.is_active == True,
        TreasuryAccount.treasury_account_id != source.treasury_account_id,
    ))
    if target is None:
        raise HTTPException(400, "حساب التحويل المقابل غير مربوط بخزينة أو بنك نشط بنفس العملة")
    if original.journal_entry_id is None:
        raise HTTPException(409, "لا يمكن إنشاء الحركة المقابلة قبل إنشاء قيد اليومية")
    mirror = TreasuryTransaction(
        treasury_account_id=target.treasury_account_id,
        transaction_date=body.transaction_date,
        inflow=body.outflow,
        outflow=body.inflow,
        description=body.description or f"تحويل مقابل من {source.name_ar}",
        voucher_no=body.voucher_no,
        status=body.status,
        recipient_name=body.recipient_name,
        project_id=body.project_id,
        counterpart_account_id=source.gl_account_id,
        transaction_type="cash_transfer",
        journal_entry_id=original.journal_entry_id,
    )
    db.add(mirror)
    db.flush()
    write_audit(db, user.user_id, "Create", "TreasuryTransactions", mirror.transaction_id, None, {
        "source": "EGPTransferMirror",
        "source_transaction_id": original.transaction_id,
        "journal_entry_id": original.journal_entry_id,
        "treasury_account_id": target.treasury_account_id,
        "inflow": str(mirror.inflow),
        "outflow": str(mirror.outflow),
    })
    return mirror


@router.post("/{screen_code}/transactions", status_code=201)
def add_tx(screen_code: str, body: TxIn, user: User = Depends(require_dynamic("Add", set(BANK_SCREENS))),
           db: Session = Depends(get_db)):
    screen_account = _bound(db, screen_code)
    a = db.get(TreasuryAccount, body.treasury_account_id) if body.treasury_account_id else screen_account
    if a is None or not a.is_active or a.currency_code != screen_account.currency_code:
        raise HTTPException(400, "اختَر حساب بنك أو خزينة نشطًا بنفس عملة الشاشة")
    if not has_permission(db, user.user_id, a.screen_code, "Add"):
        raise HTTPException(403, "ليس لديك صلاحية إضافة حركة على حساب البنك أو الخزينة المحدد")
    _check_project(db, body.project_id)
    values = body.model_dump(exclude={"treasury_account_id"})
    # Customer/supplier settlements must be tied to a master record; derive the GL account from it.
    party_required_types = {"customer_collection", "customer_advance", "supplier_payment", "supplier_advance"}
    if body.transaction_type in party_required_types and not body.counterparty_id:
        raise HTTPException(422, "اختَر بطاقة العميل أو المورد/المقاول لربط الحركة بحسابه الصحيح")
    # Resolve the counterpart GL automatically from the selected customer/supplier master.
    if body.counterparty_id:
        party = db.get(Counterparty, body.counterparty_id)
        if not party or not party.is_active:
            raise HTTPException(422, "العميل/المورد المحدد غير موجود أو غير نشط")
        expected_types = {
            "customer_collection": ("Customer", "Mixed"),
            "customer_advance": ("Customer", "Mixed"),
            "supplier_payment": ("Supplier", "Contractor", "Mixed"),
            "supplier_advance": ("Supplier", "Contractor", "Mixed"),
        }
        if body.transaction_type in expected_types and party.party_type not in expected_types[body.transaction_type]:
            raise HTTPException(422, "نوع بطاقة الطرف لا يتوافق مع نوع الحركة")
        linked = party.linked_account_id or party.account_id
        if not linked:
            raise HTTPException(422, "اربط الطرف بحساب فرعي في شجرة الحسابات أولًا")
        linked_account = db.get(Account, linked)
        if linked_account is None or not linked_account.is_active:
            raise HTTPException(422, "حساب الأستاذ المرتبط بالطرف غير موجود أو غير نشط")
        if db.scalar(select(Account.account_id).where(Account.parent_account_id == linked).limit(1)):
            raise HTTPException(422, "حساب الطرف المرتبط يجب أن يكون حسابًا فرعيًا")
        if body.counterpart_account_id and body.counterpart_account_id != linked:
            raise HTTPException(422, "حساب الطرف لا يطابق الحساب المرتبط به في بطاقة العميل/المورد")
        values["counterpart_account_id"] = linked
        body.counterpart_account_id = linked
    t = TreasuryTransaction(treasury_account_id=a.treasury_account_id, **values)
    db.add(t)
    db.flush()
    journal_no = (_create_usd_journal(db, a, t, body, user) if a.currency_code == "USD"
                  else _create_egp_journal(db, a, t, body, user))
    if a.currency_code == "EGP":
        _create_egp_transfer_mirror(db, a, t, body, user)
    write_audit(db, user.user_id, "Create", "TreasuryTransactions", t.transaction_id, None, body.model_dump())
    db.commit()
    return {"transaction_id": t.transaction_id, "journal_entry_id": t.journal_entry_id,
            "journal_entry_no": journal_no, "journal_status": "Draft" if journal_no else None}


def _tx(db: Session, screen_code: str, tid: int) -> TreasuryTransaction:
    screen_account = _bound(db, screen_code)
    t = db.get(TreasuryTransaction, tid)
    movement_account = db.get(TreasuryAccount, t.treasury_account_id) if t else None
    if (t is None or movement_account is None or not movement_account.is_active
            or movement_account.currency_code != screen_account.currency_code):
        raise HTTPException(404, "الحركة غير موجودة")
    if t.journal_entry_id is not None:
        raise HTTPException(409, "الحركة مرتبطة بقيد يومية — مينفعش تتعدّل أو تتحذف")
    return t


@router.put("/{screen_code}/transactions/{tid}")
def edit_tx(screen_code: str, tid: int, body: TxIn,
            user: User = Depends(require_dynamic("Edit", set(BANK_SCREENS))), db: Session = Depends(get_db)):
    t = _tx(db, screen_code, tid)
    screen_account = _bound(db, screen_code)
    target_account = db.get(TreasuryAccount, body.treasury_account_id) if body.treasury_account_id else screen_account
    if target_account is None or not target_account.is_active or target_account.currency_code != screen_account.currency_code:
        raise HTTPException(400, "اختَر حساب بنك أو خزينة نشطًا بنفس عملة الشاشة")
    if not has_permission(db, user.user_id, target_account.screen_code, "Edit"):
        raise HTTPException(403, "ليس لديك صلاحية تعديل حركات حساب البنك أو الخزينة المحدد")
    _check_project(db, body.project_id)
    old = {"inflow": str(t.inflow), "outflow": str(t.outflow), "description": t.description,
           "treasury_account_id": t.treasury_account_id}
    for k, v in body.model_dump(exclude={"treasury_account_id"}).items():
        setattr(t, k, v)
    t.treasury_account_id = target_account.treasury_account_id
    journal_no = _create_usd_journal(db, target_account, t, body, user, allow_legacy=True) if target_account.currency_code == "USD" else None
    write_audit(db, user.user_id, "Update", "TreasuryTransactions", tid, old, body.model_dump())
    db.commit()
    return {"transaction_id": tid, "journal_entry_no": journal_no, "journal_status": "Draft" if journal_no else None}


@router.delete("/{screen_code}/transactions/{tid}", status_code=204)
def del_tx(screen_code: str, tid: int, user: User = Depends(require_dynamic("Delete", set(BANK_SCREENS))),
           db: Session = Depends(get_db)):
    t = _tx(db, screen_code, tid)
    movement_account = db.get(TreasuryAccount, t.treasury_account_id)
    if not movement_account or not has_permission(db, user.user_id, movement_account.screen_code, "Delete"):
        raise HTTPException(403, "ليس لديك صلاحية حذف حركات حساب البنك أو الخزينة المحدد")
    write_audit(db, user.user_id, "Delete", "TreasuryTransactions", tid,
                {"inflow": str(t.inflow), "outflow": str(t.outflow)}, None)
    db.delete(t)
    db.commit()
