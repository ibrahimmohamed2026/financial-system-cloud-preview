from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission, write_audit, get_current_user, has_permission
from ..models import (Contract, ContractAddendum, ContractAddendumLine, ContractItem, ItemCatalog, ProgressBilling, User, ContractSettlement,
                      ContractDeductionRule, ContractAccountingConfig, ContractChangeOrder, ContractAttachment,
                      TechnicalSettlementEstimate, ContractSettlementItem, TechnicalSettlementEstimateItem, ContractSettlementSchedule)
from ..contract_deletion import delete_settlement_tree, require_admin
from .contract_erp import leaf_account_or_422

router = APIRouter(prefix="/api/contracts", tags=["Contracts & Technical Office"])
D0 = Decimal("0.00")

def _addendum_line_amount_change(target_quantity, target_unit_price, quantity_delta, new_unit_price):
    """Calculate the signed change in BOQ value for an addendum line."""
    quantity_delta = Decimal(str(quantity_delta))
    new_unit_price = Decimal(str(new_unit_price))
    if target_quantity is None:
        amount = quantity_delta * new_unit_price
    else:
        amount = ((new_unit_price - Decimal(str(target_unit_price))) * Decimal(str(target_quantity))
                  + quantity_delta * new_unit_price)
    return amount.quantize(Decimal("0.01"))


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

class ContractScheduleItemIn(BaseModel):
    label: str | None = Field(default=None, max_length=200)
    period_start: date
    period_end: date
    planned_submission_date: date
    due_date: date
    expected_amount: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.period_end < self.period_start: raise ValueError("نهاية فترة الأعمال يجب ألا تسبق بدايتها")
        if self.due_date < self.planned_submission_date: raise ValueError("موعد الاستحقاق لا يجوز أن يسبق موعد التقديم")
        return self

class ContractIn(BaseModel):
    contract_no: Optional[str] = Field(default=None, max_length=50)
    title: str = Field(min_length=1, max_length=250)
    title_en: str | None = Field(default=None, max_length=250)
    client_name: str = Field(min_length=1, max_length=200)
    client_name_en: str | None = Field(default=None, max_length=200)
    project_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    original_value: Decimal = Field(default=D0, ge=0)
    agreed_statement_count: int | None = Field(default=None, ge=0, le=500)
    statement_distribution_method: Literal["Monthly", "Biweekly", "Milestones", "Manual"] | None = None
    schedule_items: list[ContractScheduleItemIn] = Field(default_factory=list, max_length=500)
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
    addendum_no: str | None = Field(default=None, max_length=50)
    addendum_date: date
    description: str = Field(min_length=1, max_length=500)
    value_change: Decimal = D0

