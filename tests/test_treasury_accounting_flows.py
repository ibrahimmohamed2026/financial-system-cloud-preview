from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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
        class ScalarRows(list):
            def all(self):
                return list(self)
        return ScalarRows()

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
    assert mirror.inflow == Decimal("30000")
    assert mirror.outflow == Decimal("0")
    assert mirror.counterpart_account_id == 10
    assert mirror.journal_entry_id == movement.journal_entry_id


def test_cash_transfer_api_direction_is_source_outflow_only():
    assert treasury.USD_TRANSACTION_TYPES["cash_transfer"]["direction"] == "either"
    assert treasury._movement_direction_allowed("cash_transfer", "outflow")
    assert not treasury._movement_direction_allowed("cash_transfer", "inflow")


def test_party_reference_is_optional_and_counterpart_options_come_from_chart(monkeypatch):
    party = SimpleNamespace(
        counterparty_id=7, party_type="Customer", is_active=True,
        linked_account_id=20, account_id=21,
    )
    linked = SimpleNamespace(
        account_id=20, account_code="15401001", account_name_ar="عميل محدد",
        classification_id=8, is_active=True, normal_balance="DR",
    )
    classification = SimpleNamespace(
        name_ar="عملاء وأوراق قبض", statement_type="BalanceSheet",
    )
    screen = SimpleNamespace(
        treasury_account_id=1, gl_account_id=10, currency_code="EGP",
        is_active=True, screen_code="BankCibEgp",
    )

    class DB:
        def get(self, model, key):
            if model is treasury.TreasuryAccount:
                return screen
            if model is treasury.Counterparty:
                return party if key == 7 else None
            if model is treasury.Account:
                return linked if key == 20 else None
            if model is treasury.AccountClassification:
                return classification if key == 8 else None
            return None

        def scalar(self, statement):
            return None

        def scalars(self, statement):
            return []

        def execute(self, statement):
            return SimpleNamespace(all=lambda: [(linked, classification)])

    db = DB()
    user = SimpleNamespace(user_id=5)
    monkeypatch.setattr(treasury, "_bound", lambda *_: screen)
    monkeypatch.setattr(treasury, "has_permission", lambda *_: True)

    rows_without_card = treasury.counterpart_accounts(
        "BankCibEgp", direction="inflow", transaction_type="customer_collection",
        counterparty_id=None, user=user, db=db,
    )
    rows_with_reference = treasury.counterpart_accounts(
        "BankCibEgp", direction="inflow", transaction_type="customer_collection",
        counterparty_id=7, user=user, db=db,
    )
    assert rows_without_card == rows_with_reference
    assert len(rows_without_card) == 1
    assert rows_without_card[0]["account_id"] == 20
    assert "15401001" in rows_without_card[0]["label"]
    assert "دائن بالقيد" in rows_without_card[0]["label"]



def test_optional_party_reference_does_not_supply_the_account():
    body = treasury.TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=Decimal("100"),
        outflow=Decimal("0"),
        transaction_type="customer_collection",
        counterpart_account_id=20,
    )

    class DB:
        def get(self, model, key):
            raise AssertionError("No party lookup should happen when reference is omitted")

    treasury._validate_optional_counterparty_reference(DB(), body)
    assert body.counterpart_account_id == 20
    assert body.counterparty_id is None


def test_optional_party_reference_only_checks_consistency_with_selected_chart_account():
    party = SimpleNamespace(
        is_active=True, party_type="Customer", linked_account_id=20,
    )

    class DB:
        def get(self, model, key):
            return party if model is treasury.Counterparty and key == 7 else None

    matching = treasury.TxIn(
        transaction_date=date(2026, 11, 8), inflow=Decimal("100"), outflow=Decimal("0"),
        transaction_type="customer_collection", counterpart_account_id=20, counterparty_id=7,
    )
    treasury._validate_optional_counterparty_reference(DB(), matching)

    mismatching = treasury.TxIn(
        transaction_date=date(2026, 11, 8), inflow=Decimal("100"), outflow=Decimal("0"),
        transaction_type="customer_collection", counterpart_account_id=21, counterparty_id=7,
    )
    with pytest.raises(HTTPException) as exc:
        treasury._validate_optional_counterparty_reference(DB(), mismatching)
    assert exc.value.status_code == 422
