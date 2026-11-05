from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission, write_audit, get_current_user, has_permission
from ..models import (Contract, ContractAddendum, ContractItem, ItemCatalog, ProgressBilling, User, ContractSettlement,
                      ContractDeductionRule, ContractAccountingConfig, ContractChangeOrder, ContractAttachment,
                      TechnicalSettlementEstimate, ContractSettlementItem, TechnicalSettlementEstimateItem)
from ..contract_deletion import delete_settlement_tree, require_admin
from .contract_erp import leaf_account_or_422

router = APIRouter(prefix="/api/contracts", tags=["Contracts & Technical Office"])
D0 = Decimal("0.00")

class ContractCreateItem(BaseModel):
    catalog_item_id: int = Field(gt=0)
    description: str = Field(default="", max_length=500)
    unit: Optional[str] = Field(default=None, max_length=30)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    project_id: Optional[int] = None

class ContractCreateDeductionRule(BaseModel):
    settlement_side: Literal["Customer", "Subcontractor"]
    code: str = Field(min_length=1, max_length=50)
    name_ar: str = Field(min_length=1, max_length=150)
    calculation_type: Literal["Percent", "Fixed"] = "Percent"
    rate: Decimal = Field(default=Decimal("0"), ge=0)
    base_type: Literal["CurrentWork", "CumulativeWork", "RemainingContract"] = "CurrentWork"
    posting_side: Literal["Debit", "Credit"]
    cap_amount: Optional[Decimal] = Field(default=None, ge=0)
    gl_account_id: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0

class ContractActivationIn(BaseModel):
    # Full rule set reviewed by accounting; omitted means preserve existing rules.
    deduction_rules: list[ContractCreateDeductionRule] | None = Field(default=None, max_length=200)

class ContractIn(BaseModel):
    contract_no: Optional[str] = Field(default=None, max_length=50)
    title: str = Field(min_length=1, max_length=250)
    client_name: str = Field(min_length=1, max_length=200)
    project_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_value: Decimal = Field(default=D0, ge=0)
    status: str = Field(default="Draft", max_length=30)
    notes: Optional[str] = None
    items: list[ContractCreateItem] = Field(default_factory=list, max_length=500)
    deduction_rules: list[ContractCreateDeductionRule] = Field(default_factory=list, max_length=200)
    @model_validator(mode="after")
    def dates_valid(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("تاريخ نهاية العقد يجب ألا يسبق تاريخ البداية")
        return self

class AddendumIn(BaseModel):
    addendum_no: str = Field(min_length=1, max_length=50)
    addendum_date: date
    description: str = Field(min_length=1, max_length=500)
    value_change: Decimal = D0

class BillingIn(BaseModel):
    billing_no: str = Field(min_length=1, max_length=50)
    billing_date: date
    work_value: Decimal = Field(ge=0)
    retention_amount: Decimal = Field(default=D0, ge=0)
    advance_deduction: Decimal = Field(default=D0, ge=0)
    other_deductions: Decimal = Field(default=D0, ge=0)
    status: str = Field(default="Draft", max_length=30)
    notes: Optional[str] = None
    @model_validator(mode="after")
    def deductions_valid(self):
        if self.retention_amount + self.advance_deduction + self.other_deductions > self.work_value:
            raise ValueError("إجمالي الخصومات لا يمكن أن يتجاوز قيمة الأعمال")
        return self

def _contract(c):
    return {"contract_id":c.contract_id,"request_id":getattr(c,"request_id",None),"contract_no":c.contract_no,"title":c.title,"client_name":c.client_name,
            "project_id":c.project_id,"start_date":c.start_date,"end_date":c.end_date,"original_value":str(c.original_value),
            "status":c.status,"notes":c.notes,"created_at":c.created_at}
def _addendum(a):
    return {"addendum_id":a.addendum_id,"contract_id":a.contract_id,"addendum_no":a.addendum_no,
            "addendum_date":a.addendum_date,"description":a.description,"value_change":str(a.value_change)}
def _billing(b):
    return {"billing_id":b.billing_id,"contract_id":b.contract_id,"billing_no":b.billing_no,"billing_date":b.billing_date,
            "work_value":str(b.work_value),"retention_amount":str(b.retention_amount),"advance_deduction":str(b.advance_deduction),
            "other_deductions":str(b.other_deductions),"net_amount":str(b.net_amount),"status":b.status,"notes":b.notes}

@router.get("")
def list_contracts(q: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                   _: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    stmt = select(Contract).where(func.lower(Contract.status) == "active")
    count = select(func.count()).select_from(Contract).where(func.lower(Contract.status) == "active")
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Contract.contract_no.ilike(like)) | (Contract.title.ilike(like)) | (Contract.client_name.ilike(like)))
        count = count.where((Contract.contract_no.ilike(like)) | (Contract.title.ilike(like)) | (Contract.client_name.ilike(like)))
    rows = db.scalars(stmt.order_by(Contract.contract_id.desc()).offset(skip).limit(limit)).all()
    return {"items":[_contract(x) for x in rows],"total":db.scalar(count) or 0}

