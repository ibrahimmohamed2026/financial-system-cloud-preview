"""Contract technical-office items, configurable deductions and settlement-to-GL posting."""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission, write_audit, get_current_user, has_permission
from ..models import (Contract, ContractAddendum, ContractChangeOrder, ContractItem, ContractDeductionRule,
                      ContractAccountingConfig, ContractSettlement, ContractSettlementItem, ProgressBilling, Account, Company,
                      FiscalYear, JournalEntry, JournalEntryDetail, User, TechnicalSettlementEstimate, TechnicalSettlementEstimateItem,
                      ItemCatalog, InventoryItem, TreasuryTransaction, Check)
from ..contract_deletion import delete_settlement_tree, require_admin

router = APIRouter(prefix="/api/contracts-erp", tags=["Contracts ERP: Technical Office & Settlements"])
ZERO = Decimal("0.00")
CENT = Decimal("0.01")
def money(v): return Decimal(str(v or 0)).quantize(CENT, rounding=ROUND_HALF_UP)
def side_check(v):
    if v not in ("Customer", "Subcontractor"): raise HTTPException(422, "settlement_side يجب أن يكون Customer أو Subcontractor")


# ---- ربط قواعد الخصم بشجرة الحسابات ----
# كلمات مفتاحية (بالترتيب) لاقتراح حساب من الشجرة لكل كود خصم قياسي
RULE_KEYWORDS = {
    "retention_insurance": ["تأمين محتجز", "تامين محتجز", "محتجز", "محتجزات", "retention"],
    "final_retention": ["تأمين نهائي", "تامين نهائي", "تأمينات نهائية", "ضمان نهائي"],
    "social_insurance": ["تأمينات اجتماعية", "تامينات اجتماعية", "هيئة التأمينات", "تأمين اجتماعي"],
    "informal_labor": ["عمالة غير منتظمة", "عمالة غير منتظمه", "العمالة غير المنتظمة", "عمالة"],
    "profit_tax": ["ضريبة أرباح", "ضريبة ارباح", "خصم وإضافة", "خصم واضافة", "خصم من المنبع", "ضريبة الخصم"],
    "stamp_duty": ["دمغة", "الدمغة", "ضريبة الدمغة"],
    "advance_payment": ["دفعات مقدمة", "دفعة مقدمة", "مقدمات", "سلف مقاولين", "advance"],
    "works_guarantee": ["ضمان الأعمال", "ضمان اعمال", "حجز ضمان", "محتجز ضمان"],
    "store_withdrawals": ["مسحوبات", "خامات", "مخازن", "مستلزمات موقع"],
}
LEGACY_CFG_FIELD = {  # كود القاعدة -> حقل الحساب الافتراضي في إعدادات العقد
    "retention_insurance": "retention_account_id", "final_retention": "retention_account_id",
    "works_guarantee": "retention_account_id", "advance_payment": "advance_account_id",
    "social_insurance": "tax_account_id", "informal_labor": "tax_account_id",
    "profit_tax": "tax_account_id", "stamp_duty": "tax_account_id",
}
def leaf_account_or_422(db, aid, label=""):
    a = db.get(Account, aid)
    if not a: raise HTTPException(422, f"{label}الحساب {aid} غير موجود في شجرة الحسابات")
    if not a.is_active: raise HTTPException(422, f"{label}الحساب {a.account_code} غير نشط")
    if db.scalar(select(Account.account_id).where(Account.parent_account_id == aid).limit(1)):
        raise HTTPException(422, f"{label}الحساب {a.account_code} — {a.account_name_ar} حساب رئيسي؛ اختر حسابًا فرعيًا يقبل الترحيل")
    return a
def resolve_rule_account(rule_code, name_ar, gl_account_id, cfg):
    """حساب القاعدة: المربوط صراحة أولًا، ثم الافتراضي من إعدادات العقد (بدون تخمين خاطئ)."""
    if gl_account_id: return gl_account_id
    if not cfg: return None
    field = LEGACY_CFG_FIELD.get((rule_code or "").lower())
    if field: return getattr(cfg, field)
    code = (rule_code or "").lower()
    if "retention" in code or "محتجز" in (name_ar or "") or "ضمان" in (name_ar or ""): return cfg.retention_account_id
    if "advance" in code or "مقدم" in (name_ar or ""): return cfg.advance_account_id
    return None

def item_out(x):
    # Keep old contract lines readable; new lines expose the linked central item/account.
    return {"item_id":x.item_id,"contract_id":x.contract_id,"item_no":x.item_no,"description":x.description,"unit":x.unit,"quantity":str(x.quantity),"unit_price":str(x.unit_price),"original_quantity":str(x.original_quantity) if getattr(x,"original_quantity",None) is not None else str(x.quantity),"original_unit_price":str(x.original_unit_price) if getattr(x,"original_unit_price",None) is not None else str(x.unit_price),"total":str(money(x.quantity*x.unit_price)),"catalog_item_id":getattr(x,"catalog_item_id",None),"account_id":getattr(x,"account_id",None),"project_id":getattr(x,"project_id",None)}
def rule_out(x): return {"rule_id":x.rule_id,"contract_id":x.contract_id,"settlement_side":x.settlement_side,"code":x.code,"name_ar":x.name_ar,"calculation_type":x.calculation_type,"rate":str(x.rate),"base_type":x.base_type,"posting_side":x.posting_side,"cap_amount":str(x.cap_amount) if x.cap_amount is not None else None,"gl_account_id":x.gl_account_id,"is_active":x.is_active,"sort_order":x.sort_order}
STANDARD_SETTLEMENT_DEDUCTIONS = [
    ("ADVANCE_PAYMENT", "دفعة مقدمة"), ("RETENTION", "تأمين محجوز"),
    ("FINAL_INSURANCE", "تأمين نهائي"), ("PROFIT_TAX", "ضرائب أرباح"),
    ("ENGINEERING_STAMP", "دمغات هندسية"), ("UNION_STAMP", "دمغات اتحاد"),
    ("STORE_WITHDRAWALS", "مسحوبات ومصاريف مخازن"), ("TRANSPORT", "نقل"),
    ("DIESEL", "سولار"), ("MEALS", "وجبات"), ("ADDITIONS", "تعليات"),
]
def normalized_deductions(x):
    # Compatibility for drafts created before the standard rows were added.
    # This is presentation-only on reads; rows are persisted when a draft is edited.
    result = dict(x.deductions_json or {})
    names = [str(v.get("name", "")).casefold() for v in result.values() if isinstance(v, dict)]
    for code, label in STANDARD_SETTLEMENT_DEDUCTIONS:
        if code not in result and not any(label.casefold() in name for name in names):
            result[code] = {"name": label, "amount": "0.00", "account_id": None,
                            "posting_side": "Debit" if x.settlement_side == "Customer" else "Credit"}
    return result
def settlement_out(x, db: Session | None = None):
    paid = ZERO
    if db is not None:
        paid = Decimal(db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
            TreasuryTransaction.settlement_id == x.settlement_id,
            TreasuryTransaction.status == "تم الصرف")) or 0)
    remaining = max(ZERO, Decimal(x.net_amount or 0) - paid)
    contract = db.get(Contract, x.contract_id) if db is not None else None
    return {"settlement_id":x.settlement_id,"contract_id":x.contract_id,"contract_no":contract.contract_no if contract else None,"contract_title":contract.title if contract else None,"contract_title_en":contract.title_en if contract else None,"settlement_side":x.settlement_side,"sequence_no":x.sequence_no,"settlement_no":x.settlement_no,"settlement_date":x.settlement_date,"counterparty_name":x.counterparty_name,"counterparty_name_en":x.counterparty_name_en,"work_value":str(x.work_value),"cumulative_work_value":str(x.cumulative_work_value),"deductions":normalized_deductions(x),"vat_amount":str(x.vat_amount),"net_amount":str(x.net_amount),"paid_amount":str(money(paid)),"remaining_amount":str(money(remaining)),"status":x.status,"financial_approved_by":x.financial_approved_by,"financial_approved_at":x.financial_approved_at,"manager_approved_by":x.manager_approved_by,"manager_approved_at":x.manager_approved_at,"journal_entry_id":x.journal_entry_id,"notes":x.notes}
def settlement_line_out(line, item=None):
    item = item
    return {"settlement_item_id":line.settlement_item_id,"contract_item_id":line.contract_item_id,"item_no":item.item_no if item else "","description":item.description if item else "","unit":item.unit if item else "","contract_quantity":str(item.quantity) if item else "0","quantity":str(line.quantity),"unit_price":str(line.unit_price),"amount":str(line.amount),"account_id":getattr(line,"account_id",None) or (getattr(item,"account_id",None) if item else None)}

