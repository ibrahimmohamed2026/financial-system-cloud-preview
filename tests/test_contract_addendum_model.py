from decimal import Decimal

from app.models import ContractAddendum, ContractAddendumLine, ContractItem
from app.routers.contracts import _addendum_line_amount_change


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


def test_new_addendum_item_value_is_quantity_times_unit_price():
    assert _addendum_line_amount_change(None, None, "5", "20") == Decimal("100.00")


def test_existing_item_addendum_value_includes_rate_change_and_quantity_delta():
    # Existing: 100 × 10. Revised: 120 × 12. Difference = 440.
    assert _addendum_line_amount_change("100", "10", "20", "12") == Decimal("440.00")


def test_existing_item_reduction_uses_new_rate_for_reduced_quantity():
    # Existing: 100 × 10. Revised: 90 × 12. Difference = 80.
    assert _addendum_line_amount_change("100", "10", "-10", "12") == Decimal("80.00")
