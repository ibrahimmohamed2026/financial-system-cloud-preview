"""النسخ الاحتياطي والاستعادة والجدولة اليومية.

شكل النسخة (ملف ZIP):
  manifest.json            بيانات النسخة (النسخة، التاريخ، نوع قاعدة البيانات، عدد صفوف كل جدول)
  database/<Table>.jsonl   صف JSON في كل سطر — لكل جدول (نسخة منطقية بتشتغل على SQLite وPostgreSQL
                           من غير pg_dump ولا أي أدوات خارجية، ويمكن استعادتها على أي من القاعدتين)
  system/...               ملفات النظام (app, web, sql, scripts, requirements...) — بدون .env (فيه أسرار)

الاستعادة بتتم داخل Transaction واحدة: لو أي حاجة فشلت بيحصل Rollback والبيانات الحالية تفضل زي ما هي.
وقبل أي استعادة بتتعمل نسخة أمان تلقائية (pre_restore) في مجلد النسخ.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import tempfile
import threading
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, select

from . import db_setup
from .config import BASE_DIR, settings
from .database import engine
from .models import Base

log = logging.getLogger("uvicorn.error")

FORMAT_VERSION = 1
KINDS = ("manual", "auto", "pre_restore")
NAME_RE = re.compile(r"^financial_system_(manual|auto|pre_restore|backup)_(\d{8})_(\d{6})\.zip$")
PRE_RESTORE_KEEP = 5

_op_lock = threading.RLock()   # نسخة/استعادة واحدة في المرة (RLock عشان الاستعادة بتعمل نسخة أمان جواها)


class BackupError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ----------------------------- إعدادات تتغيّر من الواجهة -----------------------------
# بتتحفظ في backup_settings.json (جنب المشروع) وبتتغلّب على قيم .env. بتتقرأ تلقائيًا لما الملف يتغير،
# فالتغيير بيسري فورًا حتى لو في أكتر من Worker. الملف خارج القاعدة عشان الاستعادة/الهجرة ما تمسحوش.
_OVERRIDE_FIELDS = ("backup_dir", "backup_auto_enabled", "backup_time", "backup_retention")
_loaded_mtime: int | None = None
_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _settings_file() -> Path:
    return Path(os.getenv("BACKUP_SETTINGS_FILE") or BASE_DIR / "backup_settings.json")


def load_overrides() -> None:
    global _loaded_mtime
    f = _settings_file()
    try:
        mtime = f.stat().st_mtime_ns
    except OSError:
        return
    if mtime == _loaded_mtime:
        return
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    for k in _OVERRIDE_FIELDS:
        if k in data:
            setattr(settings, k, data[k])
    _loaded_mtime = mtime


def update_settings(*, directory: str, auto_enabled: bool, auto_time: str, retention: int) -> dict:
    """بيغيّر مكان النسخ ومواعيدها ويحفظها. بيتأكد إن المجلد يتعمل ويتكتب فيه قبل ما يعتمده."""
    global _loaded_mtime
    directory = (directory or "").strip()
    if not directory:
        raise BackupError("اكتب مسار مجلد النسخ الاحتياطية")
    m = _TIME_RE.match((auto_time or "").strip())
    if not m:
        raise BackupError("الوقت لازم يكون بالشكل HH:MM مثل 02:00")
    if not 1 <= retention <= 365:
        raise BackupError("عدد النسخ المحتفظ بها لازم يكون بين 1 و365")
    path = Path(directory).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".write_test_{uuid.uuid4().hex}"
        probe.write_text("ok")
        probe.unlink()
    except OSError as e:
        raise BackupError(f"المجلد غير متاح أو لا توجد صلاحية كتابة عليه: {e}")
    data = {"backup_dir": str(path), "backup_auto_enabled": bool(auto_enabled),
            "backup_time": f"{int(m.group(1)):02d}:{m.group(2)}", "backup_retention": int(retention)}
    f = _settings_file()
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, f)
    for k, v in data.items():
        setattr(settings, k, v)
    _loaded_mtime = f.stat().st_mtime_ns
    if auto_enabled:
        start_scheduler()
    return status()


# ----------------------------- مساعدات -----------------------------
def backup_dir() -> Path:
    load_overrides()
    d = settings.backup_path
    d.mkdir(parents=True, exist_ok=True)
    return d


def _kind_of(name: str) -> str:
    m = NAME_RE.match(name)
    return m.group(1) if m else "other"


def backup_path_for(name: str) -> Path:
    """مسار نسخة موجودة في مجلد النسخ (بيرفض أي اسم فيه مسارات أو غير مطابق للشكل المعتمد)."""
    if not NAME_RE.match(name or ""):
        raise BackupError("اسم ملف النسخة غير صالح")
    p = backup_dir() / name
    if not p.is_file():
        raise BackupError("ملف النسخة غير موجود", 404)
    return p


def list_backups() -> list[dict]:
    out = []
    for f in backup_dir().iterdir():
        if f.is_file() and NAME_RE.match(f.name):
            st = f.stat()
            out.append({"name": f.name, "kind": _kind_of(f.name), "size": st.st_size,
                        "created_at": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    return sorted(out, key=lambda x: x["created_at"], reverse=True)


# ----------------------------- إنشاء نسخة -----------------------------
_SYSTEM_DIRS = ("app", "web", "sql", "scripts", "tests")
_SYSTEM_FILES = ("requirements.txt", "README.md", ".env.example", "BACKUP_POSTGRES_MIGRATION.md", "pytest.ini")


def _write_database(z: zipfile.ZipFile) -> dict[str, int]:
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":      # لقطة متسقة لكل الجداول حتى لو في كتابة شغالة
            conn = conn.execution_options(isolation_level="REPEATABLE READ")
        for table in Base.metadata.sorted_tables:
            cols = db_setup.data_columns(table)
            n = 0
            with z.open(f"database/{table.name}.jsonl", "w", force_zip64=True) as f:
                for row in conn.execute(select(*cols)):
                    rec = {c.name: db_setup.to_json_value(v) for c, v in zip(cols, row)}
                    f.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))
                    n += 1
            counts[table.name] = n
    return counts


def _write_system_files(z: zipfile.ZipFile) -> int:
    n = 0
    for folder in _SYSTEM_DIRS:
        root = BASE_DIR / folder
        if root.is_dir():
            for f in sorted(root.rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
                    z.write(f, "system/" + f.relative_to(BASE_DIR).as_posix())
                    n += 1
    for name in _SYSTEM_FILES:
        f = BASE_DIR / name
        if f.is_file():
            z.write(f, "system/" + name)
            n += 1
    for f in sorted(BASE_DIR.glob("*.py")) + sorted(BASE_DIR.glob("*.bat")):
        z.write(f, "system/" + f.name)
        n += 1
    return n


def create_backup(kind: str = "manual") -> Path:
    """بيعمل نسخة كاملة (قاعدة البيانات + ملفات النظام) ويحفظها في مجلد النسخ ويرجّع مسارها."""
    if kind not in KINDS:
        raise ValueError(kind)
    with _op_lock:
        d = backup_dir()
        now = datetime.now()
        while (d / f"financial_system_{kind}_{now:%Y%m%d_%H%M%S}.zip").exists():
            now += timedelta(seconds=1)
        final = d / f"financial_system_{kind}_{now:%Y%m%d_%H%M%S}.zip"
        tmp = final.with_name(final.name + ".part")
        try:
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
                counts = _write_database(z)
                nfiles = _write_system_files(z)
                z.writestr("manifest.json", json.dumps({
                    "format": FORMAT_VERSION, "app": "financial_system", "kind": kind,
                    "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "source_backend": engine.dialect.name, "tables": counts, "system_files": nfiles,
                }, ensure_ascii=False, indent=2))
            os.replace(tmp, final)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        prune()
        return final


def prune() -> None:
    """بيحتفظ بآخر N نسخة تلقائية (BACKUP_RETENTION) وآخر 5 نسخ أمان؛ النسخ اليدوية ما بتتمسحش."""
    d = backup_dir()
    limits = {"auto": max(1, settings.backup_retention), "pre_restore": PRE_RESTORE_KEEP}
    for kind, keep in limits.items():
        files = sorted((f for f in d.glob(f"financial_system_{kind}_*.zip") if NAME_RE.match(f.name)),
                       key=lambda p: p.name, reverse=True)
        for old in files[keep:]:
            try:
                old.unlink()
            except OSError:
                log.warning("تعذر حذف النسخة القديمة %s", old)
    cutoff = datetime.now().timestamp() - 3 * 86400
    for junk in list(d.glob("*.part")) + list(d.glob(".auto_*.lock")):
        try:
            if junk.stat().st_mtime < cutoff:
                junk.unlink()
        except OSError:
            pass


# ----------------------------- الاستعادة -----------------------------
def _read_jsonl(z: zipfile.ZipFile, table) -> list[dict] | None:
    entry = f"database/{table.name}.jsonl"
    try:
        info = z.getinfo(entry)
    except KeyError:
        return None
    cols = db_setup.data_columns(table)
    rows = []
    with z.open(info) as raw:
        for line in io.TextIOWrapper(raw, encoding="utf-8"):
            if line.strip():
                rec = json.loads(line)
                rows.append({c.key: db_setup.from_json_value(c, rec[c.name]) for c in cols if c.name in rec})
    return rows



def _preflight_restore(z: zipfile.ZipFile, manifest: dict) -> dict[str, int]:
    """Validate archive/model/live-schema compatibility before creating a safety copy or deleting rows."""
    expected_tables = {table.name: table for table in Base.metadata.sorted_tables}
    declared = manifest.get("tables")
    if not isinstance(declared, dict) or set(declared) != set(expected_tables):
        missing = sorted(set(expected_tables) - set(declared or {}))
        extra = sorted(set(declared or {}) - set(expected_tables))
        raise BackupError(
            f"مخطط النسخة غير متوافق مع إصدار النظام. جداول ناقصة: {missing[:8]}، جداول زائدة: {extra[:8]}"
        )

    archive_names = set(z.namelist())
    db_files = {name for name in archive_names if name.startswith("database/") and name.endswith(".jsonl")}
    expected_files = {f"database/{name}.jsonl" for name in expected_tables}
    if db_files != expected_files:
        missing = sorted(expected_files - db_files)
        extra = sorted(db_files - expected_files)
        raise BackupError(
            f"ملفات بيانات النسخة غير مكتملة أو غير متوافقة. ملفات ناقصة: {missing[:5]}، ملفات زائدة: {extra[:5]}"
        )

    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    missing_live = sorted(set(expected_tables) - live_tables)
    if missing_live:
        raise BackupError(f"قاعدة التشغيل ينقصها جداول مطلوبة: {missing_live[:8]}")

    counts: dict[str, int] = {}
    for table_name, table in expected_tables.items():
        expected_columns = {column.name for column in db_setup.data_columns(table)}
        live_columns_info = inspector.get_columns(table_name)
        live_columns = {column["name"] for column in live_columns_info}
        missing_columns = sorted(expected_columns - live_columns)
        if missing_columns:
            raise BackupError(f"قاعدة التشغيل: أعمدة ناقصة في {table_name}: {missing_columns[:8]}")

        # Existing DB columns not represented by the current model can block inserts
        # when they are mandatory and have no database-side default.
        model_columns = {column.name for column in table.columns}
        blocking_extra = sorted(
            column["name"] for column in live_columns_info
            if column["name"] not in model_columns
            and not column.get("nullable", True)
            and column.get("default") is None
            and column.get("computed") is None
        )
        if blocking_extra:
            raise BackupError(
                f"قاعدة التشغيل تحتوي أعمدة إلزامية غير معروفة للنظام في {table_name}: {blocking_extra[:8]}"
            )

        entry = f"database/{table_name}.jsonl"
        expected_count = declared[table_name]
        if not isinstance(expected_count, int) or expected_count < 0:
            raise BackupError(f"عدد سجلات غير صالح في manifest للجدول {table_name}")

        count = 0
        with z.open(entry) as raw:
            for line_number, line in enumerate(raw, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except ValueError as exc:
                    raise BackupError(f"بيانات JSON تالفة في {table_name} عند السطر {line_number}") from exc
                if not isinstance(record, dict):
                    raise BackupError(f"صيغة سجل غير صحيحة في الجدول {table_name}")
                fields = set(record)
                if fields != expected_columns:
                    missing = sorted(expected_columns - fields)
                    extra = sorted(fields - expected_columns)
                    raise BackupError(
                        f"حقول النسخة غير متوافقة في {table_name}. ناقصة: {missing[:8]}، زائدة: {extra[:8]}"
                    )
                count += 1
        if count != expected_count:
            raise BackupError(
                f"عدد سجلات النسخة في {table_name} ({count}) لا يطابق manifest ({expected_count})"
            )
        counts[table_name] = count

    return counts


def _restore_legacy_sqlite(z: zipfile.ZipFile, conn) -> dict[str, int]:
    """نسخ قديمة (قبل الشكل الجديد) كان فيها database/database.sqlite."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    src = None
    try:
        Path(tmp).write_bytes(z.read("database/database.sqlite"))
        src = create_engine("sqlite:///" + tmp)
        present = set(inspect(src).get_table_names())
        counts: dict[str, int] = {}
        with src.connect() as sc:
            for table in Base.metadata.sorted_tables:
                if table.name not in present:
                    counts[table.name] = 0
                    continue
                have = {c["name"] for c in inspect(src).get_columns(table.name)}
                cols = [c for c in db_setup.data_columns(table) if c.name in have]
                rows = [dict(zip([c.key for c in cols], r)) for r in sc.execute(select(*cols))]
                db_setup.insert_rows(conn, table, rows)
                counts[table.name] = len(rows)
        return counts
    finally:
        if src is not None:
            src.dispose()
        Path(tmp).unlink(missing_ok=True)


