from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    Company,
    Contract,
    ContractItem,
    ContractSettlement,
    ContractSettlementItem,
    FiscalYear,
    JournalEntry,
    JournalEntryDetail,
    TechnicalSettlementEstimate,
    TechnicalSettlementEstimateItem,
    User,
)
from app.routers import contract_erp, journal, technical_settlements


@pytest.fixture
def settlement_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        contract = Contract(
            contract_no="CT-FINAL-TEST",
            title="اختبار المستخلص الختامي",
            client_name="عميل اختبار",
            original_value=Decimal("1000.00"),
            status="Active",
        )
        db.add(contract)
        db.flush()
        item = ContractItem(
            contract_id=contract.contract_id,
            item_no="1",
            description="أعمال اختبار",
            unit="متر",
            quantity=Decimal("10.0000"),
            unit_price=Decimal("10.0000"),
        )
        db.add(item)
        db.flush()
        for user_id in (1, 2, 3, 4):
            db.add(User(
                user_id=user_id,
                username=f"final-test-{user_id}",
                password_hash=b"test-hash",
                full_name=f"Test User {user_id}",
                is_active=True,
            ))
        db.commit()
        yield db, contract, item
    engine.dispose()


def _financial_settlement(db, contract, item, *, quantity, status, is_final=True,
                          work_value=None, sequence=1, financial_approved_by=2):
    quantity = Decimal(str(quantity))
    work_value = Decimal(str(work_value if work_value is not None else quantity * Decimal("10")))
    settlement = ContractSettlement(
        contract_id=contract.contract_id,
        settlement_side="Customer",
        sequence_no=sequence,
        settlement_no=f"ST-FINAL-{sequence:03d}",
        is_final=is_final,
        settlement_date=date(2026, 11, 10),
        counterparty_name="عميل اختبار",
        work_value=work_value,
        cumulative_work_value=work_value,
        deductions_json={},
        vat_amount=Decimal("0.00"),
        net_amount=work_value,
        status=status,
        financial_approved_by=financial_approved_by,
        created_by=1,
    )
    db.add(settlement)
    db.flush()
    db.add(ContractSettlementItem(
        settlement_id=settlement.settlement_id,
        contract_item_id=item.item_id,
        quantity=quantity,
        unit_price=Decimal("10.0000"),
        amount=work_value,
    ))
    db.flush()
    return settlement


def _technical_estimate(db, contract, item, *, quantity, financial=None, status="ForwardedToFinance"):
    quantity = Decimal(str(quantity))
    estimate = TechnicalSettlementEstimate(
        contract_id=contract.contract_id,
        settlement_side="Customer",
        estimate_no="TE-FINAL-001",
        estimate_date=date(2026, 11, 10),
        counterparty_name="عميل اختبار",
        work_value=quantity * Decimal("10.00"),
        status=status,
        financial_settlement_id=financial.settlement_id if financial else None,
        is_final=False,
        created_by=1,
    )
    db.add(estimate)
    db.flush()
    db.add(TechnicalSettlementEstimateItem(
        estimate_id=estimate.estimate_id,
        contract_item_id=item.item_id,
        current_quantity=quantity,
        approved_quantity=quantity,
        unit_price=Decimal("10.0000"),
        amount=quantity * Decimal("10.00"),
    ))
    db.flush()
    return estimate


def _user(user_id):
    return SimpleNamespace(user_id=user_id)


