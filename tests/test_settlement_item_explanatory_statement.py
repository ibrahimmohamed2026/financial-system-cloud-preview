from pathlib import Path


def test_settlement_item_explanatory_statement_is_persisted_and_forwarded():
    models = Path("app/models.py").read_text(encoding="utf-8")
    assert models.count('C("ExplanatoryStatement", UnicodeText, nullable=True)') == 2

    technical = Path("app/routers/technical_settlements.py").read_text(encoding="utf-8")
    assert "explanatory_statement: str | None = None" in technical
    assert '"explanatory_statement":i.explanatory_statement' in technical
    assert "explanatory_statement=explanatory_statement" in technical
    assert "explanatory_statement=line.explanatory_statement" in technical

    financial = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    assert '"explanatory_statement":getattr(line,"explanatory_statement",None)' in financial
    assert 'explanatory_statement=((requested_line.explanatory_statement or "").strip() or None)' in financial

    setup = Path("app/db_setup.py").read_text(encoding="utf-8")
    assert '"ContractSettlementItems", "TechnicalSettlementEstimates", "TechnicalSettlementEstimateItems"' in setup

    ui = Path("web/pages/settlements.js").read_text(encoding="utf-8")
    assert "data-explanatory-statement=" in ui
    assert "explanatory_statement:itemsBox.querySelector" in ui
    assert "i.explanatory_statement" in ui
    assert "البيان التوضيحي" in ui
