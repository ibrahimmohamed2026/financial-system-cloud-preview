from app.models import ContractAddendumLine, ContractItem


def test_addendum_lines_keep_signed_quantity_delta_and_price():
    columns = ContractAddendumLine.__table__.columns
    assert "QuantityDelta" in columns
    assert "UnitPrice" in columns
    assert "AmountChange" in columns
    assert "TargetItemId" in columns
    assert "EffectiveItemId" in columns


def test_contract_items_retain_original_boq_baseline():
    columns = ContractItem.__table__.columns
    assert "OriginalQuantity" in columns
    assert "OriginalUnitPrice" in columns


def test_addendum_model_foreign_keys_resolve():
    from app.models import Base

    assert Base.metadata.sorted_tables