class ItemIn(BaseModel):
    item_no: Optional[str] = Field(default=None,max_length=50); description: str = Field(min_length=1,max_length=500)
    unit: str = Field(default="وحدة",max_length=30); quantity: Decimal = Field(ge=0); unit_price: Decimal = Field(ge=0)
    catalog_item_id: Optional[int] = None
    project_id: Optional[int] = None


def next_contract_item_no(db: Session, contract_id: int) -> str:
    """Generate the next unused numeric line number within one contract."""
    used = {str(value).strip() for value in db.scalars(
        select(ContractItem.item_no).where(ContractItem.contract_id == contract_id)
    ).all() if value is not None}
    numeric = [int(value) for value in used if value.isdigit()]
    candidate = max(numeric, default=0) + 1
    while str(candidate) in used:
        candidate += 1
    return str(candidate)
class CatalogItemIn(BaseModel):
    code: str = Field(min_length=1,max_length=50)
    name: str = Field(min_length=1,max_length=250)
    unit: str = Field(default="وحدة",max_length=30)
    account_id: int
    inventory_item_id: Optional[int] = None
    is_active: bool = True
class RuleIn(BaseModel):
    settlement_side: Literal["Customer","Subcontractor"]; code: str = Field(min_length=1,max_length=50)
    name_ar: str = Field(min_length=1,max_length=150); calculation_type: Literal["Percent","Fixed"] = "Percent"
    rate: Decimal = Field(default=Decimal("0"),ge=0); base_type: Literal["CurrentWork","CumulativeWork","RemainingContract"] = "CurrentWork"
    posting_side: Literal["Debit","Credit"]; cap_amount: Optional[Decimal] = Field(default=None,ge=0)
    gl_account_id: Optional[int] = None; is_active: bool = True; sort_order: int = 0
class ConfigIn(BaseModel):
    settlement_side: Literal["Customer","Subcontractor"]; company_id: int; fiscal_year_id: int
    control_account_id: int; work_account_id: int; retention_account_id: Optional[int] = None
    advance_account_id: Optional[int] = None; tax_account_id: Optional[int] = None; vat_account_id: Optional[int] = None
    default_vat_rate: Decimal = Field(default=Decimal("0"),ge=0,le=100)
class SettlementLineIn(BaseModel):
    contract_item_id: int = Field(gt=0)
    quantity: Decimal = Field(gt=0)
class SettlementIn(BaseModel):
    settlement_side: Literal["Customer","Subcontractor"]; settlement_no: str | None = Field(default=None,max_length=50)
    settlement_date: date; counterparty_name: str = Field(min_length=1,max_length=200); counterparty_name_en: str | None = Field(default=None,max_length=200)
    work_value: Optional[Decimal] = Field(default=None,gt=0)
    items: list[SettlementLineIn] = Field(default_factory=list)
    vat_rate: Optional[Decimal] = Field(default=None,ge=0,le=100)
    deduction_overrides: dict[str,Decimal] = Field(default_factory=dict)
    notes: Optional[str] = None
    @model_validator(mode="after")
    def valid_overrides(self):
        if any(v < 0 for v in self.deduction_overrides.values()): raise ValueError("الخصومات لا يمكن أن تكون سالبة")
        return self

class SettlementDeductionsUpdate(BaseModel):
    amounts: dict[str, Decimal] = Field(default_factory=dict)
    vat_amount: Decimal = Field(default=ZERO, ge=0)
    @model_validator(mode="after")
    def valid_amounts(self):
        if any(v < 0 for v in self.amounts.values()): raise ValueError("الخصومات لا يمكن أن تكون سالبة")
        return self

class ChangeOrderIn(BaseModel):
    change_order_no: str | None = Field(default=None,max_length=50)
    change_order_date: date
    description: str = Field(min_length=1,max_length=500)
    value_change: Decimal

@router.get("/{contract_id}/change-orders")
def list_change_orders(contract_id:int, _:User=Depends(require_permission("Contracts","View")),db:Session=Depends(get_db)):
    rows=db.scalars(select(ContractChangeOrder).where(ContractChangeOrder.contract_id==contract_id).order_by(ContractChangeOrder.change_order_id.desc())).all()
    return {"items":[{"change_order_id":x.change_order_id,"change_order_no":x.change_order_no,"change_order_date":x.change_order_date,"description":x.description,"value_change":str(x.value_change),"status":x.status} for x in rows]}

@router.post("/{contract_id}/change-orders",status_code=201)
def create_change_order(contract_id:int,body:ChangeOrderIn,user:User=Depends(require_permission("Contracts","Add")),db:Session=Depends(get_db)):
    if not db.get(Contract,contract_id): raise HTTPException(404,"العقد غير موجود")
    # Internal change-order number is assigned from the database-generated ID.
    values=body.model_dump(exclude={"change_order_no"})
    x=ContractChangeOrder(contract_id=contract_id,change_order_no=f"CO-PENDING-{uuid4().hex}",**values,status="Pending",created_by=user.user_id)
    db.add(x);db.flush();x.change_order_no=f"CO-{body.change_order_date.year}-{x.change_order_id:06d}"
    write_audit(db,user.user_id,"Create","ContractChangeOrders",x.change_order_id,new={"change_order_no":x.change_order_no,"value_change":str(x.value_change),"status":x.status});db.commit()
    return {"change_order_id":x.change_order_id,"contract_id":x.contract_id,"change_order_no":x.change_order_no,"change_order_date":x.change_order_date,"description":x.description,"value_change":str(x.value_change),"status":x.status}

@router.post("/change-orders/{change_order_id}/approve")
def approve_change_order(change_order_id:int,user:User=Depends(require_permission("Contracts","Approve")),db:Session=Depends(get_db)):
    x=db.scalar(select(ContractChangeOrder).where(ContractChangeOrder.change_order_id==change_order_id).with_for_update())
    if not x: raise HTTPException(404,"الأمر التغييري غير موجود")
    if x.status!="Pending": raise HTTPException(409,"الأمر التغييري ليس في حالة انتظار الاعتماد")
    x.status="Approved";x.approved_by=user.user_id;x.approved_at=datetime.utcnow()
    write_audit(db,user.user_id,"Approve","ContractChangeOrders",x.change_order_id,new={"status":x.status,"value_change":str(x.value_change)});db.commit()
    return {"change_order_id":x.change_order_id,"status":x.status,"value_change":str(x.value_change)}

@router.get("/{contract_id}/technical-items")
def list_items(contract_id:int, _:User=Depends(require_permission("Contracts","View")), db:Session=Depends(get_db)):
    if not db.get(Contract,contract_id): raise HTTPException(404,"العقد غير موجود")
    rows=db.scalars(select(ContractItem).where(ContractItem.contract_id==contract_id).order_by(ContractItem.item_no)).all()
    return {"items":[item_out(x) for x in rows]}

@router.get("/catalog-items")
def list_catalog_items(q:str|None=None, account_id:int|None=None, inventory_only:bool=False,
                       user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    if not any(has_permission(db,user.user_id,screen,"View") for screen in ("Contracts","ContractSettlements","InventoryManagement")):
        raise HTTPException(403,"ليس لديك صلاحية عرض قائمة البنود المركزية")
    qy=select(ItemCatalog,Account).join(Account,Account.account_id==ItemCatalog.account_id).where(ItemCatalog.is_active.is_(True),Account.is_active.is_(True))
    if q and q.strip():
        like=f"%{q.strip()}%"; qy=qy.where((ItemCatalog.code.ilike(like))|(ItemCatalog.name.ilike(like))|(Account.account_code.ilike(like))|(Account.account_name_ar.ilike(like)))
    if account_id: qy=qy.where(ItemCatalog.account_id==account_id)
    if inventory_only: qy=qy.where(ItemCatalog.inventory_item_id.is_not(None))
    return {"items":[{"catalog_item_id":x.catalog_item_id,"code":x.code,"name":x.name,"unit":x.unit,"account_id":a.account_id,"account_code":a.account_code,"account_name":a.account_name_ar,"inventory_item_id":x.inventory_item_id} for x,a in db.execute(qy.order_by(ItemCatalog.code)).all()]}

@router.post("/catalog-items",status_code=201)
def create_catalog_item(body:CatalogItemIn,user:User=Depends(require_permission("InventoryManagement","Add")),db:Session=Depends(get_db)):
    leaf_account_or_422(db,body.account_id,"حساب البند: ")
    if db.scalar(select(ItemCatalog.catalog_item_id).where(ItemCatalog.code==body.code)): raise HTTPException(409,"كود البند مستخدم بالفعل")
    if body.inventory_item_id and not db.get(InventoryItem,body.inventory_item_id): raise HTTPException(422,"صنف المخزون غير موجود")
    if body.inventory_item_id and db.scalar(select(ItemCatalog.catalog_item_id).where(ItemCatalog.inventory_item_id==body.inventory_item_id)):
        raise HTTPException(409,"صنف المخزون مرتبط بالفعل ببند مركزي آخر؛ اختر صنفًا غير مرتبط أو عدّل الربط الحالي")
    x=ItemCatalog(**body.model_dump());db.add(x)
    try:
        db.flush()
        write_audit(db,user.user_id,"Create","ItemCatalog",x.catalog_item_id,new=body.model_dump())
        db.commit()
        db.refresh(x)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,"تعذر إنشاء البند: كود البند أو صنف المخزون مرتبط بالفعل ببند آخر") from exc
    return {"catalog_item_id":x.catalog_item_id,"code":x.code,"name":x.name,"account_id":x.account_id,"unit":x.unit,"inventory_item_id":x.inventory_item_id}

