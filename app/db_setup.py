"""تجهيز المخطط + نسخ البيانات بين قواعد البيانات (SQLite <-> PostgreSQL).

بتستخدمها: init_sqlite_db.py (تجهيز قاعدة جديدة)، scripts/migrate_sqlite_to_postgres.py (الهجرة)،
وapp/backup_service.py (استعادة النسخ الاحتياطية).

الوحدة دي مقصودة ما تستوردش app.config / app.database، عشان تشتغل مع أي Engine يتم تمريره.
"""
from __future__ import annotations

import base64
import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Iterator

from sqlalchemy import (Boolean, Date, DateTime, Integer, LargeBinary, Numeric, Table, delete, inspect, select, text)
from sqlalchemy.engine import Connection, Engine

from .models import Base

VIEW_NAME = "vw_EffectivePermissions"
# SQL واحد شغال على SQLite وPostgreSQL: الأسماء بين "" (PostgreSQL بيحوّل غير المقتبس لحروف صغيرة)،
# وIsAllowed بيتحوّل صراحةً لـ 1/0 لأن PostgreSQL مابيخلطش boolean مع integer جوه CASE.
VIEW_SQL = f'''CREATE VIEW "{VIEW_NAME}" AS
SELECT u."UserId" AS "UserId", p."PermissionId" AS "PermissionId",
       p."ScreenCode" AS "ScreenCode", p."ActionCode" AS "ActionCode",
       CASE
         -- An assigned job profile is the complete permission source for that user.
         -- The legacy Admin role no longer bypasses the approved job-profile model.
         -- Per-user grants/denials and ordinary roles cannot expand or override it.
         WHEN u."JobProfileId" IS NOT NULL THEN
              CASE WHEN EXISTS (
                    SELECT 1 FROM "JobProfilePermissions" jpp
                    JOIN "JobProfiles" jp ON jp."JobProfileId"=jpp."JobProfileId"
                    WHERE jpp."JobProfileId"=u."JobProfileId"
                      AND jp."IsActive" IS TRUE
                      AND jpp."PermissionId"=p."PermissionId"
              ) THEN 1 ELSE 0 END
         -- Backward compatibility for users who have not yet been assigned a job profile.
         WHEN up."IsAllowed" IS NOT NULL THEN CASE WHEN up."IsAllowed" THEN 1 ELSE 0 END
         WHEN EXISTS (SELECT 1 FROM "UserRoles" ur JOIN "RolePermissions" rp ON rp."RoleId"=ur."RoleId"
                      WHERE ur."UserId"=u."UserId" AND rp."PermissionId"=p."PermissionId") THEN 1
         ELSE 0 END AS "IsAllowed"
FROM "Users" u CROSS JOIN "Permissions" p
LEFT JOIN "UserPermissions" up ON up."UserId"=u."UserId" AND up."PermissionId"=p."PermissionId"'''
CHECK_VOUCHER_INDEX_SQL = ('CREATE UNIQUE INDEX IF NOT EXISTS "UX_TreasuryTransactions_CheckVoucher" '
                           'ON "TreasuryTransactions" ("VoucherNo") WHERE "VoucherNo" LIKE \'CHK-%\'')


def _fix_contract_item_catalog_fk(engine: Engine) -> None:
    """Point contract item catalog links at the current central catalog table.

    Older databases may still have the FK pointing at the retired ``CatalogItems``
    table. PostgreSQL can update that constraint in place without changing rows.
    """
    if engine.dialect.name != "postgresql":
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if not {"ContractItems", "ItemCatalog"}.issubset(tables):
        return
    stale = [fk for fk in inspector.get_foreign_keys("ContractItems")
             if fk.get("constrained_columns") == ["CatalogItemId"]
             and fk.get("referred_table") != "ItemCatalog"]
    if not stale:
        return
    with engine.begin() as conn:
        orphan_count = conn.execute(text('''
            SELECT COUNT(*) FROM "ContractItems" ci
            LEFT JOIN "ItemCatalog" ic ON ic."CatalogItemId" = ci."CatalogItemId"
            WHERE ci."CatalogItemId" IS NOT NULL AND ic."CatalogItemId" IS NULL
        ''')).scalar_one()
        if orphan_count:
            logging.getLogger(__name__).warning(
                "Keeping the legacy ContractItems catalog FK: %s existing catalog links do not have matching ItemCatalog rows",
                orphan_count)
            return
        quote = conn.dialect.identifier_preparer.quote
        for fk in stale:
            name = fk.get("name")
            if name:
                conn.execute(text(f'ALTER TABLE "ContractItems" DROP CONSTRAINT {quote(name)}'))
        conn.execute(text('''
            ALTER TABLE "ContractItems"
            ADD CONSTRAINT "FK_ContractItems_ItemCatalog_CatalogItemId"
            FOREIGN KEY ("CatalogItemId") REFERENCES "ItemCatalog" ("CatalogItemId")
        '''))


