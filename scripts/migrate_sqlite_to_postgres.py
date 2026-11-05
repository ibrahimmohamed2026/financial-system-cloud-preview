"""هجرة البيانات من SQLite إلى PostgreSQL.

الخطوات المنفّذة:
  1) إنشاء المخطط كاملًا على PostgreSQL من الـModels (جداول + View الصلاحيات + فهرس الشيكات).
  2) نسخ كل الجداول بالترتيب الصحيح للعلاقات في Transaction واحدة (أي خطأ = Rollback كامل).
  3) ضبط عدّادات الـIDs (sequences) على آخر رقم.
  4) مقارنة عدد صفوف كل جدول بين المصدر والهدف.

الاستخدام:
  python scripts/migrate_sqlite_to_postgres.py                      # يقرأ POSTGRES_* من .env
  python scripts/migrate_sqlite_to_postgres.py --source sqlite:///./financial_system.db \
         --target postgresql+psycopg://user:pass@127.0.0.1:5432/financial_system
  python scripts/migrate_sqlite_to_postgres.py --dry-run            # فحص فقط من غير كتابة بيانات

قاعدة الهدف لازم تكون فاضية من البيانات (الجداول ممكن تكون موجودة بدون صفوف).
خد نسخة احتياطية من ملف SQLite قبل البدء. السكريبت ما بيعدّلش ولا بيمسح أي حاجة في المصدر.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app import db_setup  # noqa: E402
from app.models import Base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _target_from_env() -> str | None:
    """بيبني رابط PostgreSQL من POSTGRES_* / DATABASE_URL في .env (من غير ما يفتح قاعدة التطبيق الحالية)."""
    try:
        from dotenv import dotenv_values
    except ImportError:
        return None
    env = dotenv_values(ROOT / ".env")
    url = (env.get("DATABASE_URL") or "").strip()
    if url.startswith(("postgresql", "postgres:")):
        return url
    if env.get("POSTGRES_DB") and env.get("POSTGRES_USER"):
        from sqlalchemy.engine import URL
        return URL.create("postgresql+psycopg", username=env["POSTGRES_USER"], password=env.get("POSTGRES_PASSWORD") or None,
                          host=env.get("POSTGRES_HOST") or "localhost", port=int(env.get("POSTGRES_PORT") or 5432),
                          database=env["POSTGRES_DB"]).render_as_string(hide_password=False)
    return None


def _normalize(url: str) -> str:
    for old in ("postgresql://", "postgres://"):
        if url.startswith(old):
            return "postgresql+psycopg://" + url[len(old):]
    return url


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="sqlite:///" + str(ROOT / "financial_system.db"), help="رابط SQLite المصدر")
    ap.add_argument("--target", default=None, help="رابط PostgreSQL الهدف (الافتراضي من .env)")
    ap.add_argument("--dry-run", action="store_true", help="فحص الاتصال وعدّ صفوف المصدر فقط")
    args = ap.parse_args()

    target = _normalize(args.target or _target_from_env() or "")
    if not target.startswith("postgresql"):
        print("حدّد قاعدة PostgreSQL الهدف: --target أو POSTGRES_* في .env", file=sys.stderr)
        return 2
    src_url = make_url(args.source)
    if src_url.get_backend_name() != "sqlite":
        print("المصدر لازم يكون SQLite", file=sys.stderr)
        return 2
    if src_url.database and src_url.database != ":memory:" and not Path(src_url.database).exists():
        print(f"ملف SQLite غير موجود: {src_url.database}", file=sys.stderr)
        return 2

    src, dst = create_engine(args.source), create_engine(target, pool_pre_ping=True)
    shown = make_url(target).render_as_string(hide_password=True)
    print(f"المصدر: {args.source}\nالهدف : {shown}")
    try:
        with dst.connect() as c:
            print("اتصال PostgreSQL:", c.execute(text("select version()")).scalar_one().split(",")[0])
    except Exception as e:
        print(f"تعذر الاتصال بـ PostgreSQL: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        with src.connect() as sc:
            from sqlalchemy import inspect
            have = set(inspect(src).get_table_names())
            for t in Base.metadata.sorted_tables:
                print(f"  - {t.name}: {db_setup.count_rows(sc, t) if t.name in have else 'مش موجود'}")
        print("dry-run: لم تتم كتابة أي بيانات.")
        return 0

    print("1) إنشاء المخطط على PostgreSQL ...")
    db_setup.ensure_schema(dst)
    print("2) نسخ البيانات ...")
    try:
        copied = db_setup.copy_tables(src, dst)
    except Exception as e:
        print(f"\nفشلت الهجرة ولم تتم كتابة أي بيانات (Rollback): {e}", file=sys.stderr)
        return 1
    print("3) مراجعة عدد الصفوف ...")
    problems = db_setup.verify_counts(src, dst)
    if problems:
        print("فروقات:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print(f"\nتمت الهجرة بنجاح: {sum(copied.values())} صف في {len(copied)} جدول.")
    print("الخطوة التالية: في .env اجعل DATABASE_URL فاضي (أو احذف سطر sqlite) وتأكد من POSTGRES_*، ثم أعد تشغيل التطبيق.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