@router.post("", status_code=201)
def create_contract(body: ContractIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    prepared_items = []
    for line in body.items:
        catalog = db.get(ItemCatalog, line.catalog_item_id)
        if not catalog or not catalog.is_active:
            raise HTTPException(422, f"البند المركزي {line.catalog_item_id} غير موجود أو غير نشط")
        account = leaf_account_or_422(db, catalog.account_id, "حساب البند: ")
        prepared_items.append((line, catalog, account))
    prepared_rules = []
    seen_rules = set()
    for rule in body.deduction_rules:
        key = (rule.settlement_side, rule.code.strip().casefold())
        if key in seen_rules:
            raise HTTPException(422, f"كود الخصم {rule.code} مكرر لنفس نوع المستخلص")
        seen_rules.add(key)
        if rule.gl_account_id:
            leaf_account_or_422(db, rule.gl_account_id, "حساب الخصم: ")
        data = rule.model_dump()
        data["code"] = rule.code.strip()
        data["name_ar"] = rule.name_ar.strip()
        prepared_rules.append(data)
    values = body.model_dump(exclude={"items", "deduction_rules"})
    # New contracts await accounting review; the reviewer activates them after checking deductions.
    values["status"] = "PendingEngineering"
    values["contract_no"] = f"CT-PENDING-{uuid4().hex}"
    c = Contract(**values, created_by=user.user_id)
    db.add(c); db.flush(); c.contract_no = f"CT-{date.today().year}-{c.contract_id:06d}"
    write_audit(db,user.user_id,"Create","Contracts",c.contract_id,new=_contract(c))
    for number, (line, catalog, account) in enumerate(prepared_items, start=1):
        item = ContractItem(contract_id=c.contract_id, catalog_item_id=catalog.catalog_item_id,
            account_id=account.account_id, project_id=line.project_id or c.project_id,
            item_no=str(number), description=(line.description or "").strip() or catalog.name,
            unit=(line.unit or catalog.unit or "وحدة").strip(), quantity=line.quantity,
            unit_price=line.unit_price)
        db.add(item); db.flush()
        write_audit(db,user.user_id,"Create","ContractItems",item.item_id,new={
            "contract_id":c.contract_id,"item_no":item.item_no,"catalog_item_id":item.catalog_item_id,
            "account_id":item.account_id,"description":item.description,"unit":item.unit,
            "quantity":str(item.quantity),"unit_price":str(item.unit_price)})
    for rule_data in prepared_rules:
        rule = ContractDeductionRule(contract_id=c.contract_id, **rule_data)
        db.add(rule); db.flush()
        write_audit(db, user.user_id, "Create", "ContractDeductionRules", rule.rule_id, new={
            "contract_id": c.contract_id, **rule_data,
            "rate": str(rule.rate), "cap_amount": str(rule.cap_amount) if rule.cap_amount is not None else None})
    db.commit(); db.refresh(c)
    return _contract(c)

@router.put("/{contract_id}")
def update_contract(contract_id: int, body: ContractIn, user: User = Depends(require_permission("Contracts", "Edit")), db: Session = Depends(get_db)):
    c = db.get(Contract, contract_id)
    if not c:
        raise HTTPException(404, "العقد غير موجود")
    if body.contract_no is not None and body.contract_no != c.contract_no:
        raise HTTPException(409, "رقم العقد يُنشأ تلقائيًا ولا يمكن تغييره")
    old = _contract(c)
    values = body.model_dump(exclude={"items", "deduction_rules"})
    values.pop("contract_no", None)
    requested_status = values.pop("status", None)
    if "status" in body.model_fields_set and requested_status != c.status:
        raise HTTPException(409, "تغيير حالة العقد يتم فقط من خلال إجراءات دورة الاعتماد")
    for key, value in values.items():
        setattr(c, key, value)
    write_audit(db, user.user_id, "Update", "Contracts", c.contract_id, old=old, new=body.model_dump())
    db.commit(); db.refresh(c)
    return _contract(c)


@router.get("/review-queue")
def contract_review_queue(_: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Contract).where(func.lower(Contract.status).in_(("draft", "pendingapproval", "pendingengineering", "pendingfinancial", "returned", "rejected"))).order_by(Contract.contract_id.desc()).limit(500)).all()
    return {"items": [_contract(x) for x in rows], "total": len(rows)}

