from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models import Account, AccountClassification, JournalEntry
from app.routers.treasury import (
    BANK_SCREENS,
    USD_TRANSACTION_TYPES,
    TxIn,
    _create_egp_journal,
    _create_usd_journal,
    _create_usd_transfer_mirror,
)


@pytest.mark.parametrize(
    ("transaction_type", "direction"),
    [
        ("funding", "inflow"),
        ("customer_collection", "inflow"),
        ("customer_advance", "inflow"),
        ("direct_income", "inflow"),
        ("supplier_payment", "outflow"),
        ("supplier_advance", "outflow"),
        ("expense_payment", "outflow"),
        ("asset_purchase", "outflow"),
        ("cash_transfer", "either"),
    ],
)
def test_all_nine_movement_types_are_descriptive_only(transaction_type, direction):
    from app.routers.treasury import TREASURY_MOVEMENT_TYPES, _movement_direction_allowed

    assert transaction_type in TREASURY_MOVEMENT_TYPES
    assert _movement_direction_allowed(transaction_type, "inflow")
    assert _movement_direction_allowed(transaction_type, "outflow")


@pytest.mark.parametrize(
    ("screen_code", "expected_currency"),
    [
        ("BankCibEgp", "EGP"),
        ("CashUsd", "USD"),
        ("CashEgp", "EGP"),
        ("BankCibUsd", "USD"),
    ],
)
def test_only_four_fixed_bank_and_cash_screens_are_registered_with_expected_currency(
    screen_code, expected_currency
):
    assert BANK_SCREENS[screen_code][1] == expected_currency


@pytest.mark.parametrize(
    ("inflow", "outflow", "cash_debit", "counterpart_debit"),
    [
        (Decimal("0"), Decimal("100"), Decimal("0"), Decimal("1000")),
        (Decimal("100"), Decimal("0"), Decimal("1000"), Decimal("0")),
    ],
)
def test_usd_transfer_journal_uses_source_carrying_value_without_realized_fx(
    monkeypatch, inflow, outflow, cash_debit, counterpart_debit
):
    import app.routers.treasury as treasury_module
    import app.routers.journal as journal_module

    monkeypatch.setattr(journal_module, "_fy_for", lambda db, entry_date:
                        SimpleNamespace(company_id=1, fiscal_year_id=2026))
    monkeypatch.setattr(journal_module, "_next_no", lambda db, fiscal_year: "JE-USD-000001")
    monkeypatch.setattr(treasury_module, "write_audit", lambda *args, **kwargs: None)

    target = SimpleNamespace(treasury_account_id=8, gl_account_id=20, currency_code="USD",
                             is_active=True, name_ar="البنك المستلم")
    source = SimpleNamespace(treasury_account_id=3, gl_account_id=10, currency_code="USD",
                             is_active=True, name_ar="البنك المصدر")
    counterpart = SimpleNamespace(account_id=20, account_code="15301003",
                                  is_active=True, classification_id=1)
    db = MagicMock()
    db.get.side_effect = lambda model, key: counterpart if model is Account else None
    db.scalar.side_effect = [target, 0, 0, source, 0, 0]
    db.scalars.return_value = []
    db.execute.return_value.all.return_value = [
        SimpleNamespace(fcy_amount=Decimal("1000"), debit_amount=Decimal("10000"),
                        credit_amount=Decimal("0"))
    ]

    def assign_entry_id(value):
        if isinstance(value, JournalEntry):
            value.journal_entry_id = 77

    db.add.side_effect = assign_entry_id
    movement = SimpleNamespace(transaction_id=41, journal_entry_id=None)
    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=inflow,
        outflow=outflow,
        exchange_rate=Decimal("50"),
        counterpart_account_id=20,
        transaction_type="cash_transfer",
        description="تحويل بين بنكين بالدولار",
    )

    entry_no = _create_usd_journal(db, source, movement, body, SimpleNamespace(user_id=7))

    assert entry_no == "JE-USD-000001"
    assert movement.journal_entry_id == 77
    lines = db.add_all.call_args.args[0]
    assert len(lines) == 2
    assert lines[0].debit_amount == cash_debit
    assert lines[0].credit_amount == (Decimal("1000") if inflow == 0 else Decimal("0"))
    assert lines[1].debit_amount == counterpart_debit
    assert lines[1].credit_amount == (Decimal("1000") if inflow > 0 else Decimal("0"))
    assert sum(x.debit_amount for x in lines) == sum(x.credit_amount for x in lines)
    assert all(x.exchange_rate == Decimal("10.000000") for x in lines)
    assert all(x.fcy_amount == Decimal("100") for x in lines)


