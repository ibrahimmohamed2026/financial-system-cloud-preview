from app.models import ContractAddendum, ContractAddendumLine, ContractItem


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


def test_addendum_foreign_keys_resolve_without_global_table_sort():
    addendum_fks = {
        fk.target_fullname for fk in ContractAddendum.__table__.foreign_keys
    }
    line_fks = {
        fk.target_fullname for fk in ContractAddendumLine.__table__.foreign_keys
    }

    assert "Contracts.ContractId" in addendum_fks
    assert "ContractAddendums.AddendumId" in line_fks
    assert "ContractItems.ItemId" in line_fks
