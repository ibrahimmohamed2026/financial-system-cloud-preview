-- وحدة العقود والمكتب الفني: جداول إضافية فقط؛ لا تعدّل الجداول المالية القائمة.
CREATE TABLE IF NOT EXISTS "Contracts" (
 "ContractId" SERIAL PRIMARY KEY,
 "ContractNo" VARCHAR(50) NOT NULL UNIQUE,
 "Title" VARCHAR(250) NOT NULL,
 "ClientName" VARCHAR(200) NOT NULL,
 "ProjectId" INTEGER NULL REFERENCES "Projects"("ProjectId"),
 "StartDate" DATE NULL,
 "EndDate" DATE NULL,
 "OriginalValue" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "Status" VARCHAR(30) NOT NULL DEFAULT 'Active',
 "Notes" TEXT NULL,
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "ContractAddendums" (
 "AddendumId" SERIAL PRIMARY KEY,
 "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "AddendumNo" VARCHAR(50) NOT NULL,
 "AddendumDate" DATE NOT NULL,
 "Description" VARCHAR(500) NOT NULL,
 "ValueChange" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "ProgressBillings" (
 "BillingId" SERIAL PRIMARY KEY,
 "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "BillingNo" VARCHAR(50) NOT NULL,
 "BillingDate" DATE NOT NULL,
 "WorkValue" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "RetentionAmount" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "AdvanceDeduction" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "OtherDeductions" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "NetAmount" NUMERIC(18,2) NOT NULL DEFAULT 0,
 "Status" VARCHAR(30) NOT NULL DEFAULT 'Draft',
 "Notes" TEXT NULL,
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "IX_ContractAddendums_ContractId" ON "ContractAddendums"("ContractId");
CREATE INDEX IF NOT EXISTS "IX_ProgressBillings_ContractId" ON "ProgressBillings"("ContractId");
INSERT INTO "Screens" ("SectionId","ScreenCode","TitleEn","TitleAr","Route","SortOrder","IsActive")
SELECT s."SectionId", 'Contracts','Contracts & Technical Office','العقود والمكتب الفني','/contracts',40,TRUE
FROM "Sections" s WHERE s."Code"='ACCOUNTING' AND NOT EXISTS (SELECT 1 FROM "Screens" x WHERE x."ScreenCode"='Contracts');
INSERT INTO "Permissions" ("ScreenCode","ActionCode")
SELECT 'Contracts', a.code FROM (VALUES ('View'),('Add'),('Edit'),('Delete'),('Print')) AS a(code)
WHERE NOT EXISTS (SELECT 1 FROM "Permissions" p WHERE p."ScreenCode"='Contracts' AND p."ActionCode"=a.code);
