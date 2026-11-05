"""Inventory and purchasing workflow. All tables are additive; existing financial tables are untouched."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import (Account, Counterparty, FiscalYear, InventoryItem, InventoryWarehouse,
    InventoryMovement, InventoryStocktake, InventoryStocktakeLine, InventoryReturn, InventoryReturnLine, SiteIssueRequest, SiteIssueRequestLine, JournalEntry, JournalEntryDetail, PurchaseOrder, PurchaseOrderLine,
    SupplierInvoice, SupplierInvoiceLine, TreasuryAccount, TreasuryTransaction, Project, User, utcnow)
from ..counterparties import resolve_counterparty

inventory = APIRouter(prefix="/api/inventory", tags=["Inventory"])
purchases = APIRouter(prefix="/api/purchases", tags=["Purchasing"])

class WarehouseIn(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    location: str | None = None
    is_active: bool = True
class ItemIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=250)
    category: str | None = None
    unit: str = Field(default="قطعة", max_length=30)
    min_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True
class MovementIn(BaseModel):
    movement_no: str = Field(min_length=1, max_length=60)
    item_id: int
    warehouse_id: int
    movement_date: date = Field(default_factory=date.today)
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    reference: str | None = None
    notes: str | None = None
class MovementBatchLineIn(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
class MovementBatchIn(BaseModel):
    movement_no: str = Field(min_length=1, max_length=50)
    warehouse_id: int
    movement_date: date = Field(default_factory=date.today)
    movement_type: str
    lines: list[MovementBatchLineIn] = Field(min_length=1)
    reference: str | None = None
    notes: str | None = None
class InventoryReturnLineIn(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_order_line_id: int | None = None
    site_issue_line_id: int | None = None
class InventoryReturnIn(BaseModel):
    return_no: str = Field(min_length=1, max_length=60)
    return_type: str
    return_date: date = Field(default_factory=date.today)
    warehouse_id: int
    counterparty_name: str | None = None
    source_document: str | None = None
    notes: str | None = None
    lines: list[InventoryReturnLineIn] = Field(min_length=1)

class StocktakeLineIn(BaseModel):
    item_id: int
    counted_quantity: Decimal = Field(ge=0)
class StocktakeIn(BaseModel):
    stocktake_no: str = Field(min_length=1, max_length=60)
    warehouse_id: int
    stocktake_date: date = Field(default_factory=date.today)
    notes: str | None = None
    lines: list[StocktakeLineIn] = Field(min_length=1)

class SiteIssueRequestLineIn(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)
class SiteIssueRequestIn(BaseModel):
    request_no: str = Field(min_length=1, max_length=60)
    request_date: date = Field(default_factory=date.today)
    needed_by: date | None = None
    project_id: int | None = None
    site_name: str | None = Field(default=None, max_length=200)
    notes: str | None = None
    lines: list[SiteIssueRequestLineIn] = Field(min_length=1)
class SiteIssueRejectIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
class SiteIssuePostLineIn(BaseModel):
    line_id: int
    quantity: Decimal = Field(gt=0)
class SiteIssuePostIn(BaseModel):
    warehouse_id: int
    lines: list[SiteIssuePostLineIn] = Field(default_factory=list)

class StockTransferLineIn(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)

class StockTransferIn(BaseModel):
    transfer_no: str = Field(min_length=1, max_length=35)
    transfer_date: date = Field(default_factory=date.today)
    source_warehouse_id: int
    destination_warehouse_id: int
    lines: list[StockTransferLineIn] = Field(min_length=1)
    reference: str | None = None
    notes: str | None = None

class POLineIn(BaseModel):
    item_id: int
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
class PurchaseIn(BaseModel):
    order_no: str | None = Field(default=None, max_length=60)
    order_date: date = Field(default_factory=date.today)
    supplier_name: str = Field(min_length=1, max_length=250)
    warehouse_id: int
    project_id: int | None = None
    notes: str | None = None
    lines: list[POLineIn] = Field(min_length=1)

class SupplierInvoiceLineIn(BaseModel):
    purchase_order_line_id: int
    account_id: int
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)

class SupplierInvoiceIn(BaseModel):
    invoice_no: str = Field(min_length=1, max_length=60)
    invoice_date: date
    purchase_order_id: int
    tax_account_id: int | None = None
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    lines: list[SupplierInvoiceLineIn] = Field(min_length=1)

class SupplierInvoicePaymentIn(BaseModel):
    treasury_account_id: int
    transaction_date: date
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    voucher_no: str | None = Field(default=None, max_length=50)

def _cent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _invoice_account(db: Session, account_id: int, normal_balance: str, label: str) -> Account:
    account = db.get(Account, account_id)
    if not account or not account.is_active:
        raise HTTPException(422, f"{label}: الحساب غير موجود أو غير نشط")
    if db.scalar(select(Account.account_id).where(Account.parent_account_id == account_id)):
        raise HTTPException(422, f"{label}: اختر حسابًا فرعيًا")
    if account.normal_balance != normal_balance:
        raise HTTPException(422, f"{label}: طبيعة الحساب غير مناسبة")
    return account

def _balance(db: Session, item_id: int, warehouse_id: int) -> Decimal:
    rows = db.execute(select(InventoryMovement.movement_type, func.sum(InventoryMovement.quantity)).where(
        InventoryMovement.item_id == item_id, InventoryMovement.warehouse_id == warehouse_id
    ).group_by(InventoryMovement.movement_type)).all()
    total = Decimal("0")
    for typ, qty in rows:
        total += Decimal(str(qty or 0)) if typ == "IN" else -Decimal(str(qty or 0))
    return total

@inventory.get("/site-issue-requests")
def list_site_issue_requests(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    rows = db.scalars(select(SiteIssueRequest).order_by(SiteIssueRequest.request_date.desc(), SiteIssueRequest.request_id.desc()).limit(300)).all()
    result = []
    for request in rows:
        project = db.get(Project, request.project_id) if request.project_id else None
        requester = db.get(User, request.requested_by)
        approver = db.get(User, request.approved_by) if request.approved_by else None
        issuer = db.get(User, request.issued_by) if request.issued_by else None
        lines = []
        for line in db.scalars(select(SiteIssueRequestLine).where(SiteIssueRequestLine.request_id == request.request_id).order_by(SiteIssueRequestLine.line_id)).all():
            item = db.get(InventoryItem, line.item_id)
            lines.append({"line_id": line.line_id, "item_id": line.item_id,
                "item_code": item.code if item else "", "item": item.name if item else "",
                "unit": item.unit if item else "", "requested_quantity": str(line.requested_quantity),
                "approved_quantity": str(line.approved_quantity), "issued_quantity": str(line.issued_quantity),
                "remaining_quantity": str(Decimal(str(line.approved_quantity or 0)) - Decimal(str(line.issued_quantity or 0)))})
        result.append({"request_id": request.request_id, "request_no": request.request_no,
            "request_date": str(request.request_date), "needed_by": str(request.needed_by) if request.needed_by else None,
            "project": project.name_ar if project else "", "site_name": request.site_name or "",
            "requested_by": getattr(requester, "username", None) or str(request.requested_by),
            "approved_by": getattr(approver, "username", None) if approver else "",
            "issued_by": getattr(issuer, "username", None) if issuer else "",
            "status": request.status, "notes": request.notes, "lines": lines})
    return {"items": result}

@inventory.post("/site-issue-requests", status_code=201)
def create_site_issue_request(body: SiteIssueRequestIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if db.scalar(select(SiteIssueRequest.request_id).where(SiteIssueRequest.request_no == body.request_no)):
        raise HTTPException(409, "رقم طلب الصرف مستخدم بالفعل")
    if body.project_id is not None and not db.get(Project, body.project_id):
        raise HTTPException(422, "المشروع المحدد غير موجود")
    if len({line.item_id for line in body.lines}) != len(body.lines):
        raise HTTPException(422, "لا تكرر الصنف داخل طلب الصرف")
    for line in body.lines:
        item = db.get(InventoryItem, line.item_id)
        if not item or not item.is_active:
            raise HTTPException(422, f"الصنف {line.item_id} غير موجود أو غير نشط")
    request = SiteIssueRequest(request_no=body.request_no, request_date=body.request_date,
        needed_by=body.needed_by, project_id=body.project_id, site_name=body.site_name,
        requested_by=user.user_id, status="PendingApproval", notes=body.notes)
    db.add(request)
    try:
        db.flush()
        for line in body.lines:
            db.add(SiteIssueRequestLine(request_id=request.request_id, item_id=line.item_id,
                requested_quantity=line.quantity, approved_quantity=0, issued_quantity=0))
        write_audit(db, user.user_id, "Create", "SiteIssueRequests", request.request_id,
            new={"request_no": request.request_no, "status": request.status, "lines": len(body.lines)})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر حفظ الطلب؛ تحقق من رقم الطلب")
    return {"request_id": request.request_id, "request_no": request.request_no, "status": request.status}

@inventory.post("/site-issue-requests/{request_id}/approve")
def approve_site_issue_request(request_id: int, user: User = Depends(require_permission("InventoryManagement", "Approve")), db: Session = Depends(get_db)):
    request = db.scalar(select(SiteIssueRequest).where(SiteIssueRequest.request_id == request_id).with_for_update())
    if not request:
        raise HTTPException(404, "طلب الصرف غير موجود")
    if request.status != "PendingApproval":
        raise HTTPException(409, "الطلب ليس في انتظار الاعتماد")
    if request.requested_by == user.user_id:
        raise HTTPException(403, "لا يجوز اعتماد طلب الصرف بواسطة مقدم الطلب")
    lines = db.scalars(select(SiteIssueRequestLine).where(SiteIssueRequestLine.request_id == request_id).with_for_update()).all()
    if not lines:
        raise HTTPException(409, "طلب الصرف لا يحتوي على أصناف")
    for line in lines:
        item = db.get(InventoryItem, line.item_id)
        if not item or not item.is_active:
            raise HTTPException(409, "يوجد صنف غير متاح")
        line.approved_quantity = line.requested_quantity
    request.status = "Approved"
    request.approved_by = user.user_id
    request.approved_at = utcnow()
    write_audit(db, user.user_id, "Approve", "SiteIssueRequests", request_id,
        new={"status": request.status, "approved_lines": len(lines)})
    db.commit()
    return {"request_id": request_id, "status": request.status}

@inventory.post("/site-issue-requests/{request_id}/reject")
def reject_site_issue_request(request_id: int, body: SiteIssueRejectIn, user: User = Depends(require_permission("InventoryManagement", "Approve")), db: Session = Depends(get_db)):
    request = db.scalar(select(SiteIssueRequest).where(SiteIssueRequest.request_id == request_id).with_for_update())
    if not request:
        raise HTTPException(404, "طلب الصرف غير موجود")
    if request.status != "PendingApproval":
        raise HTTPException(409, "لا يمكن رفض الطلب في حالته الحالية")
    if request.requested_by == user.user_id:
        raise HTTPException(403, "لا يجوز رفض طلب الصرف بواسطة مقدم الطلب")
    request.status = "Rejected"
    request.notes = ((request.notes or "") + "\nسبب الرفض: " + body.reason).strip()
    request.approved_by = user.user_id
    request.approved_at = utcnow()
    write_audit(db, user.user_id, "Reject", "SiteIssueRequests", request_id,
        new={"status": request.status, "reason": body.reason})
    db.commit()
    return {"request_id": request_id, "status": request.status}

@inventory.post("/site-issue-requests/{request_id}/issue")
def issue_site_request_stock(request_id: int, body: SiteIssuePostIn, user: User = Depends(require_permission("InventoryManagement", "Post")), db: Session = Depends(get_db)):
    request = db.scalar(select(SiteIssueRequest).where(SiteIssueRequest.request_id == request_id).with_for_update())
    if not request:
        raise HTTPException(404, "طلب الصرف غير موجود")
    if request.status not in ("Approved", "PartiallyIssued"):
        raise HTTPException(409, "يجب اعتماد الطلب قبل صرف الأصناف")
    if request.requested_by == user.user_id or request.approved_by == user.user_id:
        raise HTTPException(403, "يجب أن يكون أمين المخزن شخصًا غير مقدم الطلب والمعتمد")
    warehouse = db.get(InventoryWarehouse, body.warehouse_id)
    if not warehouse or not warehouse.is_active:
        raise HTTPException(422, "مخزن الصرف غير موجود أو غير نشط")
    lines = db.scalars(select(SiteIssueRequestLine).where(SiteIssueRequestLine.request_id == request_id).order_by(SiteIssueRequestLine.line_id).with_for_update()).all()
    by_id = {line.line_id: line for line in lines}
    if body.lines:
        if len({row.line_id for row in body.lines}) != len(body.lines):
            raise HTTPException(422, "يوجد بند مكرر في تفاصيل الصرف")
        issue_quantities = {row.line_id: row.quantity for row in body.lines}
    else:
        issue_quantities = {line.line_id: Decimal(str(line.approved_quantity or 0)) - Decimal(str(line.issued_quantity or 0))
            for line in lines if Decimal(str(line.approved_quantity or 0)) > Decimal(str(line.issued_quantity or 0))}
    if not issue_quantities:
        raise HTTPException(409, "لا توجد كميات متبقية للصرف")
    item_ids = sorted({by_id[line_id].item_id for line_id in issue_quantities if line_id in by_id})
    db.scalars(select(InventoryItem).where(InventoryItem.item_id.in_(item_ids)).order_by(InventoryItem.item_id).with_for_update()).all()
    prepared = []
    for line_id, quantity in issue_quantities.items():
        line = by_id.get(line_id)
        if not line:
            raise HTTPException(422, "بند الصرف لا يتبع الطلب المحدد")
        remaining = Decimal(str(line.approved_quantity or 0)) - Decimal(str(line.issued_quantity or 0))
        if quantity <= 0 or quantity > remaining:
            raise HTTPException(422, "كمية الصرف تتجاوز الكمية المعتمدة المتبقية")
        item = db.get(InventoryItem, line.item_id)
        if not item or not item.is_active:
            raise HTTPException(409, "يوجد صنف غير متاح")
        available = _balance(db, line.item_id, body.warehouse_id)
        if available < quantity:
            raise HTTPException(409, f"الرصيد غير كافٍ للصنف {item.code}: المتاح {available} والمطلوب {quantity}")
        prepared.append((line, item, quantity))
    created = []
    for line, item, quantity in prepared:
        movement_no = f"SIR-{request.request_id}-{line.line_id}-{uuid4().hex[:8]}"
        movement = InventoryMovement(movement_no=movement_no, item_id=line.item_id,
            warehouse_id=body.warehouse_id, movement_date=date.today(), movement_type="OUT",
            quantity=quantity, unit_cost=Decimal("0"), reference=request.request_no,
            notes=f"صرف طلب موقع {request.request_no} — {request.site_name or ''}".strip(),
            created_by=user.user_id)
        db.add(movement)
        db.flush()
        line.issued_quantity = Decimal(str(line.issued_quantity or 0)) + quantity
        created.append({"movement_no": movement_no, "item": item.name, "quantity": str(quantity)})
        write_audit(db, user.user_id, "Create", "InventoryMovements", movement.movement_id,
            new={"movement_no": movement_no, "request_no": request.request_no, "warehouse_id": body.warehouse_id,
                 "item_id": line.item_id, "quantity": str(quantity), "movement_type": "OUT"})
    fully_issued = all(Decimal(str(line.issued_quantity or 0)) >= Decimal(str(line.approved_quantity or 0)) for line in lines)
    request.status = "Issued" if fully_issued else "PartiallyIssued"
    request.issued_by = user.user_id
    request.issued_at = utcnow()
    write_audit(db, user.user_id, "Issue", "SiteIssueRequests", request_id,
        new={"status": request.status, "warehouse_id": body.warehouse_id, "movements": created})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر ترحيل الصرف؛ لم يتم تعديل الأرصدة")
    return {"request_id": request_id, "status": request.status, "warehouse": warehouse.name,
        "movements": created, "message": "تم صرف الكميات وتحديث رصيد المخزن"}

@inventory.get("/stocktakes")
def list_stocktakes(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    rows = db.scalars(select(InventoryStocktake).order_by(InventoryStocktake.stocktake_date.desc(), InventoryStocktake.stocktake_id.desc()).limit(300)).all()
    result = []
    for x in rows:
        warehouse = db.get(InventoryWarehouse, x.warehouse_id)
        creator = db.get(User, x.created_by)
        approver = db.get(User, x.approved_by) if x.approved_by else None
        lines = []
        for line in db.scalars(select(InventoryStocktakeLine).where(InventoryStocktakeLine.stocktake_id == x.stocktake_id).order_by(InventoryStocktakeLine.line_id)).all():
            item = db.get(InventoryItem, line.item_id)
            lines.append({"line_id": line.line_id, "item_id": line.item_id, "item_code": item.code if item else "",
                "item": item.name if item else "", "unit": item.unit if item else "",
                "system_quantity": str(line.system_quantity), "counted_quantity": str(line.counted_quantity),
                "variance_quantity": str(line.variance_quantity)})
        result.append({"stocktake_id": x.stocktake_id, "stocktake_no": x.stocktake_no,
            "warehouse_id": x.warehouse_id, "warehouse": warehouse.name if warehouse else "",
            "stocktake_date": str(x.stocktake_date), "status": x.status, "notes": x.notes,
            "created_by": getattr(creator, "username", None) or str(x.created_by),
            "approved_by": getattr(approver, "username", None) if approver else "", "lines": lines})
    return {"items": result}

@inventory.post("/stocktakes", status_code=201)
def create_stocktake(body: StocktakeIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if db.scalar(select(InventoryStocktake.stocktake_id).where(InventoryStocktake.stocktake_no == body.stocktake_no)):
        raise HTTPException(409, "رقم محضر الجرد مستخدم بالفعل")
    warehouse = db.get(InventoryWarehouse, body.warehouse_id)
    if not warehouse or not warehouse.is_active:
        raise HTTPException(422, "المخزن غير موجود أو غير نشط")
    if len({line.item_id for line in body.lines}) != len(body.lines):
        raise HTTPException(422, "لا تكرر الصنف في محضر الجرد")
    prepared = []
    for line in body.lines:
        item = db.get(InventoryItem, line.item_id)
        if not item or not item.is_active:
            raise HTTPException(422, f"الصنف {line.item_id} غير موجود أو غير نشط")
        prepared.append((line, _balance(db, line.item_id, body.warehouse_id)))
    x = InventoryStocktake(stocktake_no=body.stocktake_no, warehouse_id=body.warehouse_id,
        stocktake_date=body.stocktake_date, status="PendingApproval", notes=body.notes, created_by=user.user_id)
    db.add(x)
    try:
        db.flush()
        for line, system_qty in prepared:
            counted = Decimal(str(line.counted_quantity))
            db.add(InventoryStocktakeLine(stocktake_id=x.stocktake_id, item_id=line.item_id,
                system_quantity=system_qty, counted_quantity=counted, variance_quantity=counted-system_qty))
        write_audit(db, user.user_id, "Create", "InventoryStocktakes", x.stocktake_id,
            new={"stocktake_no": x.stocktake_no, "warehouse_id": x.warehouse_id, "lines": len(prepared), "status": x.status})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر حفظ محضر الجرد؛ تحقق من رقم المحضر")
    return {"stocktake_id": x.stocktake_id, "stocktake_no": x.stocktake_no, "status": x.status}

@inventory.post("/stocktakes/{stocktake_id}/approve")
def approve_stocktake(stocktake_id: int, user: User = Depends(require_permission("InventoryManagement", "Approve")), db: Session = Depends(get_db)):
    x = db.scalar(select(InventoryStocktake).where(InventoryStocktake.stocktake_id == stocktake_id).with_for_update())
    if not x:
        raise HTTPException(404, "محضر الجرد غير موجود")
    if x.status != "PendingApproval":
        raise HTTPException(409, "محضر الجرد ليس في انتظار الاعتماد")
    if x.created_by == user.user_id:
        raise HTTPException(403, "لا يجوز اعتماد محضر الجرد بواسطة معدّه")
    lines = db.scalars(select(InventoryStocktakeLine).where(InventoryStocktakeLine.stocktake_id == stocktake_id)).all()
    if not lines:
        raise HTTPException(409, "محضر الجرد لا يحتوي على أصناف")
    x.status = "Approved"
    x.approved_by = user.user_id
    x.approved_at = utcnow()
    write_audit(db, user.user_id, "Approve", "InventoryStocktakes", stocktake_id,
        new={"status": x.status, "line_count": len(lines), "total_variance": str(sum((Decimal(str(z.variance_quantity)) for z in lines), Decimal("0")))})
    db.commit()
    return {"stocktake_id": stocktake_id, "status": x.status}

@inventory.post("/stocktakes/{stocktake_id}/post")
def post_stocktake(stocktake_id: int, user: User = Depends(require_permission("InventoryManagement", "Post")), db: Session = Depends(get_db)):
    x = db.scalar(select(InventoryStocktake).where(InventoryStocktake.stocktake_id == stocktake_id).with_for_update())
    if not x:
        raise HTTPException(404, "محضر الجرد غير موجود")
    if x.status != "Approved":
        raise HTTPException(409, "يجب اعتماد محضر الجرد قبل التسوية")
    if x.created_by == user.user_id or x.approved_by == user.user_id:
        raise HTTPException(403, "يجب أن يكون مرحّل التسوية شخصًا غير معدّ المحضر والمعتمد")
    lines = db.scalars(select(InventoryStocktakeLine).where(InventoryStocktakeLine.stocktake_id == stocktake_id).order_by(InventoryStocktakeLine.line_id).with_for_update()).all()
    if not lines:
        raise HTTPException(409, "محضر الجرد لا يحتوي على أصناف")
    item_ids = [line.item_id for line in lines]
    # Any movement after the count snapshot invalidates the comparison; recount rather than post stale variances.
    newer = db.scalar(select(InventoryMovement.movement_id).where(
        InventoryMovement.warehouse_id == x.warehouse_id, InventoryMovement.item_id.in_(item_ids),
        InventoryMovement.created_at > x.created_at).limit(1))
    if newer:
        raise HTTPException(409, "تم تسجيل حركات مخزنية بعد إعداد محضر الجرد؛ أعد الجرد لضمان صحة الفروق")
    for line in lines:
        current = _balance(db, line.item_id, x.warehouse_id)
        if current != Decimal(str(line.system_quantity)):
            raise HTTPException(409, "تغير رصيد أحد الأصناف منذ إعداد الجرد؛ أعد الجرد")
        variance = Decimal(str(line.counted_quantity)) - current
        if variance < 0 and current < abs(variance):
            raise HTTPException(409, "فرق الجرد سيؤدي إلى رصيد سالب")
    created = []
    for line in lines:
        variance = Decimal(str(line.counted_quantity)) - Decimal(str(line.system_quantity))
        if variance == 0:
            continue
        movement_type = "IN" if variance > 0 else "OUT"
        movement_no = f"STK-{x.stocktake_id}-{line.line_id}-{uuid4().hex[:8]}"
        movement = InventoryMovement(movement_no=movement_no, item_id=line.item_id,
            warehouse_id=x.warehouse_id, movement_date=x.stocktake_date, movement_type=movement_type,
            quantity=abs(variance), unit_cost=Decimal("0"), reference=x.stocktake_no,
            notes=f"تسوية فرق جرد {x.stocktake_no}", created_by=user.user_id)
        db.add(movement)
        created.append({"movement_no": movement_no, "item_id": line.item_id, "movement_type": movement_type, "quantity": str(abs(variance))})
    x.status = "Posted"
    x.posted_by = user.user_id
    x.posted_at = utcnow()
    write_audit(db, user.user_id, "Post", "InventoryStocktakes", stocktake_id,
        new={"status": x.status, "warehouse_id": x.warehouse_id, "adjustments": created})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر ترحيل تسويات الجرد؛ لم يتم تعديل الأرصدة")
    return {"stocktake_id": stocktake_id, "status": x.status, "adjustments": created}

@inventory.get("/returns/lookups")
def inventory_return_lookups(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    sources = []
    for order in db.scalars(select(PurchaseOrder).where(PurchaseOrder.status == "Received").order_by(PurchaseOrder.purchase_order_id.desc())).all():
        for line in db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == order.purchase_order_id)).all():
            reserved = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                InventoryReturn.return_type == "Supplier", InventoryReturn.status.in_(("PendingApproval", "Approved", "Posted")),
                InventoryReturnLine.purchase_order_line_id == line.line_id)) or 0
            available = Decimal(str(line.received_quantity or 0)) - Decimal(str(reserved))
            if available <= 0:
                continue
            item = db.get(InventoryItem, line.item_id)
            warehouse = db.get(InventoryWarehouse, order.warehouse_id)
            sources.append({"key": f"P-{line.line_id}", "return_type": "Supplier", "source_line_id": line.line_id,
                "item_id": line.item_id, "item": item.name if item else "", "item_code": item.code if item else "",
                "warehouse_id": order.warehouse_id, "warehouse": warehouse.name if warehouse else "",
                "source_document": order.order_no, "counterparty_name": order.supplier_name,
                "available": str(available), "unit_cost": str(line.unit_price)})
    for request in db.scalars(select(SiteIssueRequest).where(SiteIssueRequest.status.in_(("Issued", "PartiallyIssued"))).order_by(SiteIssueRequest.request_id.desc())).all():
        for line in db.scalars(select(SiteIssueRequestLine).where(SiteIssueRequestLine.request_id == request.request_id)).all():
            movements = db.execute(select(InventoryMovement.warehouse_id, func.sum(InventoryMovement.quantity)).where(
                InventoryMovement.reference == request.request_no, InventoryMovement.item_id == line.item_id,
                InventoryMovement.movement_type == "OUT").group_by(InventoryMovement.warehouse_id)).all()
            for warehouse_id, issued in movements:
                reserved = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                    InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                    InventoryReturn.return_type == "Site", InventoryReturn.status.in_(("PendingApproval", "Approved", "Posted")),
                    InventoryReturnLine.site_issue_line_id == line.line_id, InventoryReturn.warehouse_id == warehouse_id)) or 0
                available = Decimal(str(issued or 0)) - Decimal(str(reserved))
                if available <= 0:
                    continue
                item = db.get(InventoryItem, line.item_id)
                warehouse = db.get(InventoryWarehouse, warehouse_id)
                sources.append({"key": f"S-{line.line_id}-{warehouse_id}", "return_type": "Site", "source_line_id": line.line_id,
                    "item_id": line.item_id, "item": item.name if item else "", "item_code": item.code if item else "",
                    "warehouse_id": warehouse_id, "warehouse": warehouse.name if warehouse else "",
                    "source_document": request.request_no, "counterparty_name": request.site_name or "",
                    "available": str(available), "unit_cost": "0"})
    return {"items": sources}

@inventory.get("/returns")
def list_inventory_returns(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    rows = db.scalars(select(InventoryReturn).order_by(InventoryReturn.return_date.desc(), InventoryReturn.return_id.desc()).limit(300)).all()
    result = []
    for x in rows:
        warehouse = db.get(InventoryWarehouse, x.warehouse_id)
        lines = []
        for line in db.scalars(select(InventoryReturnLine).where(InventoryReturnLine.return_id == x.return_id).order_by(InventoryReturnLine.line_id)).all():
            item = db.get(InventoryItem, line.item_id)
            lines.append({"line_id": line.line_id, "item_id": line.item_id, "item": item.name if item else "",
                "item_code": item.code if item else "", "quantity": str(line.quantity), "unit_cost": str(line.unit_cost)})
        result.append({"return_id": x.return_id, "return_no": x.return_no, "return_type": x.return_type,
            "return_date": str(x.return_date), "warehouse": warehouse.name if warehouse else "",
            "counterparty_name": x.counterparty_name, "source_document": x.source_document,
            "notes": x.notes, "status": x.status, "lines": lines})
    return {"items": result}

@inventory.post("/returns", status_code=201)
def create_inventory_return(body: InventoryReturnIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if body.return_type not in ("Supplier", "Site"):
        raise HTTPException(422, "نوع المرتجع غير صحيح")
    if db.scalar(select(InventoryReturn.return_id).where(InventoryReturn.return_no == body.return_no)):
        raise HTTPException(409, "رقم المرتجع مستخدم بالفعل")
    warehouse = db.get(InventoryWarehouse, body.warehouse_id)
    if not warehouse or not warehouse.is_active:
        raise HTTPException(422, "المخزن غير موجود أو غير نشط")
    if len({line.item_id for line in body.lines}) != len(body.lines):
        raise HTTPException(422, "لا تكرر الصنف في مستند المرتجع")
    prepared = []
    for row in body.lines:
        item = db.get(InventoryItem, row.item_id)
        if not item or not item.is_active:
            raise HTTPException(422, f"الصنف {row.item_id} غير موجود أو غير نشط")
        if body.return_type == "Supplier":
            if not row.purchase_order_line_id or row.site_issue_line_id:
                raise HTTPException(422, "مرتجع المورد يجب ربطه ببند أمر شراء")
            source = db.get(PurchaseOrderLine, row.purchase_order_line_id)
            if not source or source.item_id != row.item_id:
                raise HTTPException(422, "بند أمر الشراء لا يطابق الصنف")
            order = db.get(PurchaseOrder, source.purchase_order_id)
            if not order or order.warehouse_id != body.warehouse_id or order.status != "Received":
                raise HTTPException(422, "أمر الشراء غير مستلم أو لا يتبع المخزن المحدد")
            already = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                InventoryReturn.return_type == "Supplier", InventoryReturn.status.in_(("PendingApproval", "Approved", "Posted")),
                InventoryReturnLine.purchase_order_line_id == source.line_id)) or 0
            available = Decimal(str(source.received_quantity or 0)) - Decimal(str(already))
            if Decimal(str(row.quantity)) > available:
                raise HTTPException(409, f"كمية المرتجع تتجاوز الكمية المستلمة المتبقية للصنف {item.name}")
        else:
            if not row.site_issue_line_id or row.purchase_order_line_id:
                raise HTTPException(422, "مرتجع الموقع يجب ربطه ببند طلب صرف")
            source = db.get(SiteIssueRequestLine, row.site_issue_line_id)
            if not source or source.item_id != row.item_id:
                raise HTTPException(422, "بند طلب الصرف لا يطابق الصنف")
            request = db.get(SiteIssueRequest, source.request_id)
            if not request or request.status not in ("Issued", "PartiallyIssued"):
                raise HTTPException(422, "طلب الصرف غير مصروف")
            issued_at_warehouse = db.scalar(select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
                InventoryMovement.reference == request.request_no, InventoryMovement.item_id == row.item_id,
                InventoryMovement.warehouse_id == body.warehouse_id, InventoryMovement.movement_type == "OUT")) or 0
            already = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                InventoryReturn.return_type == "Site", InventoryReturn.status.in_(("PendingApproval", "Approved", "Posted")),
                InventoryReturnLine.site_issue_line_id == source.line_id,
                InventoryReturn.warehouse_id == body.warehouse_id)) or 0
            available = Decimal(str(issued_at_warehouse)) - Decimal(str(already))
            if Decimal(str(row.quantity)) > available:
                raise HTTPException(409, f"كمية المرتجع تتجاوز الكمية المصروفة المتبقية للصنف {item.name}")
        prepared.append(row)
    x = InventoryReturn(return_no=body.return_no, return_type=body.return_type, return_date=body.return_date,
        warehouse_id=body.warehouse_id, counterparty_name=body.counterparty_name, source_document=body.source_document,
        notes=body.notes, status="PendingApproval", created_by=user.user_id)
    db.add(x)
    try:
        db.flush()
        for row in prepared:
            db.add(InventoryReturnLine(return_id=x.return_id, item_id=row.item_id, quantity=row.quantity,
                unit_cost=row.unit_cost, purchase_order_line_id=row.purchase_order_line_id, site_issue_line_id=row.site_issue_line_id))
        write_audit(db, user.user_id, "Create", "InventoryReturns", x.return_id,
            new={"return_no": x.return_no, "return_type": x.return_type, "lines": len(prepared), "status": x.status})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر حفظ مستند المرتجع")
    return {"return_id": x.return_id, "return_no": x.return_no, "status": x.status}

@inventory.post("/returns/{return_id}/approve")
def approve_inventory_return(return_id: int, user: User = Depends(require_permission("InventoryManagement", "Approve")), db: Session = Depends(get_db)):
    x = db.scalar(select(InventoryReturn).where(InventoryReturn.return_id == return_id).with_for_update())
    if not x:
        raise HTTPException(404, "مستند المرتجع غير موجود")
    if x.status != "PendingApproval":
        raise HTTPException(409, "مستند المرتجع ليس في انتظار الاعتماد")
    if x.created_by == user.user_id:
        raise HTTPException(403, "لا يجوز اعتماد المرتجع بواسطة معدّه")
    x.status = "Approved"
    x.approved_by = user.user_id
    x.approved_at = utcnow()
    write_audit(db, user.user_id, "Approve", "InventoryReturns", return_id, new={"status": x.status})
    db.commit()
    return {"return_id": return_id, "status": x.status}

@inventory.post("/returns/{return_id}/post")
def post_inventory_return(return_id: int, user: User = Depends(require_permission("InventoryManagement", "Post")), db: Session = Depends(get_db)):
    x = db.scalar(select(InventoryReturn).where(InventoryReturn.return_id == return_id).with_for_update())
    if not x:
        raise HTTPException(404, "مستند المرتجع غير موجود")
    if x.status != "Approved":
        raise HTTPException(409, "يجب اعتماد المرتجع قبل الترحيل")
    if x.created_by == user.user_id or x.approved_by == user.user_id:
        raise HTTPException(403, "يجب أن يكون مرحّل المرتجع شخصًا غير معدّه والمعتمد")
    lines = db.scalars(select(InventoryReturnLine).where(InventoryReturnLine.return_id == return_id).order_by(InventoryReturnLine.line_id).with_for_update()).all()
    if not lines:
        raise HTTPException(409, "مستند المرتجع لا يحتوي على أصناف")
    adjustments = []
    for line in lines:
        if x.return_type == "Supplier":
            source = db.get(PurchaseOrderLine, line.purchase_order_line_id)
            already = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                InventoryReturn.return_type == "Supplier", InventoryReturn.status == "Posted",
                InventoryReturnLine.purchase_order_line_id == line.purchase_order_line_id)) or 0
            if not source or Decimal(str(already)) + Decimal(str(line.quantity)) > Decimal(str(source.received_quantity or 0)):
                raise HTTPException(409, "تجاوزت المرتجعات الكمية المستلمة؛ راجع المستندات السابقة")
            current = _balance(db, line.item_id, x.warehouse_id)
            if current < Decimal(str(line.quantity)):
                raise HTTPException(409, "رصيد المخزن لا يكفي لمرتجع المورد")
            movement_type = "OUT"
        else:
            source = db.get(SiteIssueRequestLine, line.site_issue_line_id)
            request = db.get(SiteIssueRequest, source.request_id) if source else None
            issued_at_warehouse = db.scalar(select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
                InventoryMovement.reference == (request.request_no if request else ""), InventoryMovement.item_id == line.item_id,
                InventoryMovement.warehouse_id == x.warehouse_id, InventoryMovement.movement_type == "OUT")) or 0
            already = db.scalar(select(func.coalesce(func.sum(InventoryReturnLine.quantity), 0)).join(
                InventoryReturn, InventoryReturn.return_id == InventoryReturnLine.return_id).where(
                InventoryReturn.return_type == "Site", InventoryReturn.status == "Posted",
                InventoryReturnLine.site_issue_line_id == line.site_issue_line_id,
                InventoryReturn.warehouse_id == x.warehouse_id)) or 0
            if not source or Decimal(str(already)) + Decimal(str(line.quantity)) > Decimal(str(issued_at_warehouse)):
                raise HTTPException(409, "تجاوزت المرتجعات الكمية المصروفة للموقع في هذا المخزن")
            movement_type = "IN"
        movement_no = f"RET-{x.return_id}-{line.line_id}-{uuid4().hex[:8]}"
        db.add(InventoryMovement(movement_no=movement_no, item_id=line.item_id, warehouse_id=x.warehouse_id,
            movement_date=x.return_date, movement_type=movement_type, quantity=line.quantity, unit_cost=line.unit_cost,
            reference=x.return_no, notes=("مرتجع مورد" if x.return_type == "Supplier" else "مرتجع موقع") + " " + x.return_no,
            created_by=user.user_id))
        adjustments.append({"movement_no": movement_no, "item_id": line.item_id, "type": movement_type, "quantity": str(line.quantity)})
    x.status = "Posted"
    x.posted_by = user.user_id
    x.posted_at = utcnow()
    write_audit(db, user.user_id, "Post", "InventoryReturns", return_id,
        new={"status": x.status, "return_type": x.return_type, "movements": adjustments})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر ترحيل المرتجع؛ لم يتم تعديل الأرصدة")
    return {"return_id": return_id, "status": x.status, "movements": adjustments}

@inventory.get("/warehouses")
def list_warehouses(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    return {"items": [{"warehouse_id":w.warehouse_id,"code":w.code,"name":w.name,"location":w.location,"is_active":w.is_active} for w in db.scalars(select(InventoryWarehouse).order_by(InventoryWarehouse.name)).all()]}

@inventory.post("/warehouses", status_code=201)
def create_warehouse(body: WarehouseIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if db.scalar(select(InventoryWarehouse.warehouse_id).where(InventoryWarehouse.code == body.code)):
        raise HTTPException(409, "كود المخزن مستخدم بالفعل")
    x=InventoryWarehouse(**body.model_dump()); db.add(x); db.flush(); write_audit(db,user.user_id,"Create","InventoryWarehouses",x.warehouse_id,new=body.model_dump()); db.commit()
    return {"warehouse_id":x.warehouse_id,"code":x.code,"name":x.name,"location":x.location,"is_active":x.is_active}

@inventory.get("/items")
def list_items(q: str | None = None, _: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    stmt=select(InventoryItem)
    if q and q.strip(): stmt=stmt.where((InventoryItem.code.ilike(f"%{q.strip()}%")) | (InventoryItem.name.ilike(f"%{q.strip()}%")))
    items=db.scalars(stmt.order_by(InventoryItem.name)).all(); warehouses=db.scalars(select(InventoryWarehouse).where(InventoryWarehouse.is_active.is_(True))).all()
    out=[]
    for x in items:
        balances=[{"warehouse_id":w.warehouse_id,"warehouse":w.name,"quantity":str(_balance(db,x.item_id,w.warehouse_id))} for w in warehouses]
        total=sum((Decimal(b["quantity"]) for b in balances),Decimal("0"))
        out.append({"item_id":x.item_id,"code":x.code,"name":x.name,"category":x.category,"unit":x.unit,"min_quantity":str(x.min_quantity),"is_active":x.is_active,"quantity":str(total),"balances":balances})
    return {"items":out,"warehouses":[{"warehouse_id":w.warehouse_id,"name":w.name} for w in warehouses]}

@inventory.post("/items", status_code=201)
def create_item(body: ItemIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if db.scalar(select(InventoryItem.item_id).where(InventoryItem.code == body.code)): raise HTTPException(409,"كود الصنف مستخدم بالفعل")
    x=InventoryItem(**body.model_dump());db.add(x);db.flush();write_audit(db,user.user_id,"Create","InventoryItems",x.item_id,new=body.model_dump());db.commit()
    return {"item_id":x.item_id,"code":x.code,"name":x.name}

@inventory.get("/movements")
def list_movements(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    rows=db.scalars(select(InventoryMovement).order_by(InventoryMovement.movement_date.desc(),InventoryMovement.movement_id.desc()).limit(500)).all()
    out=[]
    for x in rows:
        i=db.get(InventoryItem,x.item_id); w=db.get(InventoryWarehouse,x.warehouse_id)
        out.append({"movement_id":x.movement_id,"movement_no":x.movement_no,"date":str(x.movement_date),"type":x.movement_type,"item":i.name if i else "","warehouse":w.name if w else "","quantity":str(x.quantity),"unit_cost":str(x.unit_cost),"reference":x.reference,"notes":x.notes})
    return {"items":out}

@inventory.get("/items/{item_id}/card")
def item_stock_card(item_id: int, date_from: date | None = None, date_to: date | None = None,
    warehouse_id: int | None = None, _: User = Depends(require_permission("InventoryManagement", "View")),
    db: Session = Depends(get_db)):
    """Return a stock ledger and opening/running balances derived only from posted movements."""
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(404, "الصنف غير موجود")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "تاريخ البداية يجب أن يسبق تاريخ النهاية")
    if warehouse_id is not None and not db.get(InventoryWarehouse, warehouse_id):
        raise HTTPException(422, "المخزن غير موجود")

    base = select(InventoryMovement).where(InventoryMovement.item_id == item_id)
    if warehouse_id is not None:
        base = base.where(InventoryMovement.warehouse_id == warehouse_id)
    before = base
    if date_from:
        before = before.where(InventoryMovement.movement_date < date_from)
    opening_rows = db.scalars(before.order_by(InventoryMovement.movement_date, InventoryMovement.movement_id)).all()
    opening = sum((Decimal(str(m.quantity)) if m.movement_type == "IN" else -Decimal(str(m.quantity))
        for m in opening_rows), Decimal("0"))

    stmt = base
    if date_from:
        stmt = stmt.where(InventoryMovement.movement_date >= date_from)
    if date_to:
        stmt = stmt.where(InventoryMovement.movement_date <= date_to)
    rows = db.scalars(stmt.order_by(InventoryMovement.movement_date, InventoryMovement.movement_id)).all()
    running = opening
    movements = []
    incoming = outgoing = Decimal("0")
    for movement in rows:
        warehouse = db.get(InventoryWarehouse, movement.warehouse_id)
        signed = Decimal(str(movement.quantity)) if movement.movement_type == "IN" else -Decimal(str(movement.quantity))
        running += signed
        if signed > 0:
            incoming += signed
        else:
            outgoing += -signed
        movements.append({"movement_id": movement.movement_id, "movement_no": movement.movement_no,
            "date": str(movement.movement_date), "type": movement.movement_type,
            "warehouse_id": movement.warehouse_id, "warehouse": warehouse.name if warehouse else "",
            "quantity": str(movement.quantity), "signed_quantity": str(signed), "balance": str(running),
            "unit_cost": str(movement.unit_cost), "reference": movement.reference, "notes": movement.notes})
    return {"item": {"item_id": item.item_id, "code": item.code, "name": item.name, "unit": item.unit},
        "date_from": str(date_from) if date_from else None, "date_to": str(date_to) if date_to else None,
        "warehouse_id": warehouse_id, "opening_balance": str(opening), "incoming": str(incoming),
        "outgoing": str(outgoing), "closing_balance": str(running), "movements": movements}

@inventory.post("/movements", status_code=201)
def create_movement(body: MovementIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    if body.movement_type not in ("IN","OUT"): raise HTTPException(422,"نوع الحركة يجب أن يكون IN أو OUT")
    if not db.get(InventoryItem,body.item_id) or not db.get(InventoryWarehouse,body.warehouse_id): raise HTTPException(422,"الصنف أو المخزن غير موجود")
    if db.scalar(select(InventoryMovement.movement_id).where(InventoryMovement.movement_no==body.movement_no)): raise HTTPException(409,"رقم الحركة مستخدم بالفعل")
    if body.movement_type=="OUT" and _balance(db,body.item_id,body.warehouse_id)<body.quantity: raise HTTPException(409,"الرصيد غير كافٍ للصرف")
    x=InventoryMovement(**body.model_dump(),created_by=user.user_id);db.add(x);db.flush();write_audit(db,user.user_id,"Create","InventoryMovements",x.movement_id,new=body.model_dump());db.commit()
    return {"movement_id":x.movement_id,"movement_no":x.movement_no,"message":"تم حفظ حركة المخزون"}

@inventory.post("/movements/batch", status_code=201)
def create_movement_batch(body: MovementBatchIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    """Register all document lines atomically; no journal is created by stock-only movements."""
    if body.movement_type not in ("IN", "OUT"):
        raise HTTPException(422, "نوع الحركة يجب أن يكون IN أو OUT")
    if not db.get(InventoryWarehouse, body.warehouse_id):
        raise HTTPException(422, "المخزن غير موجود")
    totals: dict[int, Decimal] = {}
    for line in body.lines:
        if not db.get(InventoryItem, line.item_id):
            raise HTTPException(422, f"الصنف {line.item_id} غير موجود")
        totals[line.item_id] = totals.get(line.item_id, Decimal("0")) + line.quantity
    if body.movement_type == "OUT":
        for item_id, quantity in totals.items():
            if _balance(db, item_id, body.warehouse_id) < quantity:
                item = db.get(InventoryItem, item_id)
                raise HTTPException(409, f"الرصيد غير كافٍ للصنف {item.code if item else item_id}")
    refs = [f"{body.movement_no}-{n:03d}" for n in range(1, len(body.lines) + 1)]
    duplicate = db.scalar(select(InventoryMovement.movement_id).where(InventoryMovement.movement_no.in_(refs)).limit(1))
    if duplicate:
        raise HTTPException(409, "رقم مستند الحركة مستخدم من قبل")
    created = []
    for ref, line in zip(refs, body.lines):
        movement = InventoryMovement(movement_no=ref, item_id=line.item_id, warehouse_id=body.warehouse_id,
            movement_date=body.movement_date, movement_type=body.movement_type, quantity=line.quantity,
            unit_cost=line.unit_cost, reference=body.reference or body.movement_no, notes=body.notes, created_by=user.user_id)
        db.add(movement); db.flush()
        write_audit(db, user.user_id, "Create", "InventoryMovements", movement.movement_id,
            new={"movement_no":ref,"batch_no":body.movement_no,"item_id":line.item_id,"quantity":str(line.quantity),"movement_type":body.movement_type})
        created.append({"movement_id":movement.movement_id,"movement_no":ref,"item_id":line.item_id,"quantity":str(line.quantity)})
    db.commit()
    return {"movement_no":body.movement_no,"items":created,"message":"تم حفظ مستند المخزون متعدد البنود"}

@inventory.post("/transfers", status_code=201)
def create_stock_transfer(body: StockTransferIn, user: User = Depends(require_permission("InventoryManagement", "Add")), db: Session = Depends(get_db)):
    """Post paired OUT/IN movements as one atomic warehouse transfer document."""
    if body.source_warehouse_id == body.destination_warehouse_id:
        raise HTTPException(422, "يجب اختيار مخزنين مختلفين للتحويل")
    source = db.get(InventoryWarehouse, body.source_warehouse_id)
    destination = db.get(InventoryWarehouse, body.destination_warehouse_id)
    if not source or not destination or not source.is_active or not destination.is_active:
        raise HTTPException(422, "المخزن المصدر أو المستلم غير موجود أو غير نشط")
    totals: dict[int, Decimal] = {}
    for line in body.lines:
        totals[line.item_id] = totals.get(line.item_id, Decimal("0")) + line.quantity
    # Lock item master rows in a stable order to serialize competing transfers on databases
    # that support row locks; all paired ledger entries are committed in one transaction.
    locked_items = db.scalars(select(InventoryItem).where(InventoryItem.item_id.in_(sorted(totals)))
        .order_by(InventoryItem.item_id).with_for_update()).all()
    found = {item.item_id: item for item in locked_items}
    for item_id, quantity in totals.items():
        item = found.get(item_id)
        if not item or not item.is_active:
            raise HTTPException(422, f"الصنف {item_id} غير موجود أو غير نشط")
        available = _balance(db, item_id, body.source_warehouse_id)
        if available < quantity:
            raise HTTPException(409, f"الرصيد غير كافٍ للصنف {item.code}: المتاح {available} والمطلوب {quantity}")
    movement_numbers = []
    for index in range(1, len(body.lines) + 1):
        movement_numbers.extend((f"{body.transfer_no}-OUT-{index:03d}", f"{body.transfer_no}-IN-{index:03d}"))
    duplicate = db.scalar(select(InventoryMovement.movement_id).where(InventoryMovement.movement_no.in_(movement_numbers)).limit(1))
    if duplicate:
        raise HTTPException(409, "رقم مستند التحويل مستخدم من قبل")
    created = []
    for index, line in enumerate(body.lines, start=1):
        item = found[line.item_id]
        for suffix, warehouse_id, movement_type in (
            ("OUT", body.source_warehouse_id, "OUT"),
            ("IN", body.destination_warehouse_id, "IN"),
        ):
            number = f"{body.transfer_no}-{suffix}-{index:03d}"
            movement = InventoryMovement(movement_no=number, item_id=line.item_id,
                warehouse_id=warehouse_id, movement_date=body.transfer_date,
                movement_type=movement_type, quantity=line.quantity, unit_cost=line.unit_cost,
                reference=body.reference or body.transfer_no,
                notes=body.notes or f"تحويل مخزني {body.transfer_no}: {source.name} ← {destination.name}",
                created_by=user.user_id)
            db.add(movement)
            db.flush()
            write_audit(db, user.user_id, "Create", "InventoryMovements", movement.movement_id,
                new={"movement_no": number, "transfer_no": body.transfer_no, "item_id": line.item_id,
                     "quantity": str(line.quantity), "movement_type": movement_type,
                     "warehouse_id": warehouse_id, "source_warehouse_id": body.source_warehouse_id,
                     "destination_warehouse_id": body.destination_warehouse_id})
            created.append({"movement_id": movement.movement_id, "movement_no": number,
                "item_id": line.item_id, "warehouse_id": warehouse_id, "type": movement_type,
                "quantity": str(line.quantity)})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "تعذر حفظ التحويل؛ راجع رقم المستند وحاول مرة أخرى")
    return {"transfer_no": body.transfer_no, "source_warehouse": source.name,
        "destination_warehouse": destination.name, "movements": created,
        "message": "تم ترحيل التحويل وتحديث رصيد المخزنين"}

@purchases.get("")
def list_orders(_: User = Depends(require_permission("PurchaseCycle", "View")), db: Session = Depends(get_db)):
    rows=db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.order_date.desc(),PurchaseOrder.purchase_order_id.desc())).all()
    return {"items":[{"purchase_order_id":x.purchase_order_id,"order_no":x.order_no,"order_date":str(x.order_date),"supplier_name":x.supplier_name,"warehouse_id":x.warehouse_id,"warehouse":(db.get(InventoryWarehouse,x.warehouse_id).name if db.get(InventoryWarehouse,x.warehouse_id) else ""),"project_id":x.project_id,"project":(db.get(Project,x.project_id).name_ar if x.project_id and db.get(Project,x.project_id) else ""),"status":x.status,"notes":x.notes,"total_amount":str(x.total_amount),"lines":[{"line_id":l.line_id,"item_id":l.item_id,"item":(db.get(InventoryItem,l.item_id).name if db.get(InventoryItem,l.item_id) else ""),"quantity":str(l.quantity),"unit_price":str(l.unit_price),"received_quantity":str(l.received_quantity)} for l in db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==x.purchase_order_id)).all()]} for x in rows]}

@inventory.get("/purchase-receipts")
def list_pending_purchase_receipts(_: User = Depends(require_permission("InventoryManagement", "View")), db: Session = Depends(get_db)):
    """Expose approved purchase orders as receiving documents in the warehouse screen."""
    orders = db.scalars(select(PurchaseOrder).where(PurchaseOrder.status == "Approved")
        .order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.purchase_order_id.desc())).all()
    pending = []
    for order in orders:
        lines = db.scalars(select(PurchaseOrderLine).where(
            PurchaseOrderLine.purchase_order_id == order.purchase_order_id)).all()
        remaining = [line for line in lines if Decimal(str(line.quantity)) > Decimal(str(line.received_quantity or 0))]
        if not remaining:
            continue
        warehouse = db.get(InventoryWarehouse, order.warehouse_id)
        pending.append({"purchase_order_id": order.purchase_order_id, "order_no": order.order_no,
            "order_date": str(order.order_date), "supplier_name": order.supplier_name,
            "project": db.get(Project, order.project_id).name_ar if order.project_id and db.get(Project, order.project_id) else "",
            "warehouse": warehouse.name if warehouse else "", "total_amount": str(order.total_amount),
            "lines": [{"item": (db.get(InventoryItem, line.item_id).name if db.get(InventoryItem, line.item_id) else ""),
                "quantity": str(line.quantity), "received_quantity": str(line.received_quantity or 0),
                "unit_price": str(line.unit_price)} for line in remaining]})
    return {"items": pending}

@purchases.post("", status_code=201)
def create_order(body: PurchaseIn, user: User = Depends(require_permission("PurchaseCycle", "Add")), db: Session = Depends(get_db)):
    if not db.get(InventoryWarehouse,body.warehouse_id): raise HTTPException(422,"المخزن غير موجود")
    if body.project_id is not None:
        project=db.get(Project,body.project_id)
        if not project or not project.is_active: raise HTTPException(422,"مركز التكلفة غير موجود أو غير نشط")
    for line in body.lines:
        if not db.get(InventoryItem,line.item_id): raise HTTPException(422,f"الصنف {line.item_id} غير موجود")
    total=sum((line.quantity*line.unit_price for line in body.lines),Decimal("0"))
    # The database-generated ID is the concurrency-safe sequence; client-supplied
    # order numbers are intentionally ignored so every new order is numbered uniformly.
    party=resolve_counterparty(db,body.supplier_name,"Supplier")
    po=PurchaseOrder(order_no=f"PO-PENDING-{uuid4().hex}",order_date=body.order_date,supplier_name=party.legal_name if party else body.supplier_name,counterparty_id=party.counterparty_id if party else None,warehouse_id=body.warehouse_id,project_id=body.project_id,status="Draft",notes=body.notes,total_amount=total,created_by=user.user_id)
    db.add(po);db.flush()
    po.order_no=f"PO-{body.order_date.year}-{po.purchase_order_id:06d}"
    for line in body.lines: db.add(PurchaseOrderLine(purchase_order_id=po.purchase_order_id,item_id=line.item_id,quantity=line.quantity,unit_price=line.unit_price,received_quantity=0))
    write_audit(db,user.user_id,"Create","PurchaseOrders",po.purchase_order_id,new={"order_no":po.order_no,"total_amount":str(total),"project_id":po.project_id});db.commit()
    return {"purchase_order_id":po.purchase_order_id,"order_no":po.order_no,"status":po.status,"total_amount":str(total)}

@purchases.get("/invoices")
def list_supplier_invoices(_: User = Depends(require_permission("PurchaseCycle", "View")), db: Session = Depends(get_db)):
    invoices=db.scalars(select(SupplierInvoice).order_by(SupplierInvoice.invoice_date.desc(),SupplierInvoice.invoice_id.desc())).all()
    return {"items":[{"invoice_id":x.invoice_id,"invoice_no":x.invoice_no,"invoice_date":str(x.invoice_date),
        "purchase_order_id":x.purchase_order_id,"order_no":db.get(PurchaseOrder,x.purchase_order_id).order_no if db.get(PurchaseOrder,x.purchase_order_id) else "",
        "project_id":x.project_id,"project":db.get(Project,x.project_id).name_ar if x.project_id and db.get(Project,x.project_id) else "",
        "supplier":db.get(Counterparty,x.supplier_id).legal_name if db.get(Counterparty,x.supplier_id) else "",
        "net_amount":str(x.net_amount),"tax_amount":str(x.tax_amount),"total_amount":str(x.total_amount),
        "paid_amount":str(db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow),0)).where(TreasuryTransaction.supplier_invoice_id==x.invoice_id)) or 0),
        "status":x.status,"journal_entry_id":x.journal_entry_id} for x in invoices]}

@purchases.get("/invoice-lookups")
def supplier_invoice_lookups(_:User=Depends(require_permission("PurchaseCycle","View")),db:Session=Depends(get_db)):
    accounts=db.scalars(select(Account).where(Account.is_active.is_(True)).order_by(Account.account_code)).all()
    parents=set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    return {"accounts":[{"account_id":a.account_id,"code":a.account_code,"name":a.account_name_ar,"normal_balance":a.normal_balance}
        for a in accounts if a.account_id not in parents],
        "projects":[{"project_id":p.project_id,"name_ar":p.name_ar} for p in db.scalars(select(Project).where(Project.is_active.is_(True)).order_by(Project.name_ar)).all()],
        "treasury_accounts":[{"treasury_account_id":t.treasury_account_id,"name":t.name_ar,"gl_account_id":t.gl_account_id}
        for t in db.scalars(select(TreasuryAccount).where(TreasuryAccount.is_active.is_(True)).order_by(TreasuryAccount.name_ar)).all()],
        "received_orders":[{"purchase_order_id":p.purchase_order_id,"order_no":p.order_no,"supplier_name":p.supplier_name,"project_id":p.project_id,
        "lines":[{"line_id":l.line_id,"item":db.get(InventoryItem,l.item_id).name if db.get(InventoryItem,l.item_id) else "",
        "received_quantity":str(l.received_quantity),"unit_price":str(l.unit_price)} for l in db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==p.purchase_order_id)).all()]}
        for p in db.scalars(select(PurchaseOrder).where(PurchaseOrder.status=="Received").order_by(PurchaseOrder.purchase_order_id.desc())).all()]}

@purchases.post("/invoices",status_code=201)
def create_supplier_invoice(body:SupplierInvoiceIn,user:User=Depends(require_permission("PurchaseCycle","Add")),db:Session=Depends(get_db)):
    po=db.get(PurchaseOrder,body.purchase_order_id)
    if not po or po.status!="Received":raise HTTPException(409,"لا تسجل فاتورة المورد إلا بعد استلام أمر الشراء كاملًا")
    party=resolve_counterparty(db,po.supplier_name,"Supplier",po.counterparty_id)
    if not party:raise HTTPException(409,"سجل المورد المرتبط بأمر الشراء غير موجود")
    if db.scalar(select(SupplierInvoice.invoice_id).where(SupplierInvoice.supplier_id==party.counterparty_id,SupplierInvoice.invoice_no==body.invoice_no)):
        raise HTTPException(409,"رقم الفاتورة مستخدم لهذا المورد")
    if len({x.purchase_order_line_id for x in body.lines})!=len(body.lines):raise HTTPException(422,"لا تكرر بند أمر الشراء في الفاتورة")
    po_lines={x.line_id:x for x in db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==po.purchase_order_id)).all()}
    prepared=[];net_total=Decimal("0")
    for row in body.lines:
        pl=po_lines.get(row.purchase_order_line_id)
        if not pl:raise HTTPException(422,"بند الفاتورة لا يتبع أمر الشراء المحدد")
        _invoice_account(db,row.account_id,"DR","حساب المخزون أو المصروف")
        invoiced=Decimal(str(db.scalar(select(func.coalesce(func.sum(SupplierInvoiceLine.quantity),0)).join(SupplierInvoice).where(
            SupplierInvoiceLine.purchase_order_line_id==pl.line_id,SupplierInvoice.status!="Cancelled")) or 0))
        available=Decimal(str(pl.received_quantity or 0))-invoiced
        if row.quantity>available:raise HTTPException(409,f"كمية الفاتورة تتجاوز الكمية المستلمة غير المفوترة ({available})")
        amount=_cent(row.quantity*row.unit_price);net_total+=amount;prepared.append((row,amount))
    if body.tax_amount and not body.tax_account_id:raise HTTPException(422,"حدد حساب ضريبة المدخلات")
    if body.tax_account_id:_invoice_account(db,body.tax_account_id,"DR","حساب ضريبة المدخلات")
    tax=_cent(body.tax_amount);net_total=_cent(net_total);total=_cent(net_total+tax)
    inv=SupplierInvoice(supplier_id=party.counterparty_id,purchase_order_id=po.purchase_order_id,project_id=po.project_id,invoice_no=body.invoice_no,
        invoice_date=body.invoice_date,tax_account_id=body.tax_account_id,net_amount=net_total,tax_amount=tax,
        total_amount=total,status="Draft",created_by=user.user_id)
    db.add(inv)
    try:db.flush()
    except IntegrityError:
        db.rollback();raise HTTPException(409,"رقم الفاتورة مستخدم لهذا المورد")
    for row,amount in prepared:db.add(SupplierInvoiceLine(invoice_id=inv.invoice_id,purchase_order_line_id=row.purchase_order_line_id,
        account_id=row.account_id,quantity=row.quantity,unit_price=row.unit_price,net_amount=amount))
    write_audit(db,user.user_id,"Create","SupplierInvoices",inv.invoice_id,new={"invoice_no":inv.invoice_no,"total_amount":str(total)})
    db.commit();return {"invoice_id":inv.invoice_id,"invoice_no":inv.invoice_no,"status":inv.status,"total_amount":str(total)}

@purchases.post("/invoices/{invoice_id}/approve")
def approve_supplier_invoice(invoice_id:int,user:User=Depends(require_permission("PurchaseCycle","Approve")),db:Session=Depends(get_db)):
    inv=db.scalar(select(SupplierInvoice).where(SupplierInvoice.invoice_id==invoice_id).with_for_update())
    if not inv:raise HTTPException(404,"فاتورة المورد غير موجودة")
    if inv.status!="Draft":raise HTTPException(409,"الفاتورة ليست مسودة")
    supplier=db.get(Counterparty,inv.supplier_id)
    if not supplier or not supplier.linked_account_id:raise HTTPException(409,"اربط حساب الدائنين للمورد من سجل المورد")
    _invoice_account(db,supplier.linked_account_id,"CR","حساب الدائنين للمورد")
    inv.status="Approved";inv.approved_by=user.user_id
    write_audit(db,user.user_id,"Approve","SupplierInvoices",invoice_id,new={"status":inv.status});db.commit()
    return {"invoice_id":invoice_id,"status":inv.status}

@purchases.post("/invoices/{invoice_id}/post")
def post_supplier_invoice(invoice_id:int,user:User=Depends(require_permission("PurchaseCycle","Post")),db:Session=Depends(get_db)):
    inv=db.scalar(select(SupplierInvoice).where(SupplierInvoice.invoice_id==invoice_id).with_for_update())
    if not inv:raise HTTPException(404,"فاتورة المورد غير موجودة")
    if inv.status!="Approved" or inv.journal_entry_id:raise HTTPException(409,"اعتمد الفاتورة قبل الترحيل، ولا يمكن ترحيلها مرتين")
    fy=db.scalar(select(FiscalYear).where(FiscalYear.start_date<=inv.invoice_date,FiscalYear.end_date>=inv.invoice_date).with_for_update())
    if not fy:raise HTTPException(409,"لا توجد سنة مالية تشمل تاريخ الفاتورة")
    if fy.is_closed:raise HTTPException(409,"السنة المالية مقفولة")
    supplier=db.get(Counterparty,inv.supplier_id)
    if not supplier or not supplier.linked_account_id:raise HTTPException(409,"حساب الدائنين للمورد غير محدد")
    _invoice_account(db,supplier.linked_account_id,"CR","حساب الدائنين للمورد")
    company_id=fy.company_id
    last=db.scalar(select(func.max(JournalEntry.entry_no)).where(JournalEntry.entry_no.like(f"JE-{fy.start_date.year}-%")))
    seq=int(last.rsplit("-",1)[1])+1 if last and last.rsplit("-",1)[1].isdigit() else 1
    entry=JournalEntry(entry_no=f"JE-{fy.start_date.year}-{seq:06d}",entry_date=inv.invoice_date,company_id=company_id,
        fiscal_year_id=fy.fiscal_year_id,description=f"فاتورة مورد {inv.invoice_no}",status="Posted",created_by=user.user_id,
        posted_by=user.user_id,posted_at=utcnow())
    db.add(entry);db.flush();lines=db.scalars(select(SupplierInvoiceLine).where(SupplierInvoiceLine.invoice_id==invoice_id)).all()
    for n,line in enumerate(lines,1):
        db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=n,account_id=line.account_id,
            project_id=inv.project_id,debit_amount=line.net_amount,credit_amount=0,description=f"فاتورة {inv.invoice_no}"))
    n=len(lines)+1
    if inv.tax_amount:
        _invoice_account(db,inv.tax_account_id,"DR","حساب ضريبة المدخلات")
        db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=n,account_id=inv.tax_account_id,
            project_id=inv.project_id,debit_amount=inv.tax_amount,credit_amount=0,description=f"ضريبة فاتورة {inv.invoice_no}"));n+=1
    db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=n,account_id=supplier.linked_account_id,
        project_id=inv.project_id,debit_amount=0,credit_amount=inv.total_amount,description=f"مستحق للمورد {supplier.legal_name or supplier.name}"))
    inv.journal_entry_id=entry.journal_entry_id;inv.status="Posted"
    write_audit(db,user.user_id,"Post","SupplierInvoices",invoice_id,new={"status":inv.status,"journal_entry_id":entry.journal_entry_id})
    db.commit();return {"invoice_id":invoice_id,"status":inv.status,"journal_entry_id":entry.journal_entry_id,"entry_no":entry.entry_no}

@purchases.post("/invoices/{invoice_id}/payments",status_code=201)
def pay_supplier_invoice(invoice_id:int,body:SupplierInvoicePaymentIn,user:User=Depends(require_permission("PurchaseCycle","Post")),db:Session=Depends(get_db)):
    inv=db.scalar(select(SupplierInvoice).where(SupplierInvoice.invoice_id==invoice_id).with_for_update())
    if not inv or inv.status!="Posted":raise HTTPException(409,"يجب ترحيل فاتورة المورد قبل السداد")
    if body.transaction_date<inv.invoice_date:raise HTTPException(422,"تاريخ السداد لا يسبق تاريخ الفاتورة")
    paid=Decimal(str(db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow),0)).where(TreasuryTransaction.supplier_invoice_id==invoice_id)) or 0))
    remaining=Decimal(str(inv.total_amount))-paid
    if body.amount>remaining:raise HTTPException(409,f"مبلغ السداد يتجاوز المتبقي ({remaining:.2f})")
    treasury=db.get(TreasuryAccount,body.treasury_account_id)
    if not treasury or not treasury.is_active:raise HTTPException(422,"حساب الخزينة أو البنك غير موجود أو غير نشط")
    _invoice_account(db,treasury.gl_account_id,"DR","حساب البنك أو الخزينة")
    supplier=db.get(Counterparty,inv.supplier_id)
    if not supplier or not supplier.linked_account_id:raise HTTPException(409,"حساب الدائنين للمورد غير محدد")
    _invoice_account(db,supplier.linked_account_id,"CR","حساب الدائنين للمورد")
    fy=db.scalar(select(FiscalYear).where(FiscalYear.start_date<=body.transaction_date,FiscalYear.end_date>=body.transaction_date).with_for_update())
    if not fy:raise HTTPException(409,"لا توجد سنة مالية تشمل تاريخ السداد")
    if fy.is_closed:raise HTTPException(409,"السنة المالية مقفولة")
    last=db.scalar(select(func.max(JournalEntry.entry_no)).where(JournalEntry.entry_no.like(f"JE-{fy.start_date.year}-%")))
    seq=int(last.rsplit("-",1)[1])+1 if last and last.rsplit("-",1)[1].isdigit() else 1
    entry=JournalEntry(entry_no=f"JE-{fy.start_date.year}-{seq:06d}",entry_date=body.transaction_date,company_id=fy.company_id,
        fiscal_year_id=fy.fiscal_year_id,description=f"سداد فاتورة المورد {inv.invoice_no}",status="Posted",created_by=user.user_id,
        posted_by=user.user_id,posted_at=utcnow())
    db.add(entry);db.flush()
    db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=1,account_id=supplier.linked_account_id,
        project_id=inv.project_id,debit_amount=body.amount,credit_amount=0,description=f"سداد فاتورة {inv.invoice_no}"))
    db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,line_no=2,account_id=treasury.gl_account_id,
        project_id=inv.project_id,debit_amount=0,credit_amount=body.amount,description=f"سداد فاتورة {inv.invoice_no}"))
    voucher=body.voucher_no or f"SUP-{inv.invoice_id}-{int(paid*100)+1}"
    tx=TreasuryTransaction(treasury_account_id=treasury.treasury_account_id,transaction_date=body.transaction_date,
        inflow=0,outflow=body.amount,description=f"سداد فاتورة المورد {inv.invoice_no}",voucher_no=voucher,status="Posted",
        recipient_name=supplier.legal_name or supplier.name,counterparty_id=supplier.counterparty_id,project_id=inv.project_id,
        supplier_invoice_id=inv.invoice_id,journal_entry_id=entry.journal_entry_id)
    db.add(tx);db.flush()
    write_audit(db,user.user_id,"PaySupplierInvoice","SupplierInvoices",invoice_id,new={"amount":str(body.amount),"journal_entry_id":entry.journal_entry_id,"transaction_id":tx.transaction_id})
    db.commit()
    return {"invoice_id":invoice_id,"paid_amount":str(paid+body.amount),"remaining_amount":str(remaining-body.amount),
        "transaction_id":tx.transaction_id,"journal_entry_id":entry.journal_entry_id,"entry_no":entry.entry_no}

@purchases.post("/{order_id}/approve")
def approve_order(order_id:int,user:User=Depends(require_permission("PurchaseCycle","Approve")),db:Session=Depends(get_db)):
    po=db.scalar(select(PurchaseOrder).where(PurchaseOrder.purchase_order_id==order_id).with_for_update())
    if not po: raise HTTPException(404,"أمر الشراء غير موجود")
    if po.status!="Draft": raise HTTPException(409,"لا يمكن اعتماد أمر الشراء بهذه الحالة")
    po.status="Approved";write_audit(db,user.user_id,"Approve","PurchaseOrders",po.purchase_order_id,new={"status":po.status});db.commit()
    return {"purchase_order_id":po.purchase_order_id,"status":po.status}

@purchases.post("/{order_id}/receive")
def receive_order(order_id:int,user:User=Depends(require_permission("InventoryManagement","Post")),db:Session=Depends(get_db)):
    po=db.scalar(select(PurchaseOrder).where(PurchaseOrder.purchase_order_id==order_id).with_for_update())
    if not po: raise HTTPException(404,"أمر الشراء غير موجود")
    if po.status!="Approved": raise HTTPException(409,"يجب اعتماد أمر الشراء قبل الاستلام")
    lines=db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==order_id)).all()
    for line in lines:
        remaining=Decimal(str(line.quantity))-Decimal(str(line.received_quantity or 0))
        if remaining>0:
            movement_no=f"PO-{po.order_no}-{line.line_id}"
            if not db.scalar(select(InventoryMovement.movement_id).where(InventoryMovement.movement_no==movement_no)):
                db.add(InventoryMovement(movement_no=movement_no,item_id=line.item_id,warehouse_id=po.warehouse_id,movement_date=date.today(),movement_type="IN",quantity=remaining,unit_cost=line.unit_price,reference=po.order_no,notes="استلام أمر شراء",created_by=user.user_id))
            line.received_quantity=line.quantity
    po.status="Received";write_audit(db,user.user_id,"Receive","PurchaseOrders",po.purchase_order_id,new={"status":po.status});db.commit()
    return {"purchase_order_id":po.purchase_order_id,"status":po.status,"message":"تم الاستلام وتحديث أرصدة المخزون"}
