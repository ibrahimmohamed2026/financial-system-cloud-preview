"""Interactive PostgreSQL configuration for a central Windows application server.
This only writes .env; it does not create, drop, or modify database tables/data.
"""
from __future__ import annotations
import re
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXAMPLE = ROOT / ".env.example"
ENV = ROOT / ".env"


def set_line(text: str, key: str, value: str) -> str:
    value = value.replace("\r", "").replace("\n", "")
    pattern = rf"(?m)^{re.escape(key)}=.*$"
    replacement = f"{key}={value}"
    if re.search(pattern, text):
        return re.sub(pattern, lambda _: replacement, text)
    return text.rstrip() + "\n" + replacement + "\n"


def main() -> int:
    print("=== إعداد الاتصال بقاعدة PostgreSQL المركزية ===")
    print("الأداة تعدل إعدادات .env فقط، ولا تحذف أو تنشئ جداول أو بيانات.\n")
    existing = ENV.read_text(encoding="utf-8") if ENV.exists() else ""
    if existing:
        answer = input("يوجد ملف .env بالفعل. هل تريد إعادة ضبط إعدادات اتصال PostgreSQL؟ [y/N]: ").strip().lower()
        if answer != "y":
            print("لم يتم تعديل الملف.")
            return 0
    template = EXAMPLE.read_text(encoding="utf-8")
    # Keep current security/backup settings where possible, but start from a known template.
    content = template
    for key in ("JWT_SECRET", "ACCESS_TOKEN_MINUTES", "REFRESH_TOKEN_DAYS", "MAX_FAILED_LOGINS", "LOCKOUT_MINUTES", "CORS_ORIGINS", "BACKUP_DIR", "BACKUP_AUTO_ENABLED", "BACKUP_TIME", "BACKUP_RETENTION", "PG_BACKUP_INTERVAL_HOURS", "PG_BACKUP_RETENTION_DAYS", "PG_DUMP_PATH"):
        match = re.search(rf"(?m)^{key}=(.*)$", existing)
        if match:
            content = set_line(content, key, match.group(1))
    host = input("عنوان سيرفر PostgreSQL (IP أو اسم جهاز) [127.0.0.1]: ").strip() or "127.0.0.1"
    port = input("Port [5432]: ").strip() or "5432"
    if not port.isdigit() or not (1 <= int(port) <= 65535):
        print("خطأ: المنفذ غير صحيح.")
        return 2
    db = input("اسم قاعدة البيانات [financial_system]: ").strip() or "financial_system"
    user = input("مستخدم PostgreSQL [financial_user]: ").strip() or "financial_user"
    import getpass
    password = getpass.getpass("كلمة مرور مستخدم PostgreSQL: ")
    if not password:
        print("خطأ: كلمة المرور لا يمكن أن تكون فارغة.")
        return 2
    content = set_line(content, "DATABASE_URL", "")
    content = set_line(content, "POSTGRES_HOST", host)
    content = set_line(content, "POSTGRES_PORT", port)
    content = set_line(content, "POSTGRES_DB", db)
    content = set_line(content, "POSTGRES_USER", user)
    content = set_line(content, "POSTGRES_PASSWORD", password)
    jwt = re.search(r"(?m)^JWT_SECRET=(.*)$", content)
    if not jwt or len(jwt.group(1).strip()) < 24 or "ضع_" in jwt.group(1):
        content = set_line(content, "JWT_SECRET", secrets.token_urlsafe(48))
    ENV.write_text(content, encoding="utf-8")
    try:
        ENV.chmod(0o600)
    except OSError:
        pass
    print(f"\nتم حفظ إعدادات الاتصال في: {ENV}")
    print("الخطوة التالية: شغّل check_postgres_connection.py لاختبار الاتصال.")
    print("لا تشارك ملف .env؛ فهو يحتوي على كلمة المرور ومفتاح الجلسات.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