class AddendumLineIn(BaseModel):
    target_item_id: int | None = Field(default=None, gt=0)
    catalog_item_id: int | None = Field(default=None, gt=0)
    account_id: int | None = Field(default=None, gt=0)
    item_no: str | None = Field(default=None, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    unit: str = Field(default="وحدة", max_length=30)
    quantity_delta: Decimal
    unit_price: Decimal = Field(ge=0)
    project_id: int | None = None

    @model_validator(mode="after")
    def nonzero_delta(self):
        if self.quantity_delta == 0:
            raise ValueError("يجب أن تكون كمية التعديل أكبر أو أقل من صفر")
        return self

class AddendumTechnicalDecision(BaseModel):
    decision: Literal["Approve", "Return"]
    notes: str | None = Field(default=None, max_length=2000)

class BillingIn(BaseModel):
    billing_no: str | None = Field(default=None, max_length=50)
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
    return {"contract_id":c.contract_id,"request_id":getattr(c,"request_id",None),"contract_no":c.contract_no,"title":c.title,"title_en":c.title_en,"client_name":c.client_name,"client_name_en":c.client_name_en,
            "project_id":c.project_id,"start_date":c.start_date,"end_date":c.end_date,"original_value":str(c.original_value),
            "agreed_statement_count":getattr(c,"agreed_statement_count",None),"statement_distribution_method":getattr(c,"statement_distribution_method","Manual"),
            "status":c.status,"notes":c.notes,"created_at":c.created_at}
def _addendum(a):
    return {"addendum_id":a.addendum_id,"contract_id":a.contract_id,"addendum_no":a.addendum_no,
            "addendum_date":a.addendum_date,"description":a.description,"value_change":str(a.value_change),
            "status":getattr(a,"status","Approved"),"approved_by":a.approved_by,"approved_at":a.approved_at,
            "technical_reviewed_by":getattr(a,"technical_reviewed_by",None),
            "technical_reviewed_at":getattr(a,"technical_reviewed_at",None),
            "technical_review_notes":getattr(a,"technical_review_notes",None)}
def _billing(b):
    return {"billing_id":b.billing_id,"contract_id":b.contract_id,"billing_no":b.billing_no,"billing_date":b.billing_date,
            "work_value":str(b.work_value),"retention_amount":str(b.retention_amount),"advance_deduction":str(b.advance_deduction),
            "other_deductions":str(b.other_deductions),"net_amount":str(b.net_amount),"status":b.status,"notes":b.notes}


def _build_contract_schedule(body: ContractIn):
    count = body.agreed_statement_count or 0
    if count < 1:
        raise HTTPException(422, "حدد عدد المستخلصات أولاً")
    method = body.statement_distribution_method or "Manual"
    if method == "Manual":
        if len(body.schedule_items) != count:
            raise HTTPException(422, f"أدخل {count} صفًا في جدول المواعيد اليدوي")
        rows = body.schedule_items
    else:
        if not body.start_date or not body.end_date:
            raise HTTPException(422, "حدد تاريخ بداية ونهاية العقد لإنشاء جدول المستخلصات تلقائيًا")
        if body.end_date < body.start_date:
            raise HTTPException(422, "نهاية العقد تسبق بدايته")
        rows = []
        total_days = (body.end_date - body.start_date).days + 1
        if method == "Milestones" and count > total_days:
            raise HTTPException(422, "عدد مراحل التنفيذ أكبر من عدد أيام مدة العقد")
        cursor = body.start_date
        for n in range(1, count + 1):
            if method == "Monthly":
                if cursor > body.end_date:
                    raise HTTPException(422, "مدة العقد لا تكفي لعدد المستخلصات الشهرية المحدد")
                next_month = date(cursor.year + (1 if cursor.month == 12 else 0), 1 if cursor.month == 12 else cursor.month + 1, 1)
                period_end = min(next_month - timedelta(days=1), body.end_date)
            elif method == "Biweekly":
                if cursor > body.end_date:
                    raise HTTPException(422, "مدة العقد لا تكفي لعدد المستخلصات كل أسبوعين المحدد")
                period_end = min(cursor + timedelta(days=13), body.end_date)
            else:
                start_offset = ((n - 1) * total_days) // count
                end_offset = (n * total_days) // count - 1
                cursor = body.start_date + timedelta(days=start_offset)
                period_end = body.start_date + timedelta(days=end_offset)
            rows.append(ContractScheduleItemIn(label=("مرحلة التنفيذ " if method == "Milestones" else "المستخلص ") + str(n),
                period_start=cursor, period_end=period_end, planned_submission_date=period_end + timedelta(days=5),
                due_date=period_end + timedelta(days=35),
                expected_amount=(body.original_value / count).quantize(Decimal("0.01")) if body.original_value else None))
            cursor = period_end + timedelta(days=1)
    if method in ("Monthly", "Biweekly") and rows and body.end_date and rows[-1].period_end < body.end_date:
        raise HTTPException(422, "عدد المستخلصات لا يغطي مدة العقد بالكامل؛ زوّد العدد أو اختر طريقة أخرى")
    previous_end = None
    for n, row in enumerate(rows, start=1):
        if body.start_date and row.period_start < body.start_date or body.end_date and row.period_end > body.end_date:
            raise HTTPException(422, f"فترة المستخلص رقم {n} خارج مدة العقد")
        if previous_end is not None and row.period_start <= previous_end:
            raise HTTPException(422, "فترات المستخلصات اليدوية يجب أن تكون مرتبة وغير متداخلة")
        previous_end = row.period_end
    return rows

def _schedule_out(row):
    return {"schedule_id": row.schedule_id, "contract_id": row.contract_id, "sequence_no": row.sequence_no,
        "label": row.label, "period_start": row.period_start, "period_end": row.period_end,
        "planned_submission_date": row.planned_submission_date, "due_date": row.due_date,
        "expected_amount": str(row.expected_amount) if row.expected_amount is not None else None,
        "status": ("Overdue" if row.status == "Planned" and row.technical_estimate_id is None and row.planned_submission_date < date.today() else row.status), "technical_estimate_id": row.technical_estimate_id}

@router.get("")
def list_contracts(q: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                   _: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    stmt = select(Contract).where(func.lower(Contract.status) == "active")
    count = select(func.count()).select_from(Contract).where(func.lower(Contract.status) == "active")
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Contract.contract_no.ilike(like)) | (Contract.title.ilike(like)) | (Contract.title_en.ilike(like)) | (Contract.client_name.ilike(like)) | (Contract.client_name_en.ilike(like)))
        count = count.where((Contract.contract_no.ilike(like)) | (Contract.title.ilike(like)) | (Contract.client_name.ilike(like)))
    rows = db.scalars(stmt.order_by(Contract.contract_id.desc()).offset(skip).limit(limit)).all()
    return {"items":[_contract(x) for x in rows],"total":db.scalar(count) or 0}

