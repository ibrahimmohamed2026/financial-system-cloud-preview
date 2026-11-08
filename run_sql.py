"""تهيئة قاعدة النظام حسب DATABASE_URL الفعلي (PostgreSQL أو SQLite).

الملفات sql/001..004 هي سكربتات T-SQL قديمة لـ SQL Server ولا تُنفّذ على
PostgreSQL/SQLite. يستخدم هذا المشغّل SQLAlchemy models لإنشاء الجداول، ثم
ينفّذ 005 على PostgreSQL، وبعدها يزامن الشاشات والصلاحيات بطريقة قابلة للتكرار.
"""
from __future__ import annotations

import sys
import re
from pathlib import Path

from sqlalchemy import text

from app.database import engine, SessionLocal
from app.db_setup import ensure_schema
from app.bootstrap import seed_screens, sync_permissions

BASE_DIR = Path(__file__).resolve().parent
MIGRATION_005 = BASE_DIR / "sql" / "005_audit_analytics.sql"
MIGRATION_006 = BASE_DIR / "sql" / "006_contracts.sql"
MIGRATION_007 = BASE_DIR / "sql" / "007_contract_technical_settlements.sql"
MIGRATION_008 = BASE_DIR / "sql" / "008_contract_settlement_item_details.sql"
MIGRATION_015 = BASE_DIR / "sql" / "015_checks_hardening_postgres.sql"


def run_postgres_migration_005() -> None:
    if engine.dialect.name != "postgresql":
        print(f"تخطّي {MIGRATION_005.name}: التهيئة المكافئة ستتم عبر SQLAlchemy على {engine.dialect.name}.")
        return
    if not MIGRATION_005.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {MIGRATION_005}")
    sql = MIGRATION_005.read_text(encoding="utf-8-sig")
    # الملف يحتوي أوامر DDL/DML بسيطة بلا دوال أو كتل نصية؛ نفّذ كل أمر منفردًا.
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    cleaned = [part.strip() for part in sql.split(";") if part.strip()]
    with engine.begin() as conn:
        for statement in cleaned:
            conn.execute(text(statement))
    print("تم تنفيذ sql/005_audit_analytics.sql على PostgreSQL.")


def run_postgres_migration_006() -> None:
    """تطبيق مخطط العقود على PostgreSQL بطريقة قابلة لإعادة التشغيل."""
    if engine.dialect.name != "postgresql":
        print(f"تخطّي {MIGRATION_006.name}: الشاشات والصلاحيات ستتم مزامنتها عبر bootstrap على {engine.dialect.name}.")
        return
    if not MIGRATION_006.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {MIGRATION_006}")
    sql = MIGRATION_006.read_text(encoding="utf-8-sig")
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    cleaned = [part.strip() for part in sql.split(";") if part.strip()]
    with engine.begin() as conn:
        for statement in cleaned:
            conn.execute(text(statement))
    print("تم تنفيذ sql/006_contracts.sql على PostgreSQL.")



def run_postgres_migration_007() -> None:
    """تطبيق جداول المكتب الفني والمستخلصات بشكل إضافي وآمن."""
    if engine.dialect.name != "postgresql":
        print(f"تخطّي {MIGRATION_007.name}: النماذج تنشئ الجداول على {engine.dialect.name}.")
        return
    if not MIGRATION_007.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {MIGRATION_007}")
    sql = MIGRATION_007.read_text(encoding="utf-8-sig")
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    cleaned = [part.strip() for part in sql.split(";") if part.strip()]
    with engine.begin() as conn:
        for statement in cleaned:
            conn.execute(text(statement))
    print("تم تنفيذ sql/007_contract_technical_settlements.sql على PostgreSQL.")



def run_postgres_migration_008() -> None:
    """Add line-level contract settlement quantities, safely and rerunnably."""
    if engine.dialect.name != "postgresql":
        print(f"تخطّي {MIGRATION_008.name}: SQLAlchemy ينشئ الجدول على {engine.dialect.name}.")
        return
    if not MIGRATION_008.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {MIGRATION_008}")
    sql = MIGRATION_008.read_text(encoding="utf-8-sig")
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    cleaned = [part.strip() for part in sql.split(";") if part.strip()]
    with engine.begin() as conn:
        for statement in cleaned:
            conn.execute(text(statement))
    print("تم تنفيذ sql/008_contract_settlement_item_details.sql على PostgreSQL.")


def run_postgres_migration_010() -> None:
    """Add cheque brand/project classification without touching existing cheque rows."""
    if engine.dialect.name == "sqlite":
        from sqlalchemy import inspect
        if inspect(engine).has_table("FinancialChecks"):
            columns = {col["name"] for col in inspect(engine).get_columns("FinancialChecks")}
            if "ProjectBrand" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("""ALTER TABLE "FinancialChecks" ADD COLUMN "ProjectBrand" VARCHAR(50) NOT NULL DEFAULT 'عام'"""))
        print("تمت مراجعة عمود ProjectBrand على SQLite.")
        return
    if engine.dialect.name != "postgresql":
        return
    migration = ROOT / "sql" / "010_cheques_project_brand.sql"
    if not migration.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {migration}")
    sql = migration.read_text(encoding="utf-8-sig")
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    cleaned = [part.strip() for part in sql.split(";") if part.strip()]
    with engine.begin() as conn:
        for statement in cleaned:
            conn.execute(text(statement))
    print("تم تنفيذ sql/010_cheques_project_brand.sql على PostgreSQL.")



def run_postgres_migration_015() -> None:
    """Normalize legacy cheque states and replace global cheque-number uniqueness."""
    if engine.dialect.name != "postgresql":
        print(f"تخطّي {MIGRATION_015.name}: ترحيل PostgreSQL فقط.")
        return
    if not MIGRATION_015.is_file():
        raise FileNotFoundError(f"ملف التهيئة غير موجود: {MIGRATION_015}")
    # This migration contains a PostgreSQL DO block; execute it as one statement.
    sql = MIGRATION_015.read_text(encoding="utf-8-sig")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("تم تنفيذ sql/015_checks_hardening_postgres.sql على PostgreSQL.")


def main() -> int:
    try:
        print(f"قاعدة البيانات النشطة: {engine.dialect.name}")
        print("إنشاء الجداول الناقصة ومراجعة الـ view والفهارس...")
        ensure_schema(engine)
        run_postgres_migration_005()
        # إنشاء الأقسام والشاشات الأساسية أولًا حتى تكون مراجع SQL الخاصة بالعقود موجودة.
        with SessionLocal() as db:
            seed_screens(db)
        run_postgres_migration_006()
        run_postgres_migration_007()
        run_postgres_migration_008()
        run_postgres_migration_010()
        run_postgres_migration_015()
        print("مزامنة الشاشات والصلاحيات...")
        with SessionLocal() as db:
            seed_screens(db)
            sync_permissions(db)
        print("اكتملت التهيئة. AuditLogs وAnalyticsReports وContracts وContractSettlements وتفاصيل كميات المستخلصات وInventoryManagement وPurchaseCycle وFinancialChecks مع تصنيف Lux/Dumas مسجلة.")
        print("ملاحظة: صلاحيات العرض تُمنح تلقائيًا لدور Admin؛ امنح الأدوار الأخرى View من شاشة الصلاحيات.")
        return 0
    except Exception as exc:
        print(f"فشلت التهيئة: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
