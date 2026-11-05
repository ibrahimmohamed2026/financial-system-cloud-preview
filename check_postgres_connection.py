"""Check PostgreSQL connectivity and report schema/table counts without modifying data."""
from sqlalchemy import create_engine, inspect, text
from app.config import settings


def main() -> int:
    try:
        engine = create_engine(settings.effective_database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar_one()
            dbname = conn.execute(text("SELECT current_database()")).scalar_one()
            username = conn.execute(text("SELECT current_user")).scalar_one()
            tables = inspect(conn).get_table_names()
        print("PostgreSQL connection: OK")
        print(f"Database: {dbname}")
        print(f"Connected as: {username}")
        print(f"Existing tables: {len(tables)}")
        print(version.splitlines()[0])
        if not tables:
            print("NOTICE: database is empty. The app may create missing schema on startup; this does not migrate source data.")
        engine.dispose()
        return 0
    except Exception as exc:
        print("PostgreSQL connection: FAILED")
        print(str(exc))
        print("Check PostgreSQL service, host/port, database/user/password, pg_hba.conf, and Windows Firewall.")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
