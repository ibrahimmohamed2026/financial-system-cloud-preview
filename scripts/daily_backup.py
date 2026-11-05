"""نسخة احتياطية يومية من سطر الأوامر (بديل/تكملة للجدولة المدمجة في التطبيق).

مفيدة لو عايز تشغّلها بـ Windows Task Scheduler أو cron بدل ما التطبيق يعملها بنفسه
(في الحالة دي خلّي BACKUP_AUTO_ENABLED=false في .env عشان ما تتكررش).

التشغيل:  python scripts/daily_backup.py
بيستخدم نفس إعدادات .env (قاعدة البيانات، BACKUP_DIR، BACKUP_RETENTION) ويطبع مسار النسخة.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import backup_service  # noqa: E402

if __name__ == "__main__":
    print(backup_service.create_backup("auto"))
