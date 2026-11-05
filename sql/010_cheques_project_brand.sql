-- Additive migration for cheque project/brand tracking. Existing cheque data is preserved.
ALTER TABLE IF EXISTS "FinancialChecks"
  ADD COLUMN IF NOT EXISTS "ProjectBrand" VARCHAR(50) NOT NULL DEFAULT 'عام';
CREATE INDEX IF NOT EXISTS "IX_FinancialChecks_ProjectBrand_Status"
  ON "FinancialChecks" ("ProjectBrand", "Status");
