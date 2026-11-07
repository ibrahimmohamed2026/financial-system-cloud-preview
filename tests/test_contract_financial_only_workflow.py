from pathlib import Path


def test_new_contracts_enter_financial_review_without_engineering_stage():
    source = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    create_contract = source.split("def create_contract", 1)[1].split("@router.get", 1)[0]
    submit_contract = source.split("def submit_contract", 1)[1].split("@router.post", 1)[0]

    assert 'values["status"] = "PendingFinancial"' in create_contract
    assert 'c.status = "PendingFinancial"' in submit_contract
    assert 'values["status"] = "PendingEngineering"' not in create_contract
    assert '@router.post("/{contract_id}/engineering-approve")' not in source


def test_new_technical_estimates_are_forwarded_to_finance_when_saved():
    source = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    create_estimate = source.split("def create_estimate", 1)[1].split("@router.post", 1)[0]
    forwarding = source.split("def _create_financial_from_estimate", 1)[1].split("@router.post", 1)[0]

    assert 'status="TechnicalReviewed"' in create_estimate
    assert "approved_quantity=qty" in create_estimate
    assert "return _create_financial_from_estimate(x.estimate_id, user, db, allow_creator=True)" in create_estimate
    assert 'x.status="ForwardedToFinance"' in forwarding
    assert 'status="Draft"' in forwarding
    assert '"engineering_approval":False' in forwarding
    assert 'linked_schedule.status="Submitted"' in forwarding
    assert 'linked_schedule.status="Completed"' not in forwarding
    assert "تم حفظ المستخلص وتحويله مباشرة إلى المالية دون اعتماد هندسي" in forwarding
