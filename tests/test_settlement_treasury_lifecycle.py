from decimal import Decimal
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.routers import contract_erp, treasury


class SettlementPaymentDB:
    def __init__(self, settlement, config, paid, reserved, contract):
        self.values = [settlement, config, paid, reserved]
        self.contract = contract

    def scalar(self, statement):
        return self.values.pop(0)

    def get(self, model, key):
        return self.contract


def _payment_fixture(side, *, paid="200", reserved="100", net="1000"):
    settlement = SimpleNamespace(
        settlement_id=71, contract_id=9, settlement_side=side,
        status="Posted", journal_entry_id=81, net_amount=Decimal(net),
        counterparty_id=17,
    )
    config = SimpleNamespace(control_account_id=20)
    contract = SimpleNamespace(project_id=5)
    db = SettlementPaymentDB(settlement, config, Decimal(paid), Decimal(reserved), contract)
    return db, settlement


def _payment_body(*, side, amount, direction=None):
    direction = direction or ("inflow" if side == "Customer" else "outflow")
    return treasury.TxIn(
        transaction_date=__import__("datetime").date(2026, 11, 9),
        inflow=Decimal(amount) if direction == "inflow" else Decimal("0"),
        outflow=Decimal(amount) if direction == "outflow" else Decimal("0"),
        counterpart_account_id=20,
        counterparty_id=17,
        project_id=5,
        settlement_id=71,
        transaction_type="customer_collection" if side == "Customer" else "supplier_payment",
    )


def test_customer_partial_collection_is_allowed_and_uses_posted_and_reserved_totals():
    db, _ = _payment_fixture("Customer", paid="200", reserved="100")
    treasury._validate_settlement_payment(
        db, _payment_body(side="Customer", amount="300")
    )


def test_subcontractor_partial_payment_is_allowed_and_uses_outflow():
    db, _ = _payment_fixture("Subcontractor", paid="300", reserved="200")
    treasury._validate_settlement_payment(
        db, _payment_body(side="Subcontractor", amount="500")
    )


@pytest.mark.parametrize(
    "side,amount,paid,reserved",
    [
        ("Customer", "701", "200", "100"),
        ("Subcontractor", "501", "300", "200"),
        ("Customer", "101", "200", "700"),
    ],
)
def test_payment_cannot_exceed_remaining_amount_after_draft_reservations(side, amount, paid, reserved):
    db, _ = _payment_fixture(side, paid=paid, reserved=reserved)
    with pytest.raises(HTTPException) as exc:
        treasury._validate_settlement_payment(
            db, _payment_body(side=side, amount=amount)
        )
    assert exc.value.status_code == 409
    assert "المتاح بعد الحجوزات" in str(exc.value.detail)


def test_customer_settlement_rejects_outflow_link():
    db, _ = _payment_fixture("Customer")
    with pytest.raises(HTTPException) as exc:
        treasury._validate_settlement_payment(
            db, _payment_body(side="Customer", amount="100", direction="outflow")
        )
    assert exc.value.status_code == 422


def test_subcontractor_settlement_rejects_inflow_link():
    db, _ = _payment_fixture("Subcontractor")
    with pytest.raises(HTTPException) as exc:
        treasury._validate_settlement_payment(
            db, _payment_body(side="Subcontractor", amount="100", direction="inflow")
        )
    assert exc.value.status_code == 422


class SettlementOutputDB:
    def __init__(self, paid, reserved):
        self.values = [paid, reserved]

    def scalar(self, statement):
        return self.values.pop(0)

    def get(self, model, key):
        return SimpleNamespace(contract_no="CT-TEST", title="Test contract", title_en="Test")

    def scalars(self, statement):
        class Rows(list):
            def all(self):
                return list(self)
        return Rows()


def test_customer_paid_amount_uses_posted_inflow_and_exposes_draft_reservation():
    settlement = SimpleNamespace(
        settlement_id=71, contract_id=9, settlement_side="Customer",
        sequence_no=1, settlement_no="CUS-1", is_final=False,
        settlement_date=__import__("datetime").date(2026, 11, 9),
        counterparty_name="Customer", counterparty_name_en=None,
        work_value=Decimal("1000"), cumulative_work_value=Decimal("1000"),
        deductions_json={}, vat_amount=Decimal("0"), vat_rate=None,
        vat_tax_status=None, vat_base_type=None, vat_base_amount=None,
        vat_account_id=None, net_amount=Decimal("1000"), status="Posted",
        financial_approved_by=None, financial_approved_at=None,
        manager_approved_by=None, manager_approved_at=None,
        journal_entry_id=81, notes=None,
    )
    result = contract_erp.settlement_out(settlement, SettlementOutputDB("250", "50"))
    assert result["paid_amount"] == "250.00"
    assert result["reserved_amount"] == "50.00"
    assert result["remaining_amount"] == "750.00"
    assert result["available_amount"] == "700.00"


def test_subcontractor_paid_amount_uses_posted_outflow():
    settlement = SimpleNamespace(
        settlement_id=71, contract_id=9, settlement_side="Subcontractor",
        sequence_no=1, settlement_no="SUB-1", is_final=False,
        settlement_date=__import__("datetime").date(2026, 11, 9),
        counterparty_name="Contractor", counterparty_name_en=None,
        work_value=Decimal("1000"), cumulative_work_value=Decimal("1000"),
        deductions_json={}, vat_amount=Decimal("0"), vat_rate=None,
        vat_tax_status=None, vat_base_type=None, vat_base_amount=None,
        vat_account_id=None, net_amount=Decimal("1000"), status="Posted",
        financial_approved_by=None, financial_approved_at=None,
        manager_approved_by=None, manager_approved_at=None,
        journal_entry_id=81, notes=None,
    )
    result = contract_erp.settlement_out(settlement, SettlementOutputDB("350", "25"))
    assert result["paid_amount"] == "350.00"
    assert result["reserved_amount"] == "25.00"


def test_settlement_journal_is_created_as_draft_and_does_not_post_settlement_inline():
    source = Path("app/routers/contract_erp.py").read_text(encoding="utf-8")
    create = source.split('def post_settlement', 1)[1].split('@router.', 1)[0]
    assert 'status="Draft",created_by=user.user_id' in create
    assert 'x.status="JournalDraft"' in create
    assert 'x.status="Posted"' not in create
    assert '"journal_status":"Draft"' in create
    assert "linked_schedule.status = \"Completed\"" not in create


def test_journal_posting_finalizes_linked_settlement_and_schedule():
    source = Path("app/routers/journal.py").read_text(encoding="utf-8")
    post = source.split('def post_entry', 1)[1].split('@router.post("/{eid}/cancel")', 1)[0]
    assert 'settlement.journal_entry_id != e.journal_entry_id' in post
    assert 'settlement.status = "Posted"' in post
    assert 'linked_schedule.status = "Completed"' in post
    assert 'contract.status = "Closed"' in post


def test_treasury_api_accepts_settlement_link_and_validates_before_journal_creation():
    source = Path("app/routers/treasury.py").read_text(encoding="utf-8")
    txin = source.split("class TxIn", 1)[1].split("def _posted_treasury_movement_balance", 1)[0]
    add = source.split('def add_tx', 1)[1].split('def _tx', 1)[0]
    assert "settlement_id: int | None" in txin
    assert "_validate_settlement_payment(db, body)" in add
    assert "JournalEntry.status == \"Posted\"" in source
    assert "JournalEntry.status == \"Draft\"" in source
