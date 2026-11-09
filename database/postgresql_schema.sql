-- PostgreSQL schema generated from app/models.py
-- Database: financial_system
-- Run against an EMPTY PostgreSQL database. Does not contain business data.

BEGIN;

CREATE TABLE "AccountClassifications" (
	"ClassificationId" SERIAL NOT NULL, 
	"NameAr" VARCHAR(200) NOT NULL, 
	"StatementType" VARCHAR(30) NOT NULL, 
	PRIMARY KEY ("ClassificationId"), 
	UNIQUE ("NameAr")
);

CREATE TABLE "Companies" (
	"CompanyId" SERIAL NOT NULL, 
	"NameAr" VARCHAR(200) NOT NULL, 
	"NameEn" VARCHAR(200), 
	"TaxNumber" VARCHAR(50), 
	"CommercialRegister" VARCHAR(50), 
	"AddressAr" VARCHAR(500), 
	"Phone" VARCHAR(50), 
	"Email" VARCHAR(200), 
	"Website" VARCHAR(200), 
	"LogoData" TEXT, 
	"IsActive" BOOLEAN NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("CompanyId")
);

CREATE TABLE "ExchangeRates" (
	"ExchangeRateId" SERIAL NOT NULL, 
	"CurrencyCode" VARCHAR(3) NOT NULL, 
	"RateDate" DATE NOT NULL, 
	"RateToEGP" NUMERIC(18, 6) NOT NULL, 
	PRIMARY KEY ("ExchangeRateId"), 
	CONSTRAINT "UQ_ExchangeRates" UNIQUE ("CurrencyCode", "RateDate")
);

CREATE TABLE "InventoryItems" (
	"ItemId" SERIAL NOT NULL, 
	"Code" VARCHAR(50) NOT NULL, 
	"Name" VARCHAR(250) NOT NULL, 
	"Category" VARCHAR(100), 
	"Unit" VARCHAR(30) NOT NULL, 
	"MinQuantity" NUMERIC(18, 3) NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ItemId")
);

CREATE TABLE "InventoryWarehouses" (
	"WarehouseId" SERIAL NOT NULL, 
	"Code" VARCHAR(40) NOT NULL, 
	"Name" VARCHAR(200) NOT NULL, 
	"Location" VARCHAR(250), 
	"IsActive" BOOLEAN NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("WarehouseId")
);

CREATE TABLE "Permissions" (
	"PermissionId" SERIAL NOT NULL, 
	"ScreenCode" VARCHAR(50) NOT NULL, 
	"ActionCode" VARCHAR(30) NOT NULL, 
	PRIMARY KEY ("PermissionId"), 
	CONSTRAINT "UQ_Permissions" UNIQUE ("ScreenCode", "ActionCode")
);

CREATE TABLE "Projects" (
	"ProjectId" SERIAL NOT NULL, 
	"NameAr" VARCHAR(200) NOT NULL, 
	"NameEn" VARCHAR(200), 
	"IsHeadOffice" BOOLEAN NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	PRIMARY KEY ("ProjectId"), 
	UNIQUE ("NameAr")
);

CREATE TABLE "Roles" (
	"RoleId" SERIAL NOT NULL, 
	"RoleName" VARCHAR(100) NOT NULL, 
	PRIMARY KEY ("RoleId"), 
	UNIQUE ("RoleName")
);

CREATE TABLE "Sections" (
	"SectionId" SERIAL NOT NULL, 
	"Code" VARCHAR(50) NOT NULL, 
	"NameEn" VARCHAR(150) NOT NULL, 
	"NameAr" VARCHAR(150), 
	"SortOrder" INTEGER NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	PRIMARY KEY ("SectionId"), 
	UNIQUE ("Code")
);

CREATE TABLE "Users" (
	"UserId" SERIAL NOT NULL, 
	"Username" VARCHAR(50) NOT NULL, 
	"PasswordHash" BYTEA NOT NULL, 
	"FullName" VARCHAR(150) NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	"LastLoginAt" TIMESTAMP WITHOUT TIME ZONE, 
	"FailedLoginCount" INTEGER NOT NULL, 
	"LockedUntil" TIMESTAMP WITHOUT TIME ZONE, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("UserId"), 
	UNIQUE ("Username")
);

CREATE TABLE "AuditLog" (
	"AuditId" BIGSERIAL NOT NULL, 
	"UserId" INTEGER, 
	"ActionType" VARCHAR(30) NOT NULL, 
	"EntityName" VARCHAR(100) NOT NULL, 
	"EntityId" VARCHAR(50), 
	"OldValue" TEXT, 
	"NewValue" TEXT, 
	"Timestamp" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	"IpAddress" VARCHAR(45), 
	PRIMARY KEY ("AuditId")
);

