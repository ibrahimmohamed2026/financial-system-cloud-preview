"""Safe, explicit migration from SQL Server to PostgreSQL for this ERP.

Requires: pyodbc + Microsoft ODBC Driver 18, psycopg[binary].
Run first with --dry-run. Destination should be a dedicated, empty PostgreSQL DB.
This script never deletes or modifies the SQL Server source.
"""
from __future__ import annotations
import argparse
import os
import sys
from collections import defaultdict
from urllib.parse import quote_plus

from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
sys.path.insert(0, ROOT)
from app.models import Base  # noqa: E402

BATCH_SIZE = 500


def sqlserver_url_from_env() -> str | None:
    direct = os.getenv("SQLSERVER_URL") or os.getenv("MSSQL_URL")
    if direct:
        return direct
    server = os.getenv("SQLSERVER_HOST")
    database = os.getenv("SQLSERVER_DB")
    username = os.getenv("SQLSERVER_USER")
    password = os.getenv("SQLSERVER_PASSWORD")
    driver = os.getenv("SQLSERVER_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    if not (server and database and username):
        return None
    query = quote_plus(f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password or ''};TrustServerCertificate=yes")
    return f"mssql+pyodbc:///?odbc_connect={query}"


def pg_url_from_env() -> str | None:
    direct = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
    if direct and make_url(direct).get_backend_name() == "postgresql":
        if direct.startswith(("postgresql://", "postgres://")):
            return "postgresql+psycopg://" + direct.split("://", 1)[1]
        return direct
    user, db = os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_DB")
    if not (user and db):
        return None
    from sqlalchemy.engine import URL
    return URL.create("postgresql+psycopg", username=user, password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST", "localhost"), port=int(os.getenv("POSTGRES_PORT", "5432")), database=db).render_as_string(hide_password=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate matching ERP tables from SQL Server to PostgreSQL")
    ap.add_argument("--source", default=None, help="SQLAlchemy SQL Server URL (or set SQLSERVER_URL in .env)")
    ap.add_argument("--target", default=None, help="PostgreSQL URL (or set POSTGRES_* in .env)")
    ap.add_argument("--source-schema", default="dbo", help="SQL Server source schema; default dbo")
    ap.add_argument("--dry-run", action="store_true", help="Report table/column mapping without writing data")
    ap.add_argument("--create-schema", action="store_true", help="Create missing target tables from app.models before copying")
    ap.add_argument("--allow-nonempty-target", action="store_true", help="Allow inserts into a target that already has rows; duplicates may fail")
    args = ap.parse_args()
    src_url, dst_url = args.source or sqlserver_url_from_env(), args.target or pg_url_from_env()
    if not src_url:
        ap.error("Missing source. Set SQLSERVER_URL or SQLSERVER_HOST/DB/USER/PASSWORD, or pass --source")
    if not dst_url or make_url(dst_url).get_backend_name() != "postgresql":
        ap.error("Missing PostgreSQL target. Set POSTGRES_* / DATABASE_URL, or pass --target PostgreSQL URL")

    src = create_engine(src_url, pool_pre_ping=True)
    dst = create_engine(dst_url, pool_pre_ping=True)
    try:
        src_inspector = inspect(src)
        source_names = src_inspector.get_table_names(schema=args.source_schema)
        source_by_lower = defaultdict(list)
        for name in source_names:
            source_by_lower[name.lower()].append(name)

        metadata = MetaData()
        metadata.reflect(bind=dst)
        target_tables = {t.name: t for t in Base.metadata.sorted_tables}
        dest_existing = set(inspect(dst).get_table_names())
        if args.create_schema:
            Base.metadata.create_all(dst)
            dest_existing = set(inspect(dst).get_table_names())
        missing_dest = sorted(set(target_tables) - dest_existing)
        if missing_dest:
            print("ERROR: target is missing ERP tables. Create the schema first using app/init script or --create-schema.")
            print("Missing target tables: " + ", ".join(missing_dest))
            return 2

        plan = []
        print(f"SQL Server source schema: {args.source_schema}; source tables: {len(source_names)}")
        print(f"PostgreSQL ERP tables: {len(target_tables)}")
        for target_name in target_tables:
            matches = source_by_lower.get(target_name.lower(), [])
            if len(matches) > 1:
                print(f"AMBIGUOUS source table name {target_name}: {matches}; choose a schema/source explicitly.")
                continue
            if not matches:
                continue
            source_name = matches[0]
            src_cols = {c["name"] for c in src_inspector.get_columns(source_name, schema=args.source_schema)}
            dst_cols = {c.name for c in target_tables[target_name].columns}
            common = [c.name for c in target_tables[target_name].columns if c.name in src_cols and c.name in dst_cols]
            if not common:
                print(f"SKIP {source_name}: no same-name columns in target table {target_name}")
                continue
            count = None
            if args.dry_run:
                count = src.execute(text(f"SELECT COUNT_BIG(*) FROM [{args.source_schema}].[{source_name.replace(']', ']]')}]" )).scalar_one()
            plan.append((source_name, target_name, common, count))
            suffix = f", source rows={count}" if count is not None else ""
            print(f"PLAN {args.source_schema}.{source_name} -> {target_name}: {len(common)} shared columns{suffix}")
            if sorted(src_cols - set(common)):
                print("  source-only/unmapped columns: " + ", ".join(sorted(src_cols - set(common))[:15]))
            if sorted(dst_cols - set(common)):
                print("  target-only columns (defaults/nulls required): " + ", ".join(sorted(dst_cols - set(common))[:15]))

        if args.dry_run:
            print(f"DRY RUN complete. Matching tables: {len(plan)}. No data was written.")
            return 0

        if not args.allow_nonempty_target:
            with dst.connect() as conn:
                nonempty = []
                for _, table_name, _, _ in plan:
                    if conn.execute(select(text("1")).select_from(target_tables[table_name]).limit(1)).first():
                        nonempty.append(table_name)
                if nonempty:
                    print("ERROR: destination tables already contain rows; refusing to risk duplicates.")
                    print("Use a fresh target database, or only after backup pass --allow-nonempty-target.")
                    print("Nonempty: " + ", ".join(nonempty))
                    return 3

        # Copy in FK dependency order as defined by the ERP model metadata.
        rank = {t.name: i for i, t in enumerate(Base.metadata.sorted_tables)}
        plan.sort(key=lambda item: rank.get(item[1], 9999))
        copied = 0
        for source_name, target_name, columns, _ in plan:
            source_table = __import__("sqlalchemy").Table(source_name, MetaData(), schema=args.source_schema, autoload_with=src)
            target_table = target_tables[target_name]
            total = 0
            with src.connect() as source_conn, dst.begin() as dest_conn:
                result = source_conn.execution_options(stream_results=True).execute(select(*(source_table.c[c] for c in columns)))
                while True:
                    rows = result.mappings().fetchmany(BATCH_SIZE)
                    if not rows:
                        break
                    dest_conn.execute(target_table.insert(), [dict(row) for row in rows])
                    total += len(rows)
            copied += 1
            print(f"COPIED {source_name} -> {target_name}: {total} rows")
            # Synchronize sequence-backed integer primary keys, if this column has a sequence.
            pk_cols = list(target_table.primary_key.columns)
            if len(pk_cols) == 1 and pk_cols[0].name in columns:
                pk = pk_cols[0].name
                with dst.begin() as conn:
                    seq = conn.execute(text("SELECT pg_get_serial_sequence(:tbl, :col)"), {"tbl": target_name, "col": pk}).scalar_one_or_none()
                    if seq:
                        qtable = '"' + target_name.replace('"', '""') + '"'
                        qpk = '"' + pk.replace('"', '""') + '"'
                        maximum = conn.execute(text(f"SELECT MAX({qpk}) FROM {qtable}")).scalar_one_or_none()
                        if maximum is not None:
                            conn.execute(text("SELECT setval(CAST(:seq AS regclass), :max_id, true)"), {"seq": seq, "max_id": maximum})
        print(f"Migration complete. Tables copied: {copied}. SQL Server source was not changed.")
        return 0
    except SQLAlchemyError as exc:
        print(f"DATABASE ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        src.dispose()
        dst.dispose()

if __name__ == "__main__":
    raise SystemExit(main())
