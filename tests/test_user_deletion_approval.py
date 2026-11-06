from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.routers.admin import _active_admin_count, _is_admin


def _admin_db():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE "Users" ("UserId" INTEGER PRIMARY KEY, "IsActive" BOOLEAN, "IsDeleted" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "Roles" ("RoleId" INTEGER PRIMARY KEY, "RoleName" TEXT)'))
        conn.execute(text('CREATE TABLE "UserRoles" ("UserId" INTEGER, "RoleId" INTEGER)'))
        conn.execute(text('INSERT INTO "Roles" VALUES (1, \'Admin\'), (2, \'User\')'))
        conn.execute(text('INSERT INTO "Users" VALUES (1, 1, 0), (2, 1, 0), (3, 0, 0), (4, 1, 1)'))
        conn.execute(text('INSERT INTO "UserRoles" VALUES (1, 1), (2, 1), (3, 1), (4, 1)'))
    return engine


def test_active_admin_count_excludes_inactive_and_archived_accounts():
    engine = _admin_db()
    with Session(engine) as db:
        assert _active_admin_count(db) == 2
        assert _active_admin_count(db, excluding_user_id=1) == 1
        assert _active_admin_count(db, excluding_user_id=2) == 1
        assert _active_admin_count(db, excluding_user_id=3) == 2
        assert _is_admin(db, 1)
        assert not _is_admin(db, 99)