CREATE TABLE "ChartOfAccounts" (
	"AccountId" SERIAL NOT NULL, 
	"AccountCode" VARCHAR(30) NOT NULL, 
	"AccountNameAr" VARCHAR(300) NOT NULL, 
	"ParentAccountId" INTEGER, 
	"ClassificationId" INTEGER NOT NULL, 
	"NormalBalance" CHAR(2) NOT NULL, 
	"OpeningDebit" NUMERIC(18, 2) NOT NULL, 
	"OpeningCredit" NUMERIC(18, 2) NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("AccountId"), 
	UNIQUE ("AccountCode")
);

CREATE TABLE "ContractRequests" (
	"RequestId" SERIAL NOT NULL, 
	"RequestNo" VARCHAR(50) NOT NULL, 
	"RequestType" VARCHAR(30) NOT NULL, 
	"Title" VARCHAR(250) NOT NULL, 
	"CounterpartyName" VARCHAR(200) NOT NULL, 
	"ProjectId" INTEGER, 
	"EstimatedValue" NUMERIC(18, 2) NOT NULL, 
	"Description" TEXT, 
	"Status" VARCHAR(30) NOT NULL, 
	"ReviewNotes" TEXT, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	"ReviewedBy" INTEGER, 
	"ReviewedAt" TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY ("RequestId")
);

CREATE TABLE "FinancialStatementLines" (
	"LineId" SERIAL NOT NULL, 
	"StatementType" VARCHAR(30) NOT NULL, 
	"CaptionAr" VARCHAR(200) NOT NULL, 
	"SortOrder" INTEGER NOT NULL, 
	"ClassificationId" INTEGER, 
	"IsSubtotal" BOOLEAN NOT NULL, 
	PRIMARY KEY ("LineId")
);

CREATE TABLE "FiscalYears" (
	"FiscalYearId" SERIAL NOT NULL, 
	"CompanyId" INTEGER NOT NULL, 
	"StartDate" DATE NOT NULL, 
	"EndDate" DATE NOT NULL, 
	"IsClosed" BOOLEAN NOT NULL, 
	PRIMARY KEY ("FiscalYearId")
);

CREATE TABLE "InventoryMovements" (
	"MovementId" SERIAL NOT NULL, 
	"MovementNo" VARCHAR(60) NOT NULL, 
	"ItemId" INTEGER NOT NULL, 
	"WarehouseId" INTEGER NOT NULL, 
	"MovementDate" DATE NOT NULL, 
	"MovementType" VARCHAR(20) NOT NULL, 
	"Quantity" NUMERIC(18, 3) NOT NULL, 
	"UnitCost" NUMERIC(18, 4) NOT NULL, 
	"Reference" VARCHAR(100), 
	"Notes" TEXT, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("MovementId")
);

CREATE TABLE "PurchaseOrders" (
	"PurchaseOrderId" SERIAL NOT NULL, 
	"OrderNo" VARCHAR(60) NOT NULL, 
	"OrderDate" DATE NOT NULL, 
	"SupplierName" VARCHAR(250) NOT NULL, 
	"WarehouseId" INTEGER NOT NULL, 
	"Status" VARCHAR(20) NOT NULL, 
	"Notes" TEXT, 
	"TotalAmount" NUMERIC(18, 2) NOT NULL, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("PurchaseOrderId")
);

CREATE TABLE "RolePermissions" (
	"RoleId" INTEGER NOT NULL, 
	"PermissionId" INTEGER NOT NULL, 
	PRIMARY KEY ("RoleId", "PermissionId")
);

CREATE TABLE "Screens" (
	"ScreenId" SERIAL NOT NULL, 
	"SectionId" INTEGER NOT NULL, 
	"ScreenCode" VARCHAR(50) NOT NULL, 
	"TitleEn" VARCHAR(150) NOT NULL, 
	"TitleAr" VARCHAR(150), 
	"Route" VARCHAR(200) NOT NULL, 
	"SortOrder" INTEGER NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	PRIMARY KEY ("ScreenId"), 
	UNIQUE ("ScreenCode")
);

CREATE TABLE "UserPermissions" (
	"UserId" INTEGER NOT NULL, 
	"PermissionId" INTEGER NOT NULL, 
	"IsAllowed" BOOLEAN NOT NULL, 
	PRIMARY KEY ("UserId", "PermissionId")
);

CREATE TABLE "UserRoles" (
	"UserId" INTEGER NOT NULL, 
	"RoleId" INTEGER NOT NULL, 
	PRIMARY KEY ("UserId", "RoleId")
);