@router.post("", status_code=201)
def create_contract(body: ContractIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    if body.agreed_statement_count is None or body.agreed_statement_count < 1:
        raise HTTPException(422, "يجب تحديد عدد المستخلصات المتفق عليها من 1 إلى 500")
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
    schedule_rows = _build_contract_schedule(body)
    values = body.model_dump(exclude={"items", "deduction_rules", "schedule_items"})
    values["statement_distribution_method"] = body.statement_distribution_method or "Manual"
    # New contracts await accounting review; the reviewer activates them after checking deductions.
    values["status"] = "PendingEngineering"
    values["contract_no"] = f"CT-PENDING-{uuid4().hex}"
    c = Contract(**values, created_by=user.user_id)
    db.add(c); db.flush(); c.contract_no = f"CT-{date.today().year}-{c.contract_id:06d}"
    for n, row in enumerate(schedule_rows, start=1):
        db.add(ContractSettlementSchedule(contract_id=c.contract_id, sequence_no=n, label=row.label, period_start=row.period_start, period_end=row.period_end, planned_submission_date=row.planned_submission_date, due_date=row.due_date, expected_amount=row.expected_amount, status="Planned"))
    write_audit(db,user.user_id,"Create","Contracts",c.contract_id,new=_contract(c))
    for number, (line, catalog, account) in enumerate(prepared_items, start=1):
        item = ContractItem(contract_id=c.contract_id, catalog_item_id=catalog.catalog_item_id,
            account_id=account.account_id, project_id=line.project_id or c.project_id,
            item_no=str(number), description=(line.description or "").strip() or catalog.name,
            unit=(line.unit or catalog.unit or "وحدة").strip(), quantity=line.quantity,
            unit_price=line.unit_price, original_quantity=line.quantity,
            original_unit_price=line.unit_price)
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


@router.get("/{contract_id}/settlement-schedule")
def get_contract_settlement_schedule(contract_id: int,
        _: User = Depends(require_permission("Contracts", "View")), db: Session = Depends(get_db)):
    if not db.get(Contract, contract_id):
        raise HTTPException(404, "العقد غير موجود")
    rows = db.scalars(select(ContractSettlementSchedule).where(
        ContractSettlementSchedule.contract_id == contract_id).order_by(ContractSettlementSchedule.sequence_no)).all()
    return {"items": [_schedule_out(row) for row in rows]}

@router.put("/{contract_id}")
def update_contract(contract_id: int, body: ContractIn, user: User = Depends(require_permission("Contracts", "Edit")), db: Session = Depends(get_db)):
    c = db.get(Contract, contract_id)
    if not c:
        raise HTTPException(404, "العقد غير موجود")
    if body.contract_no is not None and body.contract_no != c.contract_no:
        raise HTTPException(409, "رقم العقد يُنشأ تلقائيًا ولا يمكن تغييره")
    old = _contract(c)
    values = body.model_dump(exclude={"items", "deduction_rules", "schedule_items"})
    values.pop("contract_no", None)
    if values.get("statement_distribution_method") is None:
        values.pop("statement_distribution_method", None)
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
    approved_addenda = [x for x in add if (getattr(x,"status","Approved") or "Approved") == "Approved"]
    addendum_rows = []
    for x in add:
        row = _addendum(x)
        row["lines"] = [{"addendum_line_id":ln.addendum_line_id,"target_item_id":ln.target_item_id,
            "effective_item_id":ln.effective_item_id,"item_no":ln.item_no,"description":ln.description,
            "unit":ln.unit,"quantity_delta":str(ln.quantity_delta),"unit_price":str(ln.unit_price),
            "amount_change":str(ln.amount_change)} for ln in db.scalars(select(ContractAddendumLine).where(
                ContractAddendumLine.addendum_id == x.addendum_id).order_by(ContractAddendumLine.addendum_line_id)).all()]
        addendum_rows.append(row)
    return {"contract":_contract(c),"addendums":addendum_rows,"billings":[_billing(x) for x in bills],
            "amended_value":str(c.original_value + sum((x.value_change for x in approved_addenda),D0)),
            "billed_value":str(sum((x.work_value for x in bills if x.status.lower() not in ("cancelled","canceled")),D0))}

@router.post("/{contract_id}/addendums", status_code=201)
def create_addendum(contract_id: int, body: AddendumIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    c=db.get(Contract,contract_id)
    if not c: raise HTTPException(404,"العقد غير موجود")
    values=body.model_dump(exclude={"addendum_no"})
    a=ContractAddendum(contract_id=contract_id,addendum_no=f"AD-PENDING-{uuid4().hex}",**values,status="Draft",created_by=user.user_id)
    db.add(a); db.flush(); a.addendum_no=f"AD-{body.addendum_date.year}-{a.addendum_id:06d}"
    write_audit(db,user.user_id,"Create","ContractAddendums",a.addendum_id,new=_addendum(a)); db.commit(); db.refresh(a)
    return _addendum(a)

@router.post("/{contract_id}/addendums/{addendum_id}/lines", status_code=201)
def add_addendum_line(contract_id: int, addendum_id: int, body: AddendumLineIn,
        user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    a = db.scalar(select(ContractAddendum).where(ContractAddendum.addendum_id == addendum_id,
        ContractAddendum.contract_id == contract_id).with_for_update())
    if not a: raise HTTPException(404, "ملحق العقد غير موجود")
    if a.status not in ("Draft", "ReturnedForCorrection"):
        raise HTTPException(409, "لا يمكن تعديل بنود الملحق بعد إرساله للمراجعة")
    target = None
    catalog = None
    if body.target_item_id:
        target = db.scalar(select(ContractItem).where(ContractItem.item_id == body.target_item_id,
            ContractItem.contract_id == contract_id).with_for_update())
        if not target: raise HTTPException(422, "البند المستهدف لا يتبع هذا العقد")
        if body.description.strip() != target.description or body.unit.strip() != target.unit:
            raise HTTPException(422, "تعديل بند قائم يغيّر الكمية والسعر فقط؛ لا تغيّر الوصف أو الوحدة حفاظًا على تاريخ القياس")
        if body.quantity_delta < 0:
            used_technical = db.scalar(select(func.coalesce(func.sum(func.coalesce(
                TechnicalSettlementEstimateItem.approved_quantity, TechnicalSettlementEstimateItem.current_quantity)), 0))
                .join(TechnicalSettlementEstimate, TechnicalSettlementEstimate.estimate_id == TechnicalSettlementEstimateItem.estimate_id)
                .where(TechnicalSettlementEstimate.contract_id == contract_id,
                    TechnicalSettlementEstimate.status == "TechnicallyApproved",
                    TechnicalSettlementEstimateItem.contract_item_id == target.item_id)) or 0
            used_financial = db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity), 0))
                .join(ContractSettlement, ContractSettlement.settlement_id == ContractSettlementItem.settlement_id)
                .where(ContractSettlement.contract_id == contract_id,
                    ContractSettlement.status.in_(("Approved", "Posted", "PendingFinalApproval")),
                    ContractSettlement.settlement_id.not_in(select(TechnicalSettlementEstimate.financial_settlement_id).where(
                        TechnicalSettlementEstimate.financial_settlement_id.is_not(None))),
                    ContractSettlementItem.contract_item_id == target.item_id)) or 0
            if Decimal(str(target.quantity)) + body.quantity_delta < Decimal(str(used_technical)) + Decimal(str(used_financial)):
                raise HTTPException(409, "التخفيض سيجعل كمية العقد أقل من الكميات التي سبق اعتمادها في المستخلصات")
        duplicate = db.scalar(select(ContractAddendumLine.addendum_line_id).where(
            ContractAddendumLine.addendum_id == addendum_id,
            ContractAddendumLine.target_item_id == target.item_id).limit(1))
        if duplicate:
            raise HTTPException(409, "لا يمكن تكرار تعديل نفس بند العقد داخل الملحق؛ اجمع التغيير في سطر واحد")
        catalog_item_id = target.catalog_item_id
        account_id = target.account_id
        project_id = body.project_id if body.project_id is not None else target.project_id
        item_no = target.item_no
        description = body.description.strip() or target.description
        unit = body.unit or target.unit
    else:
        if body.quantity_delta < 0:
            raise HTTPException(422, "البند الجديد يجب أن تكون كميته موجبة")
        catalog = db.get(ItemCatalog, body.catalog_item_id) if body.catalog_item_id else None
        if body.catalog_item_id and (not catalog or not catalog.is_active):
            raise HTTPException(422, "البند المركزي المختار غير موجود أو غير نشط")
        selected_account_id = catalog.account_id if catalog else body.account_id
        if not selected_account_id:
            raise HTTPException(422, "اختر حسابًا تفصيليًا من شجرة الحسابات للبند الجديد")
        account = leaf_account_or_422(db, selected_account_id, "حساب البند: ")
        catalog_item_id, account_id = (catalog.catalog_item_id if catalog else None), account.account_id
        project_id = body.project_id if body.project_id is not None else db.get(Contract, contract_id).project_id
        item_no = (body.item_no or "").strip()
        if not item_no:
            suffix = 1
            while True:
                candidate = f"AD{addendum_id}-{suffix}"
                exists_on_contract = db.scalar(select(ContractItem.item_id).where(
                    ContractItem.contract_id == contract_id, ContractItem.item_no == candidate).limit(1))
                exists_in_addendum = db.scalar(select(ContractAddendumLine.addendum_line_id).where(
                    ContractAddendumLine.addendum_id == addendum_id, ContractAddendumLine.item_no == candidate).limit(1))
                if not exists_on_contract and not exists_in_addendum:
                    item_no = candidate
                    break
                suffix += 1
        else:
            duplicate_no = db.scalar(select(ContractItem.item_id).where(
                ContractItem.contract_id == contract_id, ContractItem.item_no == item_no).limit(1))
            duplicate_line_no = db.scalar(select(ContractAddendumLine.addendum_line_id).where(
                ContractAddendumLine.addendum_id == addendum_id, ContractAddendumLine.item_no == item_no).limit(1))
            if duplicate_no or duplicate_line_no:
                raise HTTPException(409, "رقم البند مستخدم بالفعل داخل العقد أو الملحق")
        description, unit = body.description.strip(), body.unit or catalog.unit
    line = ContractAddendumLine(addendum_id=addendum_id, target_item_id=target.item_id if target else None,
        catalog_item_id=catalog_item_id, account_id=account_id, project_id=project_id, item_no=item_no,
        description=description, unit=unit, quantity_delta=body.quantity_delta, unit_price=body.unit_price,
        amount_change=_addendum_line_amount_change(
            Decimal(str(target.quantity)) if target else None,
            Decimal(str(target.unit_price)) if target else None,
            body.quantity_delta, body.unit_price),
        baseline_quantity=Decimal(str(target.quantity)) if target else None,
        baseline_unit_price=Decimal(str(target.unit_price)) if target else None)
    db.add(line)
    write_audit(db, user.user_id, "AddBOQLine", "ContractAddendums", addendum_id,
        new={"target_item_id": line.target_item_id, "item_no": item_no, "quantity_delta": str(line.quantity_delta),
             "unit_price": str(line.unit_price), "amount_change": str(line.amount_change)})
    db.commit(); db.refresh(line)
    return {"addendum_line_id":line.addendum_line_id,"target_item_id":line.target_item_id,"item_no":line.item_no,
        "description":line.description,"unit":line.unit,"quantity_delta":str(line.quantity_delta),
        "unit_price":str(line.unit_price),"amount_change":str(line.amount_change)}

