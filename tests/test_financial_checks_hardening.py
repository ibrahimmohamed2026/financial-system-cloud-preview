from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import FinancialCheck
from app.routers import financial_checks
from app.routers.financial_checks import (
    _allowed_next_statuses, _party_classifications, _validate_party_account, canon_status,
)


def test_legacy_returned_spelling_is_canonical():
    assert canon_status("مُرتجع") == "مرتد"
    assert canon_status("مرتجع") == "مرتد"
    assert canon_status("مرتد") == "مرتد"
    assert canon_status("مسودة") == "مسودة"


def test_legacy_returned_cheque_is_terminal_for_both_directions():
    assert _allowed_next_statuses("OUTGOING", "مُرتجع") == set()
    assert _allowed_next_statuses("INCOMING", "مُرتجع") == set()


def test_incoming_draft_can_still_be_marked_returned_with_canonical_status():
    assert "مرتد" in _allowed_next_statuses("INCOMING", "مسودة")
    assert "مُرتجع" not in _allowed_next_statuses("INCOMING", "مسودة")


def test_party_classifications_follow_direction_and_exclude_cash_bank():
    incoming = _party_classifications("INCOMING")
    outgoing = _party_classifications("OUTGOING")
    assert "عملاء وأوراق قبض" in incoming
    assert "موردون و اوراق دفع" in outgoing
    assert "اصول ثابتة بالصافي" not in incoming
    assert "نقدية بالصندوق و البنوك" not in incoming | outgoing


def _db_for_party(classification_name, has_children=False):
    db = MagicMock()
    db.scalar.return_value = 1 if has_children else None
    db.get.return_value = SimpleNamespace(name_ar=classification_name) if classification_name else None
    return db


def test_fixed_asset_party_is_rejected_for_incoming_cheque():
    party = SimpleNamespace(account_id=1, classification_id=1, is_active=True)
    with pytest.raises(HTTPException) as exc:
        _validate_party_account(_db_for_party("اصول ثابتة بالصافي"), "INCOMING", party)
    assert exc.value.status_code == 422


def test_customer_party_is_accepted_for_incoming_and_parent_account_is_rejected():
    party = SimpleNamespace(account_id=9, classification_id=8, is_active=True)
    _validate_party_account(_db_for_party("عملاء وأوراق قبض"), "INCOMING", party)
    with pytest.raises(HTTPException):
        _validate_party_account(_db_for_party("عملاء وأوراق قبض", has_children=True), "INCOMING", party)


def test_missing_party_account_is_rejected_cleanly():
    with pytest.raises(HTTPException) as exc:
        _validate_party_account(MagicMock(), "INCOMING", None)
    assert exc.value.status_code == 422


def test_cheque_number_unique_per_type_and_bank_not_globally():
    constraints = [
        c for c in FinancialCheck.__table__.constraints
        if getattr(c, "name", None) == "UQ_FinancialChecks_Type_Bank_Number"
    ]
    assert len(constraints) == 1
    assert {c.name for c in constraints[0].columns} == {
        "CheckType", "TreasuryAccountId", "CheckNumber"
    }
    assert FinancialCheck.__table__.c["CheckNumber"].unique in (None, False)


def _check(status="مسودة", ctype="OUTGOING"):
    return SimpleNamespace(
        check_id=5, check_type=ctype, status=status, journal_entry_id=None,
        check_number="X", amount=Decimal("10"), treasury_account_id=1,
        party_account_id=2,
    )


def _set(check, status, **kwargs):
    db = MagicMock()
    db.scalar.return_value = check
    body = financial_checks.StatusIn(status=status, **kwargs)
    return financial_checks.set_status(
        5, body, SimpleNamespace(user_id=1), db
    ), db


def test_repeating_the_same_status_is_rejected_without_writes():
    check = _check("مرتد", "INCOMING")
    with pytest.raises(HTTPException) as exc:
        _set(check, "مُرتجع")
    assert exc.value.status_code == 409


def test_illegal_transition_is_409_and_unknown_status_is_422():
    with pytest.raises(HTTPException) as first:
        _set(_check("مسودة"), "منصرف")
    assert first.value.status_code == 409
    with pytest.raises(HTTPException) as second:
        _set(_check("مسودة"), "حالة-غريبة")
    assert second.value.status_code == 422


def test_future_settlement_date_is_rejected():
    with pytest.raises(HTTPException) as exc:
        _set(
            _check("تم التسليم"),
            "منصرف",
            settlement_date=date(2999, 1, 1),
        )
    assert exc.value.status_code == 422
