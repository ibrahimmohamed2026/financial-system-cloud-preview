from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, Contract, ContractDeductionRule, ContractSettlement
from app.routers.contract_erp import validate_contract_rule_update


@pytest.fixture
def retention_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        contract = Contract(
            contract_no="CT-RET-TEST",
            title="اختبار عقد التأمين",
            client_name="عميل اختبار",
            original_value=Decimal("10000000.00"),
            status="Active",
        )
        db.add(contract)
        db.flush()
        rule = ContractDeductionRule(
            contract_id=contract.contract_id,
            settlement_side="Subcontractor",
            code="RETENTION",
            name_ar="تأمين محجوز",
            calculation_type="Percent",
            rate=Decimal("10"),
            base_type="CurrentWork",
            application_mode="PerSettlement",
            cap_percent=Decimal("10"),
            posting_side="Credit",
            is_active=True,
        )
        db.add(rule)
        db.flush()
        db.commit()
        yield db, contract, rule
    engine.dispose()


def add_settlement(db, contract, *, status, amount, sequence=1):
    settlement = ContractSettlement(
        contract_id=contract.contract_id,
        settlement_side="Subcontractor",
        sequence_no=sequence,
        settlement_no=f"ST-RET-{sequence:03d}",
        settlement_date=date(2026, 11, 9),
        counterparty_name="مقاول اختبار",
        work_value=Decimal("1000000.00"),
        cumulative_work_value=Decimal("1000000.00"),
        deductions_json={"RETENTION": {"name": "تأمين محجوز", "amount": str(amount)}},
        vat_amount=Decimal("0.00"),
        net_amount=Decimal("1000000.00") - Decimal(str(amount)),
        status=status,
    )
    db.add(settlement)
    db.commit()
    return settlement


def test_database_guard_blocks_regular_rate_or_mode_change_after_posted_settlement(retention_db):
    db, contract, rule = retention_db
    add_settlement(db, contract, status="Posted", amount="700000.00")

    with pytest.raises(HTTPException) as error:
        validate_contract_rule_update(db, rule, {
            "application_mode": "SingleSettlement",
            "rate": Decimal("12"),
            "cap_percent": Decimal("12"),
        })

    assert error.value.status_code == 409
    assert "مسار التعديل المنضبط" in error.value.detail


def test_database_guard_rejects_cap_below_real_reserved_amount(retention_db):
    db, contract, rule = retention_db
    add_settlement(db, contract, status="Posted", amount="700000.00")

    with pytest.raises(HTTPException) as error:
        validate_contract_rule_update(
            db, rule, {"cap_percent": Decimal("5")},
            controlled_reason="تعديل موثق لشروط التأمين",
        )

    assert error.value.status_code == 409
    assert "500000.00" in error.value.detail
    assert "700000.00" in error.value.detail


def test_controlled_rate_change_keeps_posted_settlement_snapshot_unchanged(retention_db):
    db, contract, rule = retention_db
    settlement = add_settlement(db, contract, status="Posted", amount="700000.00")

    proposed = {
        "settlement_side": rule.settlement_side,
        "code": rule.code,
        "name_ar": rule.name_ar,
        "calculation_type": rule.calculation_type,
        "rate": Decimal("12"),
        "base_type": rule.base_type,
        "application_mode": rule.application_mode,
        "cap_percent": Decimal("12"),
        "posting_side": rule.posting_side,
        "cap_amount": rule.cap_amount,
        "gl_account_id": rule.gl_account_id,
        "is_active": rule.is_active,
        "sort_order": rule.sort_order,
    }
    validate_contract_rule_update(
        db, rule, proposed,
        controlled_reason="تعديل شروط النسبة والسقف للمستخلصات المستقبلية",
    )

    rule.rate = proposed["rate"]
    rule.cap_percent = proposed["cap_percent"]
    db.commit()
    db.refresh(settlement)

    assert rule.rate == Decimal("12")
    assert rule.cap_percent == Decimal("12")
    assert settlement.deductions_json["RETENTION"]["amount"] == "700000.00"


def test_controlled_change_is_blocked_while_settlement_is_pending(retention_db):
    db, contract, rule = retention_db
    add_settlement(db, contract, status="PendingApproval", amount="0.00")

    proposed = {
        "settlement_side": rule.settlement_side,
        "code": rule.code,
        "name_ar": rule.name_ar,
        "calculation_type": rule.calculation_type,
        "rate": Decimal("12"),
        "base_type": rule.base_type,
        "application_mode": rule.application_mode,
        "cap_percent": rule.cap_percent,
        "posting_side": rule.posting_side,
        "cap_amount": rule.cap_amount,
        "gl_account_id": rule.gl_account_id,
        "is_active": rule.is_active,
        "sort_order": rule.sort_order,
    }
    with pytest.raises(HTTPException) as error:
        validate_contract_rule_update(
            db, rule, proposed,
            controlled_reason="تعديل موثق لشروط التأمين",
        )

    assert error.value.status_code == 409
    assert "ST-RET-001" in error.value.detail
