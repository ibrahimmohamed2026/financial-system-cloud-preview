"""Allow-listed CSV/XLSX exchange. Never accepts arbitrary SQL/table names."""
import csv, io, json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, has_permission, write_audit
from ..models import (Account, Contract, ContractItem, ContractSettlement, InventoryItem, Project,
                      InventoryMovement, InventoryWarehouse, JournalEntry, JournalEntryDetail,
                      PurchaseOrder, PurchaseOrderLine, Role, User, UserRole, FinancialCheck, TreasuryAccount)

router = APIRouter(prefix="/api/data-exchange", tags=["Import / Export"])
MAX_BYTES, MAX_ROWS = 8 * 1024 * 1024, 10000

# Resource names and fields are fixed here; caller input is never used as a SQL identifier.
R = {
 "accounts": (Account, "ChartOfAccounts", ("account_code","account_name_ar","parent_account_id","classification_id","normal_balance","opening_debit","opening_credit","is_active"), ("account_code","account_name_ar","parent_account_id","classification_id","normal_balance","opening_debit","opening_credit","is_active")),
 "contracts": (Contract, "Contracts", ("contract_no","title","client_name","project_id","start_date","end_date","original_value","status","notes"), ("contract_no","title","client_name","project_id","start_date","end_date","original_value","status","notes")),
 "contract_items": (ContractItem, "ContractItems", ("contract_id","item_no","description","unit","quantity","unit_price"), ("contract_id","item_no","description","unit","quantity","unit_price")),
 "inventory_items": (InventoryItem, "InventoryManagement", ("code","name","category","unit","min_quantity","is_active"), ("code","name","category","unit","min_quantity","is_active")),
 "warehouses": (InventoryWarehouse, "InventoryManagement", ("code","name","location","is_active"), ("code","name","location","is_active")),
 "inventory_movements": (InventoryMovement, "InventoryManagement", ("movement_no","item_id","warehouse_id","movement_date","movement_type","quantity","unit_cost","reference","notes"), ("movement_no","item_id","warehouse_id","movement_date","movement_type","quantity","unit_cost","reference","notes")),
 "journal_entries": (JournalEntry, "JournalBook", ("entry_no","entry_date","company_id","fiscal_year_id","description","status"), ("entry_no","entry_date","company_id","fiscal_year_id","description","account_id","line_no","debit_amount","credit_amount","project_id","line_description")),
 "purchase_orders": (None, "InventoryManagement", ("order_no","order_date","supplier_name","warehouse_id","status","notes","item_id","quantity","unit_price","received_quantity"), ()),
 "contract_settlements": (ContractSettlement, "Contracts", ("contract_id","settlement_side","sequence_no","settlement_no","settlement_date","counterparty_name","work_value","cumulative_work_value","vat_amount","net_amount","status","notes"), ()),
 "users": (User, "Users", ("user_id","username","full_name","is_active","failed_login_count","locked_until","created_at"), ()),
 "financial_checks": (FinancialCheck, "ChecksCib", ("check_number","check_type","amount","due_date","party_account_id","treasury_account_id","drawee_bank","project_id","description","status"), ("check_number","check_type","amount","due_date","party_account_id","treasury_account_id","drawee_bank","project_id","description")),
}


def _val(v: Any, typ):
    if v in (None, ""): return None
    if typ is bool:
        if isinstance(v, bool): return v
        s=str(v).strip().lower()
        if s in ("1","true","yes","نعم","نشط"): return True
        if s in ("0","false","no","لا","غير نشط"): return False
        raise ValueError("قيمة منطقية غير صحيحة")
    if typ is date:
        return v if isinstance(v,date) and not isinstance(v,datetime) else date.fromisoformat(str(v)[:10])
    if typ is datetime:
        return v if isinstance(v,datetime) else datetime.fromisoformat(str(v))
    if typ is Decimal:
        try: return Decimal(str(v))
        except InvalidOperation: raise ValueError("قيمة رقمية غير صحيحة")
    if typ is int: return int(v)
    return str(v)


