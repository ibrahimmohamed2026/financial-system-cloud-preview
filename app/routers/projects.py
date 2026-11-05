from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import Check, JournalEntryDetail, Project, TreasuryTransaction, User

SCREEN = "CostCenters"
router = APIRouter(prefix="/projects", tags=["CostCenters"])


class ProjectIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    is_head_office: bool = False
    is_active: bool = True


class ProjectOut(ProjectIn):
    model_config = ConfigDict(from_attributes=True)
    project_id: int


def _get(db: Session, pid: int) -> Project:
    p = db.get(Project, pid)
    if p is None:
        raise HTTPException(404, "المشروع غير موجود")
    return p


@router.get("", response_model=list[ProjectOut])
def list_projects(q: str | None = None, is_active: bool | None = None,
                  _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    stmt = select(Project)
    if q and q.strip():
        stmt = stmt.where(Project.name_ar.ilike(f"%{q.strip()}%"))
    if is_active is not None:
        stmt = stmt.where(Project.is_active.is_(is_active))
    return db.scalars(stmt.order_by(Project.project_id)).all()


@router.get("/lookup", response_model=list[ProjectOut])
def lookup(user: User = Depends(require_permission("JournalBook", "View")), db: Session = Depends(get_db)):
    """قايمة مراكز التكلفة النشطة لاستخدامها في القيود (صلاحية دفتر اليومية)."""
    return db.scalars(select(Project).where(Project.is_active == True).order_by(Project.name_ar)).all()


@router.post("", response_model=ProjectOut, status_code=201)
def create(body: ProjectIn, user: User = Depends(require_permission(SCREEN, "Add")), db: Session = Depends(get_db)):
    p = Project(**body.model_dump())
    db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "الاسم مستخدم قبل كده")
    write_audit(db, user.user_id, "Create", "Projects", p.project_id, None, body.model_dump())
    db.commit()
    return p


@router.put("/{pid}", response_model=ProjectOut)
def update(pid: int, body: ProjectIn, user: User = Depends(require_permission(SCREEN, "Edit")),
           db: Session = Depends(get_db)):
    p = _get(db, pid)
    old = ProjectIn.model_validate(p, from_attributes=True).model_dump()
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "الاسم مستخدم قبل كده")
    write_audit(db, user.user_id, "Update", "Projects", pid, old, body.model_dump())
    db.commit()
    return p


@router.delete("/{pid}", status_code=204)
def delete(pid: int, user: User = Depends(require_permission(SCREEN, "Delete")), db: Session = Depends(get_db)):
    p = _get(db, pid)
    used = sum(db.scalar(select(func.count()).select_from(m).where(m.project_id == pid)) or 0
               for m in (JournalEntryDetail, TreasuryTransaction, Check))
    if used:
        raise HTTPException(status.HTTP_409_CONFLICT, f"المشروع مستخدم في {used} حركة — عطّله بدل الحذف")
    write_audit(db, user.user_id, "Delete", "Projects", pid, {"name_ar": p.name_ar}, None)
    db.delete(p)
    db.commit()
