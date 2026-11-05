-- Additive session revocation field; existing users and sessions start at version zero.
ALTER TABLE "Users"
    ADD COLUMN IF NOT EXISTS "TokenVersion" INTEGER NOT NULL DEFAULT 0;
