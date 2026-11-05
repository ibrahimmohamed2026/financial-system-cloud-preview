from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # .env بيتقرأ من مجلد المشروع (مش من مجلد التشغيل) عشان Task Scheduler/cron يشتغلوا من أي مكان.
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # ---- النسخ الاحتياطي ----
    backup_dir: str = "./backups"          # مجلد حفظ النسخ (نسبي لمجلد المشروع لو مش مسار كامل)
    backup_auto_enabled: bool = True       # تشغيل النسخ اليومي التلقائي داخل التطبيق
    backup_time: str = "02:00"             # وقت النسخ اليومي HH:MM (بتوقيت جهاز السيرفر)
    backup_retention: int = 14             # عدد النسخ التلقائية اللي بيتم الاحتفاظ بيها
    backup_max_upload_mb: int = 1024       # أقصى حجم لملف استعادة
    pg_backup_interval_hours: int = 6
    pg_backup_retention_days: int = 14
    pg_dump_path: str | None = None

    @field_validator("database_url", "postgres_user", "postgres_password", "postgres_db", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("backup_time")
    @classmethod
    def _time_ok(cls, v: str) -> str:
        try:
            hh, mm = v.strip().split(":")
            assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
        except Exception:
            raise ValueError("BACKUP_TIME لازم يكون بالشكل HH:MM مثل 02:00")
        return f"{int(hh):02d}:{int(mm):02d}"

    @property
    def effective_database_url(self) -> str:
        """DATABASE_URL لو موجود (PostgreSQL أو sqlite صريح للتجارب)، وإلا بيتبني من POSTGRES_*."""
        if self.database_url:
            url = self.database_url.strip()
            # SQLAlchemy بيفترض psycopg2 لو كتبت postgresql:// — إحنا مثبّتين psycopg 3
            for old in ("postgresql://", "postgres://"):
                if url.startswith(old):
                    return "postgresql+psycopg://" + url[len(old):]
            return url
        if self.postgres_db and self.postgres_user:
            from sqlalchemy.engine import URL
            return URL.create("postgresql+psycopg", username=self.postgres_user,
                password=self.postgres_password, host=self.postgres_host,
                port=self.postgres_port, database=self.postgres_db).render_as_string(hide_password=False)
        raise ValueError("إعدادات PostgreSQL ناقصة: املا POSTGRES_USER و POSTGRES_PASSWORD و POSTGRES_DB "
                         "(و POSTGRES_HOST/POSTGRES_PORT) في ملف .env، أو اكتب DATABASE_URL كامل")

    @property
    def backup_path(self) -> Path:
        p = Path(self.backup_dir)
        return (p if p.is_absolute() else BASE_DIR / p).resolve()
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    cors_origins: str = ""
    trusted_proxy_ips: str = ""
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 60
    api_docs_enabled: bool = False
    # طباعة PDF: مسار خط .ttf بيدعم العربي (لو فاضي بندوّر على Tahoma/Arial/DejaVu تلقائيًا)
    pdf_font_path: str | None = None
    pdf_font_bold_path: str | None = None

    @field_validator("jwt_secret")
    @classmethod
    def _secret_ok(cls, v: str) -> str:
        if v.strip().upper().startswith("CHANGE_ME") or len(v) < 24:
            raise ValueError("JWT_SECRET لازم يتغيّر لقيمة عشوائية طولها 24 حرف على الأقل")
        return v

    @property
    def cors_list(self) -> list[str]:
        # Wildcard CORS is too permissive for a finance system. Require explicit origins.
        return [o.strip() for o in self.cors_origins.split(",") if o.strip() and o.strip() != "*"]

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