CREATE TABLE "Beneficiaries" (
	"BeneficiaryId" SERIAL NOT NULL, 
	"Code" VARCHAR(30) NOT NULL, 
	"NameAr" VARCHAR(200) NOT NULL, 
	"LinkedAccountId" INTEGER, 
	"DefaultProjectId" INTEGER, 
	"BankAccountNumber" VARCHAR(50), 
	"IsActive" BOOLEAN NOT NULL, 
	PRIMARY KEY ("BeneficiaryId"), 
	UNIQUE ("Code")
);

CREATE TABLE "Contracts" (
	"ContractId" SERIAL NOT NULL, 
	"RequestId" INTEGER, 
	"ContractNo" VARCHAR(50) NOT NULL, 
	"Title" VARCHAR(250) NOT NULL, 
	"ClientName" VARCHAR(200) NOT NULL, 
	"ProjectId" INTEGER, 
	"StartDate" DATE, 
	"EndDate" DATE, 
	"OriginalValue" NUMERIC(18, 2) NOT NULL, 
	"Status" VARCHAR(30) NOT NULL, 
	"Notes" TEXT, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ContractId"), 
	UNIQUE ("RequestId")
);

CREATE TABLE "JournalEntries" (
	"JournalEntryId" SERIAL NOT NULL, 
	"EntryNo" VARCHAR(30) NOT NULL, 
	"EntryDate" DATE NOT NULL, 
	"CompanyId" INTEGER NOT NULL, 
	"FiscalYearId" INTEGER NOT NULL, 
	"SourceSettlementId" INTEGER, 
	"Description" VARCHAR(500), 
	"Status" VARCHAR(20) NOT NULL, 
	"CreatedBy" INTEGER, 
	"PostedBy" INTEGER, 
	"PostedAt" TIMESTAMP WITHOUT TIME ZONE, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("JournalEntryId"), 
	UNIQUE ("EntryNo")
);
CREATE INDEX "IX_JournalEntries_SourceSettlementId" ON "JournalEntries" ("SourceSettlementId");

CREATE TABLE "PurchaseOrderLines" (
	"LineId" SERIAL NOT NULL, 
	"PurchaseOrderId" INTEGER NOT NULL, 
	"ItemId" INTEGER NOT NULL, 
	"Quantity" NUMERIC(18, 3) NOT NULL, 
	"UnitPrice" NUMERIC(18, 4) NOT NULL, 
	"ReceivedQuantity" NUMERIC(18, 3) NOT NULL, 
	PRIMARY KEY ("LineId")
);

CREATE TABLE "TreasuryAccounts" (
	"TreasuryAccountId" SERIAL NOT NULL, 
	"NameAr" VARCHAR(200) NOT NULL, 
	"AccountType" VARCHAR(10) NOT NULL, 
	"CurrencyCode" VARCHAR(3) NOT NULL, 
	"BankAccountNumber" VARCHAR(50), 
	"GLAccountId" INTEGER NOT NULL, 
	"IsActive" BOOLEAN NOT NULL, 
	"ScreenCode" VARCHAR(50), 
	"ChecksScreenCode" VARCHAR(50), 
	PRIMARY KEY ("TreasuryAccountId"), 
	UNIQUE ("ScreenCode"), 
	UNIQUE ("ChecksScreenCode")
);

CREATE TABLE "BankReconciliations" (
	"ReconciliationId" SERIAL NOT NULL, 
	"TreasuryAccountId" INTEGER NOT NULL, 
	"ReconciliationDate" DATE NOT NULL, 
	"BookBalance" NUMERIC(18, 2) NOT NULL, 
	"StatementBalance" NUMERIC(18, 2) NOT NULL, 
	"Difference" NUMERIC(18, 2) GENERATED ALWAYS AS ("StatementBalance" - "BookBalance") STORED NOT NULL, 
	"PreparedBy" INTEGER, 
	"Notes" VARCHAR(500), 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ReconciliationId")
);

CREATE TABLE "CheckPrintTemplates" (
	"TemplateId" SERIAL NOT NULL, 
	"TreasuryAccountId" INTEGER NOT NULL, 
	"FieldName" VARCHAR(50) NOT NULL, 
	"PosX" NUMERIC(10, 2) NOT NULL, 
	"PosY" NUMERIC(10, 2) NOT NULL, 
	"FontSize" NUMERIC(5, 2) NOT NULL, 
	"Alignment" VARCHAR(10) NOT NULL, 
	"SpellPiastres" BOOLEAN NOT NULL, 
	PRIMARY KEY ("TemplateId"), 
	CONSTRAINT "UQ_CheckPrintTemplates" UNIQUE ("TreasuryAccountId", "FieldName")
);