@router.post("/{contract_id}/technical-items",status_code=201)
def add_item(contract_id:int, body:ItemIn, user:User=Depends(require_permission("Contracts","Add")), db:Session=Depends(get_db)):
    contract = db.scalar(select(Contract).where(Contract.contract_id == contract_id).with_for_update())
    if not contract: raise HTTPException(404,"العقد غير موجود")
    # The server is authoritative: never accept a browser-supplied line number.
    # This also makes stale cached forms and manually edited requests harmless.
    requested_no = next_contract_item_no(db, contract_id)
    values=body.model_dump()
    values["item_no"] = requested_no
    values["original_quantity"] = body.quantity
    values["original_unit_price"] = body.unit_price
    if body.catalog_item_id:
        catalog=db.get(ItemCatalog,body.catalog_item_id)
        if not catalog or not catalog.is_active: raise HTTPException(422,"البند المركزي غير موجود أو غير نشط")
        leaf_account_or_422(db,catalog.account_id,"حساب البند: ")
        values["account_id"]=catalog.account_id
    x=ContractItem(contract_id=contract_id,**values); db.add(x)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,"تعذر توليد رقم بند فريد لهذا العقد؛ أعد المحاولة") from exc
    write_audit(db,user.user_id,"Create","ContractItems",x.item_id,new=item_out(x)); db.commit(); db.refresh(x); return item_out(x)

@router.put("/{contract_id}/technical-items/{item_id}")
def update_item(contract_id:int,item_id:int,body:ItemIn,user:User=Depends(require_permission("Contracts","Edit")),db:Session=Depends(get_db)):
    x=db.get(ContractItem,item_id)
    if not x or x.contract_id!=contract_id: raise HTTPException(404,"بند العقد غير موجود")
    # Item numbers are assigned at creation and remain stable on edits.
    requested_no = x.item_no
    if db.scalar(select(ContractSettlementItem.settlement_item_id).where(ContractSettlementItem.contract_item_id==item_id).limit(1)) or db.scalar(select(TechnicalSettlementEstimateItem.estimate_item_id).where(TechnicalSettlementEstimateItem.contract_item_id==item_id).limit(1)):
        raise HTTPException(409,"لا يمكن تعديل بند له مستخلصات أو كميات فنية محفوظة حفاظًا على التاريخ")
    values=body.model_dump()
    values["item_no"] = requested_no
    if body.catalog_item_id:
        catalog=db.get(ItemCatalog,body.catalog_item_id)
        if not catalog or not catalog.is_active: raise HTTPException(422,"البند المركزي غير موجود أو غير نشط")
        leaf_account_or_422(db,catalog.account_id,"حساب البند: ");values["account_id"]=catalog.account_id
    else: values["account_id"]=None
    old=item_out(x)
    for k,v in values.items(): setattr(x,k,v)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,"رقم البند مستخدم بالفعل في هذا العقد") from exc
    write_audit(db,user.user_id,"Update","ContractItems",x.item_id,old=old,new=item_out(x));db.commit();db.refresh(x);return item_out(x)

@router.delete("/{contract_id}/technical-items/{item_id}",status_code=204)
def delete_item(contract_id:int,item_id:int,user:User=Depends(require_permission("Contracts","Delete")),db:Session=Depends(get_db)):
    x=db.get(ContractItem,item_id)
    if not x or x.contract_id!=contract_id: raise HTTPException(404,"بند العقد غير موجود")
    if db.scalar(select(ContractSettlementItem.settlement_item_id).where(ContractSettlementItem.contract_item_id==item_id).limit(1)) or db.scalar(select(TechnicalSettlementEstimateItem.estimate_item_id).where(TechnicalSettlementEstimateItem.contract_item_id==item_id).limit(1)):
        raise HTTPException(409,"لا يمكن حذف بند له مستخلصات أو كميات فنية محفوظة")
    old=item_out(x);write_audit(db,user.user_id,"Delete","ContractItems",x.item_id,old=old,new=None);db.delete(x);db.commit()

@router.get("/{contract_id}/deduction-rules")
def list_rules(contract_id:int, settlement_side:Literal["Customer","Subcontractor"]|None=None, _:User=Depends(require_permission("Contracts","View")), db:Session=Depends(get_db)):
    q=select(ContractDeductionRule).where(ContractDeductionRule.contract_id==contract_id)
    if settlement_side: q=q.where(ContractDeductionRule.settlement_side==settlement_side)
    return {"items":[rule_out(x) for x in db.scalars(q.order_by(ContractDeductionRule.sort_order,ContractDeductionRule.rule_id)).all()]}

@router.post("/{contract_id}/deduction-rules",status_code=201)
def save_rule(contract_id:int,body:RuleIn,user:User=Depends(require_permission("Contracts","Edit")),db:Session=Depends(get_db)):
    if not db.get(Contract,contract_id): raise HTTPException(404,"العقد غير موجود")
    if body.gl_account_id: leaf_account_or_422(db,body.gl_account_id,"حساب الخصم: ")
    duplicate=db.scalar(select(ContractDeductionRule).where(ContractDeductionRule.contract_id==contract_id,ContractDeductionRule.settlement_side==body.settlement_side,ContractDeductionRule.code==body.code))
    if duplicate: raise HTTPException(409,"كود الخصم موجود بالفعل لهذا العقد والجهة")
    x=ContractDeductionRule(contract_id=contract_id,**body.model_dump());db.add(x);db.flush();write_audit(db,user.user_id,"Create","ContractDeductionRules",x.rule_id,new=rule_out(x));db.commit();db.refresh(x);return rule_out(x)

@router.put("/deduction-rules/{rule_id}")
def update_rule(rule_id:int,body:RuleIn,user:User=Depends(require_permission("Contracts","Edit")),db:Session=Depends(get_db)):
    x=db.get(ContractDeductionRule,rule_id)
    if not x: raise HTTPException(404,"قاعدة الخصم غير موجودة")
    if body.gl_account_id: leaf_account_or_422(db,body.gl_account_id,"حساب الخصم: ")
    old=rule_out(x)
    for k,v in body.model_dump().items(): setattr(x,k,v)
    write_audit(db,user.user_id,"Update","ContractDeductionRules",x.rule_id,old=old,new=rule_out(x));db.commit();db.refresh(x);return rule_out(x)

class AutoLinkIn(BaseModel):
    settlement_side: Optional[Literal["Customer","Subcontractor"]] = None
    overwrite: bool = False

@router.post("/{contract_id}/deduction-rules/auto-link")
def auto_link_rules(contract_id:int,body:AutoLinkIn,user:User=Depends(require_permission("Contracts","Edit")),db:Session=Depends(get_db)):
    """يربط قواعد الخصم غير المربوطة بحسابات الشجرة: بالبحث في أسماء الحسابات، ثم بحسابات إعدادات العقد."""
    if not db.get(Contract,contract_id): raise HTTPException(404,"العقد غير موجود")
    q=select(ContractDeductionRule).where(ContractDeductionRule.contract_id==contract_id)
    if body.settlement_side: q=q.where(ContractDeductionRule.settlement_side==body.settlement_side)
    rules=db.scalars(q).all()
    accounts=db.scalars(select(Account).where(Account.is_active.is_(True)).order_by(Account.account_code)).all()
    parents={a.parent_account_id for a in accounts if a.parent_account_id}
    leaves=[a for a in accounts if a.account_id not in parents]
    def find(words):
        for w in words:
            for a in leaves:
                if w in (a.account_name_ar or ""): return a
        return None
    linked=[];missing=[]
    for r in rules:
        if r.gl_account_id and not body.overwrite: continue
        cfg=db.scalar(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==contract_id,ContractAccountingConfig.settlement_side==r.settlement_side))
        words=RULE_KEYWORDS.get(r.code.lower(),[])+[r.name_ar]
        acc=find(words)
        aid=acc.account_id if acc else resolve_rule_account(r.code,r.name_ar,None,cfg)
        if aid:
            r.gl_account_id=aid; a=db.get(Account,aid)
            linked.append({"code":r.code,"name":r.name_ar,"side":r.settlement_side,"account":f"{a.account_code} — {a.account_name_ar}"})
        else: missing.append({"code":r.code,"name":r.name_ar,"side":r.settlement_side})
    write_audit(db,user.user_id,"AutoLinkRules","Contracts",contract_id,new={"linked":linked,"missing":missing});db.commit()
    return {"linked":linked,"missing":missing}

