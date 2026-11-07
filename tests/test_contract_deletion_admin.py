import pytest
from fastapi import HTTPException

from app.contract_deletion import require_admin


class _FakeDb:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = 0

    def scalar(self, statement):
        self.calls += 1
        return next(self.results)


def test_legacy_admin_role_keeps_global_delete_access():
    db = _FakeDb([1])
    require_admin(db, 10)
    assert db.calls == 1


def test_it_system_administrator_profile_can_use_global_delete():
    db = _FakeDb([None, 7])
    require_admin(db, 10)
    assert db.calls == 2


def test_named_system_administrator_profile_can_use_global_delete():
    db = _FakeDb([None, 8])
    require_admin(db, 10)
    assert db.calls == 2


def test_regular_user_cannot_use_global_delete():
    db = _FakeDb([None, None])
    with pytest.raises(HTTPException) as exc:
        require_admin(db, 10)
    assert exc.value.status_code == 403
    assert exc.value.detail == "الحذف العام متاح لمسؤول النظام فقط"
