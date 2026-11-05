-- Migration additive for PostgreSQL. Does not alter/drop legacy tables or data.
CREATE TABLE IF NOT EXISTS "FinancialChecks" (
  "CheckId" BIGSERIAL PRIMARY KEY,
  "CheckNumber" VARCHAR(50) NOT NULL UNIQUE,
  "CheckType" VARCHAR(20) NOT NULL CHECK ("CheckType" IN ('INCOMING','OUTGOING')),
  "Amount" NUMERIC(18,2) NOT NULL CHECK ("Amount" > 0),
  "DueDate" DATE NOT NULL,
  "DraweeBank" VARCHAR(200),
  "Status" VARCHAR(30) NOT NULL DEFAULT 'مسودة',
  "PartyAccountId" INTEGER NOT NULL REFERENCES "ChartOfAccounts"("AccountId"),
  "TreasuryAccountId" INTEGER NOT NULL REFERENCES "TreasuryAccounts"("TreasuryAccountId"),
  "JournalEntryId" INTEGER UNIQUE REFERENCES "JournalEntries"("JournalEntryId"),
  "Description" VARCHAR(500),
  "CreatedBy" INTEGER REFERENCES "Users"("UserId"),
  "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "IX_FinancialChecks_StatusDueDate" ON "FinancialChecks" ("Status", "DueDate");
