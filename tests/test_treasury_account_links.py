from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers.treasury import _ensure_gl_relink_safe, _validate_treasury_gl_link


def test_treasury_gl_link_rejects_account_already_used():
    db = MagicMock()
    db.scalar.return_value = 12

    with pytest.raises(HTTPException) as exc:
        _validate_treasury_gl_link(db, 15301002)

    assert exc.value.status_code == 409


def test_treasury_gl_link_allows_account_not_used_elsewhere():
    db = MagicMock()
    db.scalar.return_value = None

    _validate_treasury_gl_link(db, 15301002)

    db.scalar.assert_called_once()


def test_treasury_gl_link_update_excludes_current_treasury():
    db = MagicMock()
    db.scalar.return_value = None

    _validate_treasury_gl_link(db, 15301002, exclude_treasury_account_id=7)

    db.scalar.assert_called_once()


def test_relink_is_blocked_when_treasury_has_transactions():
    db = MagicMock()
    db.scalar.return_value = 1
    treasury = SimpleNamespace(treasury_account_id=7, gl_account_id=100)

    with pytest.raises(HTTPException) as exc:
        _ensure_gl_relink_safe(db, treasury, 200)

    assert exc.value.status_code == 409


def test_relink_is_blocked_when_old_gl_has_opening_balance():
    db = MagicMock()
    db.scalar.return_value = None
    db.get.return_value = SimpleNamespace(
        opening_debit=Decimal("100.00"), opening_credit=Decimal("0.00"))
    treasury = SimpleNamespace(treasury_account_id=7, gl_account_id=100)

    with pytest.raises(HTTPException) as exc:
        _ensure_gl_relink_safe(db, treasury, 200)

    assert exc.value.status_code == 409


def test_relink_is_blocked_when_old_gl_has_journal_history():
    db = MagicMock()
    db.scalar.side_effect = [None, 55]
    db.get.return_value = SimpleNamespace(
        opening_debit=Decimal("0.00"), opening_credit=Decimal("0.00"))
    treasury = SimpleNamespace(treasury_account_id=7, gl_account_id=100)

    with pytest.raises(HTTPException) as exc:
        _ensure_gl_relink_safe(db, treasury, 200)

    assert exc.value.status_code == 409


def test_saving_same_gl_link_does_not_block():
    db = MagicMock()
    treasury = SimpleNamespace(treasury_account_id=7, gl_account_id=100)

    _ensure_gl_relink_safe(db, treasury, 100)

    db.scalar.assert_not_called()
    db.get.assert_not_called()