@router.put("/{contract_id}/accounting-config")
def save_config(contract_id:int,body:ConfigIn,user:User=Depends(require_permission("Contracts","Edit")),db:Session=Depends(get_db)):
    if not db.get(Contract,contract_id): raise HTTPException(404,"العقد غير موجود")
    company=db.get(Company,body.company_id); fy=db.get(FiscalYear,body.fiscal_year_id)
    if not company or not fy or fy.company_id!=body.company_id: raise HTTPException(422,"الشركة أو السنة المالية غير صحيحة")
    if fy.is_closed: raise HTTPException(422,"السنة المالية مغلقة")
    ids=[body.control_account_id,body.work_account_id]+[v for v in [body.retention_account_id,body.advance_account_id,body.tax_account_id,body.vat_account_id] if v]
    for aid in ids:
        leaf_account_or_422(db,aid,"إعدادات المحاسبة: ")
    x=db.scalar(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==contract_id,ContractAccountingConfig.settlement_side==body.settlement_side))
    if not x: x=ContractAccountingConfig(contract_id=contract_id,settlement_side=body.settlement_side);db.add(x)
    for k,v in body.model_dump().items(): setattr(x,k,v)
    db.flush();write_audit(db,user.user_id,"Save","ContractAccountingConfig",x.config_id,new=body.model_dump());db.commit()
    return {"message":"تم حفظ إعدادات المحاسبة","contract_id":contract_id,"settlement_side":body.settlement_side}

@router.get("/{contract_id}/accounting-config")
def get_config(contract_id:int, _:User=Depends(require_permission("Contracts","View")),db:Session=Depends(get_db)):
    rows=db.scalars(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==contract_id)).all()
    return {"items":[{"settlement_side":x.settlement_side,"company_id":x.company_id,"fiscal_year_id":x.fiscal_year_id,"control_account_id":x.control_account_id,"work_account_id":x.work_account_id,"retention_account_id":x.retention_account_id,"advance_account_id":x.advance_account_id,"tax_account_id":x.tax_account_id,"vat_account_id":x.vat_account_id,"default_vat_rate":str(x.default_vat_rate)} for x in rows]}

def contract_financial_summary(db: Session, contract_id: int, side: str):
    c = db.get(Contract, contract_id)
    if not c:
        raise HTTPException(404, "العقد غير موجود")
    valid = (ContractSettlement.contract_id == contract_id, ContractSettlement.settlement_side == side,
             ContractSettlement.status.in_(("Approved", "Posted", "PendingFinalApproval")))
    previous_new = db.scalar(select(func.coalesce(func.sum(ContractSettlement.work_value), 0)).where(*valid)) or ZERO
    # Include approved historical certificates from the legacy ProgressBillings table in the financial total.
    legacy = db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value), 0)).where(
        ProgressBilling.contract_id == contract_id, func.lower(ProgressBilling.status).in_(("approved", "paid", "posted")))) or ZERO
    previous = money(Decimal(str(previous_new)) + Decimal(str(legacy)))
    addenda = db.scalar(select(func.coalesce(func.sum(ContractAddendum.value_change), 0)).where(ContractAddendum.contract_id == contract_id, ContractAddendum.status == "Approved")) or ZERO
    changes = db.scalar(select(func.coalesce(func.sum(ContractChangeOrder.value_change), 0)).where(ContractChangeOrder.contract_id == contract_id, ContractChangeOrder.status == "Approved")) or ZERO
    contract_value = money(c.original_value + addenda + changes)
    return c, money(previous), contract_value

@router.get("/{contract_id}/settlement-summary")
def settlement_summary(contract_id: int, settlement_side: Literal["Customer","Subcontractor"] = "Customer",
                       _: User = Depends(require_permission("ContractSettlements", "View")), db: Session = Depends(get_db)):
    c, _, contract_value = contract_financial_summary(db, contract_id, settlement_side)
    items = db.scalars(select(ContractItem).where(ContractItem.contract_id == contract_id).order_by(ContractItem.item_no)).all()
    # A technical estimate and its financial settlement are two views of the
    # same work. Count approved technical quantities, and only count approved
    # financial settlements that are not linked to a technical estimate.
    linked_financial_ids = select(TechnicalSettlementEstimate.financial_settlement_id).where(
        TechnicalSettlementEstimate.financial_settlement_id.is_not(None))
    valid_financial_ids = select(ContractSettlement.settlement_id).where(
        ContractSettlement.contract_id == contract_id,
        ContractSettlement.settlement_side == settlement_side,
        ContractSettlement.status.in_(("Approved", "Posted", "PendingFinalApproval")),
        ContractSettlement.settlement_id.not_in(linked_financial_ids))
    financial_rows = db.execute(select(ContractSettlementItem.contract_item_id, func.sum(ContractSettlementItem.quantity))
        .where(ContractSettlementItem.settlement_id.in_(valid_financial_ids))
        .group_by(ContractSettlementItem.contract_item_id)).all()
    valid_estimate_ids = select(TechnicalSettlementEstimate.estimate_id).where(
        TechnicalSettlementEstimate.contract_id == contract_id,
        TechnicalSettlementEstimate.settlement_side == settlement_side,
        TechnicalSettlementEstimate.status.in_(("TechnicallyApproved", "ForwardedToFinance")))
    technical_rows = db.execute(select(TechnicalSettlementEstimateItem.contract_item_id,
        func.sum(func.coalesce(TechnicalSettlementEstimateItem.approved_quantity, TechnicalSettlementEstimateItem.current_quantity)))
        .where(TechnicalSettlementEstimateItem.estimate_id.in_(valid_estimate_ids))
        .group_by(TechnicalSettlementEstimateItem.contract_item_id)).all()
    used = {}
    for item_id, qty in [*financial_rows, *technical_rows]:
        key = int(item_id)
        used[key] = used.get(key, ZERO) + Decimal(str(qty or 0))

    financial_work = db.scalar(select(func.coalesce(func.sum(ContractSettlement.work_value), 0))
        .where(ContractSettlement.settlement_id.in_(valid_financial_ids))) or ZERO
    technical_work = db.scalar(select(func.coalesce(func.sum(TechnicalSettlementEstimate.work_value), 0))
        .where(TechnicalSettlementEstimate.estimate_id.in_(valid_estimate_ids))) or ZERO
    legacy_work = db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value), 0)).where(
        ProgressBilling.contract_id == contract_id,
        func.lower(ProgressBilling.status).in_(("approved", "paid", "posted")))) or ZERO
    previous = money(Decimal(str(financial_work)) + Decimal(str(technical_work)) + Decimal(str(legacy_work)))
    item_rows = []
    for item in items:
        done = used.get(item.item_id, ZERO)
        item_rows.append({**item_out(item), "previous_quantity": str(done), "remaining_quantity": str(max(Decimal("0"), Decimal(item.quantity)-done))})
    return {"contract_id":contract_id,"contract_no":c.contract_no,"settlement_side":settlement_side,
        "contract_value":str(contract_value),"previous_settlements":str(previous),"cumulative_work_value":str(previous),
        "remaining_contract_value":str(max(ZERO, contract_value-previous)),"items":item_rows}

