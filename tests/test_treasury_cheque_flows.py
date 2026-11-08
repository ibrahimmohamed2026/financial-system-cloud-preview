from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import Account, Beneficiary
from app.routers import checks
from app.routers.financial_checks import _flow_account_ids
from app.routers.treasury import _movement_route


def test_treasury_inflow_is_party_to_bank():
    assert _movement_route("Bank GL", "Customer GL", True) == ("Customer GL", "Bank GL")


def test_treasury_outflow_is_bank_to_party():
    assert _movement_route("Bank GL", "Supplier GL", False) == ("Bank GL", "Supplier GL")


def test_incoming_and_outgoing_financial_cheques_have_opposite_routes():
    assert _flow_account_ids("INCOMING", 101, 201) == (101, 201)
    assert _flow_account_ids("OUTGOING", 101, 201) == (201, 101)


def test_issued_cheque_route_is_bank_to_beneficiary():
    beneficiary = SimpleNamespace(beneficiary_id=7, linked_account_id=101)
    party = SimpleNamespace(account_id=101, account_code="2101", account_name_ar="المستفيد")
    bank = SimpleNamespace(account_id=201, account_code="1101", account_name_ar="البنك")
    db = MagicMock()
    db.get.side_effect = lambda model, key: (
        beneficiary if model is Beneficiary else
        party if key == 101 else bank if key == 201 else None
    )
    cheque = SimpleNamespace(
        check_id=5, check_book_no="B1", sequence_no=1, check_no="123",
        check_date=date(2026, 11, 8), beneficiary_id=7, amount=None,
        purchase_order_no=None, project_id=None, settlement_id=None,
        description="test", print_date=None, delivery_date=None, cash_date=None,
        status="تم التسليم",
    )
    treasury = SimpleNamespace(
        gl_account_id=201, currency_code="EGP", name_ar="البنك",
        bank_account_number="123456", treasury_account_id=9,
    )

    result = checks._out(cheque, "المستفيد", None, treasury, db=db)

    assert result["from_account_id"] == 201
    assert result["to_account_id"] == 101
    assert result["from_account_label"] == "1101 — البنك"
    assert result["to_account_label"] == "2101 — المستفيد"
    assert result["flow_stage"] == "عند الصرف"


def test_invalid_financial_cheque_type_has_no_implicit_route():
    with pytest.raises(HTTPException) as exc:
        _flow_account_ids("UNKNOWN", 101, 201)
    assert exc.value.status_code == 422
