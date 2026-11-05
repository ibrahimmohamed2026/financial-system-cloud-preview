-- Additive migration only: no existing tables/columns/data are dropped or renamed.
CREATE TABLE IF NOT EXISTS "ContractItems" (
 "ItemId" SERIAL PRIMARY KEY,
 "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "ItemNo" VARCHAR(50) NOT NULL, "Description" VARCHAR(500) NOT NULL,
 "Unit" VARCHAR(30) NOT NULL DEFAULT 'وحدة', "Quantity" NUMERIC(18,4) NOT NULL DEFAULT 0,
 "UnitPrice" NUMERIC(18,4) NOT NULL DEFAULT 0, "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractItems_Contract_ItemNo" UNIQUE ("ContractId","ItemNo"),
 CONSTRAINT "CK_ContractItems_NonNegative" CHECK ("Quantity">=0 AND "UnitPrice">=0)
);
CREATE TABLE IF NOT EXISTS "ContractDeductionRules" (
 "RuleId" SERIAL PRIMARY KEY, "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "SettlementSide" VARCHAR(20) NOT NULL CHECK ("SettlementSide" IN ('Customer','Subcontractor')),
 "Code" VARCHAR(50) NOT NULL, "NameAr" VARCHAR(150) NOT NULL,
 "CalculationType" VARCHAR(20) NOT NULL DEFAULT 'Percent' CHECK ("CalculationType" IN ('Percent','Fixed')),
 "Rate" NUMERIC(9,4) NOT NULL DEFAULT 0, "BaseType" VARCHAR(30) NOT NULL DEFAULT 'CurrentWork',
 "PostingSide" VARCHAR(10) NOT NULL DEFAULT 'Credit' CHECK ("PostingSide" IN ('Debit','Credit')),
 "CapAmount" NUMERIC(18,2) NULL, "GLAccountId" INTEGER NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "IsActive" BOOLEAN NOT NULL DEFAULT TRUE, "SortOrder" INTEGER NOT NULL DEFAULT 0,
 "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractDeductionRules_Code" UNIQUE ("ContractId","SettlementSide","Code"),
 CONSTRAINT "CK_ContractDeductionRules_Rate" CHECK ("Rate">=0 AND ("CapAmount" IS NULL OR "CapAmount">=0))
);
CREATE TABLE IF NOT EXISTS "ContractAccountingConfig" (
 "ConfigId" SERIAL PRIMARY KEY, "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "SettlementSide" VARCHAR(20) NOT NULL CHECK ("SettlementSide" IN ('Customer','Subcontractor')),
 "CompanyId" INTEGER NOT NULL REFERENCES "Companies"("CompanyId"), "FiscalYearId" INTEGER NOT NULL REFERENCES "FiscalYears"("FiscalYearId"),
 "ControlAccountId" INTEGER NOT NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "WorkAccountId" INTEGER NOT NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "RetentionAccountId" INTEGER NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "AdvanceAccountId" INTEGER NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "TaxAccountId" INTEGER NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "VatAccountId" INTEGER NULL REFERENCES "ChartOfAccounts"("AccountId"),
 "DefaultVatRate" NUMERIC(9,4) NOT NULL DEFAULT 0 CHECK ("DefaultVatRate">=0),
 "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractAccountingConfig_Contract_Side" UNIQUE ("ContractId","SettlementSide")
);
CREATE TABLE IF NOT EXISTS "ContractSettlements" (
 "SettlementId" SERIAL PRIMARY KEY, "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "SettlementSide" VARCHAR(20) NOT NULL CHECK ("SettlementSide" IN ('Customer','Subcontractor')),
 "SequenceNo" INTEGER NOT NULL, "SettlementNo" VARCHAR(50) NOT NULL, "SettlementDate" DATE NOT NULL,
 "CounterpartyName" VARCHAR(200) NOT NULL, "WorkValue" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "CumulativeWorkValue" NUMERIC(18,2) NOT NULL DEFAULT 0, "DeductionsJson" JSONB NOT NULL DEFAULT '{}'::jsonb,
 "VatAmount" NUMERIC(18,2) NOT NULL DEFAULT 0, "NetAmount" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "Status" VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK ("Status" IN ('Draft','Approved','Posted','Cancelled')),
 "JournalEntryId" INTEGER NULL UNIQUE REFERENCES "JournalEntries"("JournalEntryId"),
 "Notes" TEXT NULL, "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"), "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractSettlements_Sequence" UNIQUE ("ContractId","SettlementSide","SequenceNo"),
 CONSTRAINT "UQ_ContractSettlements_Number" UNIQUE ("ContractId","SettlementSide","SettlementNo"),
 CONSTRAINT "CK_ContractSettlements_NonNegative" CHECK ("WorkValue">=0 AND "VatAmount">=0 AND "NetAmount">=0)
);
CREATE INDEX IF NOT EXISTS "IX_ContractItems_ContractId" ON "ContractItems"("ContractId");
CREATE INDEX IF NOT EXISTS "IX_ContractDeductionRules_ContractSide" ON "ContractDeductionRules"("ContractId","SettlementSide");
CREATE INDEX IF NOT EXISTS "IX_ContractSettlements_ContractSideDate" ON "ContractSettlements"("ContractId","SettlementSide","SettlementDate");
INSERT INTO "Screens" ("SectionId","ScreenCode","TitleEn","TitleAr","Route","SortOrder","IsActive")
SELECT s."SectionId", 'ContractSettlements','Contract Settlements','المستخلصات وتسويات المقاولين','/contracts',41,TRUE FROM "Sections" s
WHERE s."Code"='ACCOUNTING' AND NOT EXISTS (SELECT 1 FROM "Screens" x WHERE x."ScreenCode"='ContractSettlements');
INSERT INTO "Permissions" ("ScreenCode","ActionCode")
SELECT 'ContractSettlements', a.code FROM (VALUES ('View'),('Add'),('Edit'),('Approve'),('Post')) AS a(code)
WHERE NOT EXISTS (SELECT 1 FROM "Permissions" p WHERE p."ScreenCode"='ContractSettlements' AND p."ActionCode"=a.code);
CREATE TABLE IF NOT EXISTS "ContractChangeOrders" (
 "ChangeOrderId" SERIAL PRIMARY KEY,
 "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "ChangeOrderNo" VARCHAR(50) NOT NULL, "ChangeOrderDate" DATE NOT NULL,
 "Description" VARCHAR(500) NOT NULL, "ValueChange" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "Status" VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK ("Status" IN ('Pending','Approved','Rejected')),
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"), "ApprovedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "ApprovedAt" TIMESTAMP NULL, "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractChangeOrders_Number" UNIQUE ("ContractId","ChangeOrderNo")
);
CREATE INDEX IF NOT EXISTS "IX_ContractChangeOrders_ContractStatus" ON "ContractChangeOrders"("ContractId","Status");
