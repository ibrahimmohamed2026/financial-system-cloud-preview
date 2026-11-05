"""النسخ الاحتياطي والاستعادة (لمدير النظام فقط). المنطق كله في app/backup_service.py."""
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import backup_service as svc
from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import get_current_user, write_audit
from ..models import Role, User, UserRole

router = APIRouter(prefix="/admin/backup", tags=["Backup & Restore"])


def admin_only(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    ok = db.scalar(select(UserRole.user_id).join(Role, Role.role_id == UserRole.role_id)
                   .where(UserRole.user_id == user.user_id, Role.role_name == "Admin"))
    if not ok:
        raise HTTPException(403, "هذه الوظيفة لمدير النظام فقط")
    return user


def _fail(e: svc.BackupError):
    raise HTTPException(e.status, str(e)) from e


def _audit(user_id: int, action: str, detail: str) -> None:
    """تسجيل في AuditLog بجلسة مستقلة (بعد الاستعادة ممكن المستخدم يكون مش موجود في البيانات المستعادة)."""
    try:
        with SessionLocal() as s:
            if s.get(User, user_id) is not None:
                write_audit(s, user_id, action, "Backup", "-", new={"file": detail})
                s.commit()
    except Exception:
        pass


def _require_confirm(confirm: str) -> None:
    if confirm != "yes":
        raise HTTPException(400, "لازم تأكيد الاستعادة (confirm=yes)")


class BackupSettingsIn(BaseModel):
    backup_dir: str
    auto_enabled: bool = True
    auto_time: str = "02:00"
    retention: int = 14


@router.put("/settings")
def save_settings(body: BackupSettingsIn, user: User = Depends(admin_only)):
    """تغيير مكان النسخ الاحتياطية ومواعيدها من الواجهة (بيسري فورًا، من غير تعديل .env)."""
    try:
        st = svc.update_settings(directory=body.backup_dir, auto_enabled=body.auto_enabled,
                                 auto_time=body.auto_time, retention=body.retention)
    except svc.BackupError as e:
        _fail(e)
    _audit(user.user_id, "BackupSettings", st["backup_dir"])
    return {**st, "backups": svc.list_backups(), "message": "تم حفظ إعدادات النسخ الاحتياطي"}


@router.get("/status")
def backup_status(_: User = Depends(admin_only)):
    """حالة النسخ التلقائي + قايمة النسخ المحفوظة في مجلد النسخ الاحتياطية."""
    return {**svc.status(), "backups": svc.list_backups()}


@router.get("")
def create_and_download(user: User = Depends(admin_only)):
    """نسخة يدوية بنقرة واحدة: بتتحفظ في مجلد النسخ وبتتنزّل كملف ZIP."""
    try:
        path = svc.create_backup("manual")
    except svc.BackupError as e:
        _fail(e)
    _audit(user.user_id, "BackupCreate", path.name)
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.post("/run")
def create_only(user: User = Depends(admin_only)):
    """نسخة يدوية بتتحفظ في مجلد النسخ بس (من غير تنزيل)."""
    try:
        path = svc.create_backup("manual")
    except svc.BackupError as e:
        _fail(e)
    _audit(user.user_id, "BackupCreate", path.name)
    return {"ok": True, "name": path.name, "size": path.stat().st_size, "message": "تم حفظ النسخة الاحتياطية في مجلد النسخ"}


@router.get("/download/{name}")
def download_saved(name: str, _: User = Depends(admin_only)):
    try:
        path = svc.backup_path_for(name)
    except svc.BackupError as e:
        _fail(e)
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.post("/restore")
def restore_uploaded(file: UploadFile = File(...), confirm: str = Form(""), user: User = Depends(admin_only)):
    """استعادة من ملف ZIP يتم رفعه. بتعمل نسخة أمان تلقائية قبل الاستبدال."""
    _require_confirm(confirm)
    limit = settings.backup_max_upload_mb * 1024 * 1024
    tmp = svc.backup_dir() / f".upload_{uuid.uuid4().hex}.part"
    try:
        size = 0
        with tmp.open("wb") as out:
            while chunk := file.file.read(1 << 20):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"حجم ملف النسخة أكبر من {settings.backup_max_upload_mb} ميجابايت")
                out.write(chunk)
        try:
            result = svc.restore_backup(tmp)
        except svc.BackupError as e:
            _fail(e)
    finally:
        tmp.unlink(missing_ok=True)
    _audit(user.user_id, "BackupRestore", f"upload:{file.filename}")
    return {"ok": True, **result, "message": "تمت استعادة قاعدة البيانات. سجّل الدخول من جديد."}


@router.post("/restore/{name}")
def restore_saved(name: str, confirm: str = Form(""), user: User = Depends(admin_only)):
    """استعادة من نسخة محفوظة في مجلد النسخ على السيرفر."""
    _require_confirm(confirm)
    try:
        result = svc.restore_backup(svc.backup_path_for(name))
    except svc.BackupError as e:
        _fail(e)
    _audit(user.user_id, "BackupRestore", name)
    return {"ok": True, **result, "message": "تمت استعادة قاعدة البيانات. سجّل الدخول من جديد."}
