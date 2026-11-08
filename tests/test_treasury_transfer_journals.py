from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models import Account, JournalEntry
from app.routers.treasury import (
    BANK_SCREENS,
    USD_TRANSACTION_TYPES,
    TxIn,
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
def test_all_nine_movement_types_have_server_side_direction_and_classification_rules(
    transaction_type, direction
):
    config = USD_TRANSACTION_TYPES[transaction_type]
    assert config["direction"] == direction
    assert config["classifications"]


@pytest.mark.parametrize(
    ("screen_code", "expected_currency"),
    [
        ("BankCibEgp", "EGP"),
        ("CashUsd", "USD"),
        ("CashEgp", "EGP"),
        ("BankCairoEgp", "EGP"),
        ("BankHdbUsd", "USD"),
        ("BankHdbEgp", "EGP"),
        ("BankCibUsd", "USD"),
    ],
)
def test_all_seven_bank_and_cash_screens_are_registered_with_expected_currency(
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
    db.scalar.side_effect = [target, 0, 0, source]
    db.scalars.return_value = []
    db.execute.return_value.all.return_value = [
        SimpleNamespace(fcy_amount=Decimal("1000"), debit_amount=Decimal("10000"),
                        credit_amount=Decimal("0"))
    ]

    def assign_entry_id(value):
        if isinstance(value, JournalEntry):
            value.journal_entry_id = 77

    db.add.side_effect = assign_entry_id
    movement = SimpleNamespace(journal_entry_id=None)
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


def test_usd_transfer_rejects_counterpart_without_active_usd_treasury():
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

    with pytest.raises(Exception):
        _create_usd_transfer_mirror(db, source, original, body, SimpleNamespace(user_id=7))
    db.add.assert_not_called()
