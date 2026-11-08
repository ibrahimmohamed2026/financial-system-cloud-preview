from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.routers import treasury


class ScalarRows(list):
    def all(self):
        return list(self)


class USDJournalDB:
    def __init__(self, scalar_values, posted_rows):
        self.scalar_values = list(scalar_values)
        self.posted_rows = posted_rows
        self.added = []
        self.added_many = []
        self.next_id = 700

    def get(self, model, key):
        if model is treasury.Account:
            return self.accounts.get(key)
        if model is treasury.AccountClassification:
            return self.classification
        return None

    def scalars(self, statement):
        return ScalarRows()

    def scalar(self, statement):
        return self.scalar_values.pop(0) if self.scalar_values else 0

    def execute(self, statement):
        return SimpleNamespace(all=lambda: list(self.posted_rows))

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added_many.extend(values)

    def flush(self):
        self.next_id += 1
        for value in self.added:
            if isinstance(value, treasury.JournalEntry) and value.journal_entry_id is None:
                value.journal_entry_id = self.next_id


def _usd_setup(monkeypatch, *, carrying_egp, transfer=False):
    supplier_class = SimpleNamespace(classification_id=7, name_ar="موردون و اوراق دفع")
    cash_class = SimpleNamespace(classification_id=8, name_ar="نقدية بالصندوق و البنوك")
    counterpart = SimpleNamespace(
        account_id=20, account_code="21002001", account_name_ar="الطرف المقابل",
        is_active=True, classification_id=8 if transfer else 7,
    )
    fx_account = SimpleNamespace(account_id=30, account_code="32102001", is_active=True)
    source = SimpleNamespace(
        treasury_account_id=1, gl_account_id=10, name_ar="بنك الدولار",
        currency_code="USD", is_active=True,
    )
    target = SimpleNamespace(
        treasury_account_id=2, gl_account_id=20, name_ar="خزينة الدولار",
        currency_code="USD", is_active=True,
    )
    fy = SimpleNamespace(company_id=1, fiscal_year_id=2026)
    rows = [SimpleNamespace(
        fcy_amount=Decimal("100"), debit_amount=Decimal(str(carrying_egp)),
        credit_amount=Decimal("0"),
    )]
    scalar_values = [0, 0]
    if transfer:
        scalar_values.extend([target, source])
    else:
        scalar_values.append(fx_account)
    db = USDJournalDB(scalar_values, rows)
    db.accounts = {20: counterpart}
    db.classification = supplier_class if not transfer else cash_class
    user = SimpleNamespace(user_id=5)

    monkeypatch.setattr(treasury, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.routers.journal._fy_for", lambda *args: fy)
    monkeypatch.setattr("app.routers.journal._next_no", lambda *args: "JE-2026-TEST")
    return db, source, target, user


def _usd_body(kind, *, outflow="10", rate="52"):
    return treasury.TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=Decimal("0"),
        outflow=Decimal(outflow),
        exchange_rate=Decimal(rate),
        counterpart_account_id=20,
        transaction_type=kind,
        description="اختبار فروق عملة",
    )


def _totals(lines):
    debit = sum((line.debit_amount for line in lines), Decimal("0"))
    credit = sum((line.credit_amount for line in lines), Decimal("0"))
    assert debit == credit
    return debit, credit


def test_usd_supplier_payment_recognizes_realized_fx_gain(monkeypatch):
    db, source, _target, user = _usd_setup(monkeypatch, carrying_egp="5000")
    movement = SimpleNamespace(journal_entry_id=None)

    treasury._create_usd_journal(
        db, source, movement, _usd_body("supplier_payment", outflow="10", rate="52"), user,
    )

    lines = db.added_many
    assert len(lines) == 3
    assert [(line.account_id, line.debit_amount, line.credit_amount) for line in lines] == [
        (10, Decimal("0"), Decimal("500.00")),
        (20, Decimal("520.00"), Decimal("0")),
        (30, Decimal("0"), Decimal("20.00")),
    ]
    _totals(lines)
    assert movement.journal_entry_id is not None


def test_usd_supplier_payment_recognizes_realized_fx_loss(monkeypatch):
    db, source, _target, user = _usd_setup(monkeypatch, carrying_egp="5400")
    movement = SimpleNamespace(journal_entry_id=None)

    treasury._create_usd_journal(
        db, source, movement, _usd_body("supplier_payment", outflow="10", rate="52"), user,
    )

    lines = db.added_many
    assert len(lines) == 3
    assert [(line.account_id, line.debit_amount, line.credit_amount) for line in lines] == [
        (10, Decimal("0"), Decimal("540.00")),
        (20, Decimal("520.00"), Decimal("0")),
        (30, Decimal("20.00"), Decimal("0")),
    ]
    _totals(lines)


def test_usd_cash_transfer_carries_book_value_without_realized_fx(monkeypatch):
    db, source, _target, user = _usd_setup(monkeypatch, carrying_egp="5000", transfer=True)
    movement = SimpleNamespace(journal_entry_id=None)

    treasury._create_usd_journal(
        db, source, movement, _usd_body("cash_transfer", outflow="10", rate="60"), user,
    )

    lines = db.added_many
    assert len(lines) == 2
    assert [(line.account_id, line.debit_amount, line.credit_amount) for line in lines] == [
        (10, Decimal("0"), Decimal("500.00")),
        (20, Decimal("500.00"), Decimal("0")),
    ]
    _totals(lines)
    assert all(line.exchange_rate == Decimal("50.000000") for line in lines)
