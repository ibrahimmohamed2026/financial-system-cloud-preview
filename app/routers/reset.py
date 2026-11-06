"""Safe, preview-first system data reset. Never deletes protected system configuration."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from .. import backup_service
from ..database import get_db
from ..deps import get_current_user, write_audit
from ..models import Base, User, JobProfile, Account, JournalEntry, ContractSettlement
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
    "InventoryItems", "ItemCatalog",
}
PROTECTED_TABLES = {
    "Companies", "FiscalYears", "AccountClassifications", "FinancialStatementLines",
    "ChartOfAccounts", "Users", "UserAvatars", "Roles", "Permissions", "RolePermissions",
    "UserRoles", "UserPermissions", "JobProfiles", "JobProfilePermissions",
    "Sections", "Screens", "AuditLog", "UserDeletionRequests", "Projects",
    "ExchangeRates", "TreasuryAccounts", "CheckPrintTemplates",
}

def _admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    allowed = db.scalar(select(User.user_id).join(
        JobProfile, JobProfile.job_profile_id == User.job_profile_id
    ).where(
        User.user_id == user.user_id,
        User.is_active.is_(True),
        User.is_deleted.is_(False),
        JobProfile.name_ar == "مسؤول النظام IT",
        JobProfile.is_active.is_(True),
    ))
    if not allowed:
        raise HTTPException(403, "إعادة ضبط البيانات متاحة لوظيفة مسؤول النظام IT فقط")
    return user

def _tables(mode: str = "full"):
    # Compatibility: older cached screens may still send "operational".
    # This installation now has one agreed reset operation: complete reset.
    mode = "full"
    names = OPERATIONAL_TABLES | FULL_EXTRA_TABLES
    metadata_names = {t.name for t in Base.metadata.sorted_tables}
    missing = names - metadata_names
    protected_selected = names & PROTECTED_TABLES
    if missing or protected_selected:
        raise RuntimeError(
            f"Reset table safety check failed; missing={sorted(missing)}, "
            f"protected={sorted(protected_selected)}"
        )
    # Delete every registered operational/master-data table in FK-safe order.
    # Preserve users, permissions, chart of accounts, company/year, projects,
    # treasury definitions, exchange rates, cheque templates and audit history.
    return [t for t in reversed(Base.metadata.sorted_tables) if t.name in names]

@router.get("/preview")
def preview(mode: str = "full", _: User = Depends(_admin), db: Session = Depends(get_db)):
    # Ignore legacy mode values from stale browser caches; always preview full reset.
    mode = "full"
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
            "trial_balance_expected_zero": True,
            "protected": ["دليل الحسابات والتصنيفات", "الشركة والسنة المالية", "كل المستخدمين والصلاحيات والوظائف", "سجل المراجعة", "المشروعات", "تعريفات الخزائن والبنوك وربطها المحاسبي", "أسعار الصرف", "قوالب الشيكات"]}

class ResetRequest(BaseModel):
    mode: str = Field(default="full")
    confirm_text: str
    password: str = Field(min_length=1, max_length=72)

@router.post("/execute")
def execute_reset(body: ResetRequest, user: User = Depends(_admin), db: Session = Depends(get_db)):
    # Compatibility with an older cached client: always execute the approved full mode.
    mode = "full"
    if body.confirm_text != "RESET":
        raise HTTPException(400, "اكتب RESET للتأكيد النهائي")
    current = db.get(User, user.user_id)
    if not current or not verify_password(body.password, current.password_hash):
        raise HTTPException(403, "كلمة مرور المدير غير صحيحة")

    tables = _tables(mode)
    # A complete logical backup (database + application files) must succeed first.
    try:
        backup_path = backup_service.create_backup("pre_restore")
    except Exception as exc:
        raise HTTPException(500, f"تعذر إنشاء النسخة الاحتياطية؛ لم يتم حذف أي بيانات: {exc}") from exc

    deleted = {}
    try:
        # Break the nullable circular FK between journal entries and settlements
        # before deleting either side; both tables are part of every reset mode.
        db.execute(update(JournalEntry).values(source_settlement_id=None))
        db.execute(update(ContractSettlement).values(journal_entry_id=None))
        for table in tables:
            result = db.execute(delete(table))
            deleted[table.name] = int(result.rowcount or 0)
        zeroed_accounts = 0
        if mode == "full":
            rows = db.execute(
                Account.__table__.update()
                .where((Account.opening_debit != 0) | (Account.opening_credit != 0))
                .values(opening_debit=0, opening_credit=0)
            )
            zeroed_accounts = int(rows.rowcount or 0)
        write_audit(db, user.user_id, "SystemReset", "System", mode,
                    new={"mode": mode, "deleted": deleted,
                         "opening_balances_zeroed": zeroed_accounts,
                         "backup": backup_path.name})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"فشل التصفير وتم التراجع عن التغييرات. النسخة الاحتياطية: {backup_path.name}") from exc
    return {"ok": True, "mode": mode, "deleted": deleted,
            "opening_balances_zeroed": zeroed_accounts, "backup": backup_path.name,
            "message": "تمت إعادة ضبط البيانات بنجاح"}