def _add_model_columns(engine: Engine, table_name: str) -> None:
    """Add newly mapped nullable columns before create_all tries their indexes."""
    if table_name not in inspect(engine).get_table_names():
        return
    model_table = Base.metadata.tables[table_name]
    existing = {c["name"] for c in inspect(engine).get_columns(table_name)}
    for col in model_table.columns:
        if col.name in existing or col.primary_key:
            continue
        sql_type = col.type.compile(dialect=engine.dialect)
        with engine.begin() as conn:
            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {sql_type} NULL'))


def _backfill_counterparty_links(engine: Engine) -> None:
    """Create missing party masters from historical names and link rows additively."""
    from sqlalchemy import insert, update
    from .models import CounterpartyAlias
    from .counterparties import normalize_name

    links = (
        ("ContractRequests", "RequestId", "CounterpartyName", "RequestType"),
        ("Contracts", "ContractId", "ClientName", None),
        ("ContractSettlements", "SettlementId", "CounterpartyName", "SettlementSide"),
        ("TechnicalSettlementEstimates", "EstimateId", "CounterpartyName", "SettlementSide"),
        ("TreasuryTransactions", "TransactionId", "RecipientName", None),
        ("PurchaseOrders", "PurchaseOrderId", "SupplierName", None),
    )
    tables = set(inspect(engine).get_table_names())
    party = Base.metadata.tables["Counterparties"]
    alias = Base.metadata.tables[CounterpartyAlias.__tablename__]
    with engine.begin() as conn:
        # Keep both historical/current party name columns populated when upgrading
        # a database created by either schema variant.
        party_cols = {c["name"] for c in inspect(conn).get_columns("Counterparties")}
        if "Name" in party_cols and "LegalName" in party_cols:
            conn.execute(text('UPDATE "Counterparties" SET "Name"=COALESCE(NULLIF("Name", \'\'), "LegalName"), "LegalName"=COALESCE(NULLIF("LegalName", \'\'), "Name")'))
        if "PartyType" in party_cols:
            conn.execute(text('UPDATE "Counterparties" SET "PartyType"=COALESCE(NULLIF("PartyType", \'\'), \'Other\')'))
        if "Roles" in party_cols:
            conn.execute(text('UPDATE "Counterparties" SET "Roles"=\'[]\' WHERE "Roles" IS NULL'))

        party_rows = conn.execute(select(party.c.CounterpartyId, party.c.Name, party.c.LegalName,
                                         party.c.PartyType)).all()
        by_name: dict[str, int] = {}
        types: dict[int, str] = {}
        for pid, name, legal_name, typ in party_rows:
            for value in (name, legal_name):
                if value and normalize_name(value):
                    by_name[normalize_name(value)] = pid
            types[pid] = typ or "Other"
        alias_names = {}
        if CounterpartyAlias.__tablename__ in tables:
            for alias_name, canonical_name, pid in conn.execute(select(alias.c.AliasName, alias.c.CanonicalName, alias.c.CounterpartyId)).all():
                if pid:
                    alias_names[normalize_name(alias_name)] = pid
                elif normalize_name(canonical_name) in by_name:
                    alias_names[normalize_name(alias_name)] = by_name[normalize_name(canonical_name)]

        for table_name, pk_name, name_name, type_name in links:
            if table_name not in tables:
                continue
            model_table = Base.metadata.tables[table_name]
            cols = set(model_table.c.keys())
            if "CounterpartyId" not in cols or name_name not in cols or pk_name not in cols:
                continue
            fields = [model_table.c[pk_name], model_table.c[name_name], model_table.c.CounterpartyId]
            if type_name and type_name in cols:
                fields.append(model_table.c[type_name])
            for row in conn.execute(select(*fields)).all():
                record_id, raw_name, linked_id = row[:3]
                name = " ".join((raw_name or "").split())
                key = normalize_name(name)
                if not key or linked_id is not None:
                    continue
                desired = "Supplier" if table_name == "PurchaseOrders" else (
                    "Customer" if table_name == "Contracts" else
                    ("Contractor" if len(row) > 3 and row[3] == "Subcontractor" else
                     "Customer" if len(row) > 3 and row[3] == "Customer" else "Other"))
                pid = by_name.get(key) or alias_names.get(key)
                if pid is None:
                    values = {"Code": "PENDING", "Name": name, "LegalName": name,
                              "Roles": [desired] if desired != "Other" else [], "PartyType": desired,
                              "IsActive": True, "CreatedAt": datetime.utcnow()}
                    result = conn.execute(insert(party).values(**values).returning(party.c.CounterpartyId))
                    pid = result.scalar_one()
                    conn.execute(update(party).where(party.c.CounterpartyId == pid).values(Code=f"CP-{pid:06d}"))
                    by_name[key] = pid; types[pid] = desired
                else:
                    old_type = types.get(pid, "Other")
                    if desired != "Other" and old_type not in ("Other", desired, "Mixed"):
                        conn.execute(update(party).where(party.c.CounterpartyId == pid).values(PartyType="Mixed"))
                        types[pid] = "Mixed"
                conn.execute(update(model_table).where(model_table.c[pk_name] == record_id).values(CounterpartyId=pid))


