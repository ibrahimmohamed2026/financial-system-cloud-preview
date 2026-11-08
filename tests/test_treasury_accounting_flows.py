from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.routers import treasury


class FakeDB:
    def __init__(self, counterpart, classification, transfer_target=None):
        self.counterpart = counterpart
        self.classification = classification
        self.transfer_target = transfer_target
        self.added = []
        self.added_many = []
        self.next_id = 100

    def get(self, model, key):
        if model is treasury.Account:
            return self.counterpart if key == self.counterpart.account_id else None
        if model is treasury.AccountClassification:
            return self.classification if key == self.counterpart.classification_id else None
        return None

    def scalars(self, statement):
        return SimpleNamespace(all=lambda: [])

    def scalar(self, statement):
        return self.transfer_target

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added_many.extend(values)

    def flush(self):
        self.next_id += 1
        for value in self.added:
            if isinstance(value, treasury.JournalEntry) and value.journal_entry_id is None:
                value.journal_entry_id = self.next_id
            if isinstance(value, treasury.TreasuryTransaction) and value.transaction_id is None:
                value.transaction_id = self.next_id


def _setup(monkeypatch, classification_name, counterpart_id=20, transfer_target=None):
    classification = SimpleNamespace(classification_id=7, name_ar=classification_name)
    counterpart = SimpleNamespace(
        account_id=counterpart_id, account_code=str(counterpart_id),
        account_name_ar="حساب مقابل", is_active=True, classification_id=7,
    )
    db = FakeDB(counterpart, classification, transfer_target)
    fy = SimpleNamespace(company_id=1, fiscal_year_id=2026)
    monkeypatch.setattr(treasury, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.routers.journal._fy_for", lambda *args: fy)
    monkeypatch.setattr("app.routers.journal._next_no", lambda *args: "JV-TEST-0001")
    account = SimpleNamespace(
        treasury_account_id=1, gl_account_id=10, name_ar="البنك الرئيسي",
        currency_code="EGP",
    )
    user = SimpleNamespace(user_id=5)
    return db, account, user, counterpart


def _body(kind, *, inflow="0", outflow="0", counterpart_id=20):
    return treasury.TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=Decimal(inflow), outflow=Decimal(outflow),
        transaction_type=kind, counterpart_account_id=counterpart_id,
        description="اختبار حركة خزينة",
    )


def _assert_balanced(details):
    debit = sum((line.debit_amount for line in details), Decimal("0"))
    credit = sum((line.credit_amount for line in details), Decimal("0"))
    assert debit == credit


def test_customer_collection_posts_bank_debit_customer_credit(monkeypatch):
    db, account, user, counterpart = _setup(monkeypatch, "عملاء وأوراق قبض")
    movement = SimpleNamespace(journal_entry_id=None)

    entry_no = treasury._create_egp_journal(
        db, account, movement, _body("customer_collection", inflow="100000"),
        user,
    )

    assert entry_no == "JV-TEST-0001"
    details = db.added_many
    assert len(details) == 2
    assert [(d.account_id, d.debit_amount, d.credit_amount) for d in details] == [
        (10, Decimal("100000"), Decimal("0")),
        (20, Decimal("0"), Decimal("100000")),
    ]
    _assert_balanced(details)
    assert movement.journal_entry_id is not None


def test_supplier_payment_posts_supplier_debit_bank_credit(monkeypatch):
    db, account, user, counterpart = _setup(monkeypatch, "موردون و اوراق دفع")
    movement = SimpleNamespace(journal_entry_id=None)

    treasury._create_egp_journal(
        db, account, movement, _body("supplier_payment", outflow="50000"),
        user,
    )

    details = db.added_many
    assert len(details) == 2
    assert [(d.account_id, d.debit_amount, d.credit_amount) for d in details] == [
        (10, Decimal("0"), Decimal("50000")),
        (20, Decimal("50000"), Decimal("0")),
    ]
    _assert_balanced(details)


def test_egp_bank_to_cash_transfer_posts_one_journal_and_two_cash_movements(monkeypatch):
    target = SimpleNamespace(
        treasury_account_id=2, gl_account_id=20, name_ar="الخزينة",
        currency_code="EGP", is_active=True,
    )
    db, account, user, counterpart = _setup(
        monkeypatch, "نقدية بالصندوق و البنوك", transfer_target=target,
    )
    movement = SimpleNamespace(
        transaction_id=1, journal_entry_id=None, transaction_date=date(2026, 11, 8),
        inflow=Decimal("0"), outflow=Decimal("30000"), description="تحويل للخزينة",
        voucher_no="TR-1", status="تم", recipient_name=None, project_id=None,
    )
    body = _body("cash_transfer", outflow="30000")

    treasury._create_egp_journal(db, account, movement, body, user)
    mirror = treasury._create_egp_transfer_mirror(db, account, movement, body, user)

    details = db.added_many
    assert len(details) == 2
    assert [(d.account_id, d.debit_amount, d.credit_amount) for d in details] == [
        (10, Decimal("0"), Decimal("30000")),
        (20, Decimal("30000"), Decimal("0")),
    ]
    _assert_balanced(details)
    assert mirror.treasury_account_id == 2
    assert mirror.inflow == Decimal("0")
    assert mirror.outflow == Decimal("30000")
    assert mirror.counterpart_account_id == 10
    assert mirror.journal_entry_id == movement.journal_entry_id
