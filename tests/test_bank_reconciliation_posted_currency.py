from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Account, AccountClassification, Base, JournalEntry, JournalEntryDetail, TreasuryAccount,
)
from app.routers.reconciliation import posted_book_balance


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    tables = [
        AccountClassification.__table__, Account.__table__, TreasuryAccount.__table__,
        JournalEntry.__table__, JournalEntryDetail.__table__,
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
