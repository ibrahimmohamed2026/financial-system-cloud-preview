from pathlib import Path


def test_contract_deduction_rules_persist_application_mode_and_contract_cap():
    models = Path("app/models.py").read_text(encoding="utf-8")
    setup = Path("app/db_setup.py").read_text(encoding="utf-8")
    contracts = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    erp = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")

    assert 'C("ApplicationMode", Unicode(30), default="PerSettlement")' in models
    assert 'C("CapPercent", Numeric(9, 4), nullable=True)' in models
    assert '"ContractDeductionRules")' in setup
    assert 'Literal["PerSettlement", "SingleSettlement"]' in contracts
    assert 'application_mode: Literal["PerSettlement","SingleSettlement"]' in erp
    assert 'cap_percent: Optional[Decimal]' in erp


def test_single_settlement_retention_is_selected_on_the_settlement_and_uses_contract_total():
    erp = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    create = erp.split("def create_settlement", 1)[1].split("@router.get", 1)[0]

    assert "single_deduction_codes: list[str]" in erp
    assert "set(body.single_deduction_codes)" in create
    assert 'mode=="SingleSettlement"' in create
    assert "base=contract_value if mode==\"SingleSettlement\"" in create
    assert "retention_amount_used(db,r) > ZERO" in create


def test_retention_cap_uses_remaining_contract_cap_and_is_rechecked_before_approval_and_posting():
    erp = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    create = erp.split("def create_settlement", 1)[1].split("@router.get", 1)[0]
    update = erp.split("def update_settlement_deductions", 1)[1].split("class FinancialReviewLine", 1)[0]
    approve = erp.split("def approve_settlement", 1)[1].split("@router.post", 1)[0]
    manager = erp.split("def manager_approve_settlement", 1)[1].split("@router.post", 1)[0]
    post = erp.split("def post_settlement", 1)[1].split("@router.delete", 1)[0]

    assert "cap-committed" in create
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in update
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in approve
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in manager
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in post


def test_contract_ui_exposes_both_retention_modes_and_manual_single_settlement_choice():
    ui = Path("web/pages/contracts.js").read_text(encoding="utf-8")
    assert "على كل مستخلص" in ui
    assert "مرة واحدة — اختيار المستخلص" in ui
    assert "single_deduction_codes" in ui
    assert "المحجوز مرحّلًا" in ui
    assert "الحد الأقصى من إجمالي العقد (%)" in ui


from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers.contract_erp import validate_rule_change


def _rule(**overrides):
    values = {
        "settlement_side": "Subcontractor",
        "calculation_type": "Percent",
        "rate": Decimal("10"),
        "base_type": "CurrentWork",
        "application_mode": "PerSettlement",
        "cap_percent": Decimal("10"),
        "cap_amount": None,
        "posting_side": "Credit",
        "gl_account_id": 501,
        "code": "RETENTION",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _settlement(status="Draft", amount="0.00", number="ST-001"):
    return SimpleNamespace(
        status=status,
        settlement_no=number,
        settlement_id=1,
        deductions_json={"RETENTION": {"amount": amount}},
    )


def test_financial_rule_terms_cannot_change_after_a_settlement_is_linked_without_controlled_path():
    rule = _rule()
    linked = [_settlement()]
    proposed = {"application_mode": "SingleSettlement", "rate": Decimal("12"),
                "cap_percent": Decimal("12")}

    with pytest.raises(HTTPException) as error:
        validate_rule_change(rule, proposed, linked, Decimal("0"), Decimal("10000000"))

    assert error.value.status_code == 409
    assert "مسار التعديل المنضبط" in str(error.value.detail)


def test_controlled_rule_change_requires_draft_only_and_zero_reserved_amounts():
    rule = _rule()
    safe_draft = [_settlement(status="Draft", amount="0.00")]
    proposed = {"application_mode": "SingleSettlement", "rate": Decimal("12"),
                "cap_percent": Decimal("12")}

    validate_rule_change(rule, proposed, safe_draft, Decimal("0"),
                         Decimal("10000000"), controlled_reason="تصحيح شروط العقد بناءً على ملحق معتمد")

    approved = [_settlement(status="Approved", amount="0.00", number="ST-002")]
    with pytest.raises(HTTPException) as error:
        validate_rule_change(rule, proposed, approved, Decimal("0"),
                             Decimal("10000000"), controlled_reason="تعديل موثق بعد المراجعة")

    assert error.value.status_code == 409
    assert "ST-002" in str(error.value.detail)


def test_cap_cannot_be_reduced_below_amounts_already_reserved_or_posted():
    rule = _rule(cap_percent=Decimal("10"))
    # Contract value = EGP 10,000,000; new 5% cap = EGP 500,000.
    # EGP 700,000 is already reserved/posted.
    with pytest.raises(HTTPException) as error:
        validate_rule_change(
            rule,
            {"cap_percent": Decimal("5")},
            [_settlement(status="Posted", amount="700000.00", number="ST-003")],
            Decimal("700000.00"),
            Decimal("10000000"),
            controlled_reason="مراجعة شروط التأمين بناءً على اعتماد الإدارة",
        )

    assert error.value.status_code == 409
    assert "500000.00" in str(error.value.detail)
    assert "700000.00" in str(error.value.detail)


def test_cap_can_be_increased_when_it_covers_existing_reservations():
    rule = _rule(cap_percent=Decimal("10"))
    validate_rule_change(
        rule,
        {"cap_percent": Decimal("12")},
        [_settlement(status="Posted", amount="700000.00")],
        Decimal("700000.00"),
        Decimal("10000000"),
        controlled_reason="زيادة سقف التأمين وفق ملحق العقد المعتمد",
    )


def test_nonfinancial_rule_edits_remain_available_with_linked_settlements():
    rule = _rule()
    validate_rule_change(
        rule,
        {"name_ar": "تأمين ضمان الأعمال", "sort_order": 3},
        [_settlement(status="Posted", amount="700000.00")],
        Decimal("700000.00"),
        Decimal("10000000"),
    )
