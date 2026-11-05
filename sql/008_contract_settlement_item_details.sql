-- Additive, rerunnable migration. Does not drop or modify existing data.
CREATE TABLE IF NOT EXISTS "ContractSettlementItems" (
 "SettlementItemId" SERIAL PRIMARY KEY,
 "SettlementId" INTEGER NOT NULL REFERENCES "ContractSettlements"("SettlementId") ON DELETE CASCADE,
 "ContractItemId" INTEGER NOT NULL REFERENCES "ContractItems"("ItemId"),
 "Quantity" NUMERIC(18,4) NOT NULL,
 "UnitPrice" NUMERIC(18,4) NOT NULL,
 "Amount" NUMERIC(18,2) NOT NULL,
 "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_ContractSettlementItems_Line" UNIQUE ("SettlementId","ContractItemId"),
 CONSTRAINT "CK_ContractSettlementItems_Quantity" CHECK ("Quantity">0 AND "UnitPrice">=0 AND "Amount">=0)
);
CREATE INDEX IF NOT EXISTS "IX_ContractSettlementItems_SettlementId" ON "ContractSettlementItems"("SettlementId");
CREATE INDEX IF NOT EXISTS "IX_ContractSettlementItems_ContractItemId" ON "ContractSettlementItems"("ContractItemId");