@router.post("/{contract_id}/settlements",status_code=201)
def create_settlement(contract_id:int,body:SettlementIn,user:User=Depends(require_permission("ContractSettlements","Add")),db:Session=Depends(get_db)):
    c=db.scalar(select(Contract).where(Contract.contract_id==contract_id).with_for_update())
    if not c: raise HTTPException(404,"العقد غير موجود")
    if c.status.lower() != "active": raise HTTPException(409,"لا يمكن إنشاء مستخلص إلا لعقد حالته Active")
    side=body.settlement_side
    previous, contract_value = contract_financial_summary(db, contract_id, side)[1:]
    # Settlement numbers are generated internally; sequence is scoped by contract and settlement side.
    contract_items=db.scalars(select(ContractItem).where(ContractItem.contract_id==contract_id).order_by(ContractItem.item_no)).all()
    lines=[]; work=ZERO
    if contract_items:
        legacy_approved = db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value), 0)).where(
            ProgressBilling.contract_id == contract_id, func.lower(ProgressBilling.status).in_(("approved", "paid", "posted")))) or ZERO
        if Decimal(str(legacy_approved)) > ZERO:
            raise HTTPException(409,"يوجد مستخلص معتمد قديم غير موزع على بنود العقد. راجع/حوّل كمياته التاريخية إلى تفاصيل بنود قبل إنشاء مستخلصات فنية جديدة، لمنع تكرار الأعمال.")
        if not body.items: raise HTTPException(422,"هذا العقد له بنود فنية؛ يجب تحديد كميات البنود في المستخلص بدل إدخال إجمالي يدوي")
        seen=set()
        for requested in body.items:
            if requested.contract_item_id in seen: raise HTTPException(422,"لا يمكن تكرار نفس البند مرتين داخل المستخلص")
            seen.add(requested.contract_item_id)
            item=db.scalar(select(ContractItem).where(ContractItem.item_id==requested.contract_item_id,ContractItem.contract_id==contract_id))
            if not item: raise HTTPException(422,f"البند {requested.contract_item_id} لا يتبع هذا العقد")
            valid_ids=select(ContractSettlement.settlement_id).where(ContractSettlement.contract_id==contract_id,ContractSettlement.settlement_side==side,ContractSettlement.status.in_(("Approved","Posted","PendingFinalApproval")))
            done=db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity),0)).where(ContractSettlementItem.contract_item_id==item.item_id,ContractSettlementItem.settlement_id.in_(valid_ids))) or ZERO
            remaining=Decimal(item.quantity)-Decimal(str(done))
            if requested.quantity>remaining: raise HTTPException(409,f"كمية البند {item.item_no} المطلوبة {requested.quantity} تتجاوز المتبقي {max(ZERO,remaining)} {item.unit}")
            amount=money(requested.quantity*item.unit_price);work+=amount
            lines.append((item,requested.quantity,amount))
        work=money(work)
        if body.work_value is not None and money(body.work_value)!=work: raise HTTPException(422,f"قيمة الأعمال لا تطابق تفاصيل البنود؛ القيمة المحسوبة {work}")
    else:
        if body.items: raise HTTPException(422,"لا توجد بنود فنية بالعقد المختار")
        if body.work_value is None or money(body.work_value)<=0: raise HTTPException(422,"أدخل قيمة أعمال صحيحة؛ أو أضف بنود العقد الفنية أولًا")
        work=money(body.work_value)
    cumulative=money(previous+work)
    if cumulative>contract_value: raise HTTPException(409,f"إجمالي الأعمال المعتمدة {cumulative} يتجاوز قيمة العقد المعدلة {contract_value}")
    cfg=db.scalar(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==contract_id,ContractAccountingConfig.settlement_side==side))
    rules=db.scalars(select(ContractDeductionRule).where(ContractDeductionRule.contract_id==contract_id,ContractDeductionRule.settlement_side==side,ContractDeductionRule.is_active.is_(True)).order_by(ContractDeductionRule.sort_order,ContractDeductionRule.rule_id)).all()
    deductions={}; total=ZERO
    for r in rules:
        base=work if r.base_type=="CurrentWork" else cumulative if r.base_type=="CumulativeWork" else max(ZERO,contract_value-cumulative)
        amount=money(base*r.rate/Decimal("100")) if r.calculation_type=="Percent" else money(r.rate)
        if r.cap_amount is not None: amount=min(amount,money(r.cap_amount))
        if r.code in body.deduction_overrides:
            amount=money(body.deduction_overrides[r.code])
            if r.cap_amount is not None and amount > money(r.cap_amount):
                raise HTTPException(422,f"قيمة الخصم {r.name_ar} تتجاوز الحد الأقصى المسموح {money(r.cap_amount)}")
        rule_account=resolve_rule_account(r.code,r.name_ar,r.gl_account_id,cfg)
        if amount>0 and not rule_account: raise HTTPException(422,f"قاعدة الخصم «{r.name_ar}» غير مربوطة بحساب في شجرة الحسابات. افتح تفاصيل العقد ← بنود الخصومات ← «ربط تلقائي بالشجرة» أو اختر الحساب يدويًا.")
        deductions[r.code]={"name":r.name_ar,"amount":str(amount),"account_id":rule_account,"posting_side":r.posting_side};total+=amount
    unknown=set(body.deduction_overrides)-{r.code for r in rules}
    if unknown: raise HTTPException(422,"أكواد خصم غير معرفة: "+", ".join(sorted(unknown)))
    vat_rate=body.vat_rate if body.vat_rate is not None else (cfg.default_vat_rate if cfg else Decimal("0"))
    vat=money(work*vat_rate/Decimal("100")); net=money(work+vat-total)
    if net<0: raise HTTPException(422,"الخصومات والضريبة تجعل صافي المستخلص سالبًا")
    seq=(db.scalar(select(func.max(ContractSettlement.sequence_no)).where(ContractSettlement.contract_id==contract_id,ContractSettlement.settlement_side==side)) or 0)+1
    x=ContractSettlement(contract_id=contract_id,settlement_side=side,sequence_no=seq,settlement_no=f"ST-PENDING-{uuid4().hex}",settlement_date=body.settlement_date,counterparty_name=body.counterparty_name,counterparty_name_en=body.counterparty_name_en,work_value=work,cumulative_work_value=cumulative,deductions_json=deductions,vat_amount=vat,net_amount=net,status="PendingApproval",notes=body.notes,created_by=user.user_id)
    db.add(x);db.flush()
    side_code = "CUS" if side == "Customer" else "SUB"
    x.settlement_no = f"ST-{side_code}-{body.settlement_date.year}-{x.settlement_id:06d}"
    for item, quantity, amount in lines:
        db.add(ContractSettlementItem(settlement_id=x.settlement_id,contract_item_id=item.item_id,account_id=item.account_id,quantity=quantity,unit_price=item.unit_price,amount=amount))
    write_audit(db,user.user_id,"Create","ContractSettlements",x.settlement_id,new=settlement_out(x, db));db.commit();db.refresh(x);return settlement_out(x, db)

@router.get("/all-settlements")
def list_all_settlements(settlement_side: Literal["Customer","Subcontractor"] | None = None,
                         _: User = Depends(require_permission("ContractSettlements", "View")), db: Session = Depends(get_db)):
    q = select(ContractSettlement).order_by(ContractSettlement.settlement_date.desc(), ContractSettlement.settlement_id.desc())
    if settlement_side:
        q = q.where(ContractSettlement.settlement_side == settlement_side)
    rows = db.scalars(q.limit(1000)).all()
    result = []
    for x in rows:
        c = db.get(Contract, x.contract_id)
        data = settlement_out(x, db)
        data["contract_no"] = c.contract_no if c else ""
        data["contract_title"] = c.title if c else ""
        result.append(data)
    return {"items": result}

@router.get("/manager-pending-settlements")
def list_manager_pending_settlements(
        _: User = Depends(require_permission("ContractSettlements", "ManagerApprove")),
        db: Session = Depends(get_db)):
    """Dedicated manager queue; does not depend on the accounting list's View permission."""
    rows = db.scalars(
        select(ContractSettlement)
        .where(ContractSettlement.status == "PendingFinalApproval",
               ContractSettlement.financial_approved_by.is_not(None))
        .order_by(ContractSettlement.settlement_date.asc(),
                  ContractSettlement.settlement_id.asc())
        .limit(1000)
    ).all()
    items = []
    for settlement in rows:
        data = settlement_out(settlement, db)
        contract = db.get(Contract, settlement.contract_id)
        data["contract_no"] = contract.contract_no if contract else ""
        data["contract_title"] = contract.title if contract else ""
        data["contract_title_en"] = contract.title_en if contract else ""
        items.append(data)
    return {"items": items}


@router.get("/{contract_id}/settlements")
def list_settlements(contract_id:int,settlement_side:Literal["Customer","Subcontractor"]|None=None, _:User=Depends(require_permission("ContractSettlements","View")),db:Session=Depends(get_db)):
    q=select(ContractSettlement).where(ContractSettlement.contract_id==contract_id)
    if settlement_side:q=q.where(ContractSettlement.settlement_side==settlement_side)
    rows=db.scalars(q.order_by(ContractSettlement.settlement_side,ContractSettlement.sequence_no.desc())).all()
    return {"items":[{**settlement_out(x, db), "items":[settlement_line_out(line, db.get(ContractItem,line.contract_item_id)) for line in db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id==x.settlement_id)).all()]} for x in rows]}

@router.get("/settlements/{settlement_id}/items")
def get_settlement_items(settlement_id:int, _:User=Depends(require_permission("ContractSettlements","View")),db:Session=Depends(get_db)):
    x=db.get(ContractSettlement,settlement_id)
    if not x: raise HTTPException(404,"المستخلص غير موجود")
    lines=db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id==settlement_id)).all()
    return {"items":[settlement_line_out(line,db.get(ContractItem,line.contract_item_id)) for line in lines]}