def ensure_schema(engine: Engine) -> None:
    """ينشئ الجداول الناقصة ويضيف ترحيلات متوافقة مع SQLite/PostgreSQL بأمان."""
    # Add new indexed columns to pre-existing tables before create_all attempts
    # to create their indexes. This is additive and leaves every existing row intact.
    existing_tables = set(inspect(engine).get_table_names())
    for table_name in ("Users", "Companies", "Counterparties", "ChartOfAccounts", "AccountClassifications", "ContractRequests", "Contracts", "ContractSettlements", "JournalEntries",
                       "ContractItems", "ContractAddendums", "TechnicalSettlementEstimates", "TechnicalSettlementEstimateItems", "TreasuryTransactions", "PurchaseOrders", "SupplierInvoices", "Checks",
                       "CheckPrintTemplates", "FinancialChecks"):
        if table_name in existing_tables:
            _add_model_columns(engine, table_name)
    if "Users" in existing_tables:
        with engine.begin() as conn:
            conn.execute(text('UPDATE "Users" SET "TokenVersion"=0 WHERE "TokenVersion" IS NULL'))
            conn.execute(text("UPDATE \"Users\" SET \"PreferredLanguage\"='ar' WHERE \"PreferredLanguage\" IS NULL OR \"PreferredLanguage\" NOT IN ('ar', 'en')"))
            conn.execute(text('UPDATE "Users" SET "IsDeleted"=FALSE WHERE "IsDeleted" IS NULL'))
    for table_name, column_name, sql_type in (
        ("Contracts", "RequestId", "INTEGER NULL"),
        ("ContractItems", "CatalogItemId", "INTEGER NULL"),
        ("ContractItems", "AccountId", "INTEGER NULL"),
        ("ContractItems", "ProjectId", "INTEGER NULL"),
        ("ContractSettlementItems", "AccountId", "INTEGER NULL"),
        ("JournalEntries", "SourceSettlementId", "INTEGER NULL"),
    ):
        if table_name in existing_tables:
            columns = {col["name"] for col in inspect(engine).get_columns(table_name)}
            if column_name not in columns:
                with engine.begin() as conn:
                    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {sql_type}'))
    Base.metadata.create_all(engine)
    # Capture the pre-addendum BOQ baseline exactly once; never overwrite it on later revisions.
    if "ContractItems" in inspect(engine).get_table_names():
        with engine.begin() as conn:
            item_columns = {col["name"] for col in inspect(conn).get_columns("ContractItems")}
            if {"OriginalQuantity", "OriginalUnitPrice", "Quantity", "UnitPrice"}.issubset(item_columns):
                conn.execute(text('UPDATE "ContractItems" SET "OriginalQuantity"="Quantity" WHERE "OriginalQuantity" IS NULL'))
                conn.execute(text('UPDATE "ContractItems" SET "OriginalUnitPrice"="UnitPrice" WHERE "OriginalUnitPrice" IS NULL'))
    # Safely migrate the old Lux/Dumas tags only when one project has that exact
    # Arabic or English name. Ambiguous or unmatched records remain unassigned.
    table_names = set(inspect(engine).get_table_names())
    if {"FinancialChecks", "Projects"}.issubset(table_names):
        with engine.begin() as conn:
            projects = conn.execute(text('SELECT "ProjectId", "NameAr", "NameEn" FROM "Projects"')).all()
            by_name: dict[str, list[int]] = defaultdict(list)
            for project_id, name_ar, name_en in projects:
                seen_names: set[str] = set()
                for name in (name_ar, name_en):
                    normalized = name.strip().casefold() if name else ""
                    if normalized and normalized not in seen_names:
                        by_name[normalized].append(project_id)
                        seen_names.add(normalized)
            legacy = conn.execute(text('SELECT "CheckId", "ProjectBrand" FROM "FinancialChecks" WHERE "ProjectId" IS NULL AND lower("ProjectBrand") IN (\'lux\', \'dumas\')')).all()
            for check_id, brand in legacy:
                matches = by_name.get((brand or "").strip().casefold(), [])
                if len(matches) == 1:
                    conn.execute(text('UPDATE "FinancialChecks" SET "ProjectId"=:project_id WHERE "CheckId"=:check_id AND "ProjectId" IS NULL'),
                                 {"project_id": matches[0], "check_id": check_id})
    # Journal line descriptions use a text column so long multi-line statements
    # are preserved when upgrading an existing database as well as on new installs.
    table_names = set(inspect(engine).get_table_names())
    if "JournalEntryDetails" in table_names:
        line_columns = {col["name"]: col for col in inspect(engine).get_columns("JournalEntryDetails")}
        description_type = line_columns.get("Description", {}).get("type")
        if getattr(description_type, "length", None) is not None:
            if engine.dialect.name == "postgresql":
                with engine.begin() as conn:
                    conn.execute(text('ALTER TABLE "JournalEntryDetails" ALTER COLUMN "Description" TYPE TEXT'))
            elif engine.dialect.name == "mssql":
                with engine.begin() as conn:
                    conn.execute(text('ALTER TABLE [JournalEntryDetails] ALTER COLUMN [Description] NVARCHAR(MAX) NULL'))
    if "Checks" in inspect(engine).get_table_names():
        # create_all skips indexes on existing tables; this association is indexed on upgrades too.
        indexed = any(i.get("column_names") == ["SettlementId"] for i in inspect(engine).get_indexes("Checks"))
        if not indexed:
            with engine.begin() as conn:
                conn.execute(text('CREATE INDEX IF NOT EXISTS "IX_Checks_SettlementId" ON "Checks" ("SettlementId")'))
    if "JournalEntries" in inspect(engine).get_table_names():
        indexed = any(i.get("column_names") == ["SourceSettlementId"] for i in inspect(engine).get_indexes("JournalEntries"))
        if not indexed and engine.dialect.name in ("sqlite", "postgresql"):
            with engine.begin() as conn:
                conn.execute(text('CREATE INDEX IF NOT EXISTS "IX_JournalEntries_SourceSettlementId" ON "JournalEntries" ("SourceSettlementId")'))
        elif not indexed and engine.dialect.name == "mssql":
            with engine.begin() as conn:
                conn.execute(text('CREATE INDEX IX_JournalEntries_SourceSettlementId ON JournalEntries(SourceSettlementId)'))
    _fix_contract_item_catalog_fk(engine)
    _backfill_counterparty_links(engine)
    # create_all لا يضيف أعمدة لجدول موجود بالفعل؛ عالج عمود التدقيق الجديد صراحةً.
    table_names = set(inspect(engine).get_table_names())
    if "AuditLog" in table_names:
        audit_columns = {col["name"] for col in inspect(engine).get_columns("AuditLog")}
        if "IpAddress" not in audit_columns:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE "AuditLog" ADD COLUMN "IpAddress" VARCHAR(45)'))
    # Safe additive compatibility for older databases where Contracts already existed.
    contract_columns = {col["name"] for col in inspect(engine).get_columns("Contracts")} if "Contracts" in table_names else set()
    if "Contracts" in table_names and "RequestId" not in contract_columns:
        with engine.begin() as conn:
            conn.execute(text('ALTER TABLE "Contracts" ADD COLUMN "RequestId" INTEGER NULL'))
    # Additive columns required by the complete addendum workflow. create_all() does not
    # alter existing tables, so upgrade each legacy table explicitly and idempotently.
    schema_additions = {
        "Contracts": {
            "AgreedStatementCount": "INTEGER NULL",
            "StatementDistributionMethod": "VARCHAR(20) NOT NULL DEFAULT 'Manual'",
        },
        "ContractItems": {
            "OriginalQuantity": "NUMERIC(18,4) NULL",
            "OriginalUnitPrice": "NUMERIC(18,4) NULL",
        },
        "ContractAddendums": {
            "TechnicalReviewedBy": "INTEGER NULL",
            "TechnicalReviewedAt": "TIMESTAMP NULL",
            "TechnicalReviewNotes": "TEXT NULL",
        },
        "ContractAddendumLines": {
            "BaselineQuantity": "NUMERIC(18,4) NULL",
            "BaselineUnitPrice": "NUMERIC(18,4) NULL",
        },
    }
    current_tables = set(inspect(engine).get_table_names())
    for table_name, additions in schema_additions.items():
        if table_name not in current_tables:
            continue
        current_columns = {col["name"] for col in inspect(engine).get_columns(table_name)}
        missing = [(column_name, sql_type) for column_name, sql_type in additions.items()
                   if column_name not in current_columns]
        if missing:
            with engine.begin() as conn:
                for column_name, sql_type in missing:
                    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {sql_type}'))
    # Backfill signed BOQ baselines only after missing columns have been added.
    if "ContractItems" in current_tables:
        with engine.begin() as conn:
            conn.execute(text('UPDATE "ContractItems" SET "OriginalQuantity"="Quantity" WHERE "OriginalQuantity" IS NULL'))
            conn.execute(text('UPDATE "ContractItems" SET "OriginalUnitPrice"="UnitPrice" WHERE "OriginalUnitPrice" IS NULL'))
    # Preserve legacy addenda as approved; the current workflow creates new addenda as Draft.
    if "ContractAddendums" in table_names:
        addendum_columns = {col["name"] for col in inspect(engine).get_columns("ContractAddendums")}
        with engine.begin() as conn:
            if "Status" not in addendum_columns:
                conn.execute(text("ALTER TABLE \"ContractAddendums\" ADD COLUMN \"Status\" VARCHAR(20) NOT NULL DEFAULT 'Approved'"))
            if "ApprovedBy" not in addendum_columns:
                conn.execute(text('ALTER TABLE "ContractAddendums" ADD COLUMN "ApprovedBy" INTEGER NULL'))
            if "ApprovedAt" not in addendum_columns:
                conn.execute(text('ALTER TABLE "ContractAddendums" ADD COLUMN "ApprovedAt" TIMESTAMP NULL'))
    with engine.begin() as conn:
        conn.execute(text(f'DROP VIEW IF EXISTS "{VIEW_NAME}"'))
        conn.execute(text(VIEW_SQL))
        conn.execute(text(CHECK_VOUCHER_INDEX_SQL))
        if engine.dialect.name in ("sqlite", "postgresql"):
            conn.execute(text('CREATE INDEX IF NOT EXISTS "IX_AuditLog_Timestamp_UserId" ON "AuditLog" ("Timestamp", "UserId")'))