CREATE TABLE "Checks" (
	"CheckId" BIGSERIAL NOT NULL, 
	"TreasuryAccountId" INTEGER NOT NULL, 
	"CheckBookNo" VARCHAR(20) NOT NULL, 
	"SequenceNo" INTEGER NOT NULL, 
	"CheckNo" VARCHAR(30), 
	"CheckDate" DATE, 
	"BeneficiaryId" INTEGER NOT NULL, 
	"Amount" NUMERIC(18, 2), 
	"PurchaseOrderNo" VARCHAR(50), 
	"ProjectId" INTEGER, 
	"Description" VARCHAR(500), 
	"PrintDate" DATE, 
	"DeliveryDate" DATE, 
	"CashDate" DATE, 
	"Status" VARCHAR(20) NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("CheckId"), 
	CONSTRAINT "UQ_Checks_BankBook" UNIQUE ("TreasuryAccountId", "CheckBookNo", "SequenceNo")
);

CREATE TABLE "ContractAccountingConfig" (
	"ConfigId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"SettlementSide" VARCHAR(20) NOT NULL, 
	"CompanyId" INTEGER NOT NULL, 
	"FiscalYearId" INTEGER NOT NULL, 
	"ControlAccountId" INTEGER NOT NULL, 
	"WorkAccountId" INTEGER NOT NULL, 
	"RetentionAccountId" INTEGER, 
	"AdvanceAccountId" INTEGER, 
	"TaxAccountId" INTEGER, 
	"VatAccountId" INTEGER, 
	"DefaultVatRate" NUMERIC(9, 4) NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ConfigId"), 
	CONSTRAINT "UQ_ContractAccountingConfig_Contract_Side" UNIQUE ("ContractId", "SettlementSide")
);

CREATE TABLE "ContractAddendums" (
	"AddendumId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"AddendumNo" VARCHAR(50) NOT NULL, 
	"AddendumDate" DATE NOT NULL, 
	"Description" VARCHAR(500) NOT NULL, 
	"ValueChange" NUMERIC(18, 2) NOT NULL, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("AddendumId")
);

CREATE TABLE "ContractChangeOrders" (
	"ChangeOrderId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"ChangeOrderNo" VARCHAR(50) NOT NULL, 
	"ChangeOrderDate" DATE NOT NULL, 
	"Description" VARCHAR(500) NOT NULL, 
	"ValueChange" NUMERIC(18, 2) NOT NULL, 
	"Status" VARCHAR(20) NOT NULL, 
	"CreatedBy" INTEGER, 
	"ApprovedBy" INTEGER, 
	"ApprovedAt" TIMESTAMP WITHOUT TIME ZONE, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ChangeOrderId"), 
	CONSTRAINT "UQ_ContractChangeOrders_Number" UNIQUE ("ContractId", "ChangeOrderNo")
);

CREATE TABLE "ContractDeductionRules" (
	"RuleId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"SettlementSide" VARCHAR(20) NOT NULL, 
	"Code" VARCHAR(50) NOT NULL, 
	"NameAr" VARCHAR(150) NOT NULL, 
	"CalculationType" VARCHAR(20) NOT NULL, 
	"Rate" NUMERIC(9, 4) NOT NULL, 
	"BaseType" VARCHAR(30) NOT NULL, 
	"PostingSide" VARCHAR(10) NOT NULL, 
	"CapAmount" NUMERIC(18, 2), 
	"GLAccountId" INTEGER, 
	"IsActive" BOOLEAN NOT NULL, 
	"SortOrder" INTEGER NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("RuleId"), 
	CONSTRAINT "UQ_ContractDeductionRules_Code" UNIQUE ("ContractId", "SettlementSide", "Code"), 
	CONSTRAINT "CK_ContractDeductionRules_Rate" CHECK ("Rate" >= 0 AND ("CapAmount" IS NULL OR "CapAmount" >= 0))
);

CREATE TABLE "ContractItems" (
	"ItemId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"ItemNo" VARCHAR(50) NOT NULL, 
	"Description" VARCHAR(500) NOT NULL, 
	"Unit" VARCHAR(30) NOT NULL, 
	"Quantity" NUMERIC(18, 4) NOT NULL, 
	"UnitPrice" NUMERIC(18, 4) NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("ItemId"), 
	CONSTRAINT "UQ_ContractItems_Contract_ItemNo" UNIQUE ("ContractId", "ItemNo"), 
	CONSTRAINT "CK_ContractItems_NonNegative" CHECK ("Quantity" >= 0 AND "UnitPrice" >= 0)
);

