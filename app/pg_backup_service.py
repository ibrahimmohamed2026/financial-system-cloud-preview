"""Automated PostgreSQL pg_dump backups, scheduled in-process every six hours."""
from __future__ import annotations
import logging, os, shutil, subprocess, threading, uuid
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.engine import make_url
from .config import BASE_DIR, settings

log = logging.getLogger("uvicorn.error")
BACKUP_DIR = BASE_DIR / "backups"
INTERVAL_SECONDS = max(1, int(settings.pg_backup_interval_hours)) * 3600
RETENTION_DAYS = max(1, int(settings.pg_backup_retention_days))
_PREFIX = "financial_system_pg_"
_lock = threading.Lock()
_stop = threading.Event()
_thread: threading.Thread | None = None

class PgBackupError(RuntimeError): pass

def _connection():
    try:
        url = make_url(settings.effective_database_url)
    except Exception as exc:
        raise PgBackupError(f"إعدادات اتصال قاعدة البيانات غير صحيحة: {exc}") from exc
    if url.get_backend_name() != "postgresql":
        raise PgBackupError("نسخ pg_dump متاح فقط عند استخدام PostgreSQL")
    return url

def list_backups() -> list[dict]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    rows=[]
    for p in BACKUP_DIR.glob(f"{_PREFIX}*.dump"):
        if p.is_file():
            st=p.stat(); rows.append({"name":p.name,"size":st.st_size,"created_at":datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")})
    return sorted(rows,key=lambda x:x["created_at"],reverse=True)

def cleanup_old_backups(now: datetime | None = None) -> int:
    now=now or datetime.now(); cutoff=(now-timedelta(days=RETENTION_DAYS)).timestamp(); deleted=0
    BACKUP_DIR.mkdir(parents=True,exist_ok=True)
    for p in BACKUP_DIR.glob(f"{_PREFIX}*.dump"):
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink(); deleted+=1
        except OSError: log.exception("تعذر حذف النسخة القديمة %s",p)
    return deleted

def _lock_owner_is_alive(marker: Path) -> bool | None:
    """Return whether the PID recorded in a lock belongs to a live process.

    None means this is a legacy/empty lock and its owner cannot be identified.
    """
    try:
        raw=marker.read_text(encoding="ascii").strip()
        if not raw: return None
        pid=int(raw.split(":",1)[0])
        if pid <= 0: return False
        try: os.kill(pid,0)
        except ProcessLookupError: return False
        except PermissionError: return True
        return True
    except (OSError, ValueError):
        return None

def create_backup() -> Path:
    if not _lock.acquire(blocking=False): raise PgBackupError("هناك عملية نسخ احتياطي جارية بالفعل")
    marker=None; marker_token=None; owns_marker=False
    try:
        url=_connection(); BACKUP_DIR.mkdir(parents=True,exist_ok=True)
        marker=BACKUP_DIR / ".pg_backup.lock"
        if marker.exists():
            owner_alive=_lock_owner_is_alive(marker)
            stale_legacy=(owner_alive is None and datetime.now().timestamp()-marker.stat().st_mtime > 7200)
            if owner_alive is False or stale_legacy:
                marker.unlink(missing_ok=True)  # إزالة قفل عملية انتهت أو علامة قديمة
        marker_token=f"{os.getpid()}:{uuid.uuid4().hex}"
        try:
            fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            owns_marker=True
            with os.fdopen(fd,"w",encoding="ascii") as lock_file: lock_file.write(marker_token)
        except FileExistsError: raise PgBackupError("عملية نسخ احتياطي أخرى تعمل بالفعل")
        exe=settings.pg_dump_path or shutil.which("pg_dump")
        if not exe: raise PgBackupError("لم يتم العثور على pg_dump. ثبّت PostgreSQL client أو حدّد PG_DUMP_PATH في .env")
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        target=BACKUP_DIR/f"{_PREFIX}{stamp}.dump"
        temp=BACKUP_DIR/f".{target.name}.{uuid.uuid4().hex}.part"
        env=os.environ.copy()
        if url.password is not None: env["PGPASSWORD"]=url.password
        if url.query.get("sslmode"): env["PGSSLMODE"]=str(url.query["sslmode"])
        cmd=[exe,"--no-password","--format=custom","--file",str(temp)]
        if url.host: cmd += ["--host",url.host]
        if url.port: cmd += ["--port",str(url.port)]
        if url.username: cmd += ["--username",url.username]
        cmd += ["--dbname",url.database or ""]
        try:
            result=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=7200,check=False)
            if result.returncode != 0: raise PgBackupError((result.stderr or result.stdout or "pg_dump failed").strip()[-3000:])
            if not temp.is_file() or temp.stat().st_size == 0: raise PgBackupError("pg_dump لم ينتج ملف نسخة صالحًا")
            os.replace(temp,target)
        finally: temp.unlink(missing_ok=True)
        cleanup_old_backups()
        log.info("PostgreSQL backup created: %s",target.name)
        return target
    finally:
        # لا تحذف قفل عملية أخرى إذا فشلنا في امتلاكه أو استبدلته عملية أخرى.
        if owns_marker and marker and marker.exists():
            try:
                if marker.read_text(encoding="ascii").strip()==marker_token: marker.unlink(missing_ok=True)
            except OSError: log.exception("تعذر حذف ملف قفل النسخ الاحتياطي %s",marker)
        _lock.release()

def _loop():
    # نسخة عند بدء التطبيق، ثم نسخة كل 6 ساعات (قابلة للتعديل من .env).
    while not _stop.is_set():
        try: create_backup()
        except Exception: log.exception("فشل النسخ الاحتياطي التلقائي لـ PostgreSQL")
        if _stop.wait(INTERVAL_SECONDS): break

def start_scheduler():
    global _thread
    if _thread and _thread.is_alive(): return
    _stop.clear(); _thread=threading.Thread(target=_loop,name="postgres-pg-dump-backup",daemon=True); _thread.start()

def stop_scheduler():
    _stop.set()

def status() -> dict:
    return {"enabled":True,"interval_hours":INTERVAL_SECONDS//3600,"retention_days":RETENTION_DAYS,"backup_dir":str(BACKUP_DIR),"scheduler_running":bool(_thread and _thread.is_alive()),"backups":list_backups()}
