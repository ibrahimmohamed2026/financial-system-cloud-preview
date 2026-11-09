from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import contract_erp


def test_retention_is_identified_by_rule_code_or_arabic_name():
    assert contract_erp.is_retention_rule(SimpleNamespace(code="RETENTION", name_ar="تأمين"))
    assert contract_erp.is_retention_rule(SimpleNamespace(code="retention_insurance", name_ar=""))
    assert contract_erp.is_retention_rule(SimpleNamespace(code="custom_1", name_ar="التأمين المحتجز"))
    assert not contract_erp.is_retention_rule(SimpleNamespace(code="FINAL_INSURANCE", name_ar="تأمين نهائي"))


def test_cumulative_retention_only_withholds_incremental_difference():
    first = contract_erp.cumulative_retention_due(
        Decimal("1000000"), Decimal("5"), Decimal("0")
    )
    second = contract_erp.cumulative_retention_due(
        Decimal("3000000"), Decimal("5"), first
    )
    third = contract_erp.cumulative_retention_due(
        Decimal("6000000"), Decimal("5"), first + second
    )

    assert first == Decimal("50000.00")
    assert second == Decimal("100000.00")
    assert third == Decimal("150000.00")
    assert first + second + third == Decimal("300000.00")


def test_retention_stops_at_contract_cap_and_never_goes_negative():
    assert contract_erp.cumulative_retention_due(
        Decimal("10000000"), Decimal("5"), Decimal("480000"),
        cap_remaining=Decimal("20000")
    ) == Decimal("20000.00")
    assert contract_erp.cumulative_retention_due(
        Decimal("10000000"), Decimal("5"), Decimal("500000"),
        cap_remaining=Decimal("0")
    ) == Decimal("0.00")


def test_fixed_retention_is_only_withheld_until_its_target_is_reached():
    assert contract_erp.cumulative_retention_due(
        Decimal("0"), Decimal("50000"), Decimal("20000"),
        calculation_type="Fixed"
    ) == Decimal("30000.00")
    assert contract_erp.cumulative_retention_due(
        Decimal("0"), Decimal("50000"), Decimal("50000"),
        calculation_type="Fixed"
    ) == Decimal("0.00")


@pytest.mark.parametrize("name", [
    "تأمين محجوز",
    "تامين محجوز",
    "التأمين المحتجز",
    "Retention",
    "contract retention deduction",
])
def test_manual_retention_names_are_rejected(name):
    assert contract_erp.is_manual_retention_name(name)


def test_final_insurance_is_not_misclassified_as_retention():
    assert not contract_erp.is_manual_retention_name("تأمين نهائي")


def test_retention_amount_cannot_be_manually_changed_during_financial_review(monkeypatch):
    monkeypatch.setattr(
        contract_erp, "contract_financial_summary",
        lambda *_args: (None, Decimal("0"), Decimal("1000000"))
    )
    monkeypatch.setattr(
        contract_erp, "cumulative_retention_amount",
        lambda *_args, **_kwargs: Decimal("50000.00")
    )
    settlement = SimpleNamespace(cumulative_work_value=Decimal("1000000"), settlement_id=7,
                                   sequence_no=2)
    rule = SimpleNamespace(code="RETENTION", name_ar="تأمين محجوز", contract_id=1,
                           settlement_side="Subcontractor")

    with pytest.raises(HTTPException) as error:
        contract_erp.validate_rule_settlement_amount(
            None, settlement, rule, Decimal("45000")
        )

    assert error.value.status_code == 422
    assert "لا يمكن تعديل التأمين المحجوز يدويًا" in error.value.detail


def test_manual_retention_guard_is_applied_to_financial_deduction_endpoint():
    source = open("app/routers/contract_erp.py", encoding="utf-8").read()
    update = source.split("def update_settlement_deductions", 1)[1].split(
        "class FinancialReviewLine", 1
    )[0]
    assert "is_manual_retention_name(addition.name)" in update
    assert "يتم احتسابه تلقائيًا" in update


def test_technical_financial_draft_uses_same_cumulative_retention_engine():
    source = open("app/routers/technical_settlements.py", encoding="utf-8").read()
    assert "cumulative_retention_amount(db,r,cumulative,contract_value" in source
    assert "is_retention_rule(r)" in source
    assert "before_sequence_no=current_sequence_no" in source


def test_prior_retention_offset_is_limited_to_earlier_settlements():
    source = open("app/routers/contract_erp.py", encoding="utf-8").read()
    helper = source.split("def retention_amount_used", 1)[1].split("FINANCIAL_RULE_FIELDS", 1)[0]
    assert "before_sequence_no: int | None = None" in helper
    assert "ContractSettlement.sequence_no < before_sequence_no" in helper
    assert "before_sequence_no=settlement.sequence_no" in source



def test_standard_deduction_override_validation_does_not_apply_caps():
    rule = SimpleNamespace(
        code="PROFIT_TAX", name_ar="ضرائب أرباح", contract_id=1,
        settlement_side="Subcontractor", cap_amount=Decimal("100"),
        cap_percent=Decimal("1"),
    )
    # Non-retention standard deductions accept any non-negative manually entered value.
    contract_erp.validate_rule_settlement_amount(
        None, SimpleNamespace(), rule, Decimal("999999")
    )


def test_settlement_creation_allows_standard_override_above_rule_caps():
    source = open("app/routers/contract_erp.py", encoding="utf-8").read()
    create = source.split("def create_settlement", 1)[1].split(
        '@router.get("/all-settlements")', 1
    )[0]
    assert "if is_retention_rule(r) and requested != amount" in create
    assert "if mode==\"SingleSettlement\" or getattr(r,\"cap_percent\",None) is not None" not in create
    assert "requested > money(r.cap_amount)" not in create
    assert '"calculated_amount":str(calculated_amount)' in create
    assert '"manually_overridden":amount != calculated_amount' in create


def test_financial_review_allows_standard_override_above_rule_caps():
    source = open("app/routers/contract_erp.py", encoding="utf-8").read()
    update = source.split("def update_settlement_deductions", 1)[1].split(
        "class FinancialReviewLine", 1
    )[0]
    assert "rule.cap_amount" not in update
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in update
    assert 'd["calculated_amount"]=str(calculated_amount)' in update
    assert 'd["manually_overridden"]=amount != calculated_amount' in update


def test_technical_settlement_draft_does_not_apply_standard_deduction_caps():
    source = open("app/routers/technical_settlements.py", encoding="utf-8").read()
    assert "if not is_retention_rule(r) and r.cap_amount is not None" not in source
    assert '"calculated_amount":str(amount)' in source
