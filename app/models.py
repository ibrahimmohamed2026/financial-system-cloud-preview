"""SQLAlchemy models مطابقة لسكريبت financial_system_schema.sql (+ جدولي Sections/Screens من 002_screens.sql).

ملاحظة: السكريبت هو المرجع لإنشاء الداتا بيز في الإنتاج؛ الـModels هنا للقراءة/الكتابة فقط.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, CHAR, Column, Computed, Date, DateTime, ForeignKey, Integer,
    LargeBinary, MetaData, Numeric, Table, Unicode, UnicodeText, UniqueConstraint, JSON, CheckConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, synonym

BigPK = BigInteger().with_variant(Integer(), "sqlite")


def utcnow() -> datetime:
    """DATETIME2 بدون timezone — بنخزّن UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def C(name: str, type_, *args, **kwargs):
    return mapped_column(name, type_, *args, **kwargs)


class Base(DeclarativeBase):
    pass


# ----------------------------- 1) الإعدادات الأساسية -----------------------------
class Company(Base):
    __tablename__ = "Companies"
    company_id: Mapped[int] = C("CompanyId", Integer, primary_key=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(200))
    name_en: Mapped[Optional[str]] = C("NameEn", Unicode(200), nullable=True)
    tax_number: Mapped[Optional[str]] = C("TaxNumber", Unicode(50), nullable=True)
    commercial_register: Mapped[Optional[str]] = C("CommercialRegister", Unicode(50), nullable=True)
    address_ar: Mapped[Optional[str]] = C("AddressAr", Unicode(500), nullable=True)
    phone: Mapped[Optional[str]] = C("Phone", Unicode(50), nullable=True)
    email: Mapped[Optional[str]] = C("Email", Unicode(200), nullable=True)
    website: Mapped[Optional[str]] = C("Website", Unicode(200), nullable=True)
    logo_data: Mapped[Optional[str]] = C("LogoData", UnicodeText, nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class FiscalYear(Base):
    __tablename__ = "FiscalYears"
    fiscal_year_id: Mapped[int] = C("FiscalYearId", Integer, primary_key=True)
    company_id: Mapped[int] = C("CompanyId", ForeignKey("Companies.CompanyId"))
    start_date: Mapped[date] = C("StartDate", Date)
    end_date: Mapped[date] = C("EndDate", Date)
    is_closed: Mapped[bool] = C("IsClosed", Boolean, default=False)


class Project(Base):
    __tablename__ = "Projects"
    project_id: Mapped[int] = C("ProjectId", Integer, primary_key=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(200), unique=True)
    name_en: Mapped[Optional[str]] = C("NameEn", Unicode(200), nullable=True)
    is_head_office: Mapped[bool] = C("IsHeadOffice", Boolean, default=False)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)


class ExchangeRate(Base):
    __tablename__ = "ExchangeRates"
    __table_args__ = (UniqueConstraint("CurrencyCode", "RateDate", name="UQ_ExchangeRates"),)
    exchange_rate_id: Mapped[int] = C("ExchangeRateId", Integer, primary_key=True)
    currency_code: Mapped[str] = C("CurrencyCode", Unicode(3))
    rate_date: Mapped[date] = C("RateDate", Date)
    rate_to_egp: Mapped[Decimal] = C("RateToEGP", Numeric(18, 6))


# ----------------------------- 2) الحسابات والقيود -----------------------------
class AccountClassification(Base):
    __tablename__ = "AccountClassifications"
    classification_id: Mapped[int] = C("ClassificationId", Integer, primary_key=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(200), unique=True)
    name_en: Mapped[Optional[str]] = C("NameEn", Unicode(200), nullable=True)
    statement_type: Mapped[str] = C("StatementType", Unicode(30))  # BalanceSheet | IncomeStatement


class FinancialStatementLine(Base):
    __tablename__ = "FinancialStatementLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    statement_type: Mapped[str] = C("StatementType", Unicode(30))
    caption_ar: Mapped[str] = C("CaptionAr", Unicode(200))
    sort_order: Mapped[int] = C("SortOrder", Integer)
    classification_id: Mapped[Optional[int]] = C(
        "ClassificationId", ForeignKey("AccountClassifications.ClassificationId"), nullable=True)
    is_subtotal: Mapped[bool] = C("IsSubtotal", Boolean, default=False)


