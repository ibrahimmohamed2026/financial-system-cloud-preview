from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import journal


class Rows(list):
    def all(self):
        return list(self)


class PostingDB:
    def __init__(self, entry, details):
        self.entry = entry
        self.details = details
        self.commits = 0

    def scalars(self, statement):
        return Rows(self.details)

    def commit(self):
        self.commits += 1


def _posting_fixture(monkeypatch, *, status="Draft", balanced=True):
    entry = SimpleNamespace(
        journal_entry_id=41, entry_no="JE-2026-000041",
        entry_date=date(2026, 11, 8), status=status,
        source_settlement_id=None, posted_by=None, posted_at=None,
    )
    details = [
        SimpleNamespace(account_id=10, project_id=None,
                        debit_amount=Decimal("100"), credit_amount=Decimal("0")),
        SimpleNamespace(account_id=20, project_id=None,
                        debit_amount=Decimal("0"),
                        credit_amount=Decimal("100") if balanced else Decimal("90")),
    ]
    db = PostingDB(entry, details)
    user = SimpleNamespace(user_id=5)
    fy = SimpleNamespace(is_closed=False)
    monkeypatch.setattr(journal, "_get", lambda _db, _eid: entry)
    monkeypatch.setattr(journal, "_validate_settlement_link", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_fy_for", lambda *args: fy)
    monkeypatch.setattr(journal, "write_audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(journal, "_out", lambda _db, e: {
        "journal_entry_id": e.journal_entry_id, "status": e.status,
        "posted_by": e.posted_by, "posted_at": e.posted_at,
    })
    monkeypatch.setattr(journal, "utcnow", lambda: datetime(2026, 11, 8, 10, 0, 0))
    return db, entry, user, details


def test_posting_moves_balanced_draft_to_posted_and_records_actor(monkeypatch):
    db, entry, user, _details = _posting_fixture(monkeypatch)
    monkeypatch.setattr(journal, "_validate_lines", lambda _db, _lines: (
        Decimal("100"), Decimal("100"),
    ))

    result = journal.post_entry(41, user, db)

    assert result["status"] == "Posted"
    assert entry.posted_by == 5
    assert entry.posted_at == datetime(2026, 11, 8, 10, 0, 0)
    assert db.commits == 1


def test_posting_rejects_unbalanced_draft_without_committing(monkeypatch):
    db, entry, user, _details = _posting_fixture(monkeypatch)
    def reject_unbalanced(_db, _lines):
        raise HTTPException(422, "القيد غير متوازن")
    monkeypatch.setattr(journal, "_validate_lines", reject_unbalanced)

    with pytest.raises(HTTPException) as exc:
        journal.post_entry(41, user, db)

    assert exc.value.status_code == 422
    assert entry.status == "Draft"
    assert db.commits == 0


def test_posting_rejects_second_post_of_already_posted_entry(monkeypatch):
    db, entry, user, _details = _posting_fixture(monkeypatch, status="Posted")
    monkeypatch.setattr(journal, "_validate_lines", lambda *_args: pytest.fail(
        "posted entries must be rejected before line validation"
    ))

    with pytest.raises(HTTPException) as exc:
        journal.post_entry(41, user, db)

    assert exc.value.status_code == 409
    assert entry.status == "Posted"
    assert db.commits == 0
