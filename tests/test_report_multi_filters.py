from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.routers import journal, reports, trial_balance


def test_journal_account_filter_uses_exists_and_does_not_duplicate_entries():
    db = MagicMock()
    db.scalar.return_value = 0
    db.scalars.return_value = []

    result = journal.list_entries(account_ids=[11, 22], db=db, _=None)

    assert result == {"total": 0, "items": []}
    statement = str(db.scalar.call_args.args[0])
    assert "EXISTS" in statement.upper()
    assert "account_id IN" in statement


def test_trial_balance_filters_rows_and_totals_to_selected_accounts(monkeypatch):
    rows = [
        {"account_id": 1, "code": "1001", "name": "Cash", "name_en": "Cash",
         "classification_id": 1, "classification": "Assets", "classification_en": "Assets",
         "level": 1, "is_parent": False, "own": {"od": Decimal("10"), "oc": Decimal("0"), "d": Decimal("5"), "c": Decimal("0")},
         "od": Decimal("10"), "oc": Decimal("0"), "d": Decimal("5"), "c": Decimal("0"),
         "td": Decimal("15"), "tc": Decimal("0"), "bd": Decimal("15"), "bc": Decimal("0")},
        {"account_id": 2, "code": "2001", "name": "Payable", "name_en": "Payable",
         "classification_id": 2, "classification": "Liabilities", "classification_en": "Liabilities",
         "level": 1, "is_parent": False, "own": {"od": Decimal("0"), "oc": Decimal("20"), "d": Decimal("0"), "c": Decimal("7")},
         "od": Decimal("0"), "oc": Decimal("20"), "d": Decimal("0"), "c": Decimal("7"),
         "td": Decimal("0"), "tc": Decimal("27"), "bd": Decimal("0"), "bc": Decimal("27")},
    ]
    monkeypatch.setattr(trial_balance, "compute_tb", lambda *args: rows)

    result = trial_balance.trial_balance(account_ids=[1], db=MagicMock(), _=None)

    assert [item["account_id"] for item in result["items"]] == [1]
    assert result["totals"]["td"] == "15.00"
    assert result["totals"]["tc"] == "0.00"
    assert result["balanced"] is False


def test_cash_flow_report_keeps_currency_totals_separate_and_filters_multiple_banks():
    egp = SimpleNamespace(treasury_account_id=3, name_ar="Cash EGP", currency_code="EGP")
    usd = SimpleNamespace(treasury_account_id=4, name_ar="Bank USD", currency_code="USD")
    rows = [
        (SimpleNamespace(transaction_date=date(2026, 11, 7), inflow=Decimal("100"), outflow=0,
                         project_id=None, voucher_no="EG-1", description="", recipient_name=""),
         egp),
        (SimpleNamespace(transaction_date=date(2026, 11, 7), inflow=Decimal("20"), outflow=Decimal("5"),
                         project_id=None, voucher_no="US-1", description="", recipient_name=""),
         usd),
    ]
    db = MagicMock()
    db.execute.return_value.all.return_value = rows

    result = reports.cash_flow_report(treasury_account_ids=[3, 4], db=db, _=None)

    totals = {item["currency"]: item for item in result["summary"]["currency_totals"]}
    assert totals["EGP"]["inflow"] == "100"
    assert totals["USD"]["inflow"] == "20"
    assert totals["USD"]["outflow"] == "5"
    assert "inflow" not in result["summary"]
    statement = str(db.execute.call_args.args[0])
    assert "IN" in statement.upper()


def test_checks_report_keeps_bank_currency_totals_separate():
    rows = [
        (SimpleNamespace(check_no="C-1", sequence_no=1, check_date=date(2026, 11, 7),
                         amount=Decimal("500"), status="تم الصرف", project_id=None, description=""),
         "Supplier A", "CIB EGP", "EGP", None),
        (SimpleNamespace(check_no="C-2", sequence_no=2, check_date=date(2026, 11, 7),
                         amount=Decimal("50"), status="جديد", project_id=None, description=""),
         "Supplier B", "CIB USD", "USD", "SET-2"),
    ]
    db = MagicMock()
    db.execute.return_value.all.return_value = rows

    result = reports.checks_report(treasury_account_ids=[3, 4], db=db, _=None)

    totals = {item["currency"]: item for item in result["summary"]["currency_totals"]}
    assert totals["EGP"]["amount"] == "500.00"
    assert totals["EGP"]["paid_amount"] == "500.00"
    assert totals["USD"]["amount"] == "50.00"
    assert result["summary"]["unlinked_count"] == 1
    statement = str(db.execute.call_args.args[0])
    assert "IN" in statement.upper()