def _rows(file: UploadFile, raw: bytes):
    name=(file.filename or "").lower()
    try:
        if name.endswith(".xlsx"):
            ws=load_workbook(io.BytesIO(raw),read_only=True,data_only=True).active
            vals=ws.iter_rows(values_only=True)
            headers=[str(x).strip() if x is not None else "" for x in next(vals)]
            return headers,[dict(zip(headers,row)) for row in vals if any(x is not None for x in row)]
        if name.endswith(".csv"):
            text=raw.decode("utf-8-sig")
            reader=csv.DictReader(io.StringIO(text))
            return [str(x).strip() for x in (reader.fieldnames or [])],[dict(r) for r in reader]
    except Exception as e:
        raise HTTPException(400,f"تعذر قراءة الملف: {e}")
    raise HTTPException(415,"استخدم ملف CSV أو XLSX")


def _export_rows(resource: str, db: Session):
    if resource == "purchase_orders":
        fields=R[resource][2]; out=[]
        orders=db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.order_date,PurchaseOrder.order_no)).all()
        for po in orders:
            lines=db.scalars(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id==po.purchase_order_id)).all()
            for line in lines or [None]:
                out.append({"order_no":po.order_no,"order_date":po.order_date,"supplier_name":po.supplier_name,"warehouse_id":po.warehouse_id,"status":po.status,"notes":po.notes,"item_id":line.item_id if line else None,"quantity":line.quantity if line else None,"unit_price":line.unit_price if line else None,"received_quantity":line.received_quantity if line else None})
        return fields,out
    if resource == "journal_entries":
        out=[]
        entries=db.scalars(select(JournalEntry).order_by(JournalEntry.entry_date,JournalEntry.entry_no)).all()
        for e in entries:
            lines=db.scalars(select(JournalEntryDetail).where(JournalEntryDetail.journal_entry_id==e.journal_entry_id).order_by(JournalEntryDetail.line_no)).all()
            for line in lines or [None]:
                out.append({"entry_no":e.entry_no,"entry_date":e.entry_date,"company_id":e.company_id,"fiscal_year_id":e.fiscal_year_id,"description":e.description,"status":e.status,"account_id":line.account_id if line else None,"line_no":line.line_no if line else None,"debit_amount":line.debit_amount if line else None,"credit_amount":line.credit_amount if line else None,"project_id":line.project_id if line else None,"line_description":line.description if line else None})
        return R[resource][2],out
    model=R[resource][0]
    if model is None: raise HTTPException(400,"هذا النوع يدعم التصدير من الشاشة فقط عبر API الخاص به")
    fields=R[resource][2]
    rows=db.scalars(select(model)).all()
    return fields,[{f:getattr(x,f,None) for f in fields} for x in rows]