@router.put("/settlements/{settlement_id}/deductions")
def update_settlement_deductions(settlement_id:int, body:SettlementDeductionsUpdate,
        user:User=Depends(require_permission("ContractSettlements","Edit")), db:Session=Depends(get_db)):
    x=db.scalar(select(ContractSettlement).where(ContractSettlement.settlement_id==settlement_id).with_for_update())
    if not x: raise HTTPException(404,"المستخلص غير موجود")
    if x.status not in ("Draft", "PendingApproval") or x.journal_entry_id is not None:
        raise HTTPException(409,"لا يمكن تعديل الخصومات بعد الاعتماد المالي أو الترحيل؛ التعديل متاح قبل الاعتماد فقط")
    deductions=normalized_deductions(x)
    unknown=set(body.amounts)-set(deductions)
    if unknown: raise HTTPException(422,"بنود خصم غير موجودة في هذا المستخلص: "+", ".join(sorted(unknown)))
    old={"deductions":deductions,"vat_amount":str(x.vat_amount),"net_amount":str(x.net_amount)}
    live={r.code:r for r in db.scalars(select(ContractDeductionRule).where(ContractDeductionRule.contract_id==x.contract_id,ContractDeductionRule.settlement_side==x.settlement_side)).all()}
    for code,d in deductions.items():
        if not d.get("account_id") and code in live and live[code].gl_account_id: d["account_id"]=live[code].gl_account_id
    total=ZERO
    for code,d in deductions.items():
        amount=money(body.amounts.get(code, Decimal(str(d.get("amount",0)))))
        if amount<0: raise HTTPException(422,f"قيمة الخصم {code} لا يمكن أن تكون سالبة")
        rule=live.get(code)
        if rule and rule.cap_amount is not None and amount > money(rule.cap_amount):
            raise HTTPException(422,f"قيمة الخصم {d.get('name',code)} تتجاوز الحد الأقصى المسموح {money(rule.cap_amount)}")
        d["amount"]=str(amount)
        total+=amount
    vat=money(body.vat_amount)
    net=money(Decimal(str(x.work_value))+vat-total)
    if net<0: raise HTTPException(422,"إجمالي الخصومات أكبر من قيمة الأعمال والضريبة")
    x.deductions_json=deductions; x.vat_amount=vat; x.net_amount=net
    write_audit(db,user.user_id,"UpdateDeductions","ContractSettlements",x.settlement_id,old=old,new={"deductions":deductions,"vat_amount":str(vat),"net_amount":str(net)})
    db.commit();db.refresh(x)
    return settlement_out(x, db)

class FinancialReviewLine(BaseModel):
    settlement_item_id: int = Field(gt=0)
    verified: bool
    review_note: str | None = Field(default=None, max_length=2000)

class FinancialSettlementReview(BaseModel):
    checks: dict[str, bool]
    items: list[FinancialReviewLine] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=4000)

REQUIRED_FINANCIAL_REVIEW_CHECKS = {
    "quantities_verified", "unit_prices_verified", "work_value_verified",
    "deductions_verified", "vat_verified", "net_amount_verified",
    "ledger_accounts_verified", "prior_settlements_verified",
    "supporting_documents_checked",
}

@router.post("/settlements/{settlement_id}/approve")
@router.post("/settlements/{settlement_id}/financial-approve")
def approve_settlement(settlement_id:int, body:FinancialSettlementReview, user:User=Depends(require_permission("ContractSettlements","FinancialApprove")),db:Session=Depends(get_db)):
    """Stage 1: financial review. Manager approval is a separate, mandatory stage."""
    x=db.scalar(select(ContractSettlement).where(ContractSettlement.settlement_id==settlement_id).with_for_update())
    if not x: raise HTTPException(404,"المستخلص غير موجود")
    if x.status not in ("Draft", "PendingApproval"): raise HTTPException(409,"المستخلص ليس بانتظار المراجعة المالية")
    if x.created_by == user.user_id:
        raise HTTPException(403, "لا يجوز لمُعدّ المستخلص إجراء المراجعة المالية لنفسه")
    if set(body.checks) != REQUIRED_FINANCIAL_REVIEW_CHECKS or not all(body.checks.values()):
        raise HTTPException(422, "يجب استكمال جميع عناصر قائمة المراجعة المالية قبل الاعتماد")
    lines=db.scalars(select(ContractSettlementItem).where(
        ContractSettlementItem.settlement_id==x.settlement_id).with_for_update()).all()
    submitted={row.settlement_item_id:row for row in body.items}
    if len(submitted)!=len(body.items) or set(submitted)!={line.settlement_item_id for line in lines}:
        raise HTTPException(422, "يجب مراجعة كل بند مالي مرة واحدة دون تكرار أو إغفال")
    reviewed_lines=[]
    line_total=ZERO
    for line in lines:
        decision=submitted[line.settlement_item_id]
        if not decision.verified:
            raise HTTPException(422, "يجب تأكيد مراجعة كل بند مالي")
        item=db.get(ContractItem,line.contract_item_id)
        if item is None:
            raise HTTPException(409, "أحد بنود المستخلص لم يعد موجوداً في العقد")
        expected=money(Decimal(str(line.quantity))*Decimal(str(line.unit_price)))
        if money(line.amount)!=expected:
            raise HTTPException(409, f"قيمة البند {item.item_no} لا تطابق الكمية × سعر الوحدة")
        line_total+=expected
        reviewed_lines.append({"settlement_item_id":line.settlement_item_id,
            "contract_item_id":line.contract_item_id,"item_no":item.item_no,
            "quantity":str(line.quantity),"unit_price":str(line.unit_price),
            "amount":str(line.amount),"verified":True,
            "review_note":(decision.review_note or "").strip() or None})
    if lines and money(line_total)!=money(x.work_value):
        raise HTTPException(409, "إجمالي بنود المستخلص لا يطابق قيمة الأعمال المسجلة")
    deductions=dict(x.deductions_json or {})
    deduction_total=ZERO
    live_rules={r.code:r for r in db.scalars(select(ContractDeductionRule).where(
        ContractDeductionRule.contract_id==x.contract_id,
        ContractDeductionRule.settlement_side==x.settlement_side)).all()}
    for code,d in deductions.items():
        amount=money(d.get("amount",0))
        if amount<ZERO:
            raise HTTPException(422, f"قيمة الخصم {code} لا يمكن أن تكون سالبة")
        deduction_total+=amount
        rule=live_rules.get(code)
        if rule and rule.cap_amount is not None and amount>money(rule.cap_amount):
            raise HTTPException(422, f"قيمة الخصم {d.get('name',code)} تتجاوز الحد الأقصى المتفق عليه")
        if amount>ZERO:
            account_id=d.get("account_id") or (rule.gl_account_id if rule else None)
            if not account_id:
                raise HTTPException(422, f"الخصم {d.get('name',code)} موجب ولا يرتبط بحساب أستاذ")
            leaf_account_or_422(db, account_id, f"حساب الخصم {d.get('name',code)}: ")
    expected_net=money(Decimal(str(x.work_value))+Decimal(str(x.vat_amount))-deduction_total)
    if expected_net<ZERO or money(x.net_amount)!=expected_net:
        raise HTTPException(409, "صافي المستخلص لا يساوي الأعمال + الضريبة − إجمالي الخصومات")
    contract = db.scalar(select(Contract).where(Contract.contract_id==x.contract_id).with_for_update())
    if not contract or contract.status.lower() != "active": raise HTTPException(409,"لا يمكن اعتماد مستخلص لعقد غير فعّال")
    lines=db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id==x.settlement_id)).all()
    if lines:
        legacy_approved = db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value), 0)).where(
            ProgressBilling.contract_id == x.contract_id, func.lower(ProgressBilling.status).in_(("approved", "paid", "posted")))) or ZERO
        if Decimal(str(legacy_approved)) > ZERO:
            raise HTTPException(409,"لا يمكن اعتماد المستخلص الفني قبل توزيع المستخلصات القديمة المعتمدة على بنود العقد")
        for line in lines:
            item=db.get(ContractItem,line.contract_item_id)
            prior_ids=select(ContractSettlement.settlement_id).where(ContractSettlement.contract_id==x.contract_id,ContractSettlement.settlement_side==x.settlement_side,ContractSettlement.status.in_(("Approved","Posted","PendingFinalApproval")),ContractSettlement.settlement_id!=x.settlement_id)
            done=db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity),0)).where(ContractSettlementItem.contract_item_id==line.contract_item_id,ContractSettlementItem.settlement_id.in_(prior_ids))) or ZERO
            if Decimal(str(done))+Decimal(line.quantity)>Decimal(item.quantity):
                raise HTTPException(409,f"لا يمكن اعتماد المستخلص: كمية البند {item.item_no} ستتجاوز الكمية التعاقدية بعد احتساب المستخلصات المعتمدة الأخرى")
    _,previous,contract_value=contract_financial_summary(db,x.contract_id,x.settlement_side)
    if money(previous+x.work_value)>contract_value:
        raise HTTPException(409,"لا يمكن اعتماد المستخلص لأن إجمالي الأعمال المعتمدة سيتجاوز قيمة العقد المعدلة")
    x.cumulative_work_value=money(previous+x.work_value)
    x.financial_approved_by=user.user_id
    x.financial_approved_at=datetime.utcnow()
    x.status="PendingFinalApproval"
    write_audit(db,user.user_id,"FinancialApprove","ContractSettlements",x.settlement_id,
        new={"settlement":settlement_out(x, db),"review_checklist":body.checks,
             "reviewed_items":reviewed_lines,"review_notes":(body.notes or "").strip() or None,
             "verified_totals":{"work_value":str(x.work_value),"deductions":str(money(deduction_total)),
                                "vat_amount":str(x.vat_amount),"net_amount":str(x.net_amount)}})
    db.commit();db.refresh(x)
    return settlement_out(x, db)

