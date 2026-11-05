"""تجهيز قاعدة بيانات جديدة (PostgreSQL أو SQLite) حسب إعدادات .env — بديل عن run_sql.py اللي محتاج SQL Server.

مناسب لعدد موظفين صغير (زي 10) — ملف واحد (financial_system.db) من غير
أي سيرفر قاعدة بيانات منفصل ولا ODBC Driver.

التشغيل:  python init_sqlite_db.py
(آمن للتكرار — بيعمل الجداول واليوزر الأدمن لو مش موجودين بس، ومايمسّش بياناتك.)
"""
import argparse
import getpass

from app import bootstrap, db_setup
from app.database import SessionLocal, engine


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--full-name", default="System Admin")
    parser.add_argument("--company", default="الشركة")
    parser.add_argument("--year", type=int, default=None, help="ينشئ سنة مالية 1/1–31/12 لو مفيش أي سنة")
    parser.add_argument("--skip-admin", action="store_true", help="متنشأش يوزر أدمن (لو عايز تعمله بعدين)")
    args = parser.parse_args()

    print(f"قاعدة البيانات: {engine.url}")
    db_setup.ensure_schema(engine)   # جداول + View الصلاحيات + فهرس الشيكات (SQLite أو PostgreSQL)
    print("تم تجهيز الجداول والـView والفهارس")

    with SessionLocal() as session:
        bootstrap.seed_screens(session)
        bootstrap.sync_permissions(session)
        print("تم تجهيز الشاشات والصلاحيات")

        if not args.skip_admin:
            pwd = getpass.getpass(f"كلمة مرور المستخدم ({args.username}): ")
            bootstrap.create_admin(session, args.username, pwd, args.full_name)
            print(f"تم إنشاء/تأكيد المستخدم الأدمن: {args.username}")

        if args.year:
            bootstrap.ensure_fiscal_year(session, args.year, args.company)
            print(f"تم إنشاء السنة المالية {args.year} (لو مفيش سنة قبل كده)")

    print("\nتم بنجاح. شغّل الآن:  uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
