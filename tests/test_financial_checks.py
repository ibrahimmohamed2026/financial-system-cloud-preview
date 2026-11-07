from decimal import Decimal

from app.models import FinancialCheckSettlementAllocation, FinancialCheckStatusHistory
from app.routers.financial_checks import _allowed_next_statuses, _money


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
