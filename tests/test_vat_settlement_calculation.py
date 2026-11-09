from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers.contract_erp import calculate_vat


def config(**overrides):
    values = {
        "vat_enabled": True,
        "vat_tax_status": "Taxable",
        "vat_base_type": "CurrentWork",
        "default_vat_rate": Decimal("14"),
        "vat_account_id": 9001,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_vat_uses_current_work_base_and_contract_rate():
    result = calculate_vat(config(), Decimal("1000000"), Decimal("1200000"), Decimal("2000000"))
    assert result["amount"] == Decimal("140000.00")
    assert result["base_amount"] == Decimal("1000000.00")
    assert result["rate"] == Decimal("14")


@pytest.mark.parametrize(
    ("base_type", "expected"),
    [
        ("CumulativeWork", Decimal("168000.00")),
        ("RemainingContract", Decimal("112000.00")),
    ],
)
def test_vat_supports_contract_base_options(base_type, expected):
    result = calculate_vat(
        config(vat_base_type=base_type),
        Decimal("1000000"),
        Decimal("1200000"),
        Decimal("2000000"),
    )
    assert result["amount"] == expected


def test_invoice_can_override_rate_and_use_manual_tax_base():
    result = calculate_vat(
        config(),
        Decimal("1000000"),
        Decimal("1200000"),
        Decimal("2000000"),
        rate=Decimal("10"),
        tax_status="Taxable",
        base_type="Manual",
        base_amount=Decimal("750000"),
    )
    assert result["amount"] == Decimal("75000.00")
    assert result["base_type"] == "Manual"


@pytest.mark.parametrize("status", ["Exempt", "ZeroRated", "NotSubject"])
def test_non_taxable_statuses_do_not_calculate_vat(status):
    result = calculate_vat(
        config(vat_tax_status=status),
        Decimal("1000000"),
        Decimal("1200000"),
        Decimal("2000000"),
    )
    assert result["amount"] == Decimal("0.00")
    assert result["tax_status"] == status


def test_disabled_vat_does_not_apply_even_if_old_rate_exists():
    result = calculate_vat(
        config(vat_enabled=False, default_vat_rate=Decimal("14"), vat_tax_status="Taxable"),
        Decimal("1000000"),
        Decimal("1200000"),
        Decimal("2000000"),
    )
    assert result["amount"] == Decimal("0.00")
    assert result["tax_status"] == "NotSubject"


def test_manual_base_requires_an_invoice_amount():
    with pytest.raises(HTTPException) as exc:
        calculate_vat(
            config(),
            Decimal("1000000"),
            Decimal("1200000"),
            Decimal("2000000"),
            base_type="Manual",
        )
    assert exc.value.status_code == 422


def test_positive_vat_requires_a_linked_account():
    with pytest.raises(HTTPException) as exc:
        calculate_vat(
            config(vat_account_id=None),
            Decimal("1000000"),
            Decimal("1200000"),
            Decimal("2000000"),
        )
    assert exc.value.status_code == 422


def test_legacy_contract_rate_remains_enabled_when_new_flag_is_null():
    legacy = SimpleNamespace(
        default_vat_rate=Decimal("14"),
        vat_tax_status=None,
        vat_base_type=None,
        vat_account_id=9001,
    )
    result = calculate_vat(legacy, Decimal("1000000"), Decimal("1200000"), Decimal("2000000"))
    assert result["amount"] == Decimal("140000.00")
    assert result["tax_status"] == "Taxable"
