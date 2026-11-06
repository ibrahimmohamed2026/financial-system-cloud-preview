from sqlalchemy import create_engine, text

from app.db_setup import VIEW_SQL


def _permission_db():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE "Users" ("UserId" INTEGER PRIMARY KEY, "JobProfileId" INTEGER NULL)'))
        conn.execute(text('CREATE TABLE "Permissions" ("PermissionId" INTEGER PRIMARY KEY, "ScreenCode" TEXT, "ActionCode" TEXT)'))
        conn.execute(text('CREATE TABLE "UserPermissions" ("UserId" INTEGER, "PermissionId" INTEGER, "IsAllowed" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "Roles" ("RoleId" INTEGER PRIMARY KEY, "RoleName" TEXT)'))
        conn.execute(text('CREATE TABLE "UserRoles" ("UserId" INTEGER, "RoleId" INTEGER)'))
        conn.execute(text('CREATE TABLE "RolePermissions" ("RoleId" INTEGER, "PermissionId" INTEGER)'))
        conn.execute(text('CREATE TABLE "JobProfiles" ("JobProfileId" INTEGER PRIMARY KEY, "IsActive" BOOLEAN)'))
        conn.execute(text('CREATE TABLE "JobProfilePermissions" ("JobProfileId" INTEGER, "PermissionId" INTEGER)'))
        conn.execute(text('INSERT INTO "Permissions" VALUES (1, \'Contracts\', \'View\'), (2, \'Contracts\', \'Delete\')'))
        conn.execute(text('INSERT INTO "Roles" VALUES (1, \'Admin\'), (2, \'LegacyRole\')'))
        conn.execute(text('INSERT INTO "JobProfiles" VALUES (10, 1), (11, 0)'))
        conn.execute(text('INSERT INTO "Users" VALUES (1, 10), (2, 10), (3, 10), (4, 11), (5, NULL), (6, NULL)'))
        conn.execute(text('INSERT INTO "JobProfilePermissions" VALUES (10, 1)'))
        conn.execute(text('INSERT INTO "UserPermissions" VALUES (1, 2, 1), (2, 1, 0), (5, 1, 1), (5, 2, 0), (6, 1, 0)'))
        conn.execute(text('INSERT INTO "UserRoles" VALUES (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (3, 1)'))
        conn.execute(text('INSERT INTO "RolePermissions" VALUES (2, 2)'))
        conn.execute(text(VIEW_SQL))
    return engine


def _allowed(conn, user_id, permission_id):
    return conn.execute(
        text('SELECT "IsAllowed" FROM "vw_EffectivePermissions" WHERE "UserId"=:u AND "PermissionId"=:p'),
        {"u": user_id, "p": permission_id},
    ).scalar_one()


def test_job_profile_is_the_only_permission_source_for_assigned_users():
    engine = _permission_db()
    with engine.connect() as conn:
        # User-level grant and ordinary role grant cannot add Delete.
        assert _allowed(conn, 1, 2) == 0
        # User-level denial and ordinary role cannot remove/add outside profile.
        assert _allowed(conn, 2, 1) == 1
        assert _allowed(conn, 2, 2) == 0
        # The profile's assigned View permission is granted.
        assert _allowed(conn, 3, 1) == 1


def test_legacy_admin_role_does_not_bypass_job_profile_permissions():
    engine = _permission_db()
    with engine.connect() as conn:
        # User 3 still has the legacy Admin role, but its assigned job profile
        # remains the sole permission source.
        assert _allowed(conn, 3, 1) == 1
        assert _allowed(conn, 3, 2) == 0


def test_profile_permission_changes_apply_immediately_without_user_permission_copy():
    engine = _permission_db()
    with engine.begin() as conn:
        assert _allowed(conn, 1, 2) == 0
        conn.execute(text('INSERT INTO "JobProfilePermissions" VALUES (10, 2)'))
        assert _allowed(conn, 1, 2) == 1
        conn.execute(text('DELETE FROM "JobProfilePermissions" WHERE "JobProfileId"=10 AND "PermissionId"=2'))
        assert _allowed(conn, 1, 2) == 0


def test_inactive_job_profile_grants_no_permissions():
    engine = _permission_db()
    with engine.connect() as conn:
        assert _allowed(conn, 4, 1) == 0
        assert _allowed(conn, 4, 2) == 0


def test_legacy_admin_role_without_permissions_does_not_grant_global_access():
    engine = _permission_db()
    with engine.begin() as conn:
        conn.execute(text('INSERT INTO "Users" VALUES (7, NULL)'))
        conn.execute(text('INSERT INTO "UserRoles" VALUES (7, 1)'))
        assert _allowed(conn, 7, 1) == 0
        assert _allowed(conn, 7, 2) == 0


def test_legacy_users_keep_user_override_then_role_fallback():
    engine = _permission_db()
    with engine.connect() as conn:
        assert _allowed(conn, 5, 1) == 1  # explicit grant
        assert _allowed(conn, 5, 2) == 0  # explicit denial overrides role
        assert _allowed(conn, 6, 1) == 0  # no override and no role grant
        assert _allowed(conn, 6, 2) == 1  # role fallback