class ManagerSettlementDecision(BaseModel):
    decision: Literal["approve", "return", "reject"]
    notes: str | None = Field(default=None, max_length=2000)

@router.post("/settlements/{settlement_id}/manager-decision")
def manager_settlement_decision(settlement_id: int, body: ManagerSettlementDecision,
        user: User = Depends(require_permission("ContractSettlements", "ManagerApprove")),
        db: Session = Depends(get_db)):
    """Manager gate: approve, return to accounting, or permanently reject with an audited reason."""
    x = db.scalar(select(ContractSettlement).where(
        ContractSettlement.settlement_id == settlement_id).with_for_update())
    if not x:
        raise HTTPException(404, "المستخلص غير موجود")
    if x.status != "PendingFinalApproval" or not x.financial_approved_by:
        raise HTTPException(409, "المستخلص ليس في انتظار اعتماد المدير بعد المراجعة المالية")
    if x.financial_approved_by == user.user_id:
        raise HTTPException(403, "يجب أن يكون قرار المدير من مستخدم مختلف عن المراجع المالي")
    if body.decision in ("return", "reject") and not (body.notes or "").strip():
        raise HTTPException(422, "يجب كتابة سبب الإرجاع أو الرفض")
    # Route final approval through the hardened legacy manager gate so contract,
    # reserved quantity, and amended contract value validations cannot be bypassed.
    if body.decision == "approve":
        return manager_approve_settlement(settlement_id, user, db)

    old = {"status": x.status, "financial_approved_by": x.financial_approved_by,
           "manager_approved_by": x.manager_approved_by, "manager_approved_at": x.manager_approved_at}
    if body.decision == "return":
        # Re-open only the accounting review stage; no journal can exist at this point.
        x.status = "PendingApproval"
        x.financial_approved_by = None
        x.financial_approved_at = None
        x.manager_approved_by = None
        x.manager_approved_at = None
        x.notes = ((x.notes or "").rstrip() + f"\n[إعادة للحسابات بواسطة المستخدم {user.user_id}]: {(body.notes or '').strip()}").strip()
        action = "ManagerReturn"
    else:
        # Rejected is terminal through the normal workflow; reopening requires an audited admin action.
        x.status = "Rejected"
        x.notes = ((x.notes or "").rstrip() + f"\n[رفض نهائي بواسطة المستخدم {user.user_id}]: {(body.notes or '').strip()}").strip()
        action = "ManagerReject"
    write_audit(db, user.user_id, action, "ContractSettlements", x.settlement_id,
                old=old, new={"status": x.status, "decision": body.decision,
                              "notes": (body.notes or "").strip() or None})
    db.commit()
    db.refresh(x)
    return settlement_out(x, db)

@router.post("/settlements/{settlement_id}/manager-approve")
def manager_approve_settlement(settlement_id:int,user:User=Depends(require_permission("ContractSettlements","ManagerApprove")),db:Session=Depends(get_db)):
    """Stage 2: manager approval. Only this stage unlocks accounting posting."""
    x=db.scalar(select(ContractSettlement).where(ContractSettlement.settlement_id==settlement_id).with_for_update())
    if not x: raise HTTPException(404,"المستخلص غير موجود")
    if x.status!="PendingFinalApproval" or not x.financial_approved_by:
        raise HTTPException(409,"يجب إتمام المراجعة المالية أولاً قبل اعتماد المدير")
    if x.financial_approved_by==user.user_id:
        raise HTTPException(403,"يجب أن يكون اعتماد المدير من مستخدم مختلف عن المراجع المالي")
    contract=db.scalar(select(Contract).where(Contract.contract_id==x.contract_id).with_for_update())
    if not contract or contract.status.lower()!="active":
        raise HTTPException(409,"لا يمكن اعتماد مستخلص لعقد غير فعّال")
    # Recheck reserved quantities and contract value at the final approval gate.
    # This also protects against overlapping pending approvals created before
    # pending-final approvals began reserving quantities/value.
    lines=db.scalars(select(ContractSettlementItem).where(
        ContractSettlementItem.settlement_id==x.settlement_id)).all()
    if lines:
        prior_ids=select(ContractSettlement.settlement_id).where(
            ContractSettlement.contract_id==x.contract_id,
            ContractSettlement.settlement_side==x.settlement_side,
            ContractSettlement.status.in_(("Approved","Posted","PendingFinalApproval")),
            ContractSettlement.settlement_id!=x.settlement_id)
        for line in lines:
            item=db.get(ContractItem,line.contract_item_id)
            if item is None:
                raise HTTPException(409,"بند المستخلص لم يعد موجودًا في العقد")
            done=db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity),0)).where(
                ContractSettlementItem.contract_item_id==line.contract_item_id,
                ContractSettlementItem.settlement_id.in_(prior_ids))) or ZERO
            if Decimal(str(done))+Decimal(line.quantity)>Decimal(item.quantity):
                raise HTTPException(409,f"لا يمكن اعتماد المدير: كمية البند {item.item_no} تتجاوز الكمية التعاقدية بعد احتساب المستخلصات المحجوزة الأخرى")
    _,reserved_value,contract_value=contract_financial_summary(db,x.contract_id,x.settlement_side)
    if reserved_value>contract_value:
        raise HTTPException(409,"لا يمكن اعتماد المدير: إجمالي المستخلصات المعتمدة والمعلقة يتجاوز قيمة العقد المعدلة")
    x.manager_approved_by=user.user_id
    x.manager_approved_at=datetime.utcnow()
    x.status="Approved"
    write_audit(db,user.user_id,"ManagerApprove","ContractSettlements",x.settlement_id,new=settlement_out(x, db))
    db.commit();db.refresh(x)
    return settlement_out(x, db)

