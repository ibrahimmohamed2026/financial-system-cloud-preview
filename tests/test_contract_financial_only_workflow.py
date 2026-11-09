from pathlib import Path


def test_new_contracts_enter_financial_review_without_engineering_stage():
    source = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    create_contract = source.split("def create_contract", 1)[1].split("@router.get", 1)[0]
    submit_contract = source.split("def submit_contract", 1)[1].split("@router.post", 1)[0]

    assert 'values["status"] = "PendingFinancial"' in create_contract
    assert 'c.status = "PendingFinancial"' in submit_contract
    assert 'values["status"] = "PendingEngineering"' not in create_contract
    assert '@router.post("/{contract_id}/engineering-approve")' not in source


def test_technical_estimate_creates_locked_financial_draft_on_save_then_unlocks_after_technical_approval():
    source = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    create_estimate = source.split("def create_estimate", 1)[1].split("@router.post", 1)[0]
    forwarding = source.split("def _create_financial_from_estimate", 1)[1].split("@router.post", 1)[0]
    approval_endpoint = source.split('@router.post("/{estimate_id}/approve")', 1)[1].split("@router.delete", 1)[0]

    assert 'status="UnderReview"' in create_estimate
    assert "approved_quantity=None" in create_estimate
    assert "_create_financial_from_estimate(x.estimate_id, user, db, allow_unreviewed=True)" in create_estimate
    assert 'status="AwaitingTechnicalApproval" if allow_unreviewed else "Draft"' in forwarding
    assert "line.current_quantity if allow_unreviewed" in forwarding
    assert 'x.status="ForwardedToFinance"' in forwarding
    assert 'fin.status="AwaitingTechnicalApproval" if allow_unreviewed else "Draft"' in forwarding
    assert 'x.created_by == user.user_id' in forwarding
    assert 'x.technical_reviewed_by == user.user_id' in forwarding
    assert "return _create_financial_from_estimate(estimate_id, user, db)" in approval_endpoint
    assert 'linked_schedule.status="Submitted"' in forwarding
    assert 'linked_schedule.status="Completed"' not in forwarding

    financial_api = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    assert 'linked_estimate.status!="ForwardedToFinance"' in financial_api
    assert 'raise HTTPException(409,"المراجعة المالية غير متاحة قبل الاعتماد الفني للمستخلص المرتبط")' in financial_api


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
