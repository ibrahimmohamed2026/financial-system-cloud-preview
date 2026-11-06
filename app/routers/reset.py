"""Safe, preview-first system data reset. Never deletes protected system configuration."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .. import backup_service
from ..database import get_db
from ..deps import get_current_user, write_audit
from ..models import Base, User, Role, UserRole, Account, AuditLog
from ..security import verify_password

router = APIRouter(prefix="/admin/reset", tags=["System Reset"])

# Operational documents and movements. Reverse metadata order is used for FK-safe deletion.
OPERATIONAL_TABLES = {
    "JournalEntryDetails", "JournalEntries", "TreasuryTransactions", "BankReconciliations",
    "BankReconciliationLines", "Checks", "FinancialChecks", "CheckStatusHistory",
    "ContractRequests", "Contracts", "ContractSettlementSchedules", "ContractAddendums",
    "ContractAddendumLines", "ProgressBillings", "ContractItems", "ContractDeductionRules",
    "ContractAccountingConfig", "ContractSettlements", "ContractSettlementItems",
    "ContractChangeOrders", "InventoryMovements", "SiteIssueRequests", "SiteIssueRequestLines",
    "InventoryStocktakes", "InventoryStocktakeLines", "InventoryReturns", "InventoryReturnLines",
    "PurchaseRequisitions", "PurchaseRequisitionLines", "SupplierQuotations",
    "SupplierQuotationLines", "PurchaseOrders", "PurchaseOrderLines", "PurchaseGoodsReceipts",
    "PurchaseGoodsReceiptLines", "SupplierInvoices", "SupplierInvoiceLines",
    "ContractAttachments", "TechnicalSettlementEstimates", "TechnicalSettlementEstimateItems",
}
FULL_EXTRA_TABLES = {
    "CounterpartyAliases", "Counterparties", "Beneficiaries", "InventoryWarehouses",
    "InventoryItems", "TreasuryAccounts", "ItemCatalog", "CheckPrintTemplates",
}
PROTECTED_TABLES = {
    "Companies", "FiscalYears", "AccountClassifications", "FinancialStatementLines",
    "ChartOfAccounts", "Users", "UserAvatars", "Roles", "Permissions", "RolePermissions",
    "UserRoles", "UserPermissions", "JobProfiles", "JobProfilePermissions",
    "Sections", "Screens", "AuditLog", "UserDeletionRequests", "Projects",
    "ExchangeRates",
}

def _admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    role = db.scalar(select(UserRole.user_id).join(Role, Role.role_id == UserRole.role_id)
        .where(UserRole.user_id == user.user_id, Role.role_name == "Admin"))
    if not role:
        raise HTTPException(403, "إعادة ضبط النظام متاحة لمدير النظام فقط")
    return user

def _tables(mode: str):
    if mode not in {"operational", "full"}:
        raise HTTPException(422, "مستوى التصفير غير صحيح")
    names = set(OPERATIONAL_TABLES)
    if mode == "full":
        names |= FULL_EXTRA_TABLES
    return [t for t in reversed(Base.metadata.sorted_tables) if t.name in names]

@router.get("/preview")
def preview(mode: str, _: User = Depends(_admin), db: Session = Depends(get_db)):
    tables = _tables(mode)
    result = []
    for table in tables:
        count = int(db.scalar(select(func.count()).select_from(table)) or 0)
        if count:
            result.append({"table": table.name, "count": count})
    opening_count = 0
    if mode == "full":
        opening_count = int(db.scalar(select(func.count()).select_from(Account).where(
            (Account.opening_debit != 0) | (Account.opening_credit != 0))) or 0)
    return {"mode": mode, "tables": result, "total_rows": sum(x["count"] for x in result),
            "accounts_opening_balances_to_zero": opening_count,
            "protected": ["دليل الحسابات والتصنيفات", "الشركة والسنة المالية", "المستخدمون والصلاحيات", "سجل المراجعة", "المشروعات"]}

class ResetRequest(BaseModel):
    mode: str = Field(pattern="^(operational|full)$")
    confirm_text: str
    password: str = Field(min_length=1, max_length=72)

@router.post("/execute")
def execute_reset(body: ResetRequest, user: User = Depends(_admin), db: Session = Depends(get_db)):
    if body.confirm_text != "RESET":
        raise HTTPException(400, "اكتب RESET للتأكيد النهائي")
    current = db.get(User, user.user_id)
    if not current or not verify_password(body.password, current.password_hash):
        raise HTTPException(403, "كلمة مرور المدير غير صحيحة")

    tables = _tables(body.mode)
    # A complete logical backup (database + application files) must succeed first.
    try:
        backup_path = backup_service.create_backup("pre_restore")
    except Exception as exc:
        raise HTTPException(500, f"تعذر إنشاء النسخة الاحتياطية؛ لم يتم حذف أي بيانات: {exc}") from exc

    deleted = {}
    try:
        for table in tables:
            result = db.execute(delete(table))
            deleted[table.name] = int(result.rowcount or 0)
        zeroed_accounts = 0
        if body.mode == "full":
            rows = db.execute(
                Account.__table__.update()
                .where((Account.opening_debit != 0) | (Account.opening_credit != 0))
                .values(opening_debit=0, opening_credit=0)
            )
            zeroed_accounts = int(rows.rowcount or 0)
        write_audit(db, user.user_id, "SystemReset", "System", body.mode,
                    new={"mode": body.mode, "deleted": deleted,
                         "opening_balances_zeroed": zeroed_accounts,
                         "backup": backup_path.name})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"فشل التصفير وتم التراجع عن التغييرات. النسخة الاحتياطية: {backup_path.name}") from exc
    return {"ok": True, "mode": body.mode, "deleted": deleted,
            "opening_balances_zeroed": zeroed_accounts, "backup": backup_path.name,
            "message": "تمت إعادة ضبط البيانات بنجاح"}
