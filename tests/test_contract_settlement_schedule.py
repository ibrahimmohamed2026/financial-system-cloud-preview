from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models import ContractSettlementSchedule
from app.routers.contracts import ContractIn, _build_contract_schedule


def make_contract(method, count, start=date(2026, 1, 1), end=date(2026, 3, 31), **extra):
    return ContractIn(
        title="Test contract",
        client_name="Test client",
        start_date=start,
        end_date=end,
        original_value=Decimal("900"),
        agreed_statement_count=count,
        statement_distribution_method=method,
        **extra,
    )


def test_monthly_schedule_creates_expected_number_and_calendar_periods():
    rows = _build_contract_schedule(make_contract("Monthly", 3))
    assert len(rows) == 3
    assert (rows[0].period_start, rows[0].period_end) == (date(2026, 1, 1), date(2026, 1, 31))
    assert (rows[1].period_start, rows[1].period_end) == (date(2026, 2, 1), date(2026, 2, 28))
    assert (rows[2].period_start, rows[2].period_end) == (date(2026, 3, 1), date(2026, 3, 31))
    assert rows[0].expected_amount == Decimal("300.00")
    assert rows[0].planned_submission_date == date(2026, 2, 5)
    assert rows[0].due_date == date(2026, 3, 7)


def test_biweekly_schedule_uses_fourteen_day_periods():
    rows = _build_contract_schedule(make_contract("Biweekly", 2, end=date(2026, 1, 28)))
    assert [(r.period_start, r.period_end) for r in rows] == [
        (date(2026, 1, 1), date(2026, 1, 14)),
        (date(2026, 1, 15), date(2026, 1, 28)),
    ]


def test_milestone_schedule_uses_named_user_defined_execution_phases():
    phases = [
        {"label": "الأساسات", "period_start": date(2026, 1, 1), "period_end": date(2026, 1, 30),
         "planned_submission_date": date(2026, 2, 4), "due_date": date(2026, 3, 6)},
        {"label": "الهيكل", "period_start": date(2026, 1, 31), "period_end": date(2026, 2, 28),
         "planned_submission_date": date(2026, 3, 5), "due_date": date(2026, 4, 4)},
        {"label": "التشطيبات", "period_start": date(2026, 3, 1), "period_end": date(2026, 3, 31),
         "planned_submission_date": date(2026, 4, 5), "due_date": date(2026, 5, 5)},
    ]
    rows = _build_contract_schedule(make_contract("Milestones", 3, schedule_items=phases))
    assert [r.label for r in rows] == ["الأساسات", "الهيكل", "التشطيبات"]
    assert rows[0].period_start == date(2026, 1, 1)
    assert rows[-1].period_end == date(2026, 3, 31)
    assert rows[1].period_start == rows[0].period_end + timedelta(days=1)


def test_manual_schedule_requires_exact_count_and_keeps_user_dates():
    item = {
        "label": "مرحلة الأساسات",
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 20),
        "planned_submission_date": date(2026, 1, 25),
        "due_date": date(2026, 2, 25),
        "expected_amount": Decimal("250"),
    }
    rows = _build_contract_schedule(make_contract("Manual", 1, schedule_items=[item]))
    assert len(rows) == 1
    assert rows[0].label == "مرحلة الأساسات"
    assert rows[0].expected_amount == Decimal("250")


def test_manual_schedule_rejects_wrong_number_of_rows():
    with pytest.raises(HTTPException) as exc:
        _build_contract_schedule(make_contract("Manual", 2, schedule_items=[]))
    assert exc.value.status_code == 422


def test_schedule_model_has_unique_sequence_and_unique_estimate_link():
    constraints = {c.name for c in ContractSettlementSchedule.__table__.constraints}
    assert "UQ_ContractSettlementSchedules_Sequence" in constraints
    assert "UQ_ContractSettlementSchedules_TechnicalEstimate" in constraints
