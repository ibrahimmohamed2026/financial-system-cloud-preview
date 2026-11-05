"""pg_dump backup endpoints; restricted to system administrators."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from .. import pg_backup_service as svc
from .backup import admin_only, _audit

router=APIRouter(prefix="/admin/backup/pgdump",tags=["PostgreSQL pg_dump Backup"])

def fail(exc: svc.PgBackupError):
    raise HTTPException(500,str(exc)) from exc

@router.get("")
def list_saved(_: object = Depends(admin_only)):
    return svc.status()

@router.post("/run")
def run_now(user=Depends(admin_only)):
    try: path=svc.create_backup()
    except svc.PgBackupError as exc: fail(exc)
    _audit(user.user_id,"PgDumpBackupCreate",path.name)
    return {"ok":True,"name":path.name,"size":path.stat().st_size,"message":"تم إنشاء نسخة PostgreSQL بنجاح"}

@router.get("/download/{name}")
def download(name: str, _: object = Depends(admin_only)):
    if name != name.rsplit("/",1)[-1] or not name.startswith("financial_system_pg_") or not name.endswith(".dump"):
        raise HTTPException(400,"اسم ملف غير صالح")
    path=svc.BACKUP_DIR/name
    if not path.is_file(): raise HTTPException(404,"ملف النسخة غير موجود")
    return FileResponse(path,media_type="application/octet-stream",filename=path.name)