@pytest.mark.parametrize(
    ("inflow", "outflow", "mirror_inflow", "mirror_outflow"),
    [
        (Decimal("0"), Decimal("100"), Decimal("100"), Decimal("0")),
        (Decimal("100"), Decimal("0"), Decimal("0"), Decimal("100")),
    ],
)
def test_usd_transfer_creates_opposite_operational_movement(
    monkeypatch, inflow, outflow, mirror_inflow, mirror_outflow
):
    import app.routers.treasury as treasury_module

    monkeypatch.setattr(treasury_module, "write_audit", lambda *args, **kwargs: None)
    db = MagicMock()
    target = SimpleNamespace(treasury_account_id=8, name_ar="البنك المستلم",
                             gl_account_id=20, currency_code="USD", is_active=True)
    db.scalar.return_value = target
    source = SimpleNamespace(treasury_account_id=3, name_ar="البنك المصدر",
                             gl_account_id=10, currency_code="USD")
    original = SimpleNamespace(transaction_id=41, journal_entry_id=99)
    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=inflow,
        outflow=outflow,
        exchange_rate=Decimal("50"),
        counterpart_account_id=20,
        transaction_type="cash_transfer",
        description="تحويل بالدولار",
        voucher_no="USD-TR-01",
    )

    mirror = _create_usd_transfer_mirror(
        db, source, original, body, SimpleNamespace(user_id=7)
    )

    assert mirror.treasury_account_id == 8
    assert mirror.inflow == mirror_inflow
    assert mirror.outflow == mirror_outflow
    assert mirror.counterpart_account_id == 10
    assert mirror.transaction_type == "cash_transfer"
    assert mirror.journal_entry_id == 99
    assert mirror.exchange_rate == Decimal("50")
    db.add.assert_called_once_with(mirror)
    db.flush.assert_called_once()


def test_usd_movement_with_non_treasury_counterpart_does_not_create_transfer_mirror():
    db = MagicMock()
    db.scalar.return_value = None
    source = SimpleNamespace(treasury_account_id=3, gl_account_id=10, currency_code="USD")
    original = SimpleNamespace(transaction_id=41, journal_entry_id=99)
    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=0,
        outflow=100,
        exchange_rate=50,
        counterpart_account_id=20,
        transaction_type="cash_transfer",
    )

    mirror = _create_usd_transfer_mirror(db, source, original, body, SimpleNamespace(user_id=7))
    assert mirror is None
    db.add.assert_not_called()



@pytest.mark.parametrize("transaction_type", list(USD_TRANSACTION_TYPES))
def test_egp_journal_builder_creates_balanced_entry_for_every_movement_type(
    monkeypatch, transaction_type
):
    import app.routers.treasury as treasury_module
    import app.routers.journal as journal_module

    config = USD_TRANSACTION_TYPES[transaction_type]
    direction = config["direction"]
    inflow = Decimal("1250") if direction == "inflow" else Decimal("0")
    outflow = Decimal("1250") if direction == "outflow" else Decimal("0")
    if direction == "either":
        outflow = Decimal("1250")

    monkeypatch.setattr(journal_module, "_fy_for", lambda db, entry_date:
                        SimpleNamespace(company_id=1, fiscal_year_id=2026))
    monkeypatch.setattr(journal_module, "_next_no", lambda db, fiscal_year: "JE-EGP-ALL")
    monkeypatch.setattr(treasury_module, "write_audit", lambda *args, **kwargs: None)

    counterpart = SimpleNamespace(account_id=20, is_active=True, classification_id=4)
    classification = SimpleNamespace(name_ar=config["classifications"][0])
    db = MagicMock()
    db.get.side_effect = lambda model, key: (
        counterpart if model is Account else
        classification if model is AccountClassification else None
    )
    db.scalars.return_value = []
    if transaction_type == "cash_transfer":
        db.scalar.return_value = SimpleNamespace(
            treasury_account_id=8, gl_account_id=20, currency_code="EGP",
            is_active=True, name_ar="البنك المستلم"
        )

    def assign_entry_id(value):
        if isinstance(value, JournalEntry):
            value.journal_entry_id = 88

    db.add.side_effect = assign_entry_id
    movement = SimpleNamespace(journal_entry_id=None)
    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=inflow,
        outflow=outflow,
        counterpart_account_id=20,
        transaction_type=transaction_type,
    )
    treasury = SimpleNamespace(
        gl_account_id=10, name_ar="حساب نقدي", currency_code="EGP",
        treasury_account_id=3,
    )

    _create_egp_journal(db, treasury, movement, body, SimpleNamespace(user_id=7))

    lines = db.add_all.call_args.args[0]
    assert len(lines) == 2
    assert sum(line.debit_amount for line in lines) == sum(
        line.credit_amount for line in lines
    )