CREATE TABLE "ContractSettlements" (
	"SettlementId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"SettlementSide" VARCHAR(20) NOT NULL, 
	"SequenceNo" INTEGER NOT NULL, 
	"SettlementNo" VARCHAR(50) NOT NULL, 
	"SettlementDate" DATE NOT NULL, 
	"CounterpartyName" VARCHAR(200) NOT NULL, 
	"WorkValue" NUMERIC(18, 2) NOT NULL, 
	"CumulativeWorkValue" NUMERIC(18, 2) NOT NULL, 
	"DeductionsJson" JSON NOT NULL, 
	"VatAmount" NUMERIC(18, 2) NOT NULL, 
	"NetAmount" NUMERIC(18, 2) NOT NULL, 
	"Status" VARCHAR(20) NOT NULL, 
	"JournalEntryId" INTEGER, 
	"Notes" TEXT, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("SettlementId"), 
	CONSTRAINT "UQ_ContractSettlements_Sequence" UNIQUE ("ContractId", "SettlementSide", "SequenceNo"), 
	CONSTRAINT "UQ_ContractSettlements_Number" UNIQUE ("ContractId", "SettlementSide", "SettlementNo"), 
	CONSTRAINT "CK_ContractSettlements_NonNegative" CHECK ("WorkValue" >= 0 AND "NetAmount" >= 0), 
	UNIQUE ("JournalEntryId")
);

CREATE TABLE "FinancialChecks" (
	"CheckId" BIGSERIAL NOT NULL, 
	"CheckNumber" VARCHAR(50) NOT NULL, 
	"CheckType" VARCHAR(20) NOT NULL, 
	"Amount" NUMERIC(18, 2) NOT NULL, 
	"DueDate" DATE NOT NULL, 
	"DraweeBank" VARCHAR(200), 
	"ProjectBrand" VARCHAR(50) NOT NULL, 
	"Status" VARCHAR(30) NOT NULL, 
	"PartyAccountId" INTEGER NOT NULL, 
	"TreasuryAccountId" INTEGER NOT NULL, 
	"ProjectId" INTEGER, 
	"JournalEntryId" INTEGER, 
	"Description" VARCHAR(500), 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("CheckId"), 
	UNIQUE ("CheckNumber"), 
	UNIQUE ("JournalEntryId")
);
CREATE INDEX "IX_FinancialChecks_ProjectId" ON "FinancialChecks" ("ProjectId");

CREATE TABLE "JournalEntryDetails" (
	"DetailId" SERIAL NOT NULL, 
	"JournalEntryId" INTEGER NOT NULL, 
	"LineNo" INTEGER NOT NULL, 
	"AccountId" INTEGER NOT NULL, 
	"ProjectId" INTEGER, 
	"DebitAmount" NUMERIC(18, 2) NOT NULL, 
	"CreditAmount" NUMERIC(18, 2) NOT NULL, 
	"FcyAmount" NUMERIC(18, 2), 
	"ExchangeRate" NUMERIC(18, 6), 
	"Description" TEXT,
	PRIMARY KEY ("DetailId")
);

CREATE TABLE "ProgressBillings" (
	"BillingId" SERIAL NOT NULL, 
	"ContractId" INTEGER NOT NULL, 
	"BillingNo" VARCHAR(50) NOT NULL, 
	"BillingDate" DATE NOT NULL, 
	"WorkValue" NUMERIC(18, 2) NOT NULL, 
	"RetentionAmount" NUMERIC(18, 2) NOT NULL, 
	"AdvanceDeduction" NUMERIC(18, 2) NOT NULL, 
	"OtherDeductions" NUMERIC(18, 2) NOT NULL, 
	"NetAmount" NUMERIC(18, 2) NOT NULL, 
	"Status" VARCHAR(30) NOT NULL, 
	"Notes" TEXT, 
	"CreatedBy" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("BillingId")
);

CREATE TABLE "TreasuryTransactions" (
	"TransactionId" BIGSERIAL NOT NULL, 
	"TreasuryAccountId" INTEGER NOT NULL, 
	"TransactionDate" DATE NOT NULL, 
	"Inflow" NUMERIC(18, 2) NOT NULL, 
	"Outflow" NUMERIC(18, 2) NOT NULL, 
	"Description" VARCHAR(500), 
	"VoucherNo" VARCHAR(50), 
	"Status" VARCHAR(30), 
	"RecipientName" VARCHAR(200), 
	"ProjectId" INTEGER, 
	"JournalEntryId" INTEGER, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("TransactionId")
);