@router.post("/settlements/{settlement_id}/post")
def post_settlement(settlement_id:int,user:User=Depends(require_permission("ContractSettlements","Post")),db:Session=Depends(get_db)):
    x=db.scalar(select(ContractSettlement).where(ContractSettlement.settlement_id==settlement_id).with_for_update())
    if not x: raise HTTPException(404,"المستخلص غير موجود")
    if x.journal_entry_id or x.status=="Posted": raise HTTPException(409,"تم ترحيل هذا المستخلص محاسبيًا بالفعل")
    linked_manual = db.scalar(select(JournalEntry).where(
        JournalEntry.source_settlement_id == x.settlement_id,
        JournalEntry.status != "Reversed",
    ).limit(1))
    if linked_manual:
        raise HTTPException(409, f"يوجد قيد يومية {linked_manual.entry_no} مرتبط بهذا المستخلص؛ احذفه إن كان مسودة أو ألغِه إن كان مرحّلًا قبل الترحيل التلقائي")
    if x.status!="Approved": raise HTTPException(409,"يجب اعتماد المستخلص قبل الترحيل")
    contract = db.scalar(select(Contract).where(Contract.contract_id==x.contract_id).with_for_update())
    if not contract or contract.status.lower() != "active": raise HTTPException(409,"لا يمكن ترحيل مستخلص لعقد غير فعّال")
    cfg=db.scalar(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==x.contract_id,ContractAccountingConfig.settlement_side==x.settlement_side))
    if not cfg: raise HTTPException(422,"لم يتم ضبط حسابات المحاسبة لهذا العقد ونوع المستخلص")
    fy=db.get(FiscalYear,cfg.fiscal_year_id)
    if not fy or fy.is_closed or not (fy.start_date<=x.settlement_date<=fy.end_date): raise HTTPException(422,"السنة المالية مغلقة أو تاريخ المستخلص خارجها")
    lines=[]
    def line(account_id,debit=ZERO,credit=ZERO,desc="",project_id=None):
        if not account_id: raise HTTPException(422,"حساب محاسبي مطلوب غير مضبوط")
        acc=db.get(Account,account_id)
        if not acc or not acc.is_active: raise HTTPException(422,f"الحساب {account_id} غير موجود أو غير نشط")
        if money(debit)>0 or money(credit)>0: lines.append((account_id,money(debit),money(credit),desc,project_id))
    side=x.settlement_side; deductions=dict(x.deductions_json or {})
    live={r.code:r for r in db.scalars(select(ContractDeductionRule).where(ContractDeductionRule.contract_id==x.contract_id,ContractDeductionRule.settlement_side==side)).all()}
    for code,d in deductions.items():
        if money(d.get("amount",0))>0 and not d.get("account_id"):
            r=live.get(code); d["account_id"]=resolve_rule_account(code,d.get("name"),r.gl_account_id if r else None,cfg)
            if not d["account_id"]: raise HTTPException(422,f"قاعدة الخصم «{d.get('name',code)}» غير مربوطة بحساب في شجرة الحسابات؛ اربطها من تفاصيل العقد ثم أعد المحاولة")
    # Revalidate the persisted settlement arithmetic before creating any journal rows.
    # This protects against stale/inconsistent records and manual database edits; the
    # journal must agree with the settlement header, not merely balance by coincidence.
    if money(x.work_value) < ZERO or money(x.vat_amount) < ZERO or money(x.net_amount) < ZERO:
        raise HTTPException(422, "قيم المستخلص المخزنة لا يمكن أن تكون سالبة")
    for code, deduction in deductions.items():
        amount = money(deduction.get("amount", 0))
        if amount < ZERO:
            raise HTTPException(422, f"قيمة الخصم {code} سالبة؛ راجع المستخلص قبل الترحيل")
        deduction["amount"] = str(amount)
    total_d = money(sum((Decimal(str(d["amount"])) for d in deductions.values()), ZERO))
    expected_net = money(Decimal(str(x.work_value)) + Decimal(str(x.vat_amount)) - total_d)
    if expected_net < ZERO or expected_net != money(x.net_amount):
        raise HTTPException(422, f"صافي المستخلص غير مطابق للأعمال والضريبة والخصومات: المتوقع {expected_net} والمخزن {money(x.net_amount)}. أعد مراجعة المستخلص قبل الترحيل.")
    x.deductions_json=deductions
    # Customer: receivable net + deductible balances; credit contract revenue and output VAT.
    # Subcontractor: debit project cost and input VAT; credit payable net + withheld amounts.
    settlement_items=db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id==x.settlement_id).order_by(ContractSettlementItem.settlement_item_id)).all()
    item_work_total=money(sum((Decimal(str(i.amount)) for i in settlement_items),ZERO))
    if settlement_items and item_work_total!=money(x.work_value):
        raise HTTPException(422,f"إجمالي بنود المستخلص {item_work_total} لا يطابق قيمة الأعمال {money(x.work_value)}")
    def work_account_lines(*, debit=False):
        if not settlement_items:
            line(cfg.work_account_id,debit=x.work_value if debit else ZERO,credit=ZERO if debit else x.work_value,desc="أعمال عقد")
            return
        # New item lines post to their mapped accounts; legacy lines without a link
        # continue to use the contract-level work account.
        for si in settlement_items:
            aid=si.account_id or cfg.work_account_id
            contract_item=db.get(ContractItem,si.contract_item_id)
            item_desc=contract_item.description if contract_item else "بند عقد"
            line(aid,debit=si.amount if debit else ZERO,credit=ZERO if debit else si.amount,desc=item_desc,project_id=contract_item.project_id if contract_item else None)
    if side=="Customer":
        line(cfg.control_account_id,debit=x.net_amount,desc="صافي مستخلص عميل")
        for code,d in deductions.items():
            amt=money(d["amount"]); aid=d.get("account_id")
            if amt and d.get("posting_side")!="Debit": raise HTTPException(422,f"قاعدة الخصم {code}: جهة القيد يجب أن تكون Debit في مستخلص العميل")
            if amt: line(aid,debit=amt,desc=d.get("name",code))
        work_account_lines()
        if x.vat_amount: line(cfg.vat_account_id,credit=x.vat_amount,desc="ضريبة قيمة مضافة مخرجات")
    else:
        work_account_lines(debit=True)
        if x.vat_amount: line(cfg.vat_account_id,debit=x.vat_amount,desc="ضريبة قيمة مضافة مدخلات")
        for code,d in deductions.items():
            amt=money(d["amount"]); aid=d.get("account_id")
            if amt and d.get("posting_side")!="Credit": raise HTTPException(422,f"قاعدة الخصم {code}: جهة القيد يجب أن تكون Credit في مستخلص مقاول الباطن")
            if amt: line(aid,credit=amt,desc=d.get("name",code))
        line(cfg.control_account_id,credit=x.net_amount,desc="صافي مستحق مقاول باطن")
    debit=money(sum((r[1] for r in lines),ZERO));credit=money(sum((r[2] for r in lines),ZERO))
    if debit!=credit: raise HTTPException(422,f"القيد غير متوازن: مدين {debit} / دائن {credit}. راجع الحسابات وقواعد الخصم والضريبة.")
    # Number is unique; generated per company/year with row lock on the settlement and a uniqueness constraint in JournalEntries.
    entry_no=f"CS-{x.settlement_id:08d}"
    entry=JournalEntry(entry_no=entry_no,entry_date=x.settlement_date,company_id=cfg.company_id,fiscal_year_id=cfg.fiscal_year_id,description=f"ترحيل مستخلص {x.settlement_no} للعقد {x.contract_id}",source_settlement_id=x.settlement_id,status="Posted",created_by=user.user_id,posted_by=user.user_id,posted_at=datetime.utcnow())
    db.add(entry);db.flush()
    contract=db.get(Contract,x.contract_id)
    for idx,(aid,dr,cr,desc,project_id) in enumerate(lines,1): db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=idx,account_id=aid,project_id=project_id or contract.project_id,debit_amount=dr,credit_amount=cr,description=desc))
    write_audit(db,user.user_id,"Create","JournalEntries",entry.journal_entry_id,new={"entry_no":entry.entry_no,"source":"ContractSettlement","settlement_id":x.settlement_id,"settlement_no":x.settlement_no,"contract_id":x.contract_id,"debit_total":str(debit),"credit_total":str(credit)})
    x.journal_entry_id=entry.journal_entry_id;x.status="Posted";write_audit(db,user.user_id,"Post","ContractSettlements",x.settlement_id,new={**settlement_out(x, db),"journal_entry_id":entry.journal_entry_id});db.commit();db.refresh(x)
    return {"settlement":settlement_out(x, db),"journal_entry_id":entry.journal_entry_id,"entry_no":entry.entry_no,"debit_total":str(debit),"credit_total":str(credit)}


@router.delete("/settlements/{settlement_id}", status_code=204)
def delete_settlement(settlement_id: int, cascade: bool = False,
                      user: User = Depends(require_permission("ContractSettlements", "Delete")), db: Session = Depends(get_db)):
    """Delete only an unposted draft. A linked technical estimate is removed atomically too."""
    x = db.scalar(select(ContractSettlement).where(ContractSettlement.settlement_id == settlement_id).with_for_update())
    if not x: raise HTTPException(404, "المستخلص غير موجود")
    if cascade:
        require_admin(db, user.user_id)
        delete_settlement_tree(db, x, user.user_id)
        db.commit()
        return None
    if db.scalar(select(Check.check_id).where(Check.settlement_id == x.settlement_id).limit(1)) is not None:
        raise HTTPException(409, "لا يمكن حذف مستخلص مرتبط بشيك؛ استخدم الحذف العام كمسؤول نظام لفصل الشيك مع الحفاظ على سجله")
    if x.status not in ("Draft", "PendingApproval") or x.journal_entry_id is not None:
        raise HTTPException(409, "الحذف متاح قبل الاعتماد والترحيل فقط؛ المستخلص المعتمد أو المرحّل لا يُحذف حفاظًا على الأثر المحاسبي")
    linked = db.scalar(select(TechnicalSettlementEstimate).where(TechnicalSettlementEstimate.financial_settlement_id == x.settlement_id).with_for_update())
    if linked and linked.status not in ("UnderReview", "TechnicallyApproved", "ForwardedToFinance"):
        raise HTTPException(409, "لا يمكن حذف المستخلص المالي المرتبط بحالة فنية غير قابلة للحذف")
    old = settlement_out(x, db)
    if linked:
        write_audit(db, user.user_id, "Delete", "TechnicalSettlementEstimates", linked.estimate_id, old={"estimate_no": linked.estimate_no, "status": linked.status}, new=None)
        for line in db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id == linked.estimate_id)).all(): db.delete(line)
        db.delete(linked)
    for line in db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id == x.settlement_id)).all(): db.delete(line)
    write_audit(db, user.user_id, "Delete", "ContractSettlements", x.settlement_id, old=old, new=None)
    db.delete(x); db.commit()