@router.delete("/{contract_id}/addendums/{addendum_id}/lines/{line_id}", status_code=204)
def delete_addendum_line(contract_id: int, addendum_id: int, line_id: int,
        user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    a = db.scalar(select(ContractAddendum).where(ContractAddendum.addendum_id == addendum_id,
        ContractAddendum.contract_id == contract_id).with_for_update())
    if not a: raise HTTPException(404, "ملحق العقد غير موجود")
    if a.status not in ("Draft", "ReturnedForCorrection"):
        raise HTTPException(409, "لا يمكن حذف بند بعد إرسال الملحق للمراجعة")
    line = db.scalar(select(ContractAddendumLine).where(
        ContractAddendumLine.addendum_line_id == line_id,
        ContractAddendumLine.addendum_id == addendum_id).with_for_update())
    if not line: raise HTTPException(404, "بند الملحق غير موجود")
    write_audit(db, user.user_id, "DeleteBOQLine", "ContractAddendums", addendum_id,
        old={"line_id":line.addendum_line_id,"item_no":line.item_no,"quantity_delta":str(line.quantity_delta),
             "unit_price":str(line.unit_price)}, new=None)
    db.delete(line)
    db.commit()


@router.post("/{contract_id}/addendums/{addendum_id}/submit")
def submit_addendum(contract_id: int, addendum_id: int, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    a = db.scalar(select(ContractAddendum).where(ContractAddendum.addendum_id == addendum_id,
        ContractAddendum.contract_id == contract_id).with_for_update())
    if not a: raise HTTPException(404, "ملحق العقد غير موجود")
    if a.status not in ("Draft", "ReturnedForCorrection"): raise HTTPException(409, "حالة الملحق لا تسمح بالإرسال")
    lines = db.scalars(select(ContractAddendumLine).where(ContractAddendumLine.addendum_id == addendum_id)).all()
    if not lines: raise HTTPException(422, "أضف بندًا واحدًا على الأقل قبل إرسال الملحق")
    a.status = "UnderTechnicalReview"
    write_audit(db, user.user_id, "SubmitForTechnicalReview", "ContractAddendums", addendum_id,
        new={"status":a.status,"line_count":len(lines)})
    db.commit(); db.refresh(a)
    return _addendum(a)

@router.post("/{contract_id}/addendums/{addendum_id}/technical-review")
def review_addendum_technical(contract_id: int, addendum_id: int, body: AddendumTechnicalDecision,
        user: User = Depends(require_permission("Contracts", "EngineeringApprove")), db: Session = Depends(get_db)):
    a = db.scalar(select(ContractAddendum).where(ContractAddendum.addendum_id == addendum_id,
        ContractAddendum.contract_id == contract_id).with_for_update())
    if not a: raise HTTPException(404, "ملحق العقد غير موجود")
    if a.status != "UnderTechnicalReview": raise HTTPException(409, "الملحق ليس بانتظار المراجعة الفنية")
    if a.created_by == user.user_id: raise HTTPException(403, "لا يجوز لمُعدّ الملحق مراجعته فنيًا بنفسه")
    if body.decision == "Return":
        if not (body.notes or "").strip(): raise HTTPException(422, "اكتب ملاحظات الإرجاع")
        a.status = "ReturnedForCorrection"
    else:
        a.status = "TechnicallyApproved"
    a.technical_reviewed_by = user.user_id
    a.technical_reviewed_at = datetime.utcnow()
    a.technical_review_notes = (body.notes or "").strip() or None
    write_audit(db, user.user_id, "TechnicalReview" + body.decision, "ContractAddendums", addendum_id,
        new={"status":a.status,"reviewed_by":user.user_id,"reviewed_at":a.technical_reviewed_at,
             "notes":a.technical_review_notes})
    db.commit(); db.refresh(a)
    return _addendum(a)

@router.post("/{contract_id}/addendums/{addendum_id}/approve")
def approve_addendum(contract_id: int, addendum_id: int, user: User = Depends(require_permission("Contracts", "Approve")), db: Session = Depends(get_db)):
    # Serialize all addendum approvals for this contract so concurrent approvals
    # cannot calculate against the same stale contract value / BOQ snapshot.
    contract = db.scalar(select(Contract).where(Contract.contract_id == contract_id).with_for_update())
    if not contract: raise HTTPException(404, "العقد غير موجود")
    a = db.scalar(select(ContractAddendum).where(ContractAddendum.addendum_id == addendum_id,
        ContractAddendum.contract_id == contract_id).with_for_update())
    if not a: raise HTTPException(404, "ملحق العقد غير موجود")
    lines = db.scalars(select(ContractAddendumLine).where(
        ContractAddendumLine.addendum_id == addendum_id).with_for_update()).all()
    # Compatibility: pre-workflow addenda created by the previous release had no BOQ lines.
    if a.status == "Pending" and not lines:
        a.status = "Approved"
        a.approved_by = user.user_id
        a.approved_at = datetime.utcnow()
        write_audit(db, user.user_id, "ApproveLegacyAddendum", "ContractAddendums", a.addendum_id, new=_addendum(a))
        db.commit(); db.refresh(a)
        return _addendum(a)
    if a.status != "TechnicallyApproved":
        raise HTTPException(409, "يجب إتمام المراجعة الفنية قبل الاعتماد الإداري والمالي")
    if not lines: raise HTTPException(409, "لا توجد بنود معتمدة في الملحق")
    applied = []
    for line in lines:
        if line.target_item_id:
            item = db.scalar(select(ContractItem).where(ContractItem.item_id == line.target_item_id,
                ContractItem.contract_id == contract_id).with_for_update())
            if not item: raise HTTPException(409, "البند الأصلي المرتبط بالملحق لم يعد موجودًا")
            if line.baseline_quantity is not None and Decimal(str(item.quantity)) != Decimal(str(line.baseline_quantity)):
                raise HTTPException(409, f"تغيرت كمية البند {item.item_no} بعد إعداد الملحق؛ احذف السطر وأعد إدخاله بالقيمة الحالية")
            if line.baseline_unit_price is not None and Decimal(str(item.unit_price)) != Decimal(str(line.baseline_unit_price)):
                raise HTTPException(409, f"تغير سعر البند {item.item_no} بعد إعداد الملحق؛ احذف السطر وأعد إدخاله بالسعر الحالي")
            next_quantity = Decimal(str(item.quantity)) + Decimal(str(line.quantity_delta))
            used_technical = db.scalar(select(func.coalesce(func.sum(func.coalesce(
                TechnicalSettlementEstimateItem.approved_quantity, TechnicalSettlementEstimateItem.current_quantity)), 0))
                .join(TechnicalSettlementEstimate, TechnicalSettlementEstimate.estimate_id == TechnicalSettlementEstimateItem.estimate_id)
                .where(TechnicalSettlementEstimate.contract_id == contract_id,
                    TechnicalSettlementEstimate.status == "TechnicallyApproved",
                    TechnicalSettlementEstimateItem.contract_item_id == item.item_id)) or 0
            used_financial = db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity), 0))
                .join(ContractSettlement, ContractSettlement.settlement_id == ContractSettlementItem.settlement_id)
                .where(ContractSettlement.contract_id == contract_id,
                    ContractSettlement.status.in_(("Approved", "Posted", "PendingFinalApproval")),
                    ContractSettlement.settlement_id.not_in(select(TechnicalSettlementEstimate.financial_settlement_id).where(
                        TechnicalSettlementEstimate.financial_settlement_id.is_not(None))),
                    ContractSettlementItem.contract_item_id == item.item_id)) or 0
            if next_quantity < Decimal(str(used_technical)) + Decimal(str(used_financial)):
                raise HTTPException(409, f"التعديل يجعل كمية البند {item.item_no} أقل من الكميات المعتمدة في المستخلصات")
            if next_quantity < 0: raise HTTPException(409, f"التعديل يجعل كمية البند {item.item_no} سالبة")
            if item.original_quantity is None: item.original_quantity = item.quantity
            if item.original_unit_price is None: item.original_unit_price = item.unit_price
            item.quantity = next_quantity
            item.unit_price = line.unit_price
            line.effective_item_id = item.item_id
            applied.append({"item_id":item.item_id,"quantity_before":str(next_quantity-line.quantity_delta),
                "quantity_after":str(next_quantity),"unit_price_after":str(item.unit_price)})
        else:
            item = ContractItem(contract_id=contract_id, catalog_item_id=line.catalog_item_id,
                account_id=line.account_id, project_id=line.project_id, item_no=line.item_no,
                description=line.description, unit=line.unit, quantity=line.quantity_delta,
                unit_price=line.unit_price, original_quantity=line.quantity_delta,
                original_unit_price=line.unit_price)
            db.add(item); db.flush(); line.effective_item_id = item.item_id
            applied.append({"item_id":item.item_id,"item_no":item.item_no,"quantity":str(item.quantity)})
    a.value_change = sum((Decimal(str(x.amount_change)) for x in lines), D0)
    approved_addenda_value = db.scalar(select(func.coalesce(func.sum(ContractAddendum.value_change), 0)).where(
        ContractAddendum.contract_id == contract_id, ContractAddendum.status == "Approved",
        ContractAddendum.addendum_id != addendum_id)) or 0
    approved_change_value = db.scalar(select(func.coalesce(func.sum(ContractChangeOrder.value_change), 0)).where(
        ContractChangeOrder.contract_id == contract_id, ContractChangeOrder.status == "Approved")) or 0
    revised_contract_value = Decimal(str(contract.original_value)) + Decimal(str(approved_addenda_value)) + Decimal(str(approved_change_value)) + Decimal(str(a.value_change))
    if revised_contract_value < 0:
        raise HTTPException(409, "لا يمكن أن تصبح القيمة المعدلة للعقد سالبة")
    linked_financial_ids = select(TechnicalSettlementEstimate.financial_settlement_id).where(
        TechnicalSettlementEstimate.financial_settlement_id.is_not(None))
    for side in ("Customer", "Subcontractor"):
        financial_work = db.scalar(select(func.coalesce(func.sum(ContractSettlement.work_value), 0)).where(
            ContractSettlement.contract_id == contract_id, ContractSettlement.settlement_side == side,
            ContractSettlement.status.in_(("Approved", "Posted", "PendingFinalApproval")),
            ContractSettlement.settlement_id.not_in(linked_financial_ids))) or 0
        technical_work = db.scalar(select(func.coalesce(func.sum(TechnicalSettlementEstimate.work_value), 0)).where(
            TechnicalSettlementEstimate.contract_id == contract_id, TechnicalSettlementEstimate.settlement_side == side,
            TechnicalSettlementEstimate.status == "TechnicallyApproved")) or 0
        legacy_work = db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value), 0)).where(
            ProgressBilling.contract_id == contract_id,
            func.lower(ProgressBilling.status).in_(("approved", "paid", "posted")))) or 0
        certified_work = Decimal(str(financial_work)) + Decimal(str(technical_work)) + Decimal(str(legacy_work))
        if revised_contract_value < certified_work:
            raise HTTPException(409, f"لا يمكن اعتماد الملحق لأن قيمة العقد بعد التعديل ({revised_contract_value}) أقل من الأعمال المعتمدة سابقًا ({certified_work}) لنوع المستخلص {side}")
    a.status = "Approved"
    a.approved_by = user.user_id
    a.approved_at = datetime.utcnow()
    write_audit(db, user.user_id, "ApproveAndApplyBOQ", "ContractAddendums", a.addendum_id,
        new={"status":a.status,"value_change":str(a.value_change),"applied_lines":applied})
    db.commit(); db.refresh(a)
    return _addendum(a)