CREATE TABLE "BankReconciliationLines" (
	"LineId" BIGSERIAL NOT NULL, 
	"ReconciliationId" INTEGER NOT NULL, 
	"TransactionDate" DATE, 
	"Inflow" NUMERIC(18, 2) NOT NULL, 
	"Outflow" NUMERIC(18, 2) NOT NULL, 
	"Description" VARCHAR(500), 
	"CheckNo" VARCHAR(30), 
	"Status" VARCHAR(30), 
	"Recipient" VARCHAR(200), 
	"IsMatched" BOOLEAN NOT NULL, 
	PRIMARY KEY ("LineId")
);

CREATE TABLE "CheckStatusHistory" (
	"HistoryId" BIGSERIAL NOT NULL, 
	"CheckId" BIGINT NOT NULL, 
	"OldStatus" VARCHAR(20), 
	"NewStatus" VARCHAR(20) NOT NULL, 
	"ChangedBy" INTEGER, 
	"ChangedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("HistoryId")
);

CREATE TABLE "ContractAttachments" (
	"AttachmentId" SERIAL NOT NULL, 
	"ContractId" INTEGER, 
	"SettlementId" INTEGER, 
	"Category" VARCHAR(80) NOT NULL, 
	"OriginalFilename" VARCHAR(255) NOT NULL, 
	"ContentType" VARCHAR(120) NOT NULL, 
	"SizeBytes" INTEGER NOT NULL, 
	"FileContent" BYTEA NOT NULL, 
	"Notes" VARCHAR(500), 
	"UploadedBy" INTEGER, 
	"UploadedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("AttachmentId"), 
	CONSTRAINT "CK_ContractAttachments_OneParent" CHECK (("ContractId" IS NOT NULL AND "SettlementId" IS NULL) OR ("ContractId" IS NULL AND "SettlementId" IS NOT NULL))
);

CREATE TABLE "ContractSettlementItems" (
	"SettlementItemId" SERIAL NOT NULL, 
	"SettlementId" INTEGER NOT NULL, 
	"ContractItemId" INTEGER NOT NULL, 
	"Quantity" NUMERIC(18, 4) NOT NULL, 
	"UnitPrice" NUMERIC(18, 4) NOT NULL, 
	"Amount" NUMERIC(18, 2) NOT NULL, 
	"CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY ("SettlementItemId"), 
	CONSTRAINT "UQ_ContractSettlementItems_Line" UNIQUE ("SettlementId", "ContractItemId"), 
	CONSTRAINT "CK_ContractSettlementItems_Quantity" CHECK ("Quantity" > 0 AND "UnitPrice" >= 0)
);

ALTER TABLE "AuditLog" ADD FOREIGN KEY("UserId") REFERENCES "Users" ("UserId");

