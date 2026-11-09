from pathlib import Path


def test_customer_card_link_is_the_only_customer_gl_source():
    source = Path("app/counterparties.py").read_text(encoding="utf-8")
    validator = source.split("def validate_customer_party", 1)[1]
    assert "party.linked_account_id" in validator
    assert "party.account_id" not in validator
    assert "account.normal_balance" in validator
    assert '"DR"' in validator
    assert "balancesheet" in validator
    assert "Counterparty.linked_account_id == account.account_id" in validator
    assert "require_account" in validator


def test_contract_creation_requires_customer_card_and_uses_master_names():
    source = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    contract_input = source.split("class ContractIn", 1)[1].split("class AddendumIn", 1)[0]
    create = source.split("def create_contract", 1)[1].split("@router", 1)[0]
    assert "counterparty_id: int = Field(gt=0)" in contract_input
    assert "validate_customer_party(db, body.counterparty_id)" in create
    assert 'values["client_name"] = party.legal_name or party.name' in create
    assert 'values["client_name_en"] = party.name_en' in create


def test_customer_change_is_blocked_after_settlement_history_exists():
    source = Path("app/routers/contracts.py").read_text(encoding="utf-8")
    update = source.split("\ndef update_contract(", 1)[1].split("\n@router", 1)[0]
    assert "body.counterparty_id != c.counterparty_id" in update
    assert "ContractSettlement.settlement_id" in update
    assert "TechnicalSettlementEstimate.estimate_id" in update
    assert "ProgressBilling.billing_id" in update
    assert "حفاظًا على هوية المستندات والسجل المحاسبي التاريخي" in update


def test_technical_and_financial_statements_inherit_contract_customer():
    technical = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    create = technical.split("def create_estimate", 1)[1].split("@router", 1)[0]
    helper = technical.split("def _create_financial_from_estimate", 1)[1]
    assert 'validate_customer_party(db, c.counterparty_id) if body.settlement_side == "Customer"' in create
    assert "counterparty_id=customer_party.counterparty_id if customer_party else None" in create
    assert "x.counterparty_id = customer_party.counterparty_id" in helper
    assert "fin.counterparty_id=customer_party.counterparty_id if customer_party else x.counterparty_id" in helper


def test_customer_financial_posting_uses_card_link_and_blocks_mismatch():
    source = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    posting = source.split("def post_settlement", 1)[1].split("@router.delete", 1)[0]
    assert "validate_customer_party(db, contract.counterparty_id, require_account=True)" in posting
    assert "x.counterparty_id != customer_party.counterparty_id" in posting
    assert "line(customer_party.linked_account_id,debit=x.net_amount" in posting
    assert "line(cfg.control_account_id,debit=x.net_amount" not in posting


def test_accounting_config_cannot_override_customer_card_gl_account():
    source = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    save = source.split("def save_config", 1)[1].split("@router.get", 1)[0]
    get = source.split("def get_config", 1)[1].split("def contract_financial_summary", 1)[0]
    assert 'config_values["control_account_id"] = customer_party.linked_account_id' in save
    assert "customer_party.linked_account_id if x.settlement_side == \"Customer\"" in get


def test_approved_contract_request_carries_customer_card_to_contract():
    source = Path("app/routers/contract_requests.py").read_text(encoding="utf-8")
    create = source.split("def create_contract_from_request", 1)[1]
    assert "validate_customer_party(db, x.counterparty_id)" in create
    assert "counterparty_id=party.counterparty_id" in create


def test_contract_ui_selects_customer_card_instead_of_free_text_identity():
    source = Path("web/pages/contracts.js").read_text(encoding="utf-8")
    assert "/api/counterparties/contract-options" in source
    assert "name:'counterparty_id'" in source
    assert "readonly:true" in source
    assert "v.client_name=selectedCustomer.legal_name" in source



def test_customer_name_is_not_entered_again_on_technical_statement():
    technical = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    ui = Path("web/pages/settlements.js").read_text(encoding="utf-8")
    assert "counterparty_name: str | None = Field(default=None" in technical
    assert 'body.settlement_side == "Subcontractor" and not (body.counterparty_name or "").strip()' in technical
    assert "const syncPartyFields=()=>{const customer=form.settlement_side.value==='Customer'" in ui
    assert "counterparty_name:data.counterparty_name||null" in ui


def test_direct_customer_settlement_also_inherits_contract_party():
    source = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    create = source.split("def create_settlement", 1)[1].split("@router.get", 1)[0]
    assert 'validate_customer_party(db, c.counterparty_id) if side == "Customer"' in create
    assert "counterparty_id=customer_party.counterparty_id if customer_party else None" in create
    assert "if side == " + '"Subcontractor"' + " and not (body.counterparty_name or \"\").strip()" in create
