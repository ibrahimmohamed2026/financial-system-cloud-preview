from pathlib import Path


def test_new_contracts_enter_financial_review_without_engineering_stage():
    source = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    create_contract = source.split("def create_contract", 1)[1].split("@router.get", 1)[0]
    submit_contract = source.split("def submit_contract", 1)[1].split("@router.post", 1)[0]

    assert 'values["status"] = "PendingFinancial"' in create_contract
    assert 'c.status = "PendingFinancial"' in submit_contract
    assert 'values["status"] = "PendingEngineering"' not in create_contract
    assert '@router.post("/{contract_id}/engineering-approve")' not in source


def test_technical_estimate_is_automatically_technically_approved_on_save_and_finance_can_review_immediately():
    source = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    create_estimate = source.split("def create_estimate", 1)[1].split("@router.post", 1)[0]
    forwarding = source.split("def _create_financial_from_estimate", 1)[1].split("@router.post", 1)[0]

    assert 'work_value=total,status="ForwardedToFinance"' in create_estimate
    assert "technical_reviewed_by=user.user_id" in create_estimate
    assert "technical_reviewed_at=now" in create_estimate
    assert "approved_quantity=qty" in create_estimate
    assert '"engineering_approval":True' in create_estimate
    assert "_create_financial_from_estimate(x.estimate_id, user, db, allow_unreviewed=True)" in create_estimate
    assert 'status="Draft"' in forwarding
    assert 'fin.status="Draft"' in forwarding
    assert "line.current_quantity if allow_unreviewed" in forwarding
    assert 'x.status="ForwardedToFinance"' in forwarding
    assert '"engineering_approval":True' in forwarding
    assert 'AwaitingTechnicalApproval' not in forwarding
    assert 'linked_schedule.status="Submitted"' in forwarding

    financial_api = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    assert 'linked_estimate.status!="ForwardedToFinance"' in financial_api
    assert 'raise HTTPException(409,"المراجعة المالية غير متاحة قبل الاعتماد الفني للمستخلص المرتبط")' in financial_api


def test_settlement_screen_has_no_technical_approval_waiting_stage():
    screen = Path("web/pages/settlements.js").read_text(encoding="utf-8")
    assert "بانتظار الاعتماد الفني" not in screen
    assert "Awaiting technical approval" not in screen
    assert "pendingTechnicalGate" not in screen
    assert "حفظ واعتماد فني وتحويل للحسابات" in screen
    assert "المراجعة المالية" in screen

def test_final_technical_estimate_must_settle_every_contract_item_after_engineering_review():
    technical = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    create_estimate = technical.split("def create_estimate", 1)[1].split("@router.post", 1)[0]
    review_estimate = technical.split("def review_estimate", 1)[1].split("@router.post", 1)[0]
    assert "if body.is_final:" in create_estimate
    assert "final_quantity_gaps(db, c.contract_id, body.settlement_side, candidate=candidate)" in create_estimate
    assert "if x.is_final:" in review_estimate
    assert "exclude_estimate_id=x.estimate_id" in review_estimate
    assert "final_quantity_error(gaps" in review_estimate
    assert "remaining_quantity" in technical
    assert "linked_financial_ids" in technical


def test_final_financial_settlement_is_rechecked_at_api_creation_manager_approval_and_posting():
    source = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    create_settlement = source.split("def create_settlement", 1)[1].split("@router.get", 1)[0]
    manager_approve = source.split("def manager_approve_settlement", 1)[1].split("@router.post", 1)[0]
    post_settlement = source.split("def post_settlement", 1)[1].split("@router.delete", 1)[0]
    assert "if body.is_final:" in create_settlement
    assert "final_settlement_quantity_gaps(db, contract_id, side, candidate=candidate)" in create_settlement
    assert "if x.is_final:" in manager_approve
    assert "final_settlement_quantity_gaps(db, x.contract_id, x.settlement_side)" in manager_approve
    assert "if x.is_final:" in post_settlement
    assert "reject_incomplete_final_settlement(gaps, \"ترحيل\")" in post_settlement
    assert "settlement_id.not_in(linked_financial_ids)" in source
    assert "technical_qty" in source and "financial_qty" in source
    assert 'TechnicalSettlementEstimate.status.in_(("TechnicallyApproved", "ForwardedToFinance"))' in source
    assert "لا يمكن اعتماد المستخلص الختامي قبل اكتمال وترحيل المستخلصات السابقة" in source

def test_contract_settlement_status_length_and_existing_postgres_schema_upgrade():
    models = Path("app/models.py").read_text(encoding="utf-8")
    settlement_model = models.split("class ContractSettlement(Base):", 1)[1].split(
        "\nclass ", 1
    )[0]
    assert 'C("Status", Unicode(40), default="Draft")' in settlement_model

    setup = Path("app/db_setup.py").read_text(encoding="utf-8")
    assert 'if engine.dialect.name == "postgresql" and "ContractSettlements" in inspect(engine).get_table_names():' in setup
    assert 'ALTER TABLE "ContractSettlements" ALTER COLUMN "Status" TYPE VARCHAR(40)' in setup
    assert 'status_length < 40' in setup


def test_audit_log_action_type_length_and_existing_postgres_schema_upgrade():
    models = Path("app/models.py").read_text(encoding="utf-8")
    audit_model = models.split("class AuditLog(Base):", 1)[1].split(
        "\nclass ", 1
    )[0]
    assert 'C("ActionType", Unicode(100))' in audit_model

    setup = Path("app/db_setup.py").read_text(encoding="utf-8")
    assert 'if engine.dialect.name == "postgresql" and "AuditLog" in inspect(engine).get_table_names():' in setup
    assert 'ALTER TABLE "AuditLog" ALTER COLUMN "ActionType" TYPE VARCHAR(100)' in setup
    assert 'action_type_length < 100' in setup


def test_existing_awaiting_technical_approval_drafts_are_migrated_to_finance_review():
    setup = Path("app/db_setup.py").read_text(encoding="utf-8")
    assert "financial.\"Status\" = 'AwaitingTechnicalApproval'" in setup
    assert "SET \"ApprovedQuantity\" = line.\"CurrentQuantity\"" in setup
    assert "SET \"Status\" = 'ForwardedToFinance'" in setup
    assert "SET \"Status\" = 'Draft'" in setup
    assert "No journal" not in setup
