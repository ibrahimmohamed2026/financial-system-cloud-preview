from datetime import datetime
from urllib.parse import quote
from pathlib import Path
import mimetypes

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission, write_audit, get_current_user, has_permission
from ..models import Contract, ContractAttachment, ContractSettlement, User

router = APIRouter(prefix="/api", tags=["Contract and settlement attachments"])
MAX_FILE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".zip", ".rar"}
CATEGORIES = {"Contract", "CommercialRegister", "TaxCard", "Identity", "CompanyProfile", "BankDetails", "AssignmentLetter", "Quotation", "Invoice", "QuantitySurvey", "AcceptanceMinutes", "Other"}

def _validate_file_signature(ext: str, raw: bytes) -> None:
    signatures = {
        ".pdf": lambda b: b.startswith(b"%PDF-"),
        ".png": lambda b: b.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": lambda b: b.startswith(b"\xff\xd8\xff"),
        ".jpeg": lambda b: b.startswith(b"\xff\xd8\xff"),
        ".webp": lambda b: len(b) >= 12 and b.startswith(b"RIFF") and b[8:12] == b"WEBP",
        ".doc": lambda b: b.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
        ".xls": lambda b: b.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"),
        ".docx": lambda b: b.startswith(b"PK\x03\x04"),
        ".xlsx": lambda b: b.startswith(b"PK\x03\x04"),
        ".zip": lambda b: b.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
        ".rar": lambda b: b.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")),
        ".csv": lambda b: b"\x00" not in b,
        ".txt": lambda b: b"\x00" not in b,
    }
    check = signatures.get(ext)
    if check and not check(raw):
        raise HTTPException(415, "محتوى الملف لا يطابق امتداده")

def _out(x):
    return {"attachment_id": x.attachment_id, "contract_id": x.contract_id, "settlement_id": x.settlement_id,
            "category": x.category, "original_filename": x.original_filename, "content_type": x.content_type,
            "size_bytes": x.size_bytes, "notes": x.notes, "uploaded_at": x.uploaded_at, "uploaded_by": x.uploaded_by}

def _check_parent(db: Session, kind: str, parent_id: int):
    if kind == "contracts":
        parent = db.get(Contract, parent_id)
        if not parent: raise HTTPException(404, "العقد غير موجود")
    else:
        parent = db.get(ContractSettlement, parent_id)
        if not parent: raise HTTPException(404, "المستخلص غير موجود")
    return parent

def _permission(kind: str, action: str):
    return require_permission("Contracts" if kind == "contracts" else "ContractSettlements", action)

def _list(kind: str, parent_id: int, db: Session):
    field = ContractAttachment.contract_id if kind == "contracts" else ContractAttachment.settlement_id
    rows = db.scalars(select(ContractAttachment).where(field == parent_id).order_by(ContractAttachment.uploaded_at.desc(), ContractAttachment.attachment_id.desc())).all()
    return {"items": [_out(x) for x in rows], "total": len(rows)}

@router.get("/contracts/{contract_id}/attachments")
def list_contract_attachments(contract_id: int, user: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    _check_parent(db, "contracts", contract_id)
    return _list("contracts", contract_id, db)

@router.post("/contracts/{contract_id}/attachments", status_code=201)
async def upload_contract_attachment(contract_id: int, file: UploadFile = File(...), category: str = Form("Other"), notes: str = Form(""),
                                     user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    _check_parent(db, "contracts", contract_id)
    return await _save("contracts", contract_id, file, category, notes, user, db)

@router.get("/contracts-erp/settlements/{settlement_id}/attachments")
def list_settlement_attachments(settlement_id: int, user: User = Depends(require_permission("ContractSettlements", "View")), db: Session = Depends(get_db)):
    _check_parent(db, "settlements", settlement_id)
    return _list("settlements", settlement_id, db)

@router.post("/contracts-erp/settlements/{settlement_id}/attachments", status_code=201)
async def upload_settlement_attachment(settlement_id: int, file: UploadFile = File(...), category: str = Form("Other"), notes: str = Form(""),
                                       user: User = Depends(require_permission("ContractSettlements", "Add")), db: Session = Depends(get_db)):
    _check_parent(db, "settlements", settlement_id)
    return await _save("settlements", settlement_id, file, category, notes, user, db)

async def _save(kind: str, parent_id: int, file: UploadFile, category: str, notes: str, user: User, db: Session):
    name = Path(file.filename or "").name.strip()
    ext = Path(name).suffix.lower()
    if not name or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "صيغة الملف غير مدعومة. الصيغ المسموحة: PDF، الصور، Word، Excel، CSV، TXT، ZIP، RAR")
    if category not in CATEGORIES: raise HTTPException(422, "نوع المستند غير صحيح")
    raw = await file.read(MAX_FILE_BYTES + 1)
    if not raw: raise HTTPException(422, "الملف فارغ")
    if len(raw) > MAX_FILE_BYTES: raise HTTPException(413, "الحد الأقصى لحجم الملف 20 ميجابايت")
    _validate_file_signature(ext, raw)
    # Do not trust the browser-supplied Content-Type header.
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    obj = ContractAttachment(contract_id=parent_id if kind == "contracts" else None,
        settlement_id=parent_id if kind == "settlements" else None, category=category, original_filename=name[:255],
        content_type=mime[:120], size_bytes=len(raw), file_content=raw, notes=(notes.strip()[:500] or None), uploaded_by=user.user_id)
    db.add(obj); db.flush()
    write_audit(db, user.user_id, "UploadAttachment", "ContractAttachment", obj.attachment_id,
                new={"parent_type": kind, "parent_id": parent_id, "filename": obj.original_filename, "category": category, "size_bytes": len(raw)})
    db.commit(); db.refresh(obj)
    return _out(obj)

@router.get("/contract-attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.get(ContractAttachment, attachment_id)
    if not obj: raise HTTPException(404, "المرفق غير موجود")
    # المستخلصات لها صلاحية مستقلة؛ لا نكتفي بصلاحية العقود عند تنزيل مرفق مستخلص.
    screen = "Contracts" if obj.contract_id is not None else "ContractSettlements"
    if not has_permission(db, user.user_id, screen, "View"):
        raise HTTPException(403, "ليس لديك صلاحية عرض هذا المرفق")
    filename = quote(obj.original_filename)
    return Response(content=bytes(obj.file_content), media_type=obj.content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}", "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})

@router.delete("/contract-attachments/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.get(ContractAttachment, attachment_id)
    if not obj: raise HTTPException(404, "المرفق غير موجود")
    screen = "Contracts" if obj.contract_id is not None else "ContractSettlements"
    if not has_permission(db, user.user_id, screen, "Edit"):
        raise HTTPException(403, "ليس لديك صلاحية حذف هذا المرفق")
    old = _out(obj); write_audit(db, user.user_id, "DeleteAttachment", "ContractAttachment", obj.attachment_id, old=old)
    db.delete(obj); db.commit()
    return Response(status_code=204)
