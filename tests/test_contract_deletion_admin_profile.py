from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.contract_deletion import require_admin


def _db():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE "Users" ("UserId" INTEGER PRIMARY KEY, "JobProfileId" INTEGER, "IsActive" BOOLEAN, "IsDeleted" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "JobProfiles" ("JobProfileId" INTEGER PRIMARY KEY, "NameAr" TEXT, "IsActive" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "Roles" ("RoleId" INTEGER PRIMARY KEY, "RoleName" TEXT)'))
        conn.execute(text('CREATE TABLE "UserRoles" ("UserId" INTEGER, "RoleId" INTEGER)'))
        conn.execute(text('INSERT INTO "JobProfiles" VALUES (10, \'مسؤول النظام IT\', 1), (11, \'محاسب\', 1), (12, \'مسؤول النظام IT\', 0)'))
        conn.execute(text('INSERT INTO "Users" VALUES (1, 10, 1, 0), (2, 11, 1, 0), (3, 12, 1, 0), (4, 10, 0, 0), (5, 10, 1, 1), (6, NULL, 1, 0)'))
        conn.execute(text('INSERT INTO "Roles" VALUES (1, \'Admin\')'))
        conn.execute(text('INSERT INTO "UserRoles" VALUES (6, 1)'))
    return engine


def test_it_system_administrator_can_use_general_contract_deletion():
    engine = _db()
    with Session(engine) as db:
        assert require_admin(db, 1) is None


def test_regular_job_profile_cannot_use_general_contract_deletion():
    engine = _db()
    with Session(engine) as db:
        try:
            require_admin(db, 2)
        except HTTPException as exc:
            assert exc.status_code == 403
        else:
            raise AssertionError("regular user must not be allowed")


def test_inactive_or_deleted_system_administrator_cannot_use_general_deletion():
    engine = _db()
    with Session(engine) as db:
        for user_id in (3, 4, 5):
            try:
                require_admin(db, user_id)
            except HTTPException as exc:
                assert exc.status_code == 403
            else:
                raise AssertionError("inactive/deleted admin must not be allowed")


def test_legacy_admin_role_alone_does_not_grant_general_deletion():
    engine = _db()
    with Session(engine) as db:
        try:
            require_admin(db, 6)
        except HTTPException as exc:
            assert exc.status_code == 403
        else:
            raise AssertionError("legacy role must not grant system-wide deletion")
