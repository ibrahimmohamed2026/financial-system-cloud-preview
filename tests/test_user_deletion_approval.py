from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.routers.admin import _active_it_admin_count, _is_it_admin


def _admin_db():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE "Users" ("UserId" INTEGER PRIMARY KEY, "JobProfileId" INTEGER, "IsActive" BOOLEAN, "IsDeleted" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "JobProfiles" ("JobProfileId" INTEGER PRIMARY KEY, "NameAr" TEXT, "IsActive" BOOLEAN)'))
        conn.execute(text('INSERT INTO "JobProfiles" VALUES (10, \'مسؤول النظام IT\', 1), (11, \'مسؤول النظام IT\', 0), (12, \'محاسب\', 1)'))
        conn.execute(text('INSERT INTO "Users" VALUES (1, 10, 1, 0), (2, 10, 1, 0), (3, 11, 1, 0), (4, 10, 0, 0), (5, 10, 1, 1), (6, 12, 1, 0), (7, NULL, 1, 0)'))
    return engine


def test_active_it_admin_count_uses_job_profile_and_excludes_inactive_or_archived():
    engine = _admin_db()
    with Session(engine) as db:
        assert _active_it_admin_count(db) == 2
        assert _active_it_admin_count(db, excluding_user_id=1) == 1
        assert _active_it_admin_count(db, excluding_user_id=2) == 1
        assert _active_it_admin_count(db, excluding_user_id=3) == 2
        assert _is_it_admin(db, 1)
        assert not _is_it_admin(db, 3)
        assert not _is_it_admin(db, 4)
        assert not _is_it_admin(db, 5)
        assert not _is_it_admin(db, 6)
        assert not _is_it_admin(db, 7)
