"""Technical-office progress estimates and automatic financial draft creation.

All changes are additive. Financial posting continues through the existing, permission-checked
ContractSettlements approve/post workflow.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import (User, Contract, ContractItem, ContractSettlement, ContractSettlementItem,
    TechnicalSettlementEstimate, TechnicalSettlementEstimateItem, ContractDeductionRule,
    ContractAccountingConfig, ProgressBilling, ContractAddendum, ContractChangeOrder, ContractSettlementSchedule)

from .contract_erp import resolve_rule_account
from ..contract_deletion import delete_settlement_tree, require_admin
router = APIRouter(prefix="/api/technical-settlements", tags=["Technical Office Settlements"])
CENT = Decimal("0.01")
def money(v): return Decimal(str(v or 0)).quantize(CENT, rounding=ROUND_HALF_UP)

class EstimateLine(BaseModel):
    contract_item_id: int = Field(gt=0)
    current_quantity: Decimal = Field(gt=0)
class EstimateIn(BaseModel):
    contract_id: int = Field(gt=0)
    planned_schedule_id: int | None = Field(default=None, gt=0)
    is_final: bool = False
    settlement_side: Literal["Customer", "Subcontractor"]
    # Optional for backward compatibility; the server assigns the final number.
    estimate_no: str | None = Field(default=None, max_length=50)
    estimate_date: date | None = None
    counterparty_name: str = Field(min_length=1, max_length=200)
    counterparty_name_en: str | None = Field(default=None, max_length=200)
    items: list[EstimateLine] = Field(min_length=1)
    notes: str | None = None

class TechnicalReviewLine(BaseModel):
    estimate_item_id: int = Field(gt=0)
    approved_quantity: Decimal = Field(ge=0)
    review_note: str | None = Field(default=None, max_length=2000)

class TechnicalReviewIn(BaseModel):
    items: list[TechnicalReviewLine] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=2000)

class TechnicalCorrectionLine(BaseModel):
    estimate_item_id: int = Field(gt=0)
    current_quantity: Decimal = Field(ge=0)

class TechnicalCorrectionIn(BaseModel):
    items: list[TechnicalCorrectionLine] = Field(min_length=1)
    notes: str = Field(min_length=1, max_length=2000)

class TechnicalReturnIn(BaseModel):
    notes: str = Field(min_length=1, max_length=2000)

def estimate_out(x, db):
    c = db.get(Contract, x.contract_id)
    lines = db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id == x.estimate_id)).all()
    return {"estimate_id":x.estimate_id,"contract_id":x.contract_id,"contract_no":c.contract_no if c else "",
        "contract_title":c.title if c else "", "contract_title_en":c.title_en if c else None,"settlement_side":x.settlement_side,"estimate_no":x.estimate_no,
        "estimate_date":x.estimate_date,"is_final":bool(getattr(x,"is_final",False)),"counterparty_name":x.counterparty_name,"counterparty_name_en":x.counterparty_name_en,"work_value":str(x.work_value),
        "status":x.status,"notes":x.notes,"created_by":x.created_by,"financial_settlement_id":x.financial_settlement_id,"planned_schedule_id":next((r.schedule_id for r in db.scalars(select(ContractSettlementSchedule).where(ContractSettlementSchedule.technical_estimate_id==x.estimate_id)).all()),None),
        "items":[{"estimate_item_id":i.estimate_item_id,"contract_item_id":i.contract_item_id,
          "item_no":(db.get(ContractItem,i.contract_item_id).item_no if db.get(ContractItem,i.contract_item_id) else ""),
          "description":(db.get(ContractItem,i.contract_item_id).description if db.get(ContractItem,i.contract_item_id) else ""),
          "unit":(db.get(ContractItem,i.contract_item_id).unit if db.get(ContractItem,i.contract_item_id) else ""),
          "contract_quantity":str(db.get(ContractItem,i.contract_item_id).quantity if db.get(ContractItem,i.contract_item_id) else 0),"previous_quantity":str(i.previous_quantity),"current_quantity":str(i.current_quantity),
          "total_quantity":str(i.previous_quantity+(i.approved_quantity if i.approved_quantity is not None else i.current_quantity)),"progress_percent":str((i.previous_quantity+(i.approved_quantity if i.approved_quantity is not None else i.current_quantity))/Decimal(str(db.get(ContractItem,i.contract_item_id).quantity or 1))*Decimal("100")) if db.get(ContractItem,i.contract_item_id) and Decimal(str(db.get(ContractItem,i.contract_item_id).quantity or 0))>0 else "0","unit_price":str(i.unit_price),"amount":str(i.amount),"approved_quantity":str(i.approved_quantity) if i.approved_quantity is not None else None,"review_note":i.review_note,"reviewed_by":i.reviewed_by,"reviewed_at":i.reviewed_at} for i in lines]}

def next_estimate_no(db: Session, contract_id: int) -> str:
    """Return the first unused technical estimate number for a contract."""
    used = set(db.scalars(select(TechnicalSettlementEstimate.estimate_no).where(
        TechnicalSettlementEstimate.contract_id == contract_id)).all())
    sequence = 1
    while f"TE-{sequence:04d}" in used:
        sequence += 1
    return f"TE-{sequence:04d}"

@router.get("")
def list_estimates(_: User=Depends(require_permission("ContractSettlements","View")), db: Session=Depends(get_db)):
    rows=db.scalars(select(TechnicalSettlementEstimate).order_by(TechnicalSettlementEstimate.estimate_date.desc(),TechnicalSettlementEstimate.estimate_id.desc()).limit(1000)).all()
    return {"items":[estimate_out(x,db) for x in rows]}

@router.get("/next-number")
def preview_estimate_no(contract_id: int, _: User=Depends(require_permission("ContractSettlements", "Add")), db: Session=Depends(get_db)):
    if not db.get(Contract, contract_id):
        raise HTTPException(404, "العقد غير موجود")
    return {"estimate_no": next_estimate_no(db, contract_id)}

@router.post("", status_code=201)
def create_estimate(body: EstimateIn, user: User=Depends(require_permission("ContractSettlements","Add")), db: Session=Depends(get_db)):
    c=db.scalar(select(Contract).where(Contract.contract_id==body.contract_id).with_for_update())
    if not c: raise HTTPException(404,"العقد غير موجود")
    if (c.status or "").lower()!="active": raise HTTPException(409,"لا يمكن إعداد مستخلص فني إلا لعقد نشط ومعتمد نهائياً")
    if db.scalar(select(ContractSettlement.settlement_id).where(ContractSettlement.contract_id==c.contract_id,ContractSettlement.settlement_side==body.settlement_side,ContractSettlement.is_final.is_(True)).limit(1)):
        raise HTTPException(409,"تم تحديد مستخلص ختامي لهذا العقد ونوع المستخلص؛ لا يمكن إنشاء مستخلصات إضافية بعده")
    estimate_no = next_estimate_no(db, c.contract_id)
    planned_row = None
    if body.planned_schedule_id is not None:
        planned_row = db.scalar(select(ContractSettlementSchedule).where(
            ContractSettlementSchedule.schedule_id == body.planned_schedule_id,
            ContractSettlementSchedule.contract_id == c.contract_id).with_for_update())
        if not planned_row:
            raise HTTPException(422, "المستخلص المخطط لا يتبع هذا العقد")
        if planned_row.technical_estimate_id is not None:
            raise HTTPException(409, "تم ربط هذا المستخلص المخطط بمستخلص فني بالفعل")
    legacy=db.scalar(select(func.coalesce(func.sum(ProgressBilling.work_value),0)).where(ProgressBilling.contract_id==c.contract_id,func.lower(ProgressBilling.status).in_(("approved","paid","posted")))) or 0
    if Decimal(str(legacy))>0: raise HTTPException(409,"يوجد تاريخ مستخلصات قديمة غير موزع على بنود؛ راجع الكميات التاريخية قبل إعداد مستخلص فني جديد")
    seen=set(); prepared=[]; total=Decimal("0")
    for req in body.items:
        if req.contract_item_id in seen: raise HTTPException(422,"لا يمكن تكرار البند داخل المستخلص")
        seen.add(req.contract_item_id)
        item=db.scalar(select(ContractItem).where(ContractItem.item_id==req.contract_item_id,ContractItem.contract_id==c.contract_id))
        if not item: raise HTTPException(422,f"البند {req.contract_item_id} لا يتبع العقد")
        prev_ids=select(TechnicalSettlementEstimate.estimate_id).where(TechnicalSettlementEstimate.contract_id==c.contract_id,TechnicalSettlementEstimate.settlement_side==body.settlement_side,TechnicalSettlementEstimate.status.in_(("TechnicallyApproved", "ForwardedToFinance")))
        prev=db.scalar(select(func.coalesce(func.sum(func.coalesce(TechnicalSettlementEstimateItem.approved_quantity, TechnicalSettlementEstimateItem.current_quantity)),0)).where(TechnicalSettlementEstimateItem.contract_item_id==item.item_id,TechnicalSettlementEstimateItem.estimate_id.in_(prev_ids))) or 0
        # Include posted/approved financial settlement quantities if the history predates this technical workflow.
        linked_financial_ids=select(TechnicalSettlementEstimate.financial_settlement_id).where(TechnicalSettlementEstimate.financial_settlement_id.is_not(None))
        valid_ids=select(ContractSettlement.settlement_id).where(ContractSettlement.contract_id==c.contract_id,ContractSettlement.settlement_side==body.settlement_side,ContractSettlement.status.in_(("Approved","Posted")),ContractSettlement.settlement_id.not_in(linked_financial_ids))
        fin_prev=db.scalar(select(func.coalesce(func.sum(ContractSettlementItem.quantity),0)).where(ContractSettlementItem.contract_item_id==item.item_id,ContractSettlementItem.settlement_id.in_(valid_ids))) or 0
        previous=Decimal(str(prev))+Decimal(str(fin_prev))
        if req.current_quantity > Decimal(item.quantity)-previous: raise HTTPException(409,f"كمية البند {item.item_no} تتجاوز الكمية المتبقية")
        amount=money(req.current_quantity*item.unit_price); total+=amount; prepared.append((item,previous,req.current_quantity,amount))
    total=money(total)
    if total<=0: raise HTTPException(422,"قيمة الأعمال يجب أن تكون أكبر من صفر")
    # New estimates must enter the independent engineering queue. Submitted quantities
    # are not approved quantities and must never create a financial settlement here.
    x=TechnicalSettlementEstimate(contract_id=c.contract_id,settlement_side=body.settlement_side,estimate_no=estimate_no,
       estimate_date=(body.estimate_date if body.estimate_date else datetime.utcnow().date()),counterparty_name=body.counterparty_name,counterparty_name_en=body.counterparty_name_en,
       work_value=total,status="UnderReview",is_final=body.is_final,notes=body.notes,created_by=user.user_id)
    db.add(x);db.flush()
    if planned_row is not None:
        planned_row.technical_estimate_id = x.estimate_id
        planned_row.status = "Submitted"
    for item,prev,qty,amount in prepared:
        db.add(TechnicalSettlementEstimateItem(estimate_id=x.estimate_id,contract_item_id=item.item_id,previous_quantity=prev,current_quantity=qty,approved_quantity=None,unit_price=item.unit_price,amount=amount))
    write_audit(db,user.user_id,"Create","TechnicalSettlementEstimates",x.estimate_id,
        new={"estimate_no":x.estimate_no,"work_value":str(total),"status":"UnderReview","engineering_approval":False})
    db.commit()
    db.refresh(x)
    return {"estimate":estimate_out(x,db),"financial_settlement_id":None,"financial_settlement_no":None,
        "financial_status":None,"message":"تم حفظ المستخلص وإرساله إلى قائمة المراجعة الفنية. لن يُنشأ مستخلص مالي قبل المراجعة والاعتماد الفني."}

@router.post("/{estimate_id}/return")
def return_estimate_for_correction(estimate_id: int, body: TechnicalReturnIn,
        user: User = Depends(require_permission("ContractSettlements", "EngineeringApprove")),
        db: Session = Depends(get_db)):
    x = db.scalar(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.estimate_id == estimate_id).with_for_update())
    if not x:
        raise HTTPException(404, "المستخلص الفني غير موجود")
    if x.status != "UnderReview":
        raise HTTPException(409, "لا يمكن إرجاع المستخلص إلا أثناء المراجعة الفنية")
    if x.created_by == user.user_id:
        raise HTTPException(403, "لا يجوز لمُعدّ المستخلص إرجاع مستخلصه لنفسه")
    reason = body.notes.strip()
    if not reason:
        raise HTTPException(422, "يجب كتابة ملاحظات الاستكمال")
    old_status = x.status
    x.status = "ReturnedForCorrection"
    x.notes = (x.notes or "") + f"\nإرجاع للاستكمال بواسطة {user.user_id}: {reason}"
    write_audit(db, user.user_id, "ReturnForCorrection", "TechnicalSettlementEstimates", estimate_id,
        old={"status": old_status}, new={"status": x.status, "reason": reason, "created_by": x.created_by})
    db.commit()
    db.refresh(x)
    return {"estimate": estimate_out(x, db), "message": "تم إرجاع المستخلص للمهندس المُعد لاستكمال الملاحظات."}


@router.post("/{estimate_id}/resubmit")
def resubmit_corrected_estimate(estimate_id: int, body: TechnicalCorrectionIn,
        user: User = Depends(require_permission("ContractSettlements", "Add")),
        db: Session = Depends(get_db)):
    x = db.scalar(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.estimate_id == estimate_id).with_for_update())
    if not x:
        raise HTTPException(404, "المستخلص الفني غير موجود")
    if x.status != "ReturnedForCorrection":
        raise HTTPException(409, "المستخلص ليس مُعاداً للاستكمال")
    if x.created_by != user.user_id:
        raise HTTPException(403, "فقط المهندس الذي أنشأ المستخلص يمكنه استكماله وإعادة تقديمه")
    lines = db.scalars(select(TechnicalSettlementEstimateItem).where(
        TechnicalSettlementEstimateItem.estimate_id == estimate_id).with_for_update()).all()
    requested = {row.estimate_item_id: row for row in body.items}
    if len(requested) != len(body.items) or set(requested) != {line.estimate_item_id for line in lines}:
        raise HTTPException(422, "يجب إرسال جميع بنود المستخلص مرة واحدة دون تكرار")
    total = Decimal("0")
    changes = []
    for line in lines:
        item = db.get(ContractItem, line.contract_item_id)
        if not item:
            raise HTTPException(409, "أحد بنود العقد لم يعد موجوداً")
        quantity = requested[line.estimate_item_id].current_quantity
        remaining = Decimal(str(item.quantity or 0)) - Decimal(str(line.previous_quantity or 0))
        if quantity > remaining:
            raise HTTPException(422, f"الكمية المعدلة للبند {item.item_no} تتجاوز المتبقي في العقد")
        old_quantity = line.current_quantity
        line.current_quantity = quantity
        line.approved_quantity = None
        line.review_note = None
        line.reviewed_by = None
        line.reviewed_at = None
        line.amount = money(quantity * line.unit_price)
        total += line.amount
        changes.append({"estimate_item_id": line.estimate_item_id,
            "old_quantity": str(old_quantity), "resubmitted_quantity": str(quantity)})
    total = money(total)
    if total <= 0:
        raise HTTPException(422, "يجب أن يحتوي المستخلص على كمية موجبة واحدة على الأقل")
    old_status = x.status
    x.work_value = total
    x.status = "UnderReview"
    x.technical_reviewed_by = None
    x.technical_reviewed_at = None
    x.notes = (x.notes or "") + f"\nإعادة تقديم بواسطة المهندس المُعد: {body.notes.strip()}"
    write_audit(db, user.user_id, "ResubmitAfterCorrection", "TechnicalSettlementEstimates", estimate_id,
        old={"status": old_status}, new={"status": x.status, "work_value": str(total), "items": changes, "notes": body.notes.strip()})
    db.commit()
    db.refresh(x)
    return {"estimate": estimate_out(x, db), "message": "تم استكمال المستخلص وإعادة إرساله للمراجعة الفنية."}


@router.post("/{estimate_id}/review")
def review_estimate(estimate_id: int, body: TechnicalReviewIn,
                    user: User = Depends(require_permission("ContractSettlements", "EngineeringApprove")),
                    db: Session = Depends(get_db)):
    x = db.scalar(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.estimate_id == estimate_id).with_for_update())
    if not x:
        raise HTTPException(404, "المستخلص الفني غير موجود")
    if x.status != "UnderReview":
        raise HTTPException(409, "المستخلص ليس في مرحلة المراجعة الفنية")
    if x.created_by == user.user_id:
        raise HTTPException(403, "لا يجوز لمُعدّ المستخلص مراجعته بنفسه")
    lines = db.scalars(select(TechnicalSettlementEstimateItem).where(
        TechnicalSettlementEstimateItem.estimate_id == estimate_id).with_for_update()).all()
    requested = {row.estimate_item_id: row for row in body.items}
    if len(requested) != len(body.items) or set(requested) != {line.estimate_item_id for line in lines}:
        raise HTTPException(422, "يجب مراجعة جميع بنود المستخلص مرة واحدة دون تكرار")
    approved_total = Decimal("0")
    audit_lines = []
    for line in lines:
        decision = requested[line.estimate_item_id]
        approved = decision.approved_quantity
        if approved > line.current_quantity:
            raise HTTPException(422, "الكمية المعتمدة لا يجوز أن تتجاوز الكمية المقدمة")
        if approved < line.current_quantity and not (decision.review_note or "").strip():
            raise HTTPException(422, "يجب كتابة سبب عند تخفيض أو رفض كمية أي بند")
        item = db.get(ContractItem, line.contract_item_id)
        if not item:
            raise HTTPException(409, "أحد بنود العقد لم يعد موجوداً")
        line.approved_quantity = approved
        line.review_note = (decision.review_note or "").strip() or None
        line.reviewed_by = user.user_id
        line.reviewed_at = datetime.utcnow()
        line.amount = money(approved * line.unit_price)
        approved_total += line.amount
        audit_lines.append({"estimate_item_id": line.estimate_item_id,
            "submitted_quantity": str(line.current_quantity), "approved_quantity": str(approved),
            "review_note": line.review_note})
    approved_total = money(approved_total)
    if approved_total <= 0:
        raise HTTPException(422, "لا يمكن إحالة مستخلص دون أي كميات معتمدة")
    x.work_value = approved_total
    x.technical_reviewed_by = user.user_id
    x.technical_reviewed_at = datetime.utcnow()
    x.status = "TechnicalReviewed"
    write_audit(db, user.user_id, "TechnicalReview", "TechnicalSettlementEstimates", estimate_id,
        old={"status": "UnderReview"}, new={"status": x.status, "work_value": str(approved_total), "items": audit_lines, "notes": body.notes})
    if body.notes and body.notes.strip():
        x.notes = (x.notes or "") + f"\nملاحظات المراجعة الفنية: {body.notes.strip()}"
    db.commit()
    db.refresh(x)
    return {"estimate": estimate_out(x, db), "message": "تم حفظ مراجعة البنود. المستخلص جاهز للاعتماد الفني النهائي."}


def _create_financial_from_estimate(estimate_id:int, user:User, db:Session):
    x=db.scalar(select(TechnicalSettlementEstimate).where(TechnicalSettlementEstimate.estimate_id==estimate_id).with_for_update())
    if not x: raise HTTPException(404,"المستخلص الفني غير موجود")
    if x.status!="TechnicalReviewed": raise HTTPException(409,"يجب إتمام مراجعة البنود الفنية أولاً")
    if x.technical_reviewed_by == user.user_id or x.created_by == user.user_id: raise HTTPException(403,"لا يجوز لمُعدّ المستخلص أو مراجع البنود اعتماده فنياً")
    c=db.get(Contract,x.contract_id)
    if not c or (c.status or "").lower()!="active": raise HTTPException(409,"العقد لم يعد نشطاً")
    lines=db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id==x.estimate_id)).all()
    work=money(x.work_value)
    cfg=db.scalar(select(ContractAccountingConfig).where(ContractAccountingConfig.contract_id==x.contract_id,ContractAccountingConfig.settlement_side==x.settlement_side))
    rules=db.scalars(select(ContractDeductionRule).where(ContractDeductionRule.contract_id==x.contract_id,ContractDeductionRule.settlement_side==x.settlement_side,ContractDeductionRule.is_active.is_(True)).order_by(ContractDeductionRule.sort_order,ContractDeductionRule.rule_id)).all()
    # Use the same configured deductions as the existing financial-settlement engine.
    prior_technical=db.scalar(select(func.coalesce(func.sum(TechnicalSettlementEstimate.work_value),0)).where(TechnicalSettlementEstimate.contract_id==x.contract_id,TechnicalSettlementEstimate.settlement_side==x.settlement_side,TechnicalSettlementEstimate.status.in_(("TechnicallyApproved", "ForwardedToFinance")),TechnicalSettlementEstimate.estimate_id!=x.estimate_id)) or 0
    linked_financial_ids=select(TechnicalSettlementEstimate.financial_settlement_id).where(TechnicalSettlementEstimate.financial_settlement_id.is_not(None))
    prior_financial=db.scalar(select(func.coalesce(func.sum(ContractSettlement.work_value),0)).where(ContractSettlement.contract_id==x.contract_id,ContractSettlement.settlement_side==x.settlement_side,ContractSettlement.status.in_(("Approved","Posted")),ContractSettlement.settlement_id.not_in(linked_financial_ids))) or 0
    previous=money(Decimal(str(prior_technical))+Decimal(str(prior_financial)))
    # Match the financial settlement engine: remaining-contract deductions must use
    # the amended contract value, including approved change orders.
    addenda_value=db.scalar(select(func.coalesce(func.sum(ContractAddendum.value_change),0)).where(ContractAddendum.contract_id==x.contract_id,ContractAddendum.status=="Approved")) or 0
    change_value=db.scalar(select(func.coalesce(func.sum(ContractChangeOrder.value_change),0)).where(ContractChangeOrder.contract_id==x.contract_id,ContractChangeOrder.status=="Approved")) or 0
    contract_value=money(Decimal(str(c.original_value or 0))+Decimal(str(addenda_value))+Decimal(str(change_value)))
    cumulative=money(previous+work)
    if cumulative > contract_value:
        raise HTTPException(409,f"إجمالي الأعمال التراكمي {cumulative} يتجاوز قيمة العقد المعدلة {contract_value}")
    deductions={}; total_d=Decimal("0")
    for r in rules:
        base=work if r.base_type=="CurrentWork" else cumulative if r.base_type=="CumulativeWork" else max(Decimal("0"),contract_value-cumulative)
        amount=money(base*Decimal(str(r.rate))/Decimal("100")) if r.calculation_type=="Percent" else money(r.rate)
        if r.cap_amount is not None: amount=min(amount,money(r.cap_amount))
        account=resolve_rule_account(r.code,r.name_ar,r.gl_account_id,cfg)
        if amount>0 and not account: raise HTTPException(422,f"قاعدة الخصم «{r.name_ar}» غير مربوطة بحساب في شجرة الحسابات. اربطها من تفاصيل العقد (ربط تلقائي بالشجرة) ثم أعد حفظ المستخلص.")
        deductions[r.code]={"name":r.name_ar,"amount":str(amount),"account_id":account,"posting_side":r.posting_side};total_d+=amount
    # Add the standard settlement-template deduction rows to every incoming financial draft.
    # They start at zero and can be edited by Finance; positive values still require a
    # properly configured contract deduction rule/account before journal posting.
    standard_rows = [
        ("ADVANCE_PAYMENT", "دفعة مقدمة", ("دفعة مقدمة", "سلفة", "مقدم")),
        ("RETENTION", "تأمين محجوز", ("تأمين محجوز", "محجوز")),
        ("FINAL_INSURANCE", "تأمين نهائي", ("تأمين نهائي", "نهائي")),
        ("PROFIT_TAX", "ضرائب أرباح", ("ضريبة أرباح", "ضرائب أرباح", "خصم ضريبة")),
        ("ENGINEERING_STAMP", "دمغات هندسية", ("دمغة هندسية", "دمغات هندسية")),
        ("UNION_STAMP", "دمغات اتحاد", ("دمغة اتحاد", "دمغات اتحاد", "اتحاد")),
        ("STORE_WITHDRAWALS", "مسحوبات ومصاريف مخازن", ("مخازن", "مسحوبات")),
        ("TRANSPORT", "نقل", ("نقل", "مواصلات")),
        ("DIESEL", "سولار", ("سولار", "وقود")),
        ("MEALS", "وجبات", ("وجبات", "إعاشة")),
        ("ADDITIONS", "تعليات", ("تعليات", "تعلية")),
    ]
    existing_names = [str(v.get("name", "")).casefold() for v in deductions.values()]
    for code, label, aliases in standard_rows:
        if code in deductions or any(alias.casefold() in name for alias in aliases for name in existing_names):
            continue
        deductions[code] = {"name": label, "amount": "0.00", "account_id": None,
                            "posting_side": "Debit" if x.settlement_side == "Customer" else "Credit"}
    vat_rate=Decimal(str(cfg.default_vat_rate if cfg else 0)); vat=money(work*vat_rate/Decimal("100")); net=money(work+vat-total_d)
    if net<0: raise HTTPException(422,"الخصومات أكبر من صافي الأعمال والضريبة")
    seq=(db.scalar(select(func.max(ContractSettlement.sequence_no)).where(ContractSettlement.contract_id==x.contract_id,ContractSettlement.settlement_side==x.settlement_side)) or 0)+1
    fin=ContractSettlement(contract_id=x.contract_id,settlement_side=x.settlement_side,sequence_no=seq,settlement_no=f"FIN-{x.estimate_id:06d}",settlement_date=x.estimate_date,counterparty_name=x.counterparty_name,work_value=work,cumulative_work_value=cumulative,deductions_json=deductions,vat_amount=vat,net_amount=net,status="Draft",is_final=bool(getattr(x,"is_final",False)),notes=f"تم إنشاؤه تلقائياً من المستخلص الفني {x.estimate_no}. {x.notes or ''}".strip(),created_by=user.user_id)
    db.add(fin);db.flush()
    for line in lines:
        approved_qty = line.approved_quantity if line.approved_quantity is not None else Decimal("0")
        if approved_qty > 0:
            db.add(ContractSettlementItem(settlement_id=fin.settlement_id,contract_item_id=line.contract_item_id,quantity=approved_qty,unit_price=line.unit_price,amount=money(approved_qty*line.unit_price)))
    x.status="ForwardedToFinance";x.reviewed_by=None;x.reviewed_at=None;x.financial_settlement_id=fin.settlement_id
    linked_schedule=db.scalar(select(ContractSettlementSchedule).where(ContractSettlementSchedule.technical_estimate_id==x.estimate_id).with_for_update())
    if linked_schedule is not None: linked_schedule.status="Submitted"
    write_audit(db,user.user_id,"ForwardToFinance","TechnicalSettlementEstimates",x.estimate_id,new={"status":x.status,"financial_settlement_id":fin.settlement_id,"work_value":str(work),"engineering_approval":False})
    db.commit();db.refresh(fin)
    return {"estimate":estimate_out(x,db),"financial_settlement_id":fin.settlement_id,"financial_settlement_no":fin.settlement_no,"financial_status":fin.status,"net_amount":str(fin.net_amount),"message":"تم حفظ المستخلص وتحويله مباشرة إلى المالية دون اعتماد هندسي؛ المستخلص المالي الآن مسودة للمراجعة."}


@router.post("/{estimate_id}/approve")
def approve_estimate(estimate_id: int, user: User = Depends(require_permission("ContractSettlements", "Approve")), db: Session = Depends(get_db)):
    return _create_financial_from_estimate(estimate_id, user, db)


@router.delete("/{estimate_id}", status_code=204)
def delete_estimate(estimate_id: int, cascade: bool = False,
                    user: User = Depends(require_permission("ContractSettlements", "Delete")), db: Session = Depends(get_db)):
    x = db.scalar(select(TechnicalSettlementEstimate).where(TechnicalSettlementEstimate.estimate_id == estimate_id).with_for_update())
    if not x: raise HTTPException(404, "المستخلص الفني غير موجود")
    linked_schedule=db.scalar(select(ContractSettlementSchedule).where(ContractSettlementSchedule.technical_estimate_id==x.estimate_id).with_for_update())
    if linked_schedule is not None:
        linked_schedule.technical_estimate_id=None
        linked_schedule.status="Planned"
    if cascade:
        require_admin(db, user.user_id)
        financial = db.get(ContractSettlement, x.financial_settlement_id) if x.financial_settlement_id else None
        if financial:
            delete_settlement_tree(db, financial, user.user_id)
        else:
            for line in db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id == x.estimate_id)).all(): db.delete(line)
            write_audit(db, user.user_id, "DeleteCascade", "TechnicalSettlementEstimates", x.estimate_id,
                        {"estimate_no": x.estimate_no, "status": x.status}, None)
            db.delete(x)
        db.commit()
        return None
    if x.financial_settlement_id is not None or x.status != "UnderReview":
        raise HTTPException(409, "يمكن حذف المستخلص الفني قبل الاعتماد الهندسي فقط؛ بعد التحويل للحسابات احذف المسودة المالية من شاشة الحسابات إذا كانت غير معتمدة")
    old = {"estimate_no": x.estimate_no, "status": x.status, "work_value": str(x.work_value)}
    for line in db.scalars(select(TechnicalSettlementEstimateItem).where(TechnicalSettlementEstimateItem.estimate_id == x.estimate_id)).all(): db.delete(line)
    write_audit(db, user.user_id, "Delete", "TechnicalSettlementEstimates", x.estimate_id, old=old, new=None)
    db.delete(x); db.commit()