def restore_backup(path: Path) -> dict:
    """بيستبدل بيانات قاعدة البيانات الحالية بمحتوى النسخة. Transaction واحدة (كله أو ولا حاجة)."""
    if not _op_lock.acquire(timeout=1):
        raise BackupError("في عملية نسخ/استعادة شغالة حاليًا، حاول بعد لحظات", 409)
    try:
        try:
            z = zipfile.ZipFile(path)
        except zipfile.BadZipFile as e:
            raise BackupError("الملف ليس نسخة احتياطية ZIP صالحة") from e
        with z:
            names = set(z.namelist())
            legacy = "manifest.json" not in names and "database/database.sqlite" in names
            manifest: dict = {}
            if not legacy:
                if "manifest.json" not in names:
                    raise BackupError("الملف ده مش نسخة احتياطية من النظام المالي (manifest.json مفقود)")
                try:
                    manifest = json.loads(z.read("manifest.json"))
                except ValueError as e:
                    raise BackupError("manifest.json تالف") from e
                if manifest.get("app") != "financial_system" or manifest.get("format") != FORMAT_VERSION:
                    raise BackupError("إصدار النسخة غير مدعوم أو الملف من برنامج آخر")
            bad = z.testzip()
            if bad:
                raise BackupError(f"ملف النسخة تالف (فشل فحص السلامة عند: {bad})")

            _preflight_restore(z, manifest)  # رفض النسخ غير المتوافقة قبل أي تغيير أو نسخة أمان
            safety = create_backup("pre_restore")       # نسخة أمان بالحالة الحالية قبل أي تغيير
            try:
                with engine.begin() as conn:
                    db_setup.clear_all_tables(conn)
                    if legacy:
                        counts = _restore_legacy_sqlite(z, conn)
                    else:
                        counts = {}
                        for table in Base.metadata.sorted_tables:
                            rows = _read_jsonl(z, table)
                            if rows is None:
                                counts[table.name] = 0
                                continue
                            db_setup.insert_rows(conn, table, rows)
                            counts[table.name] = len(rows)
                    db_setup.reset_sequences(conn)
                    expected = manifest.get("tables") or {}
                    for tname, n in expected.items():
                        if tname in counts and counts[tname] != n:
                            raise BackupError(f"عدد صفوف الجدول {tname} بعد الاستعادة ({counts[tname]}) لا يطابق النسخة ({n})")
            except BackupError:
                raise
            except Exception as e:
                log.exception("فشلت استعادة النسخة الاحتياطية")
                raise BackupError(
                    f"فشلت الاستعادة ولم يتم تغيير أي بيانات (Rollback). السبب: {e.__class__.__name__}: {e}", 500) from e
        return {"tables": counts, "rows": sum(counts.values()), "safety_backup": safety.name,
                "source_backend": manifest.get("source_backend", "sqlite (legacy)")}
    finally:
        _op_lock.release()


