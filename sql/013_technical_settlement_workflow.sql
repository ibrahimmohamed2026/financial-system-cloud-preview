-- Additive migration for technical-office estimates. Does not drop, rename, or rewrite existing data.
CREATE TABLE IF NOT EXISTS "TechnicalSettlementEstimates" (
 "EstimateId" SERIAL PRIMARY KEY,
 "ContractId" INTEGER NOT NULL REFERENCES "Contracts"("ContractId") ON DELETE CASCADE,
 "SettlementSide" VARCHAR(20) NOT NULL CHECK ("SettlementSide" IN ('Customer','Subcontractor')),
 "EstimateNo" VARCHAR(50) NOT NULL,
 "EstimateDate" DATE NOT NULL,
 "CounterpartyName" VARCHAR(200) NOT NULL,
 "WorkValue" NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK ("WorkValue">=0),
 "Status" VARCHAR(30) NOT NULL DEFAULT 'UnderReview' CHECK ("Status" IN ('UnderReview','TechnicallyApproved','Rejected')),
 "Notes" TEXT NULL,
 "FinancialSettlementId" INTEGER NULL UNIQUE REFERENCES "ContractSettlements"("SettlementId"),
 "CreatedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "ReviewedBy" INTEGER NULL REFERENCES "Users"("UserId"),
 "ReviewedAt" TIMESTAMP NULL,
 "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_TechnicalSettlementEstimates_Number" UNIQUE ("ContractId","SettlementSide","EstimateNo")
);
CREATE TABLE IF NOT EXISTS "TechnicalSettlementEstimateItems" (
 "EstimateItemId" SERIAL PRIMARY KEY,
 "EstimateId" INTEGER NOT NULL REFERENCES "TechnicalSettlementEstimates"("EstimateId") ON DELETE CASCADE,
 "ContractItemId" INTEGER NOT NULL REFERENCES "ContractItems"("ItemId"),
 "PreviousQuantity" NUMERIC(18,4) NOT NULL DEFAULT 0,
 "CurrentQuantity" NUMERIC(18,4) NOT NULL CHECK ("CurrentQuantity">0),
 "UnitPrice" NUMERIC(18,4) NOT NULL CHECK ("UnitPrice">=0),
 "Amount" NUMERIC(18,2) NOT NULL CHECK ("Amount">=0),
 "CreatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT "UQ_TechnicalSettlementEstimateItems_Line" UNIQUE ("EstimateId","ContractItemId")
);
CREATE INDEX IF NOT EXISTS "IX_TechnicalSettlementEstimates_ContractSideStatus" ON "TechnicalSettlementEstimates"("ContractId","SettlementSide","Status");