@router.post("/{contract_id}/billings", status_code=201)
def create_billing(contract_id: int, body: BillingIn, user: User = Depends(require_permission("Contracts", "Add")), db: Session = Depends(get_db)):
    contract = db.get(Contract,contract_id)
    if not contract: raise HTTPException(404,"العقد غير موجود")
    if contract.status.lower() != "active": raise HTTPException(409,"لا يمكن إنشاء مستخلص إلا لعقد حالته Active")
    if db.scalar(select(ContractItem.item_id).where(ContractItem.contract_id==contract_id)):
        raise HTTPException(409,"هذا العقد مرتبط بجدول كميات فني؛ أنشئ المستخلص من شاشة المكتب الفني وحدد كميات البنود لمنع تكرار الأعمال.")
    net=body.work_value-body.retention_amount-body.advance_deduction-body.other_deductions
    values=body.model_dump(exclude={"billing_no"})
    b=ProgressBilling(contract_id=contract_id,billing_no=f"PB-PENDING-{uuid4().hex}",**values,net_amount=net,created_by=user.user_id)
    db.add(b); db.flush(); b.billing_no=f"PB-{body.billing_date.year}-{b.billing_id:06d}"
    write_audit(db,user.user_id,"Create","ProgressBillings",b.billing_id,new=_billing(b)); db.commit(); db.refresh(b)
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
        # Flush settlement/estimate detail deletions before deleting ContractItems.
        # These child rows reference ContractItems through restrictive foreign keys,
        # and there are no ORM relationships for SQLAlchemy to order automatically.
        db.flush()
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