@router.post("/{contract_id}/submit")
def submit_contract(contract_id: int, user: User = Depends(require_permission("Contracts", "Edit")), db: Session = Depends(get_db)):
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404, "العقد غير موجود")
    if c.status.lower() not in ("draft", "returned"):
        raise HTTPException(409, "لا يمكن إرسال العقد للمراجعة بهذه الحالة")
    old = _contract(c); c.status = "PendingEngineering"
    write_audit(db, user.user_id, "SubmitForApproval", "Contracts", c.contract_id, old=old, new=_contract(c))
    db.commit(); db.refresh(c); return _contract(c)

@router.post("/{contract_id}/engineering-approve")
def engineering_approve_contract(contract_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not has_permission(db, user.user_id, "Contracts", "EngineeringApprove"):
        raise HTTPException(403, "ليس لديك صلاحية الاعتماد الهندسي للعقود")
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404, "العقد غير موجود")
    if c.status.lower() not in ("pendingengineering", "pendingapproval"):
        raise HTTPException(409, "العقد ليس بانتظار الاعتماد الهندسي")
    old = _contract(c); c.status = "PendingFinancial"
    write_audit(db, user.user_id, "EngineeringApprove", "Contracts", c.contract_id, old=old, new=_contract(c))
    db.commit(); db.refresh(c); return _contract(c)

@router.post("/{contract_id}/approve")
def approve_contract(contract_id: int, body: ContractActivationIn | None = None,
                     user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not has_permission(db, user.user_id, "Contracts", "FinancialApprove"):
        raise HTTPException(403, "ليس لديك صلاحية الاعتماد المالي للعقود")
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404, "العقد غير موجود")
    if c.status.lower() != "pendingfinancial":
        raise HTTPException(409, "يجب إتمام الاعتماد الهندسي أولًا قبل الاعتماد المالي")
    if body and body.deduction_rules is not None:
        current = db.scalars(select(ContractDeductionRule).where(ContractDeductionRule.contract_id == contract_id)).all()
        current_by_key = {(r.settlement_side, r.code.casefold()): r for r in current}
        incoming = {}
        for rule in body.deduction_rules:
            key = (rule.settlement_side, rule.code.strip().casefold())
            if key in incoming:
                raise HTTPException(422, f"كود الخصم {rule.code} مكرر لنفس نوع المستخلص")
            if rule.gl_account_id:
                leaf_account_or_422(db, rule.gl_account_id, "حساب الخصم: ")
            data = rule.model_dump()
            data["code"] = rule.code.strip(); data["name_ar"] = rule.name_ar.strip()
            incoming[key] = data
        for key, existing in current_by_key.items():
            if key not in incoming:
                write_audit(db, user.user_id, "DeleteDuringActivation", "ContractDeductionRules", existing.rule_id,
                            old={"contract_id": contract_id, "code": existing.code, "name_ar": existing.name_ar}, new=None)
                db.delete(existing)
        for key, data in incoming.items():
            existing = current_by_key.get(key)
            if existing:
                old_rule = {k: getattr(existing, k) for k in data}
                for k, value in data.items(): setattr(existing, k, value)
                write_audit(db, user.user_id, "AccountingReview", "ContractDeductionRules", existing.rule_id,
                            old=old_rule, new={**data, "rate": str(data["rate"])})
            else:
                rule = ContractDeductionRule(contract_id=contract_id, **data)
                db.add(rule); db.flush()
                write_audit(db, user.user_id, "AddDuringActivation", "ContractDeductionRules", rule.rule_id,
                            new={"contract_id": contract_id, **data, "rate": str(data["rate"])})
    old = _contract(c); c.status = "Active"
    write_audit(db, user.user_id, "ApproveAndActivate", "Contracts", c.contract_id, old=old, new=_contract(c))
    db.commit(); db.refresh(c); return _contract(c)

