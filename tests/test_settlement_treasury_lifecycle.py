from decimal import Decimal
from types import SimpleNamespace
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import sqlite

from app.routers import contract_erp, journal, treasury
from app.services_tb import compute_tb


class SettlementPaymentDB:
    def __init__(self, settlement, config, paid, reserved, contract, duplicate_count=0):
        self.values = [settlement, config, duplicate_count, paid, reserved]
        self.contract = contract

    def scalar(self, statement):
        return self.values.pop(0)

    def get(self, model, key):
        return self.contract


def _payment_fixture(side, *, paid="200", reserved="100", net="1000", duplicate_count=0):
    settlement = SimpleNamespace(
        settlement_id=71, contract_id=9, settlement_side=side,
        status="Posted", journal_entry_id=81, net_amount=Decimal(net),
        counterparty_id=17,
    )
    config = SimpleNamespace(control_account_id=20)
    contract = SimpleNamespace(project_id=5)
    db = SettlementPaymentDB(settlement, config, Decimal(paid), Decimal(reserved), contract, duplicate_count)
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
        voucher_no="VOUCHER-TEST-01",
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


@pytest.mark.parametrize("side,paid,reserved", [
    ("Customer", "200", "100"),
    ("Subcontractor", "300", "200"),
])
def test_full_remaining_amount_can_be_paid_exactly_once(side, paid, reserved):
    db, _ = _payment_fixture(side, paid=paid, reserved=reserved)
    available = Decimal("1000") - Decimal(paid) - Decimal(reserved)
    treasury._validate_settlement_payment(
        db, _payment_body(side=side, amount=str(available))
    )


def test_duplicate_payment_voucher_is_rejected():
    db, _ = _payment_fixture("Customer", duplicate_count=1)
    with pytest.raises(HTTPException) as exc:
        treasury._validate_settlement_payment(
            db, _payment_body(side="Customer", amount="100")
        )
    assert exc.value.status_code == 409
    assert "مستخدم بالفعل" in str(exc.value.detail)


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


class SettlementPostingDB:
    def __init__(self, entry, details, accounts, scalar_values):
        from tests.test_journal_posting_lifecycle import PostingDB
        self._posting = PostingDB(entry, details, accounts)
        self.scalar_values = list(scalar_values)
        self.commits = 0

    def scalars(self, statement):
        return self._posting.scalars(statement)

    def scalar(self, statement):
        return self.scalar_values.pop(0)

    def commit(self):
        self.commits += 1


def _post_linked_settlement(monkeypatch, *, final=False):
    entry = SimpleNamespace(
        journal_entry_id=41, entry_no="CS-00000071",
        entry_date=__import__("datetime").date(2026, 11, 9),
        status="Draft", source_settlement_id=71, posted_by=None, posted_at=None,
    )
    details = [
        SimpleNamespace(account_id=10, project_id=5,
                        debit_amount=Decimal("100"), credit_amount=Decimal("0")),
        SimpleNamespace(account_id=20, project_id=5,
                        debit_amount=Decimal("0"), credit_amount=Decimal("100")),
    ]
    accounts = [
        SimpleNamespace(account_id=10, is_active=True, account_code="10101001"),
        SimpleNamespace(account_id=20, is_active=True, account_code="20101001"),
    ]
    settlement = SimpleNamespace(
        settlement_id=71, journal_entry_id=41, status="JournalDraft",
        contract_id=9, is_final=final,
    )
    contract = SimpleNamespace(status="Active", contract_id=9, closed_at=None, closed_by=None)
    estimate = SimpleNamespace(estimate_id=3)
    schedule = SimpleNamespace(status="Submitted")
    values = [settlement, contract, estimate, schedule, 71, 0] if final else [
        settlement, contract, None, None,
    ]
    db = SettlementPostingDB(entry, details, accounts, values)
    fy = SimpleNamespace(is_closed=False)
    monkeypatch.setattr(journal, "_get", lambda _db, _eid: entry)
    monkeypatch.setattr(journal, "_validate_settlement_link", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_fy_for", lambda *args: fy)
    monkeypatch.setattr(journal, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_out", lambda _db, e: {"status": e.status})
    monkeypatch.setattr(journal, "utcnow", lambda: __import__("datetime").datetime(2026, 11, 9, 10))
    result = journal.post_entry(41, SimpleNamespace(user_id=5), db)
    return result, settlement, contract, schedule, db


def test_posting_settlement_journal_changes_status_only_at_journal_post():
    result, settlement, contract, schedule, db = _post_linked_settlement(pytest.MonkeyPatch())
    assert result["status"] == "Posted"
    assert settlement.status == "Posted"
    assert contract.status == "Active"
    assert db.commits == 1


def test_posting_final_settlement_completes_schedule_and_closes_contract():
    result, settlement, contract, schedule, db = _post_linked_settlement(pytest.MonkeyPatch(), final=True)
    assert result["status"] == "Posted"
    assert settlement.status == "Posted"
    assert schedule.status == "Completed"
    assert contract.status == "Closed"
    assert contract.closed_by == 5
    assert db.commits == 1


def test_trial_balance_query_uses_posted_journals_only():
    class CaptureDB:
        statement = None

        def execute(self, statement):
            self.statement = statement
            return []

    db = CaptureDB()
    assert compute_tb(db) == []
    compiled = db.statement.compile(dialect=sqlite.dialect())
    assert "JournalEntries" in str(compiled)
    assert "Status" in str(compiled)
    assert "Posted" in compiled.params.values()


def test_treasury_ledger_balance_query_uses_posted_journals_only():
    class CaptureDB:
        statement = None

        def scalar(self, statement):
            self.statement = statement
            return Decimal("0")

        def get(self, model, key):
            return SimpleNamespace(opening_debit=Decimal("0"), opening_credit=Decimal("0"))

    db = CaptureDB()
    account = SimpleNamespace(
        treasury_account_id=3, currency_code="EGP", gl_account_id=10,
    )
    assert treasury._posted_treasury_movement_balance(db, account) == Decimal("0")
    compiled = db.statement.compile(dialect=sqlite.dialect())
    assert "JournalEntries" in str(compiled)
    assert "Status" in str(compiled)
    assert "Posted" in compiled.params.values()


def test_treasury_api_accepts_settlement_link_and_validates_before_journal_creation():
    source = Path("app/routers/treasury.py").read_text(encoding="utf-8")
    txin = source.split("class TxIn", 1)[1].split("def _posted_treasury_movement_balance", 1)[0]
    add = source.split('def add_tx', 1)[1].split('def _tx', 1)[0]
    assert "settlement_id: int | None" in txin
    assert "_validate_settlement_payment(db, body)" in add
    assert "JournalEntry.status == \"Posted\"" in source
    assert "JournalEntry.status == \"Draft\"" in source
