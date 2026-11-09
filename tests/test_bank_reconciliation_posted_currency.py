from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Account, AccountClassification, Base, JournalEntry, JournalEntryDetail, TreasuryAccount, TreasuryTransaction,
)
from app.routers.reconciliation import posted_book_balance
from app.routers.treasury import balance_of, _posted_treasury_movement_balance, balance_reconciliation


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    tables = [
        AccountClassification.__table__, Account.__table__, TreasuryAccount.__table__,
        JournalEntry.__table__, JournalEntryDetail.__table__, TreasuryTransaction.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _account(db, *, currency, opening_debit="0", opening_credit="0"):
    classification = AccountClassification(
        classification_id=1, name_ar="نقدية بالصندوق و البنوك",
        name_en="Cash and Banks", statement_type="BalanceSheet",
    )
    account = Account(
        account_id=10, account_code="10101001", account_name_ar="حساب البنك",
        classification_id=1, normal_balance="DR",
        opening_debit=Decimal(opening_debit), opening_credit=Decimal(opening_credit),
        is_active=True,
    )
    treasury = TreasuryAccount(
        treasury_account_id=1, name_ar="البنك", account_type="Bank",
        currency_code=currency, gl_account_id=10, is_active=True,
    )
    db.add_all([classification, account, treasury])
    db.flush()
    return treasury


def _entry(db, entry_id, *, status, entry_date=date(2026, 11, 8)):
    entry = JournalEntry(
        journal_entry_id=entry_id, entry_no=f"JE-{entry_id}", entry_date=entry_date,
        company_id=1, fiscal_year_id=2026, status=status,
    )
    db.add(entry)
    db.flush()
    return entry


def _line(db, entry, *, debit="0", credit="0", fcy=None):
    db.add(JournalEntryDetail(
        journal_entry_id=entry.journal_entry_id, line_no=1, account_id=10,
        debit_amount=Decimal(debit), credit_amount=Decimal(credit),
        fcy_amount=Decimal(fcy) if fcy is not None else None,
    ))


def test_egp_reconciliation_uses_posted_gl_only_and_includes_egp_opening_balance(db):
    treasury = _account(db, currency="EGP", opening_debit="1000", opening_credit="100")
    posted = _entry(db, 1, status="Posted")
    _line(db, posted, debit="500")
    _line(db, posted, credit="50")
    draft = _entry(db, 2, status="Draft")
    _line(db, draft, debit="900")
    reversed_entry = _entry(db, 3, status="Reversed")
    _line(db, reversed_entry, debit="700")
    future = _entry(db, 4, status="Posted", entry_date=date(2026, 11, 9))
    _line(db, future, debit="300")
    db.flush()

    result = posted_book_balance(db, treasury, date(2026, 11, 8))

    assert result == Decimal("1350.00")


def test_usd_reconciliation_uses_original_fcy_and_excludes_draft_and_egp_opening(db):
    treasury = _account(db, currency="USD", opening_debit="25000", opening_credit="5000")
    posted_in = _entry(db, 11, status="Posted")
    _line(db, posted_in, debit="5200", fcy="100")
    posted_out = _entry(db, 12, status="Posted")
    _line(db, posted_out, credit="1040", fcy="20")
    draft = _entry(db, 13, status="Draft")
    _line(db, draft, debit="2600", fcy="50")
    # A posted EGP-only adjustment must not be treated as a USD movement.
    egp_only = _entry(db, 14, status="Posted")
    _line(db, egp_only, debit="300", fcy=None)
    db.flush()

    result = posted_book_balance(db, treasury, date(2026, 11, 8))

    assert result == Decimal("80.00")


def _movement(db, movement_id, *, entry_id=None, inflow="0", outflow="0"):
    db.add(TreasuryTransaction(
        transaction_id=movement_id, treasury_account_id=1,
        transaction_date=date(2026, 11, 8), inflow=Decimal(inflow),
        outflow=Decimal(outflow), journal_entry_id=entry_id,
        description=f"Movement {movement_id}",
    ))


def test_official_treasury_balance_uses_posted_gl_only(db):
    treasury = _account(db, currency="EGP", opening_debit="1000", opening_credit="100")
    posted = _entry(db, 21, status="Posted")
    _line(db, posted, debit="500")
    draft = _entry(db, 22, status="Draft")
    _line(db, draft, debit="900")
    reversed_entry = _entry(db, 23, status="Reversed")
    _line(db, reversed_entry, debit="700")
    db.flush()
    _movement(db, 21, entry_id=21, inflow="500")
    _movement(db, 22, entry_id=22, inflow="900")
    _movement(db, 23, entry_id=23, inflow="700")
    _movement(db, 24, inflow="300")
    db.flush()

    assert balance_of(db, treasury.treasury_account_id) == Decimal("1400.00")
    assert _posted_treasury_movement_balance(db, treasury) == Decimal("1400.00")


def test_balance_reconciliation_explains_drafts_reversals_unlinked_and_orphans(db, monkeypatch):
    treasury = _account(db, currency="EGP", opening_debit="1000", opening_credit="100")
    # Posted and linked: the movement and GL line agree.
    posted = _entry(db, 31, status="Posted")
    _line(db, posted, debit="500")
    _movement(db, 31, entry_id=31, inflow="500")
    # Draft and reversed movements must remain visible but not affect balances.
    draft = _entry(db, 32, status="Draft")
    _line(db, draft, debit="900")
    _movement(db, 32, entry_id=32, inflow="900")
    reversed_entry = _entry(db, 33, status="Reversed")
    _line(db, reversed_entry, debit="700")
    _movement(db, 33, entry_id=33, inflow="700")
    _movement(db, 34, inflow="300")
    # A posted manual GL entry without a treasury transaction.
    manual = _entry(db, 35, status="Posted")
    _line(db, manual, credit="50")
    # A posted treasury transaction whose journal has no line for the bank GL account.
    missing_line = _entry(db, 36, status="Posted")
    db.add(JournalEntryDetail(
        journal_entry_id=36, line_no=1, account_id=20,
        debit_amount=Decimal("20"), credit_amount=Decimal("0"),
    ))
    _movement(db, 36, entry_id=36, outflow="20")
    other = Account(
        account_id=20, account_code="201", account_name_ar="طرف مقابل",
        classification_id=1, normal_balance="DR", opening_debit=0,
        opening_credit=0, is_active=True,
    )
    db.add(other)
    db.flush()

    from app.routers import treasury as treasury_router
    monkeypatch.setattr(treasury_router, "_bound", lambda _db, _screen: treasury)
    monkeypatch.setattr(treasury_router, "has_permission", lambda *_args: True)
    result = balance_reconciliation(
        "BankCibEgp", None, date(2026, 11, 8),
        type("UserStub", (), {"user_id": 1})(), db,
    )

    assert result["ledger_balance"] == "1350.00"
    assert result["posted_treasury_movement_balance"] == "1380.00"
    assert result["difference"] == "-30.00"
    assert result["excluded_movements"]["Draft"]["count"] == 1
    assert result["excluded_movements"]["Reversed"]["count"] == 1
    assert result["excluded_movements"]["Unlinked"]["count"] == 1
    assert len(result["posted_ledger_entries_without_treasury_movement"]) == 1
    assert len(result["posted_treasury_movements_without_gl_line"]) == 1