@router.get("/{resource}/export")
def export_data(resource: str, fmt: str="csv", user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    if resource not in R: raise HTTPException(404,"نوع البيانات غير مسموح")
    # Resource-specific permissions are enforced below too.
    screen=R[resource][1]
    if resource=="users":
        is_admin=db.scalar(select(UserRole.user_id).join(Role,Role.role_id==UserRole.role_id).where(UserRole.user_id==user.user_id,Role.role_name=="Admin"))
        if not is_admin: raise HTTPException(403,"تصدير المستخدمين متاح لمدير النظام فقط")
    elif resource == "financial_checks":
        if not any(has_permission(db,user.user_id,sc,"View") for sc in ("FinancialChecks","ChecksCib","ChecksCairoEgp","ChecksCairoUsd")): raise HTTPException(403,"لا توجد صلاحية عرض/تصدير")
    elif not has_permission(db,user.user_id,screen,"View"):
        raise HTTPException(403,"لا توجد صلاحية عرض/تصدير")
    fields,rows=_export_rows(resource,db)
    if len(rows)>MAX_ROWS: raise HTTPException(413,"عدد الصفوف يتجاوز الحد؛ استخدم فلاتر الشاشة")
    if fmt.lower()=="xlsx":
        wb=Workbook(write_only=True); ws=wb.create_sheet("Export"); ws.append(list(fields))
        for row in rows: ws.append([str(row.get(f)) if row.get(f) is not None else "" for f in fields])
        buf=io.BytesIO(); wb.save(buf); content=buf.getvalue(); media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; ext="xlsx"
    elif fmt.lower()=="csv":
        buf=io.StringIO(newline=""); w=csv.DictWriter(buf,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for row in rows: w.writerow({k:str(v) if v is not None else "" for k,v in row.items()})
        content=buf.getvalue().encode("utf-8-sig"); media="text/csv; charset=utf-8"; ext="csv"
    else: raise HTTPException(400,"format يجب أن يكون csv أو xlsx")
    write_audit(db,user.user_id,"Export",resource,None,new={"rows":len(rows),"format":ext}); db.commit()
    return StreamingResponse(io.BytesIO(content),media_type=media,headers={"Content-Disposition":f'attachment; filename="{resource}.{ext}"'})

@router.post("/{resource}/import")
async def import_data(resource: str, file: UploadFile=File(...), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    if resource not in R: raise HTTPException(404,"نوع البيانات غير مسموح")
    model,screen,_,allowed=R[resource]
    if resource == "financial_checks":
        if not any(has_permission(db,user.user_id,sc,"Add") for sc in ("FinancialChecks","ChecksCib","ChecksCairoEgp","ChecksCairoUsd")): raise HTTPException(403,"لا توجد صلاحية استيراد لهذا القسم")
    elif not has_permission(db,user.user_id,screen,"Add"):
        raise HTTPException(403,"لا توجد صلاحية استيراد لهذا القسم")
    if resource=="users":
        # Separate admin workflow must hash passwords and assign roles.
        raise HTTPException(400,"استيراد المستخدمين يتم من شاشة إدارة المستخدمين مع تعيين كلمة مرور وصلاحيات")
    if resource=="contract_settlements":
        raise HTTPException(400,"لا يُستورد المستخلص المالي من ملف عام؛ يجب إدخال تفاصيل البنود واحتساب الخصومات والضريبة من شاشة المستخلص ثم الاعتماد")
    raw=await file.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise HTTPException(413,"الملف أكبر من 8MB")
    headers,rows=_rows(file,raw)
    if not rows: raise HTTPException(400,"الملف لا يحتوي على بيانات")
    if len(rows)>MAX_ROWS: raise HTTPException(413,"الحد الأقصى 10000 صف")
    if resource=="financial_checks":
        required={"check_number","check_type","amount","due_date","party_account_id","treasury_account_id"}
        if required-set(headers): raise HTTPException(400,"أعمدة الشيكات المطلوبة: "+", ".join(sorted(required)))
        made=[]
        try:
            for n,row in enumerate(rows,2):
                number=str(row.get("check_number") or "").strip(); typ=str(row.get("check_type") or "").strip().upper()
                amount=Decimal(str(row.get("amount") or "0")); due=date.fromisoformat(str(row.get("due_date") or "")[:10])
                party=int(row.get("party_account_id")); treasury=int(row.get("treasury_account_id"))
                project_id=int(row["project_id"]) if row.get("project_id") not in (None, "") else None
                if not number or typ not in ("INCOMING","OUTGOING") or amount<=0: raise ValueError(f"صف {n}: رقم/نوع/مبلغ غير صحيح")
                party_account = db.get(Account, party)
                treasury_account = db.get(TreasuryAccount, treasury)
                if not party_account or not party_account.is_active or not treasury_account or not treasury_account.is_active or treasury_account.account_type != "Bank" or treasury_account.currency_code != "EGP":
                    raise ValueError(f"صف {n}: حساب العميل أو البنك غير موجود أو غير صالح")
                from .financial_checks import _validate_party_account
                _validate_party_account(db, typ, party_account)
                if project_id is not None:
                    project = db.get(Project, project_id)
                    if not project or not project.is_active: raise ValueError(f"صف {n}: المشروع غير موجود أو غير نشط")
                if db.scalar(select(FinancialCheck.check_id).where(
                    FinancialCheck.check_number == number,
                    FinancialCheck.check_type == typ,
                    FinancialCheck.treasury_account_id == treasury
                )):
                    raise ValueError(f"صف {n}: رقم الشيك موجود لنفس النوع والحساب البنكي: {number}")
                made.append(FinancialCheck(check_number=number,check_type=typ,amount=amount,due_date=due,party_account_id=party,treasury_account_id=treasury,drawee_bank=(row.get("drawee_bank") or None),project_id=project_id,project_brand="عام",description=(row.get("description") or None),status="مسودة",created_by=user.user_id))
            for c in made: db.add(c)
            write_audit(db,user.user_id,"Import","FinancialChecks",None,new={"rows":len(made)}); db.commit()
            return {"success":True,"imported":len(made),"message":f"تم استيراد {len(made)} شيك كمسودات"}
        except HTTPException: db.rollback(); raise
        except Exception as e: db.rollback(); raise HTTPException(422,f"فشل استيراد الشيكات دون حفظ جزئي: {e}")
    if resource=="purchase_orders":
        required={"order_no","order_date","supplier_name","warehouse_id","item_id","quantity","unit_price"}
        if required-set(headers): raise HTTPException(400,"أعمدة المشتريات المطلوبة: "+", ".join(sorted(required)))
        grouped={}
        for n,row in enumerate(rows,2):
            try:
                key=str(row["order_no"]).strip()
                if not key: raise ValueError("رقم أمر الشراء مطلوب")
                wh=int(row["warehouse_id"]); item=int(row["item_id"]); qty=Decimal(str(row["quantity"])); price=Decimal(str(row["unit_price"]))
                if not db.get(InventoryWarehouse,wh) or not db.get(InventoryItem,item): raise ValueError("المخزن أو الصنف غير موجود")
                if qty<=0 or price<0: raise ValueError("الكمية يجب أن تكون موجبة والسعر غير سالب")
                head={"order_date":date.fromisoformat(str(row["order_date"])[:10]),"supplier_name":str(row["supplier_name"]).strip(),"warehouse_id":wh,"notes":str(row.get("notes") or "")}
                if not head["supplier_name"]: raise ValueError("اسم المورد مطلوب")
                if key in grouped and grouped[key][0]!=head: raise ValueError("بيانات أمر الشراء غير متطابقة بين صفوفه")
                grouped.setdefault(key,[head,[]])[1].append({"item_id":item,"quantity":qty,"unit_price":price})
            except Exception as e: raise HTTPException(422,f"صف {n}: {e}")
        for key in grouped:
            if db.scalar(select(PurchaseOrder.purchase_order_id).where(PurchaseOrder.order_no==key)): raise HTTPException(409,f"رقم أمر الشراء موجود: {key}")
        try:
            for key,(head,lines) in grouped.items():
                total=sum((x["quantity"]*x["unit_price"] for x in lines),Decimal(0))
                po=PurchaseOrder(order_no=key,**head,status="Draft",total_amount=total,created_by=user.user_id);db.add(po);db.flush()
                for line in lines: db.add(PurchaseOrderLine(purchase_order_id=po.purchase_order_id,**line,received_quantity=0))
            write_audit(db,user.user_id,"Import","PurchaseOrders",None,new={"orders":len(grouped),"rows":len(rows)});db.commit()
            return {"success":True,"imported":len(rows),"orders":len(grouped),"message":"تم استيراد أوامر الشراء كمسودات؛ يلزم مراجعتها واعتمادها من شاشة المشتريات"}
        except Exception as e: db.rollback(); raise HTTPException(422,f"فشل الاستيراد وتم التراجع عن كامل العملية: {e}")
    if model is None: raise HTTPException(400,"هذا النوع غير قابل للاستيراد من ملف عام")
    missing=set(allowed)-set(headers)
    # Journal import accepts line-level rows and groups them into balanced draft entries.
    if resource=="journal_entries":
        required={"entry_no","entry_date","company_id","fiscal_year_id","account_id","debit_amount","credit_amount"}
        if required-set(headers): raise HTTPException(400,"أعمدة القيود المطلوبة: "+", ".join(sorted(required)))
        grouped={}
        for n,row in enumerate(rows,2):
            try:
                key=str(row["entry_no"]).strip(); line={"account_id":int(row["account_id"]),"line_no":int(row.get("line_no") or len(grouped.get(key,[]))+1),"debit_amount":Decimal(str(row.get("debit_amount") or 0)),"credit_amount":Decimal(str(row.get("credit_amount") or 0)),"project_id":int(row["project_id"]) if row.get("project_id") else None,"description":str(row.get("line_description") or row.get("description") or "")}
                if not key or line["debit_amount"]<0 or line["credit_amount"]<0 or (line["debit_amount"] and line["credit_amount"]): raise ValueError("رقم القيد أو المدين/الدائن غير صحيح")
                head={"entry_date":date.fromisoformat(str(row["entry_date"])[:10]),"company_id":int(row["company_id"]),"fiscal_year_id":int(row["fiscal_year_id"]),"description":str(row.get("description") or "استيراد CSV/XLSX")}
                if key in grouped and grouped[key][0]!=head: raise ValueError("بيانات رأس القيد غير متطابقة داخل نفس الرقم")
                grouped.setdefault(key,[head,[]])[1].append(line)
            except Exception as e: raise HTTPException(422,f"صف {n}: {e}")
        for key,(head,lines) in grouped.items():
            if db.scalar(select(JournalEntry.journal_entry_id).where(JournalEntry.entry_no==key)): raise HTTPException(409,f"رقم القيد موجود بالفعل: {key}")
            debit=sum((x["debit_amount"] for x in lines),Decimal(0)); credit=sum((x["credit_amount"] for x in lines),Decimal(0))
            if len(lines)<2 or debit<=0 or debit!=credit: raise HTTPException(422,f"القيد {key} غير متوازن أو يحتوي على أقل من سطرين")
            if any(not db.get(Account,x["account_id"]) for x in lines): raise HTTPException(422,f"القيد {key}: يوجد حساب غير موجود")
        try:
            created=0
            for key,(head,lines) in grouped.items():
                entry=JournalEntry(entry_no=key,**head,status="Draft",created_by=user.user_id);db.add(entry);db.flush()
                for line in lines: db.add(JournalEntryDetail(journal_entry_id=entry.journal_entry_id,**line))
                created+=1
            write_audit(db,user.user_id,"Import","JournalEntries",None,new={"entries":created,"rows":len(rows)});db.commit()
            return {"success":True,"imported":len(rows),"entries":created,"message":"تم استيراد القيود كمسودات متوازنة؛ يلزم مراجعتها وترحيلها من شاشة اليومية"}
        except Exception as e: db.rollback(); raise HTTPException(422,f"فشل الاستيراد وتم التراجع عن كامل العملية: {e}")
    if missing: raise HTTPException(400,"أعمدة ناقصة: "+", ".join(sorted(missing)))
    clean=[]
    for n,row in enumerate(rows,2):
        try:
            data={}
            for field in allowed:
                col=getattr(model,field).property.columns[0]
                typ=bool if str(col.type).lower()=="boolean" else date if str(col.type).lower()=="date" else int if "INTEGER" in str(col.type).upper() else Decimal if any(x in str(col.type).upper() for x in ("NUMERIC","DECIMAL")) else str
                v=_val(row.get(field),typ)
                if v is not None: data[field]=v
            if resource=="accounts":
                if not data.get("account_code") or not data.get("account_name_ar") or not data.get("classification_id"): raise ValueError("كود الحساب والاسم والتصنيف مطلوبة")
                if data.get("normal_balance") not in ("DR","CR"): raise ValueError("normal_balance يجب DR أو CR")
                if data.get("opening_debit",Decimal(0)) and data.get("opening_credit",Decimal(0)): raise ValueError("لا يجوز وجود رصيد افتتاحي مدين ودائن معًا")
            if resource=="inventory_items" and (not data.get("code") or not data.get("name")): raise ValueError("كود واسم الصنف مطلوبان")
            if resource=="warehouses" and (not data.get("code") or not data.get("name")): raise ValueError("كود واسم المخزن مطلوبان")
            if resource=="contracts" and (not data.get("contract_no") or not data.get("title") or not data.get("client_name")): raise ValueError("رقم العقد والعنوان والعميل مطلوبة")
            if resource=="contract_items" and (not data.get("contract_id") or not db.get(Contract,data["contract_id"])): raise ValueError("العقد غير موجود")
            if resource=="inventory_movements":
                if data.get("movement_type") not in ("IN","OUT"): raise ValueError("movement_type يجب IN أو OUT")
                if data.get("quantity",0)<=0 or not db.get(InventoryItem,data.get("item_id")) or not db.get(InventoryWarehouse,data.get("warehouse_id")): raise ValueError("الصنف/المخزن غير موجود أو الكمية غير صحيحة")
            clean.append(data)
        except Exception as e: raise HTTPException(422,f"صف {n}: {e}")
    # Validate duplicates against DB and within file before inserting any rows.
    uniq={"accounts":"account_code","contracts":"contract_no","inventory_items":"code","warehouses":"code","inventory_movements":"movement_no"}.get(resource)
    if uniq:
        seen=set()
        for i,row in enumerate(clean,2):
            value=row.get(uniq)
            if value in seen or (value is not None and db.scalar(select(model).where(getattr(model,uniq)==value))): raise HTTPException(409,f"صف {i}: قيمة مكررة للحقل {uniq}: {value}")
            seen.add(value)
    try:
        stock={}
        for data in clean:
            if resource=="inventory_movements":
                key=(data["item_id"],data["warehouse_id"])
                if key not in stock:
                    movs=db.scalars(select(InventoryMovement).where(InventoryMovement.item_id==key[0],InventoryMovement.warehouse_id==key[1])).all()
                    stock[key]=sum((Decimal(x.quantity) if x.movement_type=="IN" else -Decimal(x.quantity) for x in movs),Decimal(0))
                delta=Decimal(data["quantity"]) if data["movement_type"]=="IN" else -Decimal(data["quantity"])
                if stock[key]+delta<0: raise ValueError(f"الرصيد غير كافٍ للصرف للصنف {key[0]} بالمخزن {key[1]}")
                stock[key]+=delta
                data["created_by"]=user.user_id
            if resource=="contracts": data["created_by"]=user.user_id
            db.add(model(**data))
        write_audit(db,user.user_id,"Import",resource,None,new={"rows":len(clean)});db.commit()
    except Exception as e:
        db.rollback(); raise HTTPException(422,f"فشل الاستيراد وتم التراجع عن كامل العملية: {e}")
    return {"success":True,"imported":len(clean),"message":f"تم استيراد {len(clean)} صف بنجاح"}


# Compatibility endpoints used by frontend exports/imports: /api/export/{module} and /api/import/{module}.
exchange_alias_router = APIRouter(prefix="/api", tags=["Import / Export"])
_ALIASES = {"accounting":"accounts", "journal":"journal_entries", "inventory":"inventory_items", "checks":"financial_checks", "financial-checks":"financial_checks", "purchases":"purchase_orders", "purchase-orders":"purchase_orders", "settlements":"contract_settlements"}
@exchange_alias_router.get("/export/{module_name}")
def export_alias(module_name: str, format: str="csv", fmt: str|None=None, user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    resource=_ALIASES.get(module_name,module_name)
    return export_data(resource, fmt or format, user, db)
@exchange_alias_router.post("/import/{module_name}")
async def import_alias(module_name: str, file: UploadFile=File(...), user: User=Depends(get_current_user), db: Session=Depends(get_db)):
    resource=_ALIASES.get(module_name,module_name)
    return await import_data(resource,file,user,db)