# ----------------------------- الجدولة اليومية -----------------------------
def _today_auto_exists(d: Path, now: datetime) -> bool:
    return any(d.glob(f"financial_system_auto_{now:%Y%m%d}_*.zip"))


def last_auto_backup() -> dict | None:
    autos = [b for b in list_backups() if b["kind"] == "auto"]
    return autos[0] if autos else None


def run_due_auto_backup(now: datetime | None = None) -> Path | None:
    """بينفّذ النسخة اليومية لو الوقت المحدد عدّى ولسه ماتعملتش نسخة تلقائية النهارده.
    (لو الجهاز كان مقفول وقت الجدولة، بتتعمل أول ما التطبيق يشتغل — وأمان من تكرارها لو في أكتر من Worker.)"""
    now = now or datetime.now()
    hh, mm = (int(x) for x in settings.backup_time.split(":"))
    if now < now.replace(hour=hh, minute=mm, second=0, microsecond=0):
        return None
    d = backup_dir()
    if _today_auto_exists(d, now):
        return None
    marker = d / f".auto_{now:%Y%m%d}.lock"
    # استخدم ساعة الجهاز لقياس عمر القفل؛ now قد تكون قيمة اختبارية/محاكاة ولا تصلح لعمر الملف.
    if marker.exists() and datetime.now().timestamp() - marker.stat().st_mtime > 1800:   # علامة قديمة من تشغيل انهار
        marker.unlink(missing_ok=True)
    try:
        os.close(os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return None
    try:
        path = create_backup("auto")
        log.info("تم إنشاء النسخة الاحتياطية اليومية: %s", path.name)
        return path
    except BaseException:
        marker.unlink(missing_ok=True)     # نسمح بإعادة المحاولة
        raise


_stop = threading.Event()
_thread: threading.Thread | None = None


def _loop() -> None:
    retry_at = 0.0
    wait = 5.0
    while not _stop.wait(wait):
        wait = 30.0
        load_overrides()
        if not settings.backup_auto_enabled or datetime.now().timestamp() < retry_at:
            continue
        try:
            run_due_auto_backup()
        except Exception:
            log.exception("فشلت النسخة الاحتياطية اليومية — إعادة المحاولة بعد 15 دقيقة")
            retry_at = datetime.now().timestamp() + 900


def start_scheduler() -> None:
    global _thread
    load_overrides()
    if not settings.backup_auto_enabled or (_thread and _thread.is_alive()):
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="daily-backup", daemon=True)
    _thread.start()
    log.info("النسخ الاحتياطي اليومي مفعّل: %s -> %s (الاحتفاظ بآخر %s)",
             settings.backup_time, settings.backup_path, settings.backup_retention)


def stop_scheduler() -> None:
    _stop.set()


def status() -> dict:
    load_overrides()
    return {
        "db_backend": engine.dialect.name,
        "backup_dir": str(settings.backup_path),
        "auto_enabled": settings.backup_auto_enabled,
        "auto_time": settings.backup_time,
        "retention": settings.backup_retention,
        "scheduler_running": bool(_thread and _thread.is_alive()),
        "last_auto": last_auto_backup(),
    }
