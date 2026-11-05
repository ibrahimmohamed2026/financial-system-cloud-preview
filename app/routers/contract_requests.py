from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import ContractRequest, Contract, Project, User

router = APIRouter(prefix="/api/contract-requests", tags=["Contract Requests"])

class RequestIn(BaseModel):
    request_no: str = Field(min_length=1, max_length=50)
    request_type: Literal["Customer", "Subcontractor", "Supplier"] = "Customer"
    title: str = Field(min_length=1, max_length=250)
    title_en: str | None = Field(default=None, max_length=250)
    counterparty_name: str = Field(min_length=1, max_length=200)
    counterparty_name_en: str | None = Field(default=None, max_length=200)
    project_id: Optional[int] = None
    estimated_value: Decimal = Field(default=Decimal("0"), ge=0)
    description: Optional[str] = None

class ReviewIn(BaseModel):
    action: Literal["Approve", "Return", "Reject"]
    review_notes: Optional[str] = None

def out(x):
    return {"request_id":x.request_id,"request_no":x.request_no,"request_type":x.request_type,"title":x.title,"title_en":x.title_en,
            "counterparty_name":x.counterparty_name,"counterparty_name_en":x.counterparty_name_en,"project_id":x.project_id,"estimated_value":str(x.estimated_value),
            "description":x.description,"status":x.status,"review_notes":x.review_notes,"created_by":x.created_by,
            "created_at":x.created_at,"reviewed_by":x.reviewed_by,"reviewed_at":x.reviewed_at}

@router.get("")
def list_requests(status: Optional[str] = None, q: Optional[str] = None,
                  _: User = Depends(require_permission("ContractRequests", "View")), db: Session = Depends(get_db)):
    stmt=select(ContractRequest)
    if status: stmt=stmt.where(ContractRequest.status==status)
    if q:
        like=f"%{q.strip()}%"
        stmt=stmt.where((ContractRequest.request_no.ilike(like)) | (ContractRequest.title.ilike(like)) | (ContractRequest.title_en.ilike(like)) | (ContractRequest.counterparty_name.ilike(like)) | (ContractRequest.counterparty_name_en.ilike(like)))
    rows=db.scalars(stmt.order_by(ContractRequest.request_id.desc()).limit(500)).all()
    return {"items":[out(x) for x in rows],"total":len(rows)}

@router.get("/projects")
def request_projects(_: User = Depends(require_permission("ContractRequests", "Add")), db: Session = Depends(get_db)):
    """مشروعات نشطة للاختيار من شاشة طلب التعاقد بدل إدخال رقم مشروع غير موجود."""
    return [{"project_id": p.project_id, "name_ar": p.name_ar} for p in db.scalars(
        select(Project).where(Project.is_active.is_(True)).order_by(Project.name_ar))]

@router.post("", status_code=201)
def create_request(body: RequestIn, user: User = Depends(require_permission("ContractRequests", "Add")), db: Session = Depends(get_db)):
    if body.project_id is not None:
        project = db.get(Project, body.project_id)
        if project is None or not project.is_active:
            raise HTTPException(422, "المشروع المحدد غير موجود أو غير نشط؛ اختر مشروعًا من القائمة")
    if db.scalar(select(ContractRequest.request_id).where(ContractRequest.request_no==body.request_no)):
        raise HTTPException(409,"رقم طلب التعاقد مستخدم بالفعل")
    x=ContractRequest(**body.model_dump(),created_by=user.user_id,status="Draft")
    db.add(x)
    try:
        db.flush(); write_audit(db,user.user_id,"Create","ContractRequests",x.request_id,new=out(x)); db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409,"تعذر حفظ الطلب: رقم الطلب مستخدم بالفعل أو توجد بيانات مرتبطة غير صالحة")
    db.refresh(x)
    return out(x)

@router.post("/{request_id}/submit")
def submit_request(request_id:int,user:User=Depends(require_permission("ContractRequests","Edit")),db:Session=Depends(get_db)):
    x=db.get(ContractRequest,request_id)
    if not x: raise HTTPException(404,"طلب التعاقد غير موجود")
    if x.status not in ("Draft","Returned"): raise HTTPException(409,"لا يمكن إرسال الطلب بهذه الحالة")
    x.status="Pending"; x.review_notes=None
    write_audit(db,user.user_id,"Submit","ContractRequests",x.request_id,new=out(x)); db.commit(); db.refresh(x)
    return out(x)

@router.post("/{request_id}/review")
def review_request(request_id:int,body:ReviewIn,user:User=Depends(require_permission("ContractRequests","Approve")),db:Session=Depends(get_db)):
    x=db.get(ContractRequest,request_id)
    if not x: raise HTTPException(404,"طلب التعاقد غير موجود")
    if x.status!="Pending": raise HTTPException(409,"الطلب ليس قيد المراجعة")
    x.status={"Approve":"Approved","Return":"Returned","Reject":"Rejected"}[body.action]
    x.review_notes=body.review_notes; x.reviewed_by=user.user_id; x.reviewed_at=datetime.utcnow()
    write_audit(db,user.user_id,body.action,"ContractRequests",x.request_id,new=out(x)); db.commit(); db.refresh(x)
    return out(x)

@router.post("/{request_id}/create-contract", status_code=201)
def create_contract_from_request(request_id:int,contract_no:Optional[str]=None,title:Optional[str]=None,title_en:Optional[str]=None,start_date:Optional[str]=None,end_date:Optional[str]=None,
    user:User=Depends(require_permission("Contracts","Add")),db:Session=Depends(get_db)):
    x=db.get(ContractRequest,request_id)
    if not x: raise HTTPException(404,"طلب التعاقد غير موجود")
    if x.status!="Approved": raise HTTPException(409,"لا يمكن إنشاء عقد إلا من طلب تعاقد معتمد")
    if db.scalar(select(Contract.contract_id).where(Contract.request_id==request_id)): raise HTTPException(409,"تم إنشاء عقد من هذا الطلب بالفعل")
    from datetime import date
    def parsed(v): return date.fromisoformat(v) if v else None
    c=Contract(request_id=request_id,contract_no=f"CT-PENDING-{uuid4().hex}",title=title or x.title,title_en=title_en or x.title_en,client_name=x.counterparty_name,client_name_en=x.counterparty_name_en,project_id=x.project_id,
        start_date=parsed(start_date),end_date=parsed(end_date),original_value=x.estimated_value,status="Draft",notes=f"تم إنشاؤه من طلب التعاقد {x.request_no}",created_by=user.user_id)
    db.add(c); db.flush(); c.contract_no=f"CT-{date.today().year}-{c.contract_id:06d}"
    write_audit(db,user.user_id,"CreateFromRequest","Contracts",c.contract_id,new={"request_id":request_id,"contract_no":c.contract_no})
    db.commit(); db.refresh(c)
    return {"contract_id":c.contract_id,"contract_no":c.contract_no,"request_id":request_id,"status":c.status,"message":"تم إنشاء العقد كمسودة؛ يلزم إرساله واعتماده بشكل مستقل قبل التفعيل"}
