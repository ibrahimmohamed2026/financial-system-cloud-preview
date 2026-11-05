-- Additive migration: request-to-contract lifecycle; no existing financial data is deleted.
CREATE TABLE IF NOT EXISTS "ContractRequests" (
 "RequestId" SERIAL PRIMARY KEY,
 "RequestNo" VARCHAR(50) NOT NULL UNIQUE,
 "RequestType" VARCHAR(30) NOT NULL DEFAULT 'Customer' CHECK ("RequestType" IN ('Customer','Subcontractor','Supplier')),
 "Title" VARCHAR(250) NOT NULL,
 "CounterpartyName" VARCHAR(200) NOT NULL,
 "ProjectId" INTEGER NULL REFERENCES "Projects"("ProjectId"),
 "EstimatedValue" NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK ("EstimatedValue">=0),
 "Description" TEXT NULL,
 "Status" VARCHAR(30) NOT NULL DEFAULT 'Draft' CHECK ("Status" IN ('Draft','Pending','Approved','Returned','Rejected')),
 "ReviewNotes" TEXT NULL,
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "CreatedAt" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
 "ReviewedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "ReviewedAt" TIMESTAMP WITHOUT TIME ZONE NULL
);
ALTER TABLE "Contracts" ADD COLUMN IF NOT EXISTS "RequestId" INTEGER NULL REFERENCES "ContractRequests"("RequestId");
CREATE UNIQUE INDEX IF NOT EXISTS "UX_Contracts_RequestId" ON "Contracts"("RequestId") WHERE "RequestId" IS NOT NULL;
CREATE INDEX IF NOT EXISTS "IX_ContractRequests_Status" ON "ContractRequests"("Status");
INSERT INTO "Screens" ("SectionId","ScreenCode","TitleEn","TitleAr","Route","SortOrder","IsActive")
SELECT s."SectionId", 'ContractRequests','Contract Requests','طلبات التعاقد','/contract-requests',41,TRUE
FROM "Sections" s WHERE s."Code"='ACCOUNTING' AND NOT EXISTS (SELECT 1 FROM "Screens" x WHERE x."ScreenCode"='ContractRequests');
INSERT INTO "Permissions" ("ScreenCode","ActionCode")
SELECT 'ContractRequests', a.code FROM (VALUES ('View'),('Add'),('Edit'),('Approve'),('Print')) AS a(code)
WHERE NOT EXISTS (SELECT 1 FROM "Permissions" p WHERE p."ScreenCode"='ContractRequests' AND p."ActionCode"=a.code);
