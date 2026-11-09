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
    post = erp.split("def post_settlement", 1)[1].split("@router.delete", 1)[0]

    assert "cap-committed" in create
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in update
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in approve
    assert "validate_rule_settlement_amount(db, x, rule, amount)" in post


def test_contract_ui_exposes_both_retention_modes_and_manual_single_settlement_choice():
    ui = Path("web/pages/contracts.js").read_text(encoding="utf-8")
    assert "على كل مستخلص" in ui
    assert "مرة واحدة — اختيار المستخلص" in ui
    assert "single_deduction_codes" in ui
    assert "المحجوز مرحّلًا" in ui
    assert "الحد الأقصى من إجمالي العقد (%)" in ui
