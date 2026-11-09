from app.bootstrap import SCREENS
from app.routers.checks import CHECK_BANK_SCREEN, CHECK_CURRENCY, CHECK_SCREENS
from app.routers.treasury import BANK_SCREENS


def test_only_two_cashboxes_and_two_cib_bank_accounts_are_configured():
    assert BANK_SCREENS == {
        "BankCibEgp": ("Bank", "EGP"),
        "BankCibUsd": ("Bank", "USD"),
        "CashEgp": ("Cash", "EGP"),
        "CashUsd": ("Cash", "USD"),
    }


def test_cheque_books_are_cib_egp_and_cib_usd_only():
    assert CHECK_SCREENS == {"ChecksCib", "ChecksCibUsd"}
    assert CHECK_CURRENCY == {"ChecksCib": "EGP", "ChecksCibUsd": "USD"}
    assert CHECK_BANK_SCREEN == {"ChecksCib": "BankCibEgp", "ChecksCibUsd": "BankCibUsd"}


def test_seeded_treasury_and_cheque_routes_match_the_fixed_scope():
    screens = {item["code"]: item["route"] for item in SCREENS}
    assert {code for code in screens if code.startswith("BankCib") or (code.startswith("Cash") and code != "CashAnalysis")} == {
        "BankCibEgp", "BankCibUsd", "CashEgp", "CashUsd"
    }
    assert {code for code in screens if code.startswith("Checks")} == {
        "ChecksCib", "ChecksCibUsd"
    }
    assert screens["BankCibEgp"] == "/treasury/cib-egp"
    assert screens["BankCibUsd"] == "/treasury/cib-usd"
    assert screens["CashEgp"] == "/treasury/cash-egp"
    assert screens["CashUsd"] == "/treasury/cash-usd"
    assert screens["ChecksCib"] == "/checks/cib"
    assert screens["ChecksCibUsd"] == "/checks/cib-usd"
