from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Account, AccountClassification, JournalEntry
from app.routers.treasury import TxIn, _create_egp_journal, _create_egp_transfer_mirror, _egp_journal_sides


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
    monkeypatch.setattr(journal_module, "_fy_for", lambda db, entry_date: fy)
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



@pytest.mark.parametrize(
    ("inflow", "outflow", "mirror_inflow", "mirror_outflow"),
    [
        (Decimal("100000"), Decimal("0"), Decimal("0"), Decimal("100000")),
        (Decimal("0"), Decimal("25000"), Decimal("25000"), Decimal("0")),
    ],
)
def test_egp_cash_transfer_creates_one_opposite_operational_movement(
    monkeypatch, inflow, outflow, mirror_inflow, mirror_outflow
):
    import app.routers.treasury as treasury_module

    monkeypatch.setattr(treasury_module, "write_audit", lambda *args, **kwargs: None)
    db = MagicMock()
    target = SimpleNamespace(treasury_account_id=8, name_ar="البنك التجاري الدولي",
                             gl_account_id=20, currency_code="EGP")
    db.scalar.return_value = target
    source = SimpleNamespace(treasury_account_id=3, name_ar="خزينة الجنيه",
                             gl_account_id=10, currency_code="EGP")
    original = SimpleNamespace(transaction_id=41, journal_entry_id=99)
    body = TxIn(transaction_date=date(2026, 11, 7), inflow=inflow, outflow=outflow,
                counterpart_account_id=20, transaction_type="cash_transfer",
                description="تحويل تجريبي", voucher_no="TR-001", project_id=2)

    mirror = _create_egp_transfer_mirror(db, source, original, body, SimpleNamespace(user_id=7))

    assert mirror is not None
    assert mirror.treasury_account_id == 8
    assert mirror.inflow == mirror_inflow
    assert mirror.outflow == mirror_outflow
    assert mirror.counterpart_account_id == 10
    assert mirror.transaction_type == "cash_transfer"
    assert mirror.journal_entry_id == 99
    assert mirror.voucher_no == "TR-001"
    db.add.assert_called_once_with(mirror)
    db.flush.assert_called_once()


def test_egp_non_transfer_does_not_create_a_mirror():
    db = MagicMock()
    db.scalar.return_value = None
    source = SimpleNamespace(treasury_account_id=3, gl_account_id=10, currency_code="EGP")
    original = SimpleNamespace(transaction_id=41, journal_entry_id=99)
    body = TxIn(transaction_date=date(2026, 11, 7), inflow=100, outflow=0,
                counterpart_account_id=20, transaction_type="direct_income")

    assert _create_egp_transfer_mirror(db, source, original, body, SimpleNamespace(user_id=7)) is None
    db.add.assert_not_called()


def test_egp_transfer_mirror_requires_existing_journal():
    db = MagicMock()
    target = SimpleNamespace(treasury_account_id=8, name_ar="البنك", gl_account_id=20, currency_code="EGP")
    db.scalar.return_value = target
    source = SimpleNamespace(treasury_account_id=3, name_ar="الخزينة", gl_account_id=10, currency_code="EGP")
    original = SimpleNamespace(transaction_id=41, journal_entry_id=None)
    body = TxIn(transaction_date=date(2026, 11, 7), inflow=100, outflow=0,
                counterpart_account_id=20, transaction_type="cash_transfer")

    with pytest.raises(HTTPException) as exc:
        _create_egp_transfer_mirror(db, source, original, body, SimpleNamespace(user_id=7))
    assert exc.value.status_code == 409
    db.add.assert_not_called()