class Account(Base):
    __tablename__ = "ChartOfAccounts"
    account_id: Mapped[int] = C("AccountId", Integer, primary_key=True)
    account_code: Mapped[str] = C("AccountCode", Unicode(30), unique=True)
    account_name_ar: Mapped[str] = C("AccountNameAr", Unicode(300))
    account_name_en: Mapped[Optional[str]] = C("AccountNameEn", Unicode(300), nullable=True)
    parent_account_id: Mapped[Optional[int]] = C(
        "ParentAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    classification_id: Mapped[int] = C("ClassificationId", ForeignKey("AccountClassifications.ClassificationId"))
    normal_balance: Mapped[str] = C("NormalBalance", CHAR(2))  # DR | CR
    opening_debit: Mapped[Decimal] = C("OpeningDebit", Numeric(18, 2), default=Decimal("0"))
    opening_credit: Mapped[Decimal] = C("OpeningCredit", Numeric(18, 2), default=Decimal("0"))
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class Counterparty(Base):
    """Unified customer, supplier and subcontractor master record."""
    __tablename__ = "Counterparties"
    counterparty_id: Mapped[int] = C("CounterpartyId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(50), unique=True, index=True)
    name: Mapped[str] = C("Name", Unicode(250), index=True)
    legal_name: Mapped[Optional[str]] = C("LegalName", Unicode(250), nullable=True, index=True)
    name_en: Mapped[Optional[str]] = C("NameEn", Unicode(250), nullable=True)
    roles: Mapped[list] = C("Roles", JSON, default=list)
    party_type: Mapped[str] = C("PartyType", Unicode(20), default="Other", index=True)
    account_id: Mapped[Optional[int]] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True, index=True)
    linked_account_id: Mapped[Optional[int]] = C("LinkedAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    tax_number: Mapped[Optional[str]] = C("TaxNumber", Unicode(50), nullable=True)
    tax_no: Mapped[Optional[str]] = C("TaxNo", Unicode(50), nullable=True)
    commercial_register: Mapped[Optional[str]] = C("CommercialRegister", Unicode(50), nullable=True)
    commercial_registration: Mapped[Optional[str]] = C("CommercialRegistration", Unicode(50), nullable=True)
    phone: Mapped[Optional[str]] = C("Phone", Unicode(50), nullable=True)
    email: Mapped[Optional[str]] = C("Email", Unicode(200), nullable=True)
    address: Mapped[Optional[str]] = C("Address", Unicode(500), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)
    # Attribute aliases keep the current model schema compatible with the
    # unified-party API and report code carried in 25.zip.
    party_id = synonym("counterparty_id")


class CounterpartyAlias(Base):
    __tablename__ = "CounterpartyAliases"
    alias_id: Mapped[int] = C("AliasId", Integer, primary_key=True)
    alias_name: Mapped[str] = C("AliasName", Unicode(200), unique=True, index=True)
    canonical_name: Mapped[str] = C("CanonicalName", Unicode(250), index=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class JournalEntry(Base):
    __tablename__ = "JournalEntries"
    journal_entry_id: Mapped[int] = C("JournalEntryId", Integer, primary_key=True)
    entry_no: Mapped[str] = C("EntryNo", Unicode(30), unique=True)
    entry_date: Mapped[date] = C("EntryDate", Date)
    company_id: Mapped[int] = C("CompanyId", ForeignKey("Companies.CompanyId"))
    fiscal_year_id: Mapped[int] = C("FiscalYearId", ForeignKey("FiscalYears.FiscalYearId"))
    source_settlement_id: Mapped[Optional[int]] = C("SourceSettlementId", ForeignKey("ContractSettlements.SettlementId"), nullable=True, index=True)
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    status: Mapped[str] = C("Status", Unicode(20), default="Draft")  # Draft | Posted | Reversed
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    posted_by: Mapped[Optional[int]] = C("PostedBy", ForeignKey("Users.UserId"), nullable=True)
    posted_at: Mapped[Optional[datetime]] = C("PostedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class JournalEntryDetail(Base):
    __tablename__ = "JournalEntryDetails"
    detail_id: Mapped[int] = C("DetailId", Integer, primary_key=True)
    journal_entry_id: Mapped[int] = C("JournalEntryId", ForeignKey("JournalEntries.JournalEntryId"))
    line_no: Mapped[int] = C("LineNo", Integer)  # LINENO كلمة محجوزة في T-SQL → لازم [LineNo] في السكريبت
    account_id: Mapped[int] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"))
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    debit_amount: Mapped[Decimal] = C("DebitAmount", Numeric(18, 2), default=Decimal("0"))
    credit_amount: Mapped[Decimal] = C("CreditAmount", Numeric(18, 2), default=Decimal("0"))
    fcy_amount: Mapped[Optional[Decimal]] = C("FcyAmount", Numeric(18, 2), nullable=True)
    exchange_rate: Mapped[Optional[Decimal]] = C("ExchangeRate", Numeric(18, 6), nullable=True)
    description: Mapped[Optional[str]] = C("Description", UnicodeText, nullable=True)


# ----------------------------- 3) الخزائن والبنوك -----------------------------
class TreasuryAccount(Base):
    __tablename__ = "TreasuryAccounts"
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", Integer, primary_key=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(200))
    account_type: Mapped[str] = C("AccountType", Unicode(10))  # Bank | Cash
    currency_code: Mapped[str] = C("CurrencyCode", Unicode(3))
    bank_account_number: Mapped[Optional[str]] = C("BankAccountNumber", Unicode(50), nullable=True)
    gl_account_id: Mapped[int] = C("GLAccountId", ForeignKey("ChartOfAccounts.AccountId"))
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    screen_code: Mapped[Optional[str]] = C("ScreenCode", Unicode(50), nullable=True, unique=True)  # 004
    checks_screen_code: Mapped[Optional[str]] = C("ChecksScreenCode", Unicode(50), nullable=True, unique=True)  # 004


class TreasuryTransaction(Base):
    __tablename__ = "TreasuryTransactions"
    transaction_id: Mapped[int] = C("TransactionId", BigPK, primary_key=True)
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", ForeignKey("TreasuryAccounts.TreasuryAccountId"))
    transaction_date: Mapped[date] = C("TransactionDate", Date)
    inflow: Mapped[Decimal] = C("Inflow", Numeric(18, 2), default=Decimal("0"))
    outflow: Mapped[Decimal] = C("Outflow", Numeric(18, 2), default=Decimal("0"))
    exchange_rate: Mapped[Optional[Decimal]] = C("ExchangeRate", Numeric(18, 6), nullable=True)
    counterpart_account_id: Mapped[Optional[int]] = C("CounterpartAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    transaction_type: Mapped[Optional[str]] = C("TransactionType", Unicode(40), nullable=True)
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    voucher_no: Mapped[Optional[str]] = C("VoucherNo", Unicode(50), nullable=True)
    status: Mapped[Optional[str]] = C("Status", Unicode(30), nullable=True)
    recipient_name: Mapped[Optional[str]] = C("RecipientName", Unicode(200), nullable=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    settlement_id: Mapped[Optional[int]] = C("SettlementId", ForeignKey("ContractSettlements.SettlementId"), nullable=True, index=True)
    supplier_invoice_id: Mapped[Optional[int]] = C("SupplierInvoiceId", ForeignKey("SupplierInvoices.InvoiceId"), nullable=True, index=True)
    journal_entry_id: Mapped[Optional[int]] = C(
        "JournalEntryId", ForeignKey("JournalEntries.JournalEntryId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class BankReconciliation(Base):
    __tablename__ = "BankReconciliations"
    reconciliation_id: Mapped[int] = C("ReconciliationId", Integer, primary_key=True)
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", ForeignKey("TreasuryAccounts.TreasuryAccountId"))
    reconciliation_date: Mapped[date] = C("ReconciliationDate", Date)
    book_balance: Mapped[Decimal] = C("BookBalance", Numeric(18, 2))
    statement_balance: Mapped[Decimal] = C("StatementBalance", Numeric(18, 2))
    difference: Mapped[Decimal] = C(
        "Difference", Numeric(18, 2), Computed('"StatementBalance" - "BookBalance"', persisted=True))
    prepared_by: Mapped[Optional[int]] = C("PreparedBy", ForeignKey("Users.UserId"), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", Unicode(500), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class BankReconciliationLine(Base):
    __tablename__ = "BankReconciliationLines"
    line_id: Mapped[int] = C("LineId", BigPK, primary_key=True)
    reconciliation_id: Mapped[int] = C("ReconciliationId", ForeignKey("BankReconciliations.ReconciliationId"))
    transaction_date: Mapped[Optional[date]] = C("TransactionDate", Date, nullable=True)
    inflow: Mapped[Decimal] = C("Inflow", Numeric(18, 2), default=Decimal("0"))
    outflow: Mapped[Decimal] = C("Outflow", Numeric(18, 2), default=Decimal("0"))
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    check_no: Mapped[Optional[str]] = C("CheckNo", Unicode(30), nullable=True)
    status: Mapped[Optional[str]] = C("Status", Unicode(30), nullable=True)
    recipient: Mapped[Optional[str]] = C("Recipient", Unicode(200), nullable=True)
    is_matched: Mapped[bool] = C("IsMatched", Boolean, default=False)


# ----------------------------- 4) المستفيدون والشيكات -----------------------------
class Beneficiary(Base):
    __tablename__ = "Beneficiaries"
    beneficiary_id: Mapped[int] = C("BeneficiaryId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(30), unique=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(200))
    linked_account_id: Mapped[Optional[int]] = C(
        "LinkedAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    default_project_id: Mapped[Optional[int]] = C(
        "DefaultProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    bank_account_number: Mapped[Optional[str]] = C("BankAccountNumber", Unicode(50), nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)


class Check(Base):
    __tablename__ = "Checks"
    __table_args__ = (UniqueConstraint("TreasuryAccountId", "CheckBookNo", "SequenceNo", name="UQ_Checks_BankBook"),)
    check_id: Mapped[int] = C("CheckId", BigPK, primary_key=True)
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", ForeignKey("TreasuryAccounts.TreasuryAccountId"))
    check_book_no: Mapped[str] = C("CheckBookNo", Unicode(20))
    sequence_no: Mapped[int] = C("SequenceNo", Integer)
    check_no: Mapped[Optional[str]] = C("CheckNo", Unicode(30), nullable=True)
    check_date: Mapped[Optional[date]] = C("CheckDate", Date, nullable=True)
    beneficiary_id: Mapped[int] = C("BeneficiaryId", ForeignKey("Beneficiaries.BeneficiaryId"))
    amount: Mapped[Optional[Decimal]] = C("Amount", Numeric(18, 2), nullable=True)
    purchase_order_no: Mapped[Optional[str]] = C("PurchaseOrderNo", Unicode(50), nullable=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    settlement_id: Mapped[Optional[int]] = C("SettlementId", ForeignKey("ContractSettlements.SettlementId"), nullable=True, index=True)
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    print_date: Mapped[Optional[date]] = C("PrintDate", Date, nullable=True)
    delivery_date: Mapped[Optional[date]] = C("DeliveryDate", Date, nullable=True)
    cash_date: Mapped[Optional[date]] = C("CashDate", Date, nullable=True)
    status: Mapped[str] = C("Status", Unicode(20), default="جديد")
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class FinancialCheck(Base):
    """سجل شيكات محاسبي إضافي؛ لا يغيّر جدول Checks القديم."""
    __tablename__ = "FinancialChecks"
    check_id: Mapped[int] = C("CheckId", BigPK, primary_key=True)
    check_number: Mapped[str] = C("CheckNumber", Unicode(50), unique=True)
    check_type: Mapped[str] = C("CheckType", Unicode(20))  # INCOMING / OUTGOING
    amount: Mapped[Decimal] = C("Amount", Numeric(18, 2))
    due_date: Mapped[date] = C("DueDate", Date)
    drawee_bank: Mapped[Optional[str]] = C("DraweeBank", Unicode(200), nullable=True)
    project_brand: Mapped[str] = C("ProjectBrand", Unicode(50), default="عام", nullable=False)
    status: Mapped[str] = C("Status", Unicode(30), default="مسودة")
    party_account_id: Mapped[int] = C("PartyAccountId", ForeignKey("ChartOfAccounts.AccountId"))
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", ForeignKey("TreasuryAccounts.TreasuryAccountId"))
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    journal_entry_id: Mapped[Optional[int]] = C("JournalEntryId", ForeignKey("JournalEntries.JournalEntryId"), nullable=True, unique=True)
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class CheckStatusHistory(Base):
    __tablename__ = "CheckStatusHistory"
    history_id: Mapped[int] = C("HistoryId", BigPK, primary_key=True)
    check_id: Mapped[int] = C("CheckId", ForeignKey("Checks.CheckId"))
    old_status: Mapped[Optional[str]] = C("OldStatus", Unicode(20), nullable=True)
    new_status: Mapped[str] = C("NewStatus", Unicode(20))
    changed_by: Mapped[Optional[int]] = C("ChangedBy", ForeignKey("Users.UserId"), nullable=True)
    changed_at: Mapped[datetime] = C("ChangedAt", DateTime, default=utcnow)


class CheckPrintTemplate(Base):
    __tablename__ = "CheckPrintTemplates"
    __table_args__ = (UniqueConstraint("TreasuryAccountId", "FieldName", name="UQ_CheckPrintTemplates"),)
    template_id: Mapped[int] = C("TemplateId", Integer, primary_key=True)
    treasury_account_id: Mapped[int] = C("TreasuryAccountId", ForeignKey("TreasuryAccounts.TreasuryAccountId"))
    field_name: Mapped[str] = C("FieldName", Unicode(50))
    pos_x: Mapped[Decimal] = C("PosX", Numeric(10, 2))
    pos_y: Mapped[Decimal] = C("PosY", Numeric(10, 2))
    font_size: Mapped[Decimal] = C("FontSize", Numeric(5, 2), default=Decimal("11"))
    alignment: Mapped[str] = C("Alignment", Unicode(10), default="Left")
    spell_piastres: Mapped[bool] = C("SpellPiastres", Boolean, default=True)
    text_value: Mapped[Optional[str]] = C("TextValue", Unicode(200), nullable=True)


# ----------------------------- الوظائف -----------------------------
class JobProfile(Base):
    __tablename__ = "JobProfiles"
    job_profile_id: Mapped[int] = C("JobProfileId", Integer, primary_key=True)
    name_ar: Mapped[str] = C("NameAr", Unicode(150), unique=True)
    name_en: Mapped[str] = C("NameEn", Unicode(150))
    description: Mapped[Optional[str]] = C("Description", Unicode(500), nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)


class JobProfilePermission(Base):
    __tablename__ = "JobProfilePermissions"
    job_profile_id: Mapped[int] = C("JobProfileId", ForeignKey("JobProfiles.JobProfileId", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = C("PermissionId", ForeignKey("Permissions.PermissionId", ondelete="CASCADE"), primary_key=True)


# ----------------------------- 5) المستخدمون والصلاحيات -----------------------------
class User(Base):
    __tablename__ = "Users"
    user_id: Mapped[int] = C("UserId", Integer, primary_key=True)
    job_profile_id: Mapped[Optional[int]] = C("JobProfileId", ForeignKey("JobProfiles.JobProfileId"), nullable=True, index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    username: Mapped[str] = C("Username", Unicode(50), unique=True)
    password_hash: Mapped[bytes] = C("PasswordHash", LargeBinary)
    full_name: Mapped[str] = C("FullName", Unicode(150))
    preferred_language: Mapped[str] = C("PreferredLanguage", Unicode(5), default="ar")
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    is_deleted: Mapped[bool] = C("IsDeleted", Boolean, default=False, server_default="false")
    last_login_at: Mapped[Optional[datetime]] = C("LastLoginAt", DateTime, nullable=True)
    failed_login_count: Mapped[int] = C("FailedLoginCount", Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = C("LockedUntil", DateTime, nullable=True)
    token_version: Mapped[int] = C("TokenVersion", Integer, default=0, nullable=False, server_default="0")
    avatar_updated_at: Mapped[Optional[datetime]] = C("AvatarUpdatedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class UserDeletionRequest(Base):
    """Two-person approval workflow for archiving a user without breaking historical references."""
    __tablename__ = "UserDeletionRequests"
    request_id: Mapped[int] = C("RequestId", Integer, primary_key=True)
    user_id: Mapped[int] = C("UserId", ForeignKey("Users.UserId"), index=True)
    requested_by: Mapped[int] = C("RequestedBy", ForeignKey("Users.UserId"))
    decided_by: Mapped[Optional[int]] = C("DecidedBy", ForeignKey("Users.UserId"), nullable=True)
    status: Mapped[str] = C("Status", Unicode(20), default="Pending", index=True)
    reason: Mapped[str] = C("Reason", Unicode(500))
    decision_note: Mapped[Optional[str]] = C("DecisionNote", Unicode(500), nullable=True)
    requested_at: Mapped[datetime] = C("RequestedAt", DateTime, default=utcnow)
    decided_at: Mapped[Optional[datetime]] = C("DecidedAt", DateTime, nullable=True)


class UserAvatar(Base):
    """Private profile image stored separately so normal user queries stay small."""
    __tablename__ = "UserAvatars"
    user_id: Mapped[int] = C("UserId", ForeignKey("Users.UserId", ondelete="CASCADE"), primary_key=True)
    image_data: Mapped[bytes] = C("ImageData", LargeBinary)
    media_type: Mapped[str] = C("MediaType", Unicode(30))


class Role(Base):
    __tablename__ = "Roles"
    role_id: Mapped[int] = C("RoleId", Integer, primary_key=True)
    role_name: Mapped[str] = C("RoleName", Unicode(100), unique=True)


class Permission(Base):
    __tablename__ = "Permissions"
    __table_args__ = (UniqueConstraint("ScreenCode", "ActionCode", name="UQ_Permissions"),)
    permission_id: Mapped[int] = C("PermissionId", Integer, primary_key=True)
    screen_code: Mapped[str] = C("ScreenCode", Unicode(50))
    action_code: Mapped[str] = C("ActionCode", Unicode(30))  # View, Add, Edit, Delete, Post, Approve, Print


class RolePermission(Base):
    __tablename__ = "RolePermissions"
    role_id: Mapped[int] = C("RoleId", ForeignKey("Roles.RoleId"), primary_key=True)
    permission_id: Mapped[int] = C("PermissionId", ForeignKey("Permissions.PermissionId"), primary_key=True)


class UserRole(Base):
    __tablename__ = "UserRoles"
    user_id: Mapped[int] = C("UserId", ForeignKey("Users.UserId"), primary_key=True)
    role_id: Mapped[int] = C("RoleId", ForeignKey("Roles.RoleId"), primary_key=True)


class UserPermission(Base):
    __tablename__ = "UserPermissions"
    user_id: Mapped[int] = C("UserId", ForeignKey("Users.UserId"), primary_key=True)
    permission_id: Mapped[int] = C("PermissionId", ForeignKey("Permissions.PermissionId"), primary_key=True)
    is_allowed: Mapped[bool] = C("IsAllowed", Boolean)


class AuditLog(Base):
    __tablename__ = "AuditLog"
    audit_id: Mapped[int] = C("AuditId", BigPK, primary_key=True)
    user_id: Mapped[Optional[int]] = C("UserId", ForeignKey("Users.UserId"), nullable=True)
    action_type: Mapped[str] = C("ActionType", Unicode(30))
    entity_name: Mapped[str] = C("EntityName", Unicode(100))
    entity_id: Mapped[Optional[str]] = C("EntityId", Unicode(50), nullable=True)
    old_value: Mapped[Optional[str]] = C("OldValue", UnicodeText, nullable=True)
    new_value: Mapped[Optional[str]] = C("NewValue", UnicodeText, nullable=True)
    timestamp: Mapped[datetime] = C("Timestamp", DateTime, default=utcnow)
    ip_address: Mapped[Optional[str]] = C("IpAddress", Unicode(45), nullable=True)


# ----------------------------- 6) الأقسام والشاشات (جديد — 002_screens.sql) -----------------------------
class Section(Base):
    __tablename__ = "Sections"
    section_id: Mapped[int] = C("SectionId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(50), unique=True)
    name_en: Mapped[str] = C("NameEn", Unicode(150))
    name_ar: Mapped[Optional[str]] = C("NameAr", Unicode(150), nullable=True)
    sort_order: Mapped[int] = C("SortOrder", Integer, default=0)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)


class Screen(Base):
    __tablename__ = "Screens"
    screen_id: Mapped[int] = C("ScreenId", Integer, primary_key=True)
    section_id: Mapped[int] = C("SectionId", ForeignKey("Sections.SectionId"))
    screen_code: Mapped[str] = C("ScreenCode", Unicode(50), unique=True)  # = Permissions.ScreenCode
    title_en: Mapped[str] = C("TitleEn", Unicode(150))
    title_ar: Mapped[Optional[str]] = C("TitleAr", Unicode(150), nullable=True)
    route: Mapped[str] = C("Route", Unicode(200))
    sort_order: Mapped[int] = C("SortOrder", Integer, default=0)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)


# ----------------------------- View: vw_EffectivePermissions (للقراءة فقط) -----------------------------
# metadata منفصلة عشان create_all ما يحاولش يعمله كـ Table.
_view_meta = MetaData()
effective_permissions = Table(
    "vw_EffectivePermissions", _view_meta,
    Column("UserId", Integer), Column("PermissionId", Integer),
    Column("ScreenCode", Unicode(50)), Column("ActionCode", Unicode(30)),
    Column("IsAllowed", Integer),
)


# ----------------------------- طلبات التعاقد -----------------------------
class ContractRequest(Base):
    __tablename__ = "ContractRequests"
    request_id: Mapped[int] = C("RequestId", Integer, primary_key=True)
    request_no: Mapped[str] = C("RequestNo", Unicode(50), unique=True, index=True)
    request_type: Mapped[str] = C("RequestType", Unicode(30), default="Customer")
    title: Mapped[str] = C("Title", Unicode(250))
    title_en: Mapped[Optional[str]] = C("TitleEn", Unicode(250), nullable=True)
    counterparty_name: Mapped[str] = C("CounterpartyName", Unicode(200))
    counterparty_name_en: Mapped[Optional[str]] = C("CounterpartyNameEn", Unicode(200), nullable=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    estimated_value: Mapped[Decimal] = C("EstimatedValue", Numeric(18, 2), default=Decimal("0"))
    description: Mapped[Optional[str]] = C("Description", UnicodeText, nullable=True)
    status: Mapped[str] = C("Status", Unicode(30), default="Draft")
    review_notes: Mapped[Optional[str]] = C("ReviewNotes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)
    reviewed_by: Mapped[Optional[int]] = C("ReviewedBy", ForeignKey("Users.UserId"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = C("ReviewedAt", DateTime, nullable=True)

# ----------------------------- العقود والمكتب الفني -----------------------------
class Contract(Base):
    __tablename__ = "Contracts"
    contract_id: Mapped[int] = C("ContractId", Integer, primary_key=True)
    request_id: Mapped[Optional[int]] = C("RequestId", ForeignKey("ContractRequests.RequestId"), nullable=True, unique=True)
    contract_no: Mapped[str] = C("ContractNo", Unicode(50), unique=True, index=True)
    title: Mapped[str] = C("Title", Unicode(250))
    title_en: Mapped[Optional[str]] = C("TitleEn", Unicode(250), nullable=True)
    client_name: Mapped[str] = C("ClientName", Unicode(200))
    client_name_en: Mapped[Optional[str]] = C("ClientNameEn", Unicode(200), nullable=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    start_date: Mapped[Optional[date]] = C("StartDate", Date, nullable=True)
    end_date: Mapped[Optional[date]] = C("EndDate", Date, nullable=True)
    original_value: Mapped[Decimal] = C("OriginalValue", Numeric(18, 2), default=Decimal("0"))
    agreed_statement_count: Mapped[Optional[int]] = C("AgreedStatementCount", Integer, nullable=True)
    statement_distribution_method: Mapped[str] = C("StatementDistributionMethod", Unicode(20), default="Manual")
    status: Mapped[str] = C("Status", Unicode(30), default="Active")
    closed_at: Mapped[Optional[datetime]] = C("ClosedAt", DateTime, nullable=True)
    closed_by: Mapped[Optional[int]] = C("ClosedBy", ForeignKey("Users.UserId"), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class ContractSettlementSchedule(Base):
    __tablename__ = "ContractSettlementSchedules"
    __table_args__ = (UniqueConstraint("ContractId", "SequenceNo", name="UQ_ContractSettlementSchedules_Sequence"),
                      UniqueConstraint("TechnicalEstimateId", name="UQ_ContractSettlementSchedules_TechnicalEstimate"))
    schedule_id: Mapped[int] = C("ScheduleId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    sequence_no: Mapped[int] = C("SequenceNo", Integer)
    label: Mapped[Optional[str]] = C("Label", Unicode(200), nullable=True)
    period_start: Mapped[date] = C("PeriodStart", Date)
    period_end: Mapped[date] = C("PeriodEnd", Date)
    planned_submission_date: Mapped[date] = C("PlannedSubmissionDate", Date)
    due_date: Mapped[date] = C("DueDate", Date)
    expected_amount: Mapped[Optional[Decimal]] = C("ExpectedAmount", Numeric(18, 2), nullable=True)
    status: Mapped[str] = C("Status", Unicode(20), default="Planned")
    technical_estimate_id: Mapped[Optional[int]] = C("TechnicalEstimateId", ForeignKey("TechnicalSettlementEstimates.EstimateId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class ContractAddendum(Base):
    __tablename__ = "ContractAddendums"
    addendum_id: Mapped[int] = C("AddendumId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    addendum_no: Mapped[str] = C("AddendumNo", Unicode(50))
    addendum_date: Mapped[date] = C("AddendumDate", Date)
    description: Mapped[str] = C("Description", Unicode(500))
    value_change: Mapped[Decimal] = C("ValueChange", Numeric(18, 2), default=Decimal("0"))
    status: Mapped[str] = C("Status", Unicode(20), default="Approved")
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = C("ApprovedAt", DateTime, nullable=True)
    technical_reviewed_by: Mapped[Optional[int]] = C("TechnicalReviewedBy", ForeignKey("Users.UserId"), nullable=True)
    technical_reviewed_at: Mapped[Optional[datetime]] = C("TechnicalReviewedAt", DateTime, nullable=True)
    technical_review_notes: Mapped[Optional[str]] = C("TechnicalReviewNotes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class ContractAddendumLine(Base):
    __tablename__ = "ContractAddendumLines"
    __table_args__ = (
        CheckConstraint('"QuantityDelta" <> 0', name="CK_ContractAddendumLines_NonZeroDelta"),
        CheckConstraint('"UnitPrice" >= 0', name="CK_ContractAddendumLines_NonNegativePrice"),
    )
    addendum_line_id: Mapped[int] = C("AddendumLineId", Integer, primary_key=True)
    addendum_id: Mapped[int] = C("AddendumId", ForeignKey("ContractAddendums.AddendumId", ondelete="CASCADE"), index=True)
    target_item_id: Mapped[Optional[int]] = C("TargetItemId", ForeignKey("ContractItems.ItemId"), nullable=True, index=True)
    effective_item_id: Mapped[Optional[int]] = C("EffectiveItemId", ForeignKey("ContractItems.ItemId"), nullable=True, index=True)
    catalog_item_id: Mapped[Optional[int]] = C("CatalogItemId", ForeignKey("ItemCatalog.CatalogItemId"), nullable=True)
    account_id: Mapped[Optional[int]] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    item_no: Mapped[str] = C("ItemNo", Unicode(50))
    description: Mapped[str] = C("Description", Unicode(500))
    unit: Mapped[str] = C("Unit", Unicode(30), default="وحدة")
    quantity_delta: Mapped[Decimal] = C("QuantityDelta", Numeric(18, 4))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))
    amount_change: Mapped[Decimal] = C("AmountChange", Numeric(18, 2), default=Decimal("0"))
    baseline_quantity: Mapped[Optional[Decimal]] = C("BaselineQuantity", Numeric(18, 4), nullable=True)
    baseline_unit_price: Mapped[Optional[Decimal]] = C("BaselineUnitPrice", Numeric(18, 4), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class ProgressBilling(Base):
    __tablename__ = "ProgressBillings"
    billing_id: Mapped[int] = C("BillingId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    billing_no: Mapped[str] = C("BillingNo", Unicode(50))
    billing_date: Mapped[date] = C("BillingDate", Date)
    work_value: Mapped[Decimal] = C("WorkValue", Numeric(18, 2), default=Decimal("0"))
    retention_amount: Mapped[Decimal] = C("RetentionAmount", Numeric(18, 2), default=Decimal("0"))
    advance_deduction: Mapped[Decimal] = C("AdvanceDeduction", Numeric(18, 2), default=Decimal("0"))
    other_deductions: Mapped[Decimal] = C("OtherDeductions", Numeric(18, 2), default=Decimal("0"))
    net_amount: Mapped[Decimal] = C("NetAmount", Numeric(18, 2), default=Decimal("0"))
    status: Mapped[str] = C("Status", Unicode(30), default="Draft")
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


# ----------------------------- ERP: Technical Office & Contract Settlements -----------------------------
class ItemCatalog(Base):
    """Central catalogue of contract/store items mapped to a posting account."""
    __tablename__ = "ItemCatalog"
    catalog_item_id: Mapped[int] = C("CatalogItemId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(50), unique=True, index=True)
    name: Mapped[str] = C("Name", Unicode(250))
    unit: Mapped[str] = C("Unit", Unicode(30), default="وحدة")
    account_id: Mapped[int] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"), index=True)
    inventory_item_id: Mapped[Optional[int]] = C("InventoryItemId", ForeignKey("InventoryItems.ItemId"), nullable=True, unique=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class ContractItem(Base):
    __tablename__ = "ContractItems"
    __table_args__ = (UniqueConstraint("ContractId", "ItemNo", name="UQ_ContractItems_Contract_ItemNo"), CheckConstraint('"Quantity" >= 0 AND "UnitPrice" >= 0', name="CK_ContractItems_NonNegative"))
    item_id: Mapped[int] = C("ItemId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    catalog_item_id: Mapped[Optional[int]] = C("CatalogItemId", ForeignKey("ItemCatalog.CatalogItemId"), nullable=True, index=True)
    account_id: Mapped[Optional[int]] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True, index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True)
    item_no: Mapped[str] = C("ItemNo", Unicode(50))
    description: Mapped[str] = C("Description", Unicode(500))
    unit: Mapped[str] = C("Unit", Unicode(30), default="وحدة")
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 4), default=Decimal("0"))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4), default=Decimal("0"))
    original_quantity: Mapped[Optional[Decimal]] = C("OriginalQuantity", Numeric(18, 4), nullable=True)
    original_unit_price: Mapped[Optional[Decimal]] = C("OriginalUnitPrice", Numeric(18, 4), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class ContractDeductionRule(Base):
    __tablename__ = "ContractDeductionRules"
    __table_args__ = (UniqueConstraint("ContractId", "SettlementSide", "Code", name="UQ_ContractDeductionRules_Code"), CheckConstraint('"Rate" >= 0 AND ("CapAmount" IS NULL OR "CapAmount" >= 0)', name="CK_ContractDeductionRules_Rate"))
    rule_id: Mapped[int] = C("RuleId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    settlement_side: Mapped[str] = C("SettlementSide", Unicode(20))
    code: Mapped[str] = C("Code", Unicode(50))
    name_ar: Mapped[str] = C("NameAr", Unicode(150))
    calculation_type: Mapped[str] = C("CalculationType", Unicode(20), default="Percent")
    rate: Mapped[Decimal] = C("Rate", Numeric(9, 4), default=Decimal("0"))
    base_type: Mapped[str] = C("BaseType", Unicode(30), default="CurrentWork")
    posting_side: Mapped[str] = C("PostingSide", Unicode(10), default="Credit") # Debit | Credit
    cap_amount: Mapped[Optional[Decimal]] = C("CapAmount", Numeric(18, 2), nullable=True)
    gl_account_id: Mapped[Optional[int]] = C("GLAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    sort_order: Mapped[int] = C("SortOrder", Integer, default=0)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class ContractAccountingConfig(Base):
    __tablename__ = "ContractAccountingConfig"
    __table_args__ = (UniqueConstraint("ContractId", "SettlementSide", name="UQ_ContractAccountingConfig_Contract_Side"),)
    config_id: Mapped[int] = C("ConfigId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    settlement_side: Mapped[str] = C("SettlementSide", Unicode(20))
    company_id: Mapped[int] = C("CompanyId", ForeignKey("Companies.CompanyId"))
    fiscal_year_id: Mapped[int] = C("FiscalYearId", ForeignKey("FiscalYears.FiscalYearId"))
    control_account_id: Mapped[int] = C("ControlAccountId", ForeignKey("ChartOfAccounts.AccountId"))
    work_account_id: Mapped[int] = C("WorkAccountId", ForeignKey("ChartOfAccounts.AccountId"))
    retention_account_id: Mapped[Optional[int]] = C("RetentionAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    advance_account_id: Mapped[Optional[int]] = C("AdvanceAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    tax_account_id: Mapped[Optional[int]] = C("TaxAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    vat_account_id: Mapped[Optional[int]] = C("VatAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    default_vat_rate: Mapped[Decimal] = C("DefaultVatRate", Numeric(9, 4), default=Decimal("0"))
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class ContractSettlement(Base):
    __tablename__ = "ContractSettlements"
    __table_args__ = (UniqueConstraint("ContractId", "SettlementSide", "SequenceNo", name="UQ_ContractSettlements_Sequence"), UniqueConstraint("ContractId", "SettlementSide", "SettlementNo", name="UQ_ContractSettlements_Number"), CheckConstraint('"WorkValue" >= 0 AND "NetAmount" >= 0', name="CK_ContractSettlements_NonNegative"))
    settlement_id: Mapped[int] = C("SettlementId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    settlement_side: Mapped[str] = C("SettlementSide", Unicode(20))
    sequence_no: Mapped[int] = C("SequenceNo", Integer)
    settlement_no: Mapped[str] = C("SettlementNo", Unicode(50))
    is_final: Mapped[bool] = C("IsFinal", Boolean, default=False, nullable=False)
    settlement_date: Mapped[date] = C("SettlementDate", Date)
    counterparty_name: Mapped[str] = C("CounterpartyName", Unicode(200))
    counterparty_name_en: Mapped[Optional[str]] = C("CounterpartyNameEn", Unicode(200), nullable=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    work_value: Mapped[Decimal] = C("WorkValue", Numeric(18, 2), default=Decimal("0"))
    cumulative_work_value: Mapped[Decimal] = C("CumulativeWorkValue", Numeric(18, 2), default=Decimal("0"))
    deductions_json: Mapped[dict] = C("DeductionsJson", JSON, default=dict)
    vat_amount: Mapped[Decimal] = C("VatAmount", Numeric(18, 2), default=Decimal("0"))
    net_amount: Mapped[Decimal] = C("NetAmount", Numeric(18, 2), default=Decimal("0"))
    status: Mapped[str] = C("Status", Unicode(20), default="Draft")
    financial_approved_by: Mapped[Optional[int]] = C("FinancialApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    financial_approved_at: Mapped[Optional[datetime]] = C("FinancialApprovedAt", DateTime, nullable=True)
    manager_approved_by: Mapped[Optional[int]] = C("ManagerApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    manager_approved_at: Mapped[Optional[datetime]] = C("ManagerApprovedAt", DateTime, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = C("JournalEntryId", ForeignKey("JournalEntries.JournalEntryId"), nullable=True, unique=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class ContractSettlementItem(Base):
    __tablename__ = "ContractSettlementItems"
    __table_args__ = (
        UniqueConstraint("SettlementId", "ContractItemId", name="UQ_ContractSettlementItems_Line"),
        CheckConstraint('"Quantity" > 0 AND "UnitPrice" >= 0', name="CK_ContractSettlementItems_Quantity"),
    )
    settlement_item_id: Mapped[int] = C("SettlementItemId", Integer, primary_key=True)
    settlement_id: Mapped[int] = C("SettlementId", ForeignKey("ContractSettlements.SettlementId", ondelete="CASCADE"), index=True)
    contract_item_id: Mapped[int] = C("ContractItemId", ForeignKey("ContractItems.ItemId"), index=True)
    account_id: Mapped[Optional[int]] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True, index=True)
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 4))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))
    amount: Mapped[Decimal] = C("Amount", Numeric(18, 2))
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class ContractChangeOrder(Base):
    __tablename__ = "ContractChangeOrders"
    __table_args__ = (UniqueConstraint("ContractId", "ChangeOrderNo", name="UQ_ContractChangeOrders_Number"),)
    change_order_id: Mapped[int] = C("ChangeOrderId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    change_order_no: Mapped[str] = C("ChangeOrderNo", Unicode(50))
    change_order_date: Mapped[date] = C("ChangeOrderDate", Date)
    description: Mapped[str] = C("Description", Unicode(500))
    value_change: Mapped[Decimal] = C("ValueChange", Numeric(18, 2), default=Decimal("0"))
    status: Mapped[str] = C("Status", Unicode(20), default="Pending")
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = C("ApprovedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

# ----------------------------- إدارة المخزون ودورة المشتريات (إضافة آمنة) -----------------------------
class InventoryWarehouse(Base):
    __tablename__ = "InventoryWarehouses"
    warehouse_id: Mapped[int] = C("WarehouseId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(40), unique=True, index=True)
    name: Mapped[str] = C("Name", Unicode(200))
    location: Mapped[Optional[str]] = C("Location", Unicode(250), nullable=True)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class InventoryItem(Base):
    __tablename__ = "InventoryItems"
    item_id: Mapped[int] = C("ItemId", Integer, primary_key=True)
    code: Mapped[str] = C("Code", Unicode(50), unique=True, index=True)
    name: Mapped[str] = C("Name", Unicode(250))
    category: Mapped[Optional[str]] = C("Category", Unicode(100), nullable=True)
    unit: Mapped[str] = C("Unit", Unicode(30), default="قطعة")
    min_quantity: Mapped[Decimal] = C("MinQuantity", Numeric(18, 3), default=0)
    is_active: Mapped[bool] = C("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class InventoryMovement(Base):
    __tablename__ = "InventoryMovements"
    movement_id: Mapped[int] = C("MovementId", Integer, primary_key=True)
    movement_no: Mapped[str] = C("MovementNo", Unicode(60), unique=True, index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    movement_date: Mapped[date] = C("MovementDate", Date, default=date.today)
    movement_type: Mapped[str] = C("MovementType", Unicode(20)) # IN / OUT / ADJUST
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_cost: Mapped[Decimal] = C("UnitCost", Numeric(18, 4), default=0)
    reference: Mapped[Optional[str]] = C("Reference", Unicode(100), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class SiteIssueRequest(Base):
    __tablename__ = "SiteIssueRequests"
    request_id: Mapped[int] = C("RequestId", Integer, primary_key=True)
    request_no: Mapped[str] = C("RequestNo", Unicode(60), unique=True, index=True)
    request_date: Mapped[date] = C("RequestDate", Date, default=date.today)
    needed_by: Mapped[Optional[date]] = C("NeededBy", Date, nullable=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    site_name: Mapped[Optional[str]] = C("SiteName", Unicode(200), nullable=True)
    requested_by: Mapped[int] = C("RequestedBy", ForeignKey("Users.UserId"))
    status: Mapped[str] = C("Status", Unicode(30), default="PendingApproval", index=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = C("ApprovedAt", DateTime, nullable=True)
    issued_by: Mapped[Optional[int]] = C("IssuedBy", ForeignKey("Users.UserId"), nullable=True)
    issued_at: Mapped[Optional[datetime]] = C("IssuedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class SiteIssueRequestLine(Base):
    __tablename__ = "SiteIssueRequestLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    request_id: Mapped[int] = C("RequestId", ForeignKey("SiteIssueRequests.RequestId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    requested_quantity: Mapped[Decimal] = C("RequestedQuantity", Numeric(18, 3))
    approved_quantity: Mapped[Decimal] = C("ApprovedQuantity", Numeric(18, 3), default=0)
    issued_quantity: Mapped[Decimal] = C("IssuedQuantity", Numeric(18, 3), default=0)

class InventoryStocktake(Base):
    __tablename__ = "InventoryStocktakes"
    stocktake_id: Mapped[int] = C("StocktakeId", Integer, primary_key=True)
    stocktake_no: Mapped[str] = C("StocktakeNo", Unicode(60), unique=True, index=True)
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    stocktake_date: Mapped[date] = C("StocktakeDate", Date, default=date.today)
    status: Mapped[str] = C("Status", Unicode(30), default="PendingApproval", index=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_by: Mapped[int] = C("CreatedBy", ForeignKey("Users.UserId"))
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = C("ApprovedAt", DateTime, nullable=True)
    posted_by: Mapped[Optional[int]] = C("PostedBy", ForeignKey("Users.UserId"), nullable=True)
    posted_at: Mapped[Optional[datetime]] = C("PostedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class InventoryStocktakeLine(Base):
    __tablename__ = "InventoryStocktakeLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    stocktake_id: Mapped[int] = C("StocktakeId", ForeignKey("InventoryStocktakes.StocktakeId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    system_quantity: Mapped[Decimal] = C("SystemQuantity", Numeric(18, 3))
    counted_quantity: Mapped[Decimal] = C("CountedQuantity", Numeric(18, 3))
    variance_quantity: Mapped[Decimal] = C("VarianceQuantity", Numeric(18, 3))

class InventoryReturn(Base):
    __tablename__ = "InventoryReturns"
    return_id: Mapped[int] = C("ReturnId", Integer, primary_key=True)
    return_no: Mapped[str] = C("ReturnNo", Unicode(60), unique=True, index=True)
    return_type: Mapped[str] = C("ReturnType", Unicode(20))  # Supplier / Site
    return_date: Mapped[date] = C("ReturnDate", Date, default=date.today)
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    counterparty_name: Mapped[Optional[str]] = C("CounterpartyName", Unicode(250), nullable=True)
    source_document: Mapped[Optional[str]] = C("SourceDocument", Unicode(100), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    status: Mapped[str] = C("Status", Unicode(30), default="PendingApproval", index=True)
    created_by: Mapped[int] = C("CreatedBy", ForeignKey("Users.UserId"))
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = C("ApprovedAt", DateTime, nullable=True)
    posted_by: Mapped[Optional[int]] = C("PostedBy", ForeignKey("Users.UserId"), nullable=True)
    posted_at: Mapped[Optional[datetime]] = C("PostedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class InventoryReturnLine(Base):
    __tablename__ = "InventoryReturnLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    return_id: Mapped[int] = C("ReturnId", ForeignKey("InventoryReturns.ReturnId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_cost: Mapped[Decimal] = C("UnitCost", Numeric(18, 4), default=0)
    purchase_order_line_id: Mapped[Optional[int]] = C("PurchaseOrderLineId", ForeignKey("PurchaseOrderLines.LineId"), nullable=True)
    site_issue_line_id: Mapped[Optional[int]] = C("SiteIssueLineId", ForeignKey("SiteIssueRequestLines.LineId"), nullable=True)

class PurchaseRequisition(Base):
    __tablename__ = "PurchaseRequisitions"
    requisition_id: Mapped[int] = C("RequisitionId", Integer, primary_key=True)
    requisition_no: Mapped[str] = C("RequisitionNo", Unicode(60), unique=True, index=True)
    request_date: Mapped[date] = C("RequestDate", Date, default=date.today)
    required_date: Mapped[Optional[date]] = C("RequiredDate", Date, nullable=True)
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    requested_by: Mapped[Optional[int]] = C("RequestedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    status: Mapped[str] = C("Status", Unicode(24), default="Draft")
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class PurchaseRequisitionLine(Base):
    __tablename__ = "PurchaseRequisitionLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    requisition_id: Mapped[int] = C("RequisitionId", ForeignKey("PurchaseRequisitions.RequisitionId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    notes: Mapped[Optional[str]] = C("Notes", Unicode(500), nullable=True)

class SupplierQuotation(Base):
    __tablename__ = "SupplierQuotations"
    quotation_id: Mapped[int] = C("QuotationId", Integer, primary_key=True)
    quotation_no: Mapped[str] = C("QuotationNo", Unicode(60), unique=True, index=True)
    requisition_id: Mapped[int] = C("RequisitionId", ForeignKey("PurchaseRequisitions.RequisitionId"), index=True)
    supplier_name: Mapped[str] = C("SupplierName", Unicode(250))
    quotation_date: Mapped[date] = C("QuotationDate", Date, default=date.today)
    valid_until: Mapped[Optional[date]] = C("ValidUntil", Date, nullable=True)
    delivery_days: Mapped[Optional[int]] = C("DeliveryDays", Integer, nullable=True)
    payment_terms: Mapped[Optional[str]] = C("PaymentTerms", Unicode(500), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    status: Mapped[str] = C("Status", Unicode(24), default="Submitted")
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    converted_purchase_order_id: Mapped[Optional[int]] = C("ConvertedPurchaseOrderId", ForeignKey("PurchaseOrders.PurchaseOrderId"), nullable=True, unique=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class SupplierQuotationLine(Base):
    __tablename__ = "SupplierQuotationLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    quotation_id: Mapped[int] = C("QuotationId", ForeignKey("SupplierQuotations.QuotationId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))

class PurchaseOrder(Base):
    __tablename__ = "PurchaseOrders"
    purchase_order_id: Mapped[int] = C("PurchaseOrderId", Integer, primary_key=True)
    order_no: Mapped[str] = C("OrderNo", Unicode(60), unique=True, index=True)
    order_date: Mapped[date] = C("OrderDate", Date, default=date.today)
    supplier_name: Mapped[str] = C("SupplierName", Unicode(250))
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    status: Mapped[str] = C("Status", Unicode(20), default="Draft") # Draft/Approved/Received/Cancelled
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    total_amount: Mapped[Decimal] = C("TotalAmount", Numeric(18, 2), default=0)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class PurchaseOrderLine(Base):
    __tablename__ = "PurchaseOrderLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    purchase_order_id: Mapped[int] = C("PurchaseOrderId", ForeignKey("PurchaseOrders.PurchaseOrderId", ondelete="CASCADE"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))
    received_quantity: Mapped[Decimal] = C("ReceivedQuantity", Numeric(18, 3), default=0)


class PurchaseGoodsReceipt(Base):
    __tablename__ = "PurchaseGoodsReceipts"
    __table_args__ = (UniqueConstraint("ReceiptNo", name="UQ_PurchaseGoodsReceipts_ReceiptNo"),)
    receipt_id: Mapped[int] = C("ReceiptId", Integer, primary_key=True)
    receipt_no: Mapped[str] = C("ReceiptNo", Unicode(60), unique=True, index=True)
    purchase_order_id: Mapped[int] = C("PurchaseOrderId", ForeignKey("PurchaseOrders.PurchaseOrderId"), index=True)
    receipt_date: Mapped[date] = C("ReceiptDate", Date, default=date.today)
    warehouse_id: Mapped[int] = C("WarehouseId", ForeignKey("InventoryWarehouses.WarehouseId"))
    delivery_note_no: Mapped[Optional[str]] = C("DeliveryNoteNo", Unicode(100), nullable=True)
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    received_by: Mapped[Optional[int]] = C("ReceivedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class PurchaseGoodsReceiptLine(Base):
    __tablename__ = "PurchaseGoodsReceiptLines"
    receipt_line_id: Mapped[int] = C("ReceiptLineId", Integer, primary_key=True)
    receipt_id: Mapped[int] = C("ReceiptId", ForeignKey("PurchaseGoodsReceipts.ReceiptId", ondelete="CASCADE"), index=True)
    purchase_order_line_id: Mapped[int] = C("PurchaseOrderLineId", ForeignKey("PurchaseOrderLines.LineId"), index=True)
    item_id: Mapped[int] = C("ItemId", ForeignKey("InventoryItems.ItemId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_cost: Mapped[Decimal] = C("UnitCost", Numeric(18, 4), default=0)


class SupplierInvoice(Base):
    """Supplier bills are the accounting source; purchase orders/receipts alone do not post journals."""
    __tablename__ = "SupplierInvoices"
    __table_args__ = (UniqueConstraint("SupplierId", "InvoiceNo", name="UQ_SupplierInvoices_Supplier_InvoiceNo"),)
    invoice_id: Mapped[int] = C("InvoiceId", Integer, primary_key=True)
    supplier_id: Mapped[int] = C("SupplierId", ForeignKey("Counterparties.CounterpartyId"), index=True)
    purchase_order_id: Mapped[int] = C("PurchaseOrderId", ForeignKey("PurchaseOrders.PurchaseOrderId"), index=True)
    project_id: Mapped[Optional[int]] = C("ProjectId", ForeignKey("Projects.ProjectId"), nullable=True, index=True)
    invoice_no: Mapped[str] = C("InvoiceNo", Unicode(60))
    invoice_date: Mapped[date] = C("InvoiceDate", Date)
    tax_account_id: Mapped[Optional[int]] = C("TaxAccountId", ForeignKey("ChartOfAccounts.AccountId"), nullable=True)
    net_amount: Mapped[Decimal] = C("NetAmount", Numeric(18, 2), default=0)
    tax_amount: Mapped[Decimal] = C("TaxAmount", Numeric(18, 2), default=0)
    total_amount: Mapped[Decimal] = C("TotalAmount", Numeric(18, 2), default=0)
    status: Mapped[str] = C("Status", Unicode(20), default="Draft")
    journal_entry_id: Mapped[Optional[int]] = C("JournalEntryId", ForeignKey("JournalEntries.JournalEntryId"), nullable=True, unique=True)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    approved_by: Mapped[Optional[int]] = C("ApprovedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class SupplierInvoiceLine(Base):
    __tablename__ = "SupplierInvoiceLines"
    line_id: Mapped[int] = C("LineId", Integer, primary_key=True)
    invoice_id: Mapped[int] = C("InvoiceId", ForeignKey("SupplierInvoices.InvoiceId", ondelete="CASCADE"), index=True)
    purchase_order_line_id: Mapped[int] = C("PurchaseOrderLineId", ForeignKey("PurchaseOrderLines.LineId"), index=True)
    account_id: Mapped[int] = C("AccountId", ForeignKey("ChartOfAccounts.AccountId"))
    quantity: Mapped[Decimal] = C("Quantity", Numeric(18, 3))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))
    net_amount: Mapped[Decimal] = C("NetAmount", Numeric(18, 2))


class ContractAttachment(Base):
    """مرفقات العقود والمستخلصات محفوظة داخل قاعدة البيانات لتدخل ضمن النسخ الاحتياطية."""
    __tablename__ = "ContractAttachments"
    __table_args__ = (
        CheckConstraint('("ContractId" IS NOT NULL AND "SettlementId" IS NULL) OR ("ContractId" IS NULL AND "SettlementId" IS NOT NULL)', name="CK_ContractAttachments_OneParent"),
    )
    attachment_id: Mapped[int] = C("AttachmentId", Integer, primary_key=True)
    contract_id: Mapped[Optional[int]] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), nullable=True, index=True)
    settlement_id: Mapped[Optional[int]] = C("SettlementId", ForeignKey("ContractSettlements.SettlementId", ondelete="CASCADE"), nullable=True, index=True)
    category: Mapped[str] = C("Category", Unicode(80), default="Other")
    original_filename: Mapped[str] = C("OriginalFilename", Unicode(255))
    content_type: Mapped[str] = C("ContentType", Unicode(120), default="application/octet-stream")
    size_bytes: Mapped[int] = C("SizeBytes", Integer)
    file_content: Mapped[bytes] = C("FileContent", LargeBinary)
    notes: Mapped[Optional[str]] = C("Notes", Unicode(500), nullable=True)
    uploaded_by: Mapped[Optional[int]] = C("UploadedBy", ForeignKey("Users.UserId"), nullable=True)
    uploaded_at: Mapped[datetime] = C("UploadedAt", DateTime, default=utcnow)

# ----------------------------- Technical-office estimate workflow (additive) -----------------------------
class TechnicalSettlementEstimate(Base):
    __tablename__ = "TechnicalSettlementEstimates"
    __table_args__ = (UniqueConstraint("ContractId", "SettlementSide", "EstimateNo", name="UQ_TechnicalSettlementEstimates_Number"),)
    estimate_id: Mapped[int] = C("EstimateId", Integer, primary_key=True)
    contract_id: Mapped[int] = C("ContractId", ForeignKey("Contracts.ContractId", ondelete="CASCADE"), index=True)
    settlement_side: Mapped[str] = C("SettlementSide", Unicode(20))
    estimate_no: Mapped[str] = C("EstimateNo", Unicode(50))
    estimate_date: Mapped[date] = C("EstimateDate", Date)
    counterparty_name: Mapped[str] = C("CounterpartyName", Unicode(200))
    counterparty_name_en: Mapped[Optional[str]] = C("CounterpartyNameEn", Unicode(200), nullable=True)
    counterparty_id: Mapped[Optional[int]] = C("CounterpartyId", ForeignKey("Counterparties.CounterpartyId"), nullable=True, index=True)
    work_value: Mapped[Decimal] = C("WorkValue", Numeric(18, 2), default=Decimal("0"))
    status: Mapped[str] = C("Status", Unicode(30), default="Draft")
    notes: Mapped[Optional[str]] = C("Notes", UnicodeText, nullable=True)
    financial_settlement_id: Mapped[Optional[int]] = C("FinancialSettlementId", ForeignKey("ContractSettlements.SettlementId"), nullable=True, unique=True)
    is_final: Mapped[bool] = C("IsFinal", Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    reviewed_by: Mapped[Optional[int]] = C("ReviewedBy", ForeignKey("Users.UserId"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = C("ReviewedAt", DateTime, nullable=True)
    technical_reviewed_by: Mapped[Optional[int]] = C("TechnicalReviewedBy", ForeignKey("Users.UserId"), nullable=True)
    technical_reviewed_at: Mapped[Optional[datetime]] = C("TechnicalReviewedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)

class TechnicalSettlementEstimateItem(Base):
    __tablename__ = "TechnicalSettlementEstimateItems"
    __table_args__ = (UniqueConstraint("EstimateId", "ContractItemId", name="UQ_TechnicalSettlementEstimateItems_Line"),)
    estimate_item_id: Mapped[int] = C("EstimateItemId", Integer, primary_key=True)
    estimate_id: Mapped[int] = C("EstimateId", ForeignKey("TechnicalSettlementEstimates.EstimateId", ondelete="CASCADE"), index=True)
    contract_item_id: Mapped[int] = C("ContractItemId", ForeignKey("ContractItems.ItemId"), index=True)
    previous_quantity: Mapped[Decimal] = C("PreviousQuantity", Numeric(18, 4), default=Decimal("0"))
    current_quantity: Mapped[Decimal] = C("CurrentQuantity", Numeric(18, 4))
    unit_price: Mapped[Decimal] = C("UnitPrice", Numeric(18, 4))
    amount: Mapped[Decimal] = C("Amount", Numeric(18, 2))
    approved_quantity: Mapped[Optional[Decimal]] = C("ApprovedQuantity", Numeric(18, 4), nullable=True)
    review_note: Mapped[Optional[str]] = C("ReviewNote", UnicodeText, nullable=True)
    reviewed_by: Mapped[Optional[int]] = C("ReviewedBy", ForeignKey("Users.UserId"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = C("ReviewedAt", DateTime, nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class FinancialCheckSettlementAllocation(Base):
    """Many-to-many allocation between financial cheques and posted settlements."""
    __tablename__ = "FinancialCheckSettlementAllocations"
    __table_args__ = (
        UniqueConstraint("CheckId", "SettlementId", name="UQ_FinancialCheckSettlementAllocations"),
        CheckConstraint('"AllocatedAmount" > 0', name="CK_FinancialCheckSettlementAllocations_Positive"),
    )
    allocation_id: Mapped[int] = C("AllocationId", BigPK, primary_key=True)
    check_id: Mapped[int] = C("CheckId", ForeignKey("FinancialChecks.CheckId", ondelete="CASCADE"), index=True)
    settlement_id: Mapped[int] = C("SettlementId", ForeignKey("ContractSettlements.SettlementId"), index=True)
    allocated_amount: Mapped[Decimal] = C("AllocatedAmount", Numeric(18, 2))
    created_by: Mapped[Optional[int]] = C("CreatedBy", ForeignKey("Users.UserId"), nullable=True)
    created_at: Mapped[datetime] = C("CreatedAt", DateTime, default=utcnow)


class FinancialCheckStatusHistory(Base):
    """Immutable status audit trail for the unified financial cheque register."""
    __tablename__ = "FinancialCheckStatusHistory"
    history_id: Mapped[int] = C("HistoryId", BigPK, primary_key=True)
    check_id: Mapped[int] = C("CheckId", ForeignKey("FinancialChecks.CheckId", ondelete="CASCADE"), index=True)
    old_status: Mapped[Optional[str]] = C("OldStatus", Unicode(30), nullable=True)
    new_status: Mapped[str] = C("NewStatus", Unicode(30))
    changed_by: Mapped[Optional[int]] = C("ChangedBy", ForeignKey("Users.UserId"), nullable=True)
    note: Mapped[Optional[str]] = C("Note", Unicode(500), nullable=True)
    changed_at: Mapped[datetime] = C("ChangedAt", DateTime, default=utcnow)