def _patch_audit_and_output(monkeypatch):
    monkeypatch.setattr(contract_erp, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(technical_settlements, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        contract_erp, "settlement_out",
        lambda x, db: {"settlement_id": x.settlement_id, "status": x.status, "is_final": x.is_final},
    )


def test_final_quantity_helper_allows_exact_zero_remaining(settlement_db):
    db, contract, item = settlement_db

    gaps = contract_erp.final_settlement_quantity_gaps(
        db, contract.contract_id, "Customer",
        candidate={item.item_id: Decimal("10.0000")},
    )

    assert gaps == []


def test_final_quantity_helper_reports_every_remaining_item_quantity(settlement_db):
    db, contract, item = settlement_db

    gaps = contract_erp.final_settlement_quantity_gaps(
        db, contract.contract_id, "Customer",
        candidate={item.item_id: Decimal("9.0000")},
    )

    assert len(gaps) == 1
    assert gaps[0]["item_no"] == "1"
    assert Decimal(gaps[0]["remaining_quantity"]) == Decimal("1.0000")


def test_linked_technical_and_financial_settlement_are_counted_once(settlement_db):
    db, contract, item = settlement_db
    financial = _financial_settlement(
        db, contract, item, quantity="6", status="Posted", is_final=False,
        sequence=1, work_value="60",
    )
    estimate = _technical_estimate(db, contract, item, quantity="6", financial=financial)
    db.commit()

    used = contract_erp.settled_contract_item_quantities(db, contract.contract_id, "Customer")
    gaps = contract_erp.final_settlement_quantity_gaps(
        db, contract.contract_id, "Customer",
        candidate={item.item_id: Decimal("4.0000")},
    )

    assert used[item.item_id] == Decimal("6.0000")
    assert estimate.financial_settlement_id == financial.settlement_id
    assert gaps == []


def test_technical_final_creation_api_accepts_exact_quantities_and_keeps_contract_active(
    settlement_db, monkeypatch
):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    body = technical_settlements.EstimateIn(
        contract_id=contract.contract_id,
        is_final=True,
        settlement_side="Customer",
        counterparty_name="عميل اختبار",
        items=[technical_settlements.EstimateLine(
            contract_item_id=item.item_id,
            current_quantity=Decimal("10.0000"),
        )],
    )

    result = technical_settlements.create_estimate(body, _user(1), db)

    assert result["estimate"]["is_final"] is True
    assert result["financial_status"] == "Draft"
    assert contract.status == "Active"


def test_technical_final_creation_api_rejects_any_remaining_quantity(settlement_db, monkeypatch):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    body = technical_settlements.EstimateIn(
        contract_id=contract.contract_id,
        is_final=True,
        settlement_side="Customer",
        counterparty_name="عميل اختبار",
        items=[technical_settlements.EstimateLine(
            contract_item_id=item.item_id,
            current_quantity=Decimal("9.0000"),
        )],
    )

    with pytest.raises(HTTPException) as error:
        technical_settlements.create_estimate(body, _user(1), db)

    assert error.value.status_code == 409
    assert "البند 1" in error.value.detail
    assert "المتبقي 1.0000" in error.value.detail


def test_financial_final_creation_api_accepts_exact_quantities(settlement_db, monkeypatch):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    body = contract_erp.SettlementIn(
        settlement_side="Customer",
        is_final=True,
        settlement_date=date(2026, 11, 10),
        counterparty_name="عميل اختبار",
        items=[contract_erp.SettlementLineIn(
            contract_item_id=item.item_id,
            quantity=Decimal("10.0000"),
        )],
    )

    result = contract_erp.create_settlement(contract.contract_id, body, _user(1), db)

    assert result["is_final"] is True
    assert result["status"] == "PendingApproval"
    assert contract.status == "Active"


def test_financial_final_creation_api_rejects_any_remaining_quantity(settlement_db, monkeypatch):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    body = contract_erp.SettlementIn(
        settlement_side="Customer",
        is_final=True,
        settlement_date=date(2026, 11, 10),
        counterparty_name="عميل اختبار",
        items=[contract_erp.SettlementLineIn(
            contract_item_id=item.item_id,
            quantity=Decimal("9.0000"),
        )],
    )

    with pytest.raises(HTTPException) as error:
        contract_erp.create_settlement(contract.contract_id, body, _user(1), db)

    assert error.value.status_code == 409
    assert "البند 1" in error.value.detail
    assert "المتبقي 1.0000" in error.value.detail


def test_final_manager_approval_api_rejects_incomplete_item_quantities(settlement_db, monkeypatch):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    settlement = _financial_settlement(
        db, contract, item, quantity="9", status="PendingFinalApproval",
        work_value="90", sequence=1, financial_approved_by=2,
    )
    db.commit()

    with pytest.raises(HTTPException) as error:
        contract_erp.manager_approve_settlement(settlement.settlement_id, _user(3), db)

    assert error.value.status_code == 409
    assert "المتبقي 1.0000" in error.value.detail
    assert contract.status == "Active"
    assert settlement.status == "PendingFinalApproval"


def test_final_manager_approval_does_not_close_before_journal_posting(settlement_db, monkeypatch):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    settlement = _financial_settlement(
        db, contract, item, quantity="10", status="PendingFinalApproval",
        work_value="100", sequence=1, financial_approved_by=2,
    )
    db.commit()

    result = contract_erp.manager_approve_settlement(settlement.settlement_id, _user(3), db)

    assert result["status"] == "Approved"
    assert contract.status == "Active"


def test_final_settlement_posting_api_rejects_incomplete_item_quantities(settlement_db):
    db, contract, item = settlement_db
    settlement = _financial_settlement(
        db, contract, item, quantity="9", status="Approved",
        work_value="90", sequence=1, financial_approved_by=2,
    )
    db.commit()

    with pytest.raises(HTTPException) as error:
        contract_erp.post_settlement(settlement.settlement_id, _user(4), db)

    assert error.value.status_code == 409
    assert "المتبقي 1.0000" in error.value.detail
    assert contract.status == "Active"
    assert settlement.status == "Approved"


def _journal_fixture(db, contract, item, quantity):
    settlement = _financial_settlement(
        db, contract, item, quantity=quantity, status="JournalDraft",
        work_value=Decimal(str(quantity)) * Decimal("10"), sequence=1,
        financial_approved_by=2,
    )
    company = Company(name_ar="شركة اختبار")
    db.add(company)
    db.flush()
    fiscal_year = FiscalYear(
        company_id=company.company_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_closed=False,
    )
    db.add(fiscal_year)
    db.flush()
    entry = JournalEntry(
        entry_no="JE-FINAL-TEST",
        entry_date=date(2026, 11, 10),
        company_id=company.company_id,
        fiscal_year_id=fiscal_year.fiscal_year_id,
        source_settlement_id=settlement.settlement_id,
        description="قيد اختبار المستخلص الختامي",
        status="Draft",
        created_by=1,
    )
    db.add(entry)
    db.flush()
    settlement.journal_entry_id = entry.journal_entry_id
    db.add_all([
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id,
            line_no=1,
            account_id=1,
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("0.00"),
            description="مدين",
        ),
        JournalEntryDetail(
            journal_entry_id=entry.journal_entry_id,
            line_no=2,
            account_id=2,
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("100.00"),
            description="دائن",
        ),
    ])
    db.commit()
    return settlement, entry


