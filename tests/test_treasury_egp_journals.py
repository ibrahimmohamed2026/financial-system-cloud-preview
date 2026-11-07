from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Account, AccountClassification, JournalEntry
from app.routers.treasury import TxIn, _create_egp_journal, _egp_journal_sides


@pytest.mark.parametrize(
    ("inflow", "outflow", "expected"),
    [
        (Decimal("1250.00"), Decimal("0"), (Decimal("1250.00"), Decimal("0"), Decimal("0"), Decimal("1250.00"))),
        (Decimal("0"), Decimal("850.00"), (Decimal("0"), Decimal("850.00"), Decimal("850.00"), Decimal("0"))),
    ],
)
def test_egp_journal_sides_are_balanced_for_receipts_and_payments(inflow, outflow, expected):
    sides = _egp_journal_sides(inflow, outflow)
    assert sides == expected
    treasury_debit, treasury_credit, counterpart_debit, counterpart_credit = sides
    assert treasury_debit + counterpart_debit == treasury_credit + counterpart_credit


def test_egp_journal_rejects_invalid_zero_or_two_sided_movement():
    with pytest.raises(HTTPException):
        _egp_journal_sides(Decimal("0"), Decimal("0"))
    with pytest.raises(HTTPException):
        _egp_journal_sides(Decimal("10"), Decimal("10"))


def test_egp_journal_creates_one_draft_entry_and_links_transaction(monkeypatch):
    import app.routers.treasury as treasury_module
    import app.routers.journal as journal_module

    fy = SimpleNamespace(company_id=1, fiscal_year_id=2026)
    monkeypatch.setattr(treasury_module, "_fy_for", lambda db, entry_date: fy)
    monkeypatch.setattr(journal_module, "_next_no", lambda db, fiscal_year: "JE-2026-000001")

    db = MagicMock()
    counterpart = SimpleNamespace(account_id=20, is_active=True, classification_id=4)
    db.get.side_effect = lambda model, key: (
        counterpart if model is Account else
        SimpleNamespace(name_ar="مصروفات عمومية و ادارية") if model is AccountClassification else None
    )
    db.scalars.return_value = []
    def assign_entry_id(value):
        if isinstance(value, JournalEntry):
            value.journal_entry_id = 99
    db.add.side_effect = assign_entry_id

    account = SimpleNamespace(gl_account_id=10, name_ar="الخزينة الرئيسية",
                              currency_code="EGP", treasury_account_id=3)
    movement = SimpleNamespace(journal_entry_id=None)
    body = TxIn(transaction_date=date(2026, 11, 7), inflow=0, outflow=850,
                counterpart_account_id=20, transaction_type="expense_payment",
                description="مصروف تشغيل")

    entry_no = _create_egp_journal(db, account, movement, body, SimpleNamespace(user_id=7))

    assert entry_no == "JE-2026-000001"
    assert movement.journal_entry_id == 99
    db.add_all.assert_called_once()
    lines = db.add_all.call_args.args[0]
    assert len(lines) == 2
    assert lines[0].account_id == 10
    assert lines[0].debit_amount == 0 and lines[0].credit_amount == Decimal("850")
    assert lines[1].account_id == 20
    assert lines[1].debit_amount == Decimal("850") and lines[1].credit_amount == 0


def test_egp_journal_never_creates_a_duplicate_for_already_linked_transaction():
    db = MagicMock()
    movement = SimpleNamespace(journal_entry_id=99)
    with pytest.raises(HTTPException) as exc:
        _create_egp_journal(
            db,
            SimpleNamespace(gl_account_id=10),
            movement,
            TxIn(transaction_date=date(2026, 11, 7), inflow=100, outflow=0,
                 counterpart_account_id=20, transaction_type="direct_income"),
            SimpleNamespace(user_id=7),
        )
    assert exc.value.status_code == 409
    db.add.assert_not_called()