# ----------------------------- تحويل القيم (للنسخ الاحتياطي JSON) -----------------------------
def _computed_cols(table: Table) -> set[str]:
    return {c.name for c in table.columns if c.computed is not None}


def data_columns(table: Table):
    """أعمدة قابلة للكتابة (من غير الأعمدة المحسوبة زي Difference)."""
    return [c for c in table.columns if c.computed is None]


def to_json_value(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return {"__b64__": base64.b64encode(bytes(v)).decode("ascii")}
    return str(v)


def from_json_value(col, v):
    if v is None:
        return None
    t = col.type
    if isinstance(v, dict) and "__b64__" in v:
        return base64.b64decode(v["__b64__"])
    if isinstance(t, DateTime):
        return datetime.fromisoformat(v)
    if isinstance(t, Date):
        return date.fromisoformat(v)
    if isinstance(t, Numeric):
        return Decimal(str(v))
    if isinstance(t, Boolean):
        return bool(v)
    return v


# ----------------------------- ترتيب الإدخال -----------------------------
def order_self_referencing(table: Table, rows: list[dict]) -> list[dict]:
    """الجداول اللي ليها FK على نفسها (شجرة الحسابات): الأب لازم يتدخل قبل الابن.
    الصفوف (rows) مفاتيحها = Column.key (اسم الخاصية في الـModel)."""
    self_fks = [(fk.parent.key, fk.column.key) for fk in table.foreign_keys if fk.column.table is table]
    if not self_fks or not rows:
        return rows
    child_col, parent_col = self_fks[0]
    pending, done, out = list(rows), set(), []
    while pending:
        progressed, nxt = False, []
        for r in pending:
            parent = r.get(child_col)
            if parent is None or parent in done or parent == r.get(parent_col):
                out.append(r)
                done.add(r.get(parent_col))
                progressed = True
            else:
                nxt.append(r)
        if not progressed:      # أب مش موجود في الداتا — نضيفهم زي ما هم ونسيب القاعدة تقرر
            out.extend(nxt)
            break
        pending = nxt
    return out


def count_rows(conn: Connection, table: Table) -> int:
    return conn.execute(text(f'SELECT COUNT(*) FROM "{table.name}"')).scalar_one()


def clear_all_tables(conn: Connection) -> None:
    """بيمسح كل بيانات الجداول (الأبناء الأول). لازم يتنفّذ جوه Transaction."""
    for table in reversed(Base.metadata.sorted_tables):
        conn.execute(delete(table))


def insert_rows(conn: Connection, table: Table, rows: list[dict], chunk: int = 1000) -> None:
    rows = order_self_referencing(table, rows)
    for i in range(0, len(rows), chunk):
        conn.execute(table.insert(), rows[i:i + chunk])


def reset_sequences(conn: Connection) -> None:
    """PostgreSQL: بعد إدخال IDs يدويًا لازم نظبط العدّاد عشان الإدخال الجديد ما يتعارضش."""
    if conn.dialect.name != "postgresql":
        return
    for table in Base.metadata.sorted_tables:
        pk = list(table.primary_key.columns)
        if len(pk) != 1 or not isinstance(pk[0].type, Integer) or pk[0].autoincrement not in (True, "auto"):
            continue
        col = pk[0].name
        conn.execute(text(
            f'SELECT setval(pg_get_serial_sequence(:t, :c), '
            f'COALESCE((SELECT MAX("{col}") FROM "{table.name}"), 0) + 1, false)'),
            {"t": f'"{table.name}"', "c": col})


def copy_tables(src: Engine, dst: Engine, *, progress=print) -> dict[str, int]:
    """نسخ كل الجداول من قاعدة لقاعدة (بنفس مخطط الـModels) في Transaction واحدة على الهدف.

    الهدف لازم يكون فاضي. لو أي خطأ حصل بيتعمل Rollback كامل ومفيش حاجة بتتكتب.
    بترجّع {اسم الجدول: عدد الصفوف المنسوخة}.
    """
    src_tables = set(inspect(src).get_table_names())
    copied: dict[str, int] = {}
    with src.connect() as sc, dst.begin() as dc:
        for table in Base.metadata.sorted_tables:
            if count_rows(dc, table):
                raise RuntimeError(f'الجدول "{table.name}" في قاعدة الهدف فيه بيانات بالفعل — الهجرة محتاجة قاعدة فاضية')
        for table in Base.metadata.sorted_tables:
            if table.name not in src_tables:
                progress(f"  - {table.name}: مش موجود في المصدر (تخطّي)")
                copied[table.name] = 0
                continue
            src_cols = {c["name"] for c in inspect(src).get_columns(table.name)}
            cols = [c for c in data_columns(table) if c.name in src_cols]
            keys = [c.key for c in cols]
            rows = [dict(zip(keys, r)) for r in sc.execute(select(*cols))]
            if rows:
                try:
                    insert_rows(dc, table, rows)
                except Exception as e:
                    raise RuntimeError(f'فشل نقل الجدول "{table.name}": {e}') from e
            copied[table.name] = len(rows)
            progress(f"  - {table.name}: {len(rows)} صف")
        reset_sequences(dc)
    return copied


def verify_counts(src: Engine, dst: Engine) -> list[str]:
    """بيقارن عدد الصفوف في كل جدول؛ بيرجّع قايمة الفروقات (فاضية = تمام)."""
    problems = []
    src_tables = set(inspect(src).get_table_names())
    with src.connect() as sc, dst.connect() as dc:
        for table in Base.metadata.sorted_tables:
            a = count_rows(sc, table) if table.name in src_tables else 0
            b = count_rows(dc, table)
            if a != b:
                problems.append(f'{table.name}: المصدر {a} ≠ الهدف {b}')
    return problems
