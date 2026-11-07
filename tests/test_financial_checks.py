from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models import (
    Contract, Counterparty, FinancialCheckSettlementAllocation,
    FinancialCheckStatusHistory,
)
from app.routers import financial_checks
from app.routers.financial_checks import AllocationIn, _allowed_next_statuses, _money


def test_outgoing_cheque_must_follow_approval_issuance_and_delivery():
    assert _allowed_next_statuses("OUTGOING", "مسودة") == {"معتمد", "ملغي"}
    assert "منصرف" not in _allowed_next_statuses("OUTGOING", "مسودة")
    assert "منصرف" not in _allowed_next_statuses("OUTGOING", "معتمد")
    assert "منصرف" in _allowed_next_statuses("OUTGOING", "تم التسليم")


def test_incoming_cheque_only_posts_after_collection_state():
    assert "تم التحصيل" not in _allowed_next_statuses("INCOMING", "مسودة")
    assert "تم التحصيل" in _allowed_next_statuses("INCOMING", "تحت التحصيل")


def test_money_normalizes_values_to_two_decimal_places():
    assert _money("125.5") == Decimal("125.50")
    assert _money(Decimal("0.004")) == Decimal("0.00")


def test_allocation_table_has_duplicate_and_positive_amount_guards():
    constraints = list(FinancialCheckSettlementAllocation.__table__.constraints)
    unique = [x for x in constraints if getattr(x, "name", None) == "UQ_FinancialCheckSettlementAllocations"]
    positive = [x for x in constraints if getattr(x, "name", None) == "CK_FinancialCheckSettlementAllocations_Positive"]
    assert len(unique) == 1
    assert len(positive) == 1


def test_cheque_status_history_has_immutable_transition_fields():
    columns = FinancialCheckStatusHistory.__table__.columns
    assert {"CheckId", "OldStatus", "NewStatus", "ChangedBy", "ChangedAt"}.issubset(set(columns.keys()))


def _allocation_test_objects():
    check = SimpleNamespace(
        check_id=11, check_type="OUTGOING", status="مسودة",
        amount=Decimal("500.00"), project_id=4, party_account_id=20,
    )
    settlement = SimpleNamespace(
        settlement_id=31, contract_id=41, settlement_side="Subcontractor",
        status="Approved", manager_approved_by=7, manager_approved_at=datetime(2026, 11, 7),
        counterparty_id=51, net_amount=Decimal("900.00"),
    )
    contract = SimpleNamespace(
        contract_id=41, status="Active", counterparty_id=51, project_id=4,
    )
    party = SimpleNamespace(
        counterparty_id=51, account_id=20, linked_account_id=None, is_active=True,
    )
    return check, settlement, contract, party


def test_allocation_loads_contract_before_comparing_counterparty(monkeypatch):
    check, settlement, contract, party = _allocation_test_objects()
    db = MagicMock()
    db.scalar.side_effect = [check, settlement, None, 0, 0, 0]
    db.get.side_effect = lambda model, key: contract if model is Contract else party
    db.execute.return_value.all.return_value = []
    monkeypatch.setattr(financial_checks, "write_audit", lambda *args, **kwargs: None)

    result = financial_checks.add_allocation(
        11, AllocationIn(settlement_id=31, allocated_amount=Decimal("250.00")),
        SimpleNamespace(user_id=7), db,
    )

    assert result["allocated_total"] == "250.00"
    db.commit.assert_called_once()
    allocation = db.add.call_args.args[0]
    assert isinstance(allocation, FinancialCheckSettlementAllocation)
    assert allocation.check_id == 11
    assert allocation.settlement_id == 31
    assert allocation.allocated_amount == Decimal("250.00")


def test_allocation_rejects_counterparty_mismatch_without_writing(monkeypatch):
    check, settlement, contract, party = _allocation_test_objects()
    contract.counterparty_id = 999
    db = MagicMock()
    db.scalar.side_effect = [check, settlement]
    db.get.return_value = contract
    monkeypatch.setattr(financial_checks, "write_audit", lambda *args, **kwargs: None)

    with pytest.raises(HTTPException) as exc:
        financial_checks.add_allocation(
            11, AllocationIn(settlement_id=31, allocated_amount=Decimal("250.00")),
            SimpleNamespace(user_id=7), db,
        )

    assert exc.value.status_code == 409
    db.commit.assert_not_called()
