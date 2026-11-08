from app.routers.contracts import ContractIn


def test_new_contracts_do_not_require_a_fixed_settlement_count_or_schedule():
    # The agreed workflow allows progress settlements as work is completed;
    # a fixed count/distribution schedule is no longer part of contract creation.
    assert "agreed_statement_count" not in ContractIn.model_fields
    assert "statement_distribution_method" not in ContractIn.model_fields
    assert "schedule_items" not in ContractIn.model_fields