def _patch_journal_validation(monkeypatch):
    monkeypatch.setattr(journal, "_validate_settlement_link", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_fy_for", lambda *args, **kwargs: SimpleNamespace(is_closed=False))
    monkeypatch.setattr(journal, "_validate_lines", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_out", lambda db, entry: {"status": entry.status})


def test_final_journal_post_api_rejects_incomplete_quantities_without_closing_contract(
    settlement_db, monkeypatch
):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    _patch_journal_validation(monkeypatch)
    settlement, entry = _journal_fixture(db, contract, item, "9")

    with pytest.raises(HTTPException) as error:
        journal.post_entry(entry.journal_entry_id, _user(4), db)

    assert error.value.status_code == 409
    assert "المتبقي 1.0000" in error.value.detail
    assert entry.status == "Draft"
    assert settlement.status == "JournalDraft"
    assert contract.status == "Active"


def test_contract_closes_only_after_complete_final_journal_is_posted(
    settlement_db, monkeypatch
):
    db, contract, item = settlement_db
    _patch_audit_and_output(monkeypatch)
    _patch_journal_validation(monkeypatch)
    settlement, entry = _journal_fixture(db, contract, item, "10")

    result = journal.post_entry(entry.journal_entry_id, _user(4), db)

    assert result["status"] == "Posted"
    assert settlement.status == "Posted"
    assert contract.status == "Closed"
    assert contract.closed_by == 4
    assert contract.closed_at is not None


def test_contract_auto_close_exists_only_in_final_journal_posting_path():
    technical = open("app/routers/technical_settlements.py", encoding="utf-8").read()
    contract_erp_source = open("app/routers/contract_erp.py", encoding="utf-8").read()
    journal_source = open("app/routers/journal.py", encoding="utf-8").read()

    create_estimate = technical.split("def create_estimate", 1)[1].split("@router.post", 1)[0]
    create_settlement = contract_erp_source.split("def create_settlement", 1)[1].split("@router.get", 1)[0]
    manager_approve = contract_erp_source.split("def manager_approve_settlement", 1)[1].split("@router.post", 1)[0]
    journal_post = journal_source.split('def post_entry', 1)[1].split('@router.post("/{eid}/cancel")', 1)[0]

    assert 'status = "Closed"' not in create_estimate
    assert 'status = "Closed"' not in create_settlement
    assert 'status = "Closed"' not in manager_approve
    assert 'contract.status = "Closed"' in journal_post
    assert "final_settlement_quantity_gaps" in journal_post
    assert "ensure_no_unfinished_final_settlements" in journal_post