@router.post("/{contract_id}/return")
def return_contract(contract_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404, "العقد غير موجود")
    action = "FinancialApprove" if c.status.lower() == "pendingfinancial" else "EngineeringApprove"
    if not has_permission(db, user.user_id, "Contracts", action):
        raise HTTPException(403, "ليس لديك صلاحية إعادة العقد للتعديل")
    if c.status.lower() not in ("pendingengineering", "pendingfinancial", "pendingapproval"):
        raise HTTPException(409, "العقد ليس بانتظار الاعتماد")
    old = _contract(c); c.status = "Returned"
    write_audit(db, user.user_id, "ReturnForChanges", "Contracts", c.contract_id, old=old, new=_contract(c))
    db.commit(); db.refresh(c); return _contract(c)

@router.get("/{contract_id}")
def contract_detail(contract_id: int, _: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404,"العقد غير موجود")
    add = db.scalars(select(ContractAddendum).where(ContractAddendum.contract_id==contract_id).order_by(ContractAddendum.addendum_date.desc())).all()
    bills = db.scalars(select(ProgressBilling).where(ProgressBilling.contract_id==contract_id).order_by(ProgressBilling.billing_date.desc())).all()
    return {"contract":_contract(c),"addendums":[_addendum(x) for x in add],"billings":[_billing(x) for x in bills],
            "amended_value":str(c.original_value + sum((x.value_change for x in add),D0)),
            "billed_value":str(sum((x.work_value for x in bills if x.status.lower() not in ("cancelled","canceled")),D0))}