ALTER TABLE "ChartOfAccounts" ADD FOREIGN KEY("ParentAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ChartOfAccounts" ADD FOREIGN KEY("ClassificationId") REFERENCES "AccountClassifications" ("ClassificationId");

ALTER TABLE "ContractRequests" ADD FOREIGN KEY("ReviewedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractRequests" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractRequests" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "FinancialStatementLines" ADD FOREIGN KEY("ClassificationId") REFERENCES "AccountClassifications" ("ClassificationId");

ALTER TABLE "FiscalYears" ADD FOREIGN KEY("CompanyId") REFERENCES "Companies" ("CompanyId");

ALTER TABLE "InventoryMovements" ADD FOREIGN KEY("ItemId") REFERENCES "InventoryItems" ("ItemId");

ALTER TABLE "InventoryMovements" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "InventoryMovements" ADD FOREIGN KEY("WarehouseId") REFERENCES "InventoryWarehouses" ("WarehouseId");

ALTER TABLE "PurchaseOrders" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "PurchaseOrders" ADD FOREIGN KEY("WarehouseId") REFERENCES "InventoryWarehouses" ("WarehouseId");

ALTER TABLE "RolePermissions" ADD FOREIGN KEY("PermissionId") REFERENCES "Permissions" ("PermissionId");

ALTER TABLE "RolePermissions" ADD FOREIGN KEY("RoleId") REFERENCES "Roles" ("RoleId");

ALTER TABLE "Screens" ADD FOREIGN KEY("SectionId") REFERENCES "Sections" ("SectionId");

ALTER TABLE "UserPermissions" ADD FOREIGN KEY("PermissionId") REFERENCES "Permissions" ("PermissionId");

ALTER TABLE "UserPermissions" ADD FOREIGN KEY("UserId") REFERENCES "Users" ("UserId");

ALTER TABLE "UserRoles" ADD FOREIGN KEY("RoleId") REFERENCES "Roles" ("RoleId");

ALTER TABLE "UserRoles" ADD FOREIGN KEY("UserId") REFERENCES "Users" ("UserId");

ALTER TABLE "Beneficiaries" ADD FOREIGN KEY("DefaultProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "Beneficiaries" ADD FOREIGN KEY("LinkedAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "Contracts" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "Contracts" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "Contracts" ADD FOREIGN KEY("RequestId") REFERENCES "ContractRequests" ("RequestId");

ALTER TABLE "JournalEntries" ADD FOREIGN KEY("PostedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "JournalEntries" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "JournalEntries" ADD FOREIGN KEY("FiscalYearId") REFERENCES "FiscalYears" ("FiscalYearId");

ALTER TABLE "JournalEntries" ADD FOREIGN KEY("CompanyId") REFERENCES "Companies" ("CompanyId");
ALTER TABLE "JournalEntries" ADD FOREIGN KEY("SourceSettlementId") REFERENCES "ContractSettlements" ("SettlementId");

ALTER TABLE "PurchaseOrderLines" ADD FOREIGN KEY("ItemId") REFERENCES "InventoryItems" ("ItemId");

ALTER TABLE "PurchaseOrderLines" ADD FOREIGN KEY("PurchaseOrderId") REFERENCES "PurchaseOrders" ("PurchaseOrderId") ON DELETE CASCADE;

ALTER TABLE "TreasuryAccounts" ADD FOREIGN KEY("GLAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "BankReconciliations" ADD FOREIGN KEY("PreparedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "BankReconciliations" ADD FOREIGN KEY("TreasuryAccountId") REFERENCES "TreasuryAccounts" ("TreasuryAccountId");

ALTER TABLE "CheckPrintTemplates" ADD FOREIGN KEY("TreasuryAccountId") REFERENCES "TreasuryAccounts" ("TreasuryAccountId");

ALTER TABLE "Checks" ADD FOREIGN KEY("TreasuryAccountId") REFERENCES "TreasuryAccounts" ("TreasuryAccountId");

ALTER TABLE "Checks" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "Checks" ADD FOREIGN KEY("BeneficiaryId") REFERENCES "Beneficiaries" ("BeneficiaryId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("CompanyId") REFERENCES "Companies" ("CompanyId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("VatAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("AdvanceAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("WorkAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("FiscalYearId") REFERENCES "FiscalYears" ("FiscalYearId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("TaxAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("RetentionAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAccountingConfig" ADD FOREIGN KEY("ControlAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractAddendums" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractAddendums" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractChangeOrders" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractChangeOrders" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractChangeOrders" ADD FOREIGN KEY("ApprovedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractDeductionRules" ADD FOREIGN KEY("GLAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ContractDeductionRules" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractItems" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractSettlements" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractSettlements" ADD FOREIGN KEY("JournalEntryId") REFERENCES "JournalEntries" ("JournalEntryId");

ALTER TABLE "ContractSettlements" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "FinancialChecks" ADD FOREIGN KEY("TreasuryAccountId") REFERENCES "TreasuryAccounts" ("TreasuryAccountId");

ALTER TABLE "FinancialChecks" ADD FOREIGN KEY("PartyAccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "FinancialChecks" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "FinancialChecks" ADD FOREIGN KEY("JournalEntryId") REFERENCES "JournalEntries" ("JournalEntryId");
ALTER TABLE "FinancialChecks" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "JournalEntryDetails" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "JournalEntryDetails" ADD FOREIGN KEY("JournalEntryId") REFERENCES "JournalEntries" ("JournalEntryId");

ALTER TABLE "JournalEntryDetails" ADD FOREIGN KEY("AccountId") REFERENCES "ChartOfAccounts" ("AccountId");

ALTER TABLE "ProgressBillings" ADD FOREIGN KEY("CreatedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ProgressBillings" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "TreasuryTransactions" ADD FOREIGN KEY("JournalEntryId") REFERENCES "JournalEntries" ("JournalEntryId");

ALTER TABLE "TreasuryTransactions" ADD FOREIGN KEY("ProjectId") REFERENCES "Projects" ("ProjectId");

ALTER TABLE "TreasuryTransactions" ADD FOREIGN KEY("TreasuryAccountId") REFERENCES "TreasuryAccounts" ("TreasuryAccountId");

ALTER TABLE "BankReconciliationLines" ADD FOREIGN KEY("ReconciliationId") REFERENCES "BankReconciliations" ("ReconciliationId");

ALTER TABLE "CheckStatusHistory" ADD FOREIGN KEY("ChangedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "CheckStatusHistory" ADD FOREIGN KEY("CheckId") REFERENCES "Checks" ("CheckId");

ALTER TABLE "ContractAttachments" ADD FOREIGN KEY("ContractId") REFERENCES "Contracts" ("ContractId") ON DELETE CASCADE;

ALTER TABLE "ContractAttachments" ADD FOREIGN KEY("UploadedBy") REFERENCES "Users" ("UserId");

ALTER TABLE "ContractAttachments" ADD FOREIGN KEY("SettlementId") REFERENCES "ContractSettlements" ("SettlementId") ON DELETE CASCADE;

ALTER TABLE "ContractSettlementItems" ADD FOREIGN KEY("ContractItemId") REFERENCES "ContractItems" ("ItemId");

ALTER TABLE "ContractSettlementItems" ADD FOREIGN KEY("SettlementId") REFERENCES "ContractSettlements" ("SettlementId") ON DELETE CASCADE;

CREATE UNIQUE INDEX "ix_InventoryItems_Code" ON "InventoryItems" ("Code");

CREATE UNIQUE INDEX "ix_InventoryWarehouses_Code" ON "InventoryWarehouses" ("Code");

CREATE UNIQUE INDEX "ix_ContractRequests_RequestNo" ON "ContractRequests" ("RequestNo");

CREATE UNIQUE INDEX "ix_InventoryMovements_MovementNo" ON "InventoryMovements" ("MovementNo");

CREATE UNIQUE INDEX "ix_PurchaseOrders_OrderNo" ON "PurchaseOrders" ("OrderNo");

CREATE UNIQUE INDEX "ix_Contracts_ContractNo" ON "Contracts" ("ContractNo");

CREATE INDEX "ix_PurchaseOrderLines_PurchaseOrderId" ON "PurchaseOrderLines" ("PurchaseOrderId");

CREATE INDEX "ix_ContractAccountingConfig_ContractId" ON "ContractAccountingConfig" ("ContractId");

CREATE INDEX "ix_ContractAddendums_ContractId" ON "ContractAddendums" ("ContractId");

CREATE INDEX "ix_ContractChangeOrders_ContractId" ON "ContractChangeOrders" ("ContractId");

CREATE INDEX "ix_ContractDeductionRules_ContractId" ON "ContractDeductionRules" ("ContractId");

CREATE INDEX "ix_ContractItems_ContractId" ON "ContractItems" ("ContractId");

CREATE INDEX "ix_ContractSettlements_ContractId" ON "ContractSettlements" ("ContractId");

CREATE INDEX "ix_ProgressBillings_ContractId" ON "ProgressBillings" ("ContractId");

CREATE INDEX "ix_ContractAttachments_SettlementId" ON "ContractAttachments" ("SettlementId");

CREATE INDEX "ix_ContractAttachments_ContractId" ON "ContractAttachments" ("ContractId");

CREATE INDEX "ix_ContractSettlementItems_SettlementId" ON "ContractSettlementItems" ("SettlementId");

CREATE INDEX "ix_ContractSettlementItems_ContractItemId" ON "ContractSettlementItems" ("ContractItemId");


-- Application compatibility objects
CREATE OR REPLACE VIEW "vw_EffectivePermissions" AS
SELECT u."UserId" AS "UserId", p."PermissionId" AS "PermissionId",
       p."ScreenCode" AS "ScreenCode", p."ActionCode" AS "ActionCode",
       CASE
         WHEN up."IsAllowed" IS NOT NULL THEN CASE WHEN up."IsAllowed" THEN 1 ELSE 0 END
         WHEN u."JobProfileId" IS NOT NULL THEN
              CASE WHEN EXISTS (
                    SELECT 1 FROM "JobProfilePermissions" jpp
                    JOIN "JobProfiles" jp ON jp."JobProfileId"=jpp."JobProfileId"
                    WHERE jpp."JobProfileId"=u."JobProfileId"
                      AND jp."IsActive" IS TRUE
                      AND jpp."PermissionId"=p."PermissionId"
              ) THEN 1 ELSE 0 END
         WHEN EXISTS (
              SELECT 1 FROM "UserRoles" ur
              JOIN "RolePermissions" rp ON rp."RoleId"=ur."RoleId"
              WHERE ur."UserId"=u."UserId" AND rp."PermissionId"=p."PermissionId"
         ) THEN 1
         ELSE 0
       END AS "IsAllowed"
FROM "Users" u CROSS JOIN "Permissions" p
LEFT JOIN "UserPermissions" up ON up."UserId"=u."UserId" AND up."PermissionId"=p."PermissionId";

CREATE INDEX IF NOT EXISTS "IX_AuditLog_Timestamp_UserId" ON "AuditLog" ("Timestamp", "UserId");
CREATE UNIQUE INDEX IF NOT EXISTS "UX_TreasuryTransactions_CheckVoucher" ON "TreasuryTransactions" ("VoucherNo") WHERE "VoucherNo" LIKE 'CHK-%';
COMMIT;