@pytest.mark.parametrize("transaction_type", list(USD_TRANSACTION_TYPES))
def test_usd_journal_builder_creates_balanced_entry_for_every_movement_type(
    monkeypatch, transaction_type
):
    import app.routers.treasury as treasury_module
    import app.routers.journal as journal_module

    config = USD_TRANSACTION_TYPES[transaction_type]
    direction = config["direction"]
    inflow = Decimal("1000") if direction == "inflow" else Decimal("0")
    outflow = Decimal("1000") if direction == "outflow" else Decimal("0")
    if direction == "either":
        outflow = Decimal("1000")

    monkeypatch.setattr(journal_module, "_fy_for", lambda db, entry_date:
                        SimpleNamespace(company_id=1, fiscal_year_id=2026))
    monkeypatch.setattr(journal_module, "_next_no", lambda db, fiscal_year: "JE-USD-ALL")
    monkeypatch.setattr(treasury_module, "write_audit", lambda *args, **kwargs: None)

    counterpart = SimpleNamespace(account_id=20, account_code="15301003",
                                  is_active=True, classification_id=4)
    classification = SimpleNamespace(name_ar=config["classifications"][0])
    treasury_source = SimpleNamespace(
        treasury_account_id=3, gl_account_id=10, currency_code="USD",
        is_active=True, name_ar="حساب الدولار"
    )
    db = MagicMock()
    db.get.side_effect = lambda model, key: (
        counterpart if model is Account else
        classification if model is AccountClassification else None
    )
    db.scalars.return_value = []
    if transaction_type == "cash_transfer":
        db.scalar.side_effect = [
            SimpleNamespace(treasury_account_id=8, gl_account_id=20,
                            currency_code="USD", is_active=True),
            0,
            0,
            treasury_source,
            0,
            0,
        ]
    else:
        db.scalar.side_effect = [0, 0]
    db.execute.return_value.all.return_value = [
        SimpleNamespace(fcy_amount=Decimal("1000"), debit_amount=Decimal("10000"),
                        credit_amount=Decimal("0"))
    ]

    def assign_entry_id(value):
        if isinstance(value, JournalEntry):
            value.journal_entry_id = 89

    db.add.side_effect = assign_entry_id
    movement = SimpleNamespace(transaction_id=41, journal_entry_id=None)
    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=inflow,
        outflow=outflow,
        exchange_rate=Decimal("10"),
        counterpart_account_id=20,
        transaction_type=transaction_type,
    )

    _create_usd_journal(db, treasury_source, movement, body, SimpleNamespace(user_id=7))

    lines = db.add_all.call_args.args[0]
    assert len(lines) == 2
    assert sum(line.debit_amount for line in lines) == sum(
        line.credit_amount for line in lines
    )


def test_usd_inflow_transfer_rejects_pending_source_account_movements(monkeypatch):
    import app.routers.treasury as treasury_module
    import app.routers.journal as journal_module

    monkeypatch.setattr(journal_module, "_fy_for", lambda db, entry_date:
                        SimpleNamespace(company_id=1, fiscal_year_id=2026, is_closed=False))
    monkeypatch.setattr(journal_module, "_next_no", lambda db, fiscal_year: "JE-USD-GUARD")

    counterpart = SimpleNamespace(account_id=10, account_code="15301001",
                                  is_active=True, classification_id=1)
    classification = SimpleNamespace(name_ar="نقدية بالصندوق و البنوك")
    source = SimpleNamespace(treasury_account_id=3, gl_account_id=10,
                             currency_code="USD", is_active=True)
    destination = SimpleNamespace(treasury_account_id=8, gl_account_id=20,
                                  currency_code="USD", is_active=True, name_ar="البنك المستلم")
    db = MagicMock()
    db.get.side_effect = lambda model, key: (
        counterpart if model is Account else
        classification if model is AccountClassification else None
    )
    db.scalars.return_value = []
    # Destination has no pending rows; source lookup succeeds; the source has
    # no unlinked movements but does have a draft journal, which must block transfer.
    db.scalar.side_effect = [source, 0, 0, source, 0, 1]

    body = TxIn(
        transaction_date=date(2026, 11, 8),
        inflow=Decimal("100"),
        outflow=Decimal("0"),
        exchange_rate=Decimal("50"),
        counterpart_account_id=10,
        transaction_type="cash_transfer",
    )
    movement = SimpleNamespace(transaction_id=41, journal_entry_id=None)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        treasury_module._create_usd_journal(
            db, destination, movement, body, SimpleNamespace(user_id=7)
        )

    assert exc.value.status_code == 409
    assert "مصدر التحويل" in exc.value.detail
    db.add.assert_not_called()