@router.post("/{contract_id}/addendums", status_code=201)
def create_addendum(contract_id: int, body: AddendumIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    c=db.get(Contract,contract_id)
    if not c: raise HTTPException(404,"العقد غير موجود")
    a=ContractAddendum(contract_id=contract_id,**body.model_dump(),created_by=user.user_id)
    db.add(a); db.flush(); write_audit(db,user.user_id,"Create","ContractAddendums",a.addendum_id,new=_addendum(a)); db.commit(); db.refresh(a)
    return _addendum(a)

@router.post("/{contract_id}/billings", status_code=201)
def create_billing(contract_id: int, body: BillingIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    contract = db.get(Contract,contract_id)
    if not contract: raise HTTPException(404,"العقد غير موجود")
    if contract.status.lower() != "active": raise HTTPException(409,"لا يمكن إنشاء مستخلص إلا لعقد حالته Active")
    if db.scalar(select(ContractItem.item_id).where(ContractItem.contract_id==contract_id)):
        raise HTTPException(409,"هذا العقد مرتبط بجدول كميات فني؛ أنشئ المستخلص من شاشة المكتب الفني وحدد كميات البنود لمنع تكرار الأعمال.")
    net=body.work_value-body.retention_amount-body.advance_deduction-body.other_deductions
    b=ProgressBilling(contract_id=contract_id,**body.model_dump(),net_amount=net,created_by=user.user_id)
    db.add(b); db.flush(); write_audit(db,user.user_id,"Create","ProgressBillings",b.billing_id,new=_billing(b)); db.commit(); db.refresh(b)
    return _billing(b)


@router.delete("/{contract_id}/billings/{billing_id}", status_code=204)
def delete_billing(contract_id: int, billing_id: int, cascade: bool = False,
                   user: User = Depends(require_permission("Contracts", "Delete")), db: Session = Depends(get_db)):
    billing = db.scalar(select(ProgressBilling).where(
        ProgressBilling.billing_id == billing_id, ProgressBilling.contract_id == contract_id).with_for_update())
    if not billing: raise HTTPException(404, "مستخلص الأعمال غير موجود")
    if cascade: require_admin(db, user.user_id)
    elif billing.status not in ("Draft", "Cancelled"):
        raise HTTPException(409, "الحذف متاح للمسودة أو الملغي فقط؛ استخدم الحذف العام كمسؤول نظام إذا كان مطلوبًا")
    write_audit(db, user.user_id, "Delete" if not cascade else "DeleteCascade", "ProgressBillings",
                billing_id, old=_billing(billing), new=None)
    db.delete(billing); db.commit()


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, cascade: bool = False,
                    user: User = Depends(require_permission("Contracts", "Delete")), db: Session = Depends(get_db)):
    """Delete only an unapproved, unused contract with no financial/technical history."""
    c = db.get(Contract, contract_id)
    if not c: raise HTTPException(404, "العقد غير موجود")
    if cascade:
        require_admin(db, user.user_id)
        old = _contract(c)
        settlement_rows = db.scalars(select(ContractSettlement).where(ContractSettlement.contract_id == contract_id)).all()
        for settlement in settlement_rows:
            delete_settlement_tree(db, settlement, user.user_id)
        for estimate in db.scalars(select(TechnicalSettlementEstimate).where(TechnicalSettlementEstimate.contract_id == contract_id)).all():
            for line in db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id == estimate.estimate_id)).all(): db.delete(line)
            write_audit(db, user.user_id, "DeleteCascade", "TechnicalSettlementEstimates", estimate.estimate_id,
                        {"estimate_no": estimate.estimate_no, "status": estimate.status}, None)
            db.delete(estimate)
        for attachment in db.scalars(select(ContractAttachment).where(ContractAttachment.contract_id == contract_id)).all(): db.delete(attachment)
        for model, column in ((ContractItem, ContractItem.contract_id), (ContractAddendum, ContractAddendum.contract_id),
                (ProgressBilling, ProgressBilling.contract_id), (ContractDeductionRule, ContractDeductionRule.contract_id),
                (ContractAccountingConfig, ContractAccountingConfig.contract_id), (ContractChangeOrder, ContractChangeOrder.contract_id)):
            for row in db.scalars(select(model).where(column == contract_id)).all(): db.delete(row)
        db.flush()
        write_audit(db, user.user_id, "DeleteCascade", "Contracts", contract_id, old=old,
                    new={"deleted_settlements": len(settlement_rows)})
        db.delete(c); db.commit()
        return None
    if (c.status or "").lower() not in ("draft", "returned", "rejected"):
        raise HTTPException(409, "لا يمكن حذف عقد نشط أو معتمد؛ أوقف استخدامه وفق دورة الاعتماد بدلًا من حذف تاريخه")
    checks = [
        (ContractSettlement, ContractSettlement.contract_id, "مستخلصات مالية"),
        (TechnicalSettlementEstimate, TechnicalSettlementEstimate.contract_id, "مستخلصات فنية"),
        (ContractItem, ContractItem.contract_id, "بنود فنية"),
        (ContractAddendum, ContractAddendum.contract_id, "ملاحق عقد"),
        (ProgressBilling, ProgressBilling.contract_id, "مستخلصات أعمال قديمة"),
        (ContractDeductionRule, ContractDeductionRule.contract_id, "قواعد خصم"),
        (ContractAccountingConfig, ContractAccountingConfig.contract_id, "إعدادات محاسبية"),
        (ContractChangeOrder, ContractChangeOrder.contract_id, "أوامر تغييرية"),
        (ContractAttachment, ContractAttachment.contract_id, "مرفقات"),
    ]
    used = [label for model, col, label in checks if db.scalar(select(model).where(col == contract_id).limit(1)) is not None]
    if used: raise HTTPException(409, "لا يمكن حذف العقد لوجود بيانات مرتبطة به: " + "، ".join(used) + ". احذف/عالج البيانات التابعة وفق صلاحياتها أولًا.")
    old = _contract(c)
    write_audit(db, user.user_id, "Delete", "Contracts", contract_id, old=old, new=None)
    db.delete(c); db.commit()
