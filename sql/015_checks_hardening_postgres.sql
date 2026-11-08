-- 015: cheque register hardening (PostgreSQL), safe to rerun.
-- Normalize legacy returned statuses, then scope cheque-number uniqueness by type and bank.
DO $migration$
DECLARE
    constraint_name text;
BEGIN
    IF to_regclass('"FinancialChecks"') IS NULL THEN
        RAISE EXCEPTION 'FinancialChecks table does not exist; run schema setup first';
    END IF;

    INSERT INTO "FinancialCheckStatusHistory"
        ("CheckId", "OldStatus", "NewStatus", "ChangedBy", "Note", "ChangedAt")
    SELECT "CheckId", "Status", 'مرتد', NULL,
           'تطبيع تهجئة الحالة بواسطة الترحيل 015', CURRENT_TIMESTAMP
    FROM "FinancialChecks"
    WHERE "Status" IN ('مُرتجع', 'مرتجع');

    UPDATE "FinancialChecks"
       SET "Status" = 'مرتد'
     WHERE "Status" IN ('مُرتجع', 'مرتجع');

    -- Never discard cheque rows to make a new constraint fit. Stop and report
    -- collisions so they can be reviewed and resolved explicitly.
    IF EXISTS (
        SELECT 1
          FROM "FinancialChecks"
         GROUP BY "CheckType", "TreasuryAccountId", "CheckNumber"
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Duplicate cheque numbers exist within the same type and treasury account; resolve them before migration 015';
    END IF;

    FOR constraint_name IN
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_class rel ON rel.oid = con.conrelid
          JOIN pg_namespace ns ON ns.oid = rel.relnamespace
         WHERE ns.nspname = current_schema()
           AND rel.relname = 'FinancialChecks'
           AND con.contype = 'u'
           AND (
               SELECT array_agg(att.attname::text ORDER BY att.attname)
                 FROM unnest(con.conkey) AS key(attnum)
                 JOIN pg_attribute att
                   ON att.attrelid = rel.oid AND att.attnum = key.attnum
           ) = ARRAY['CheckNumber']::text[]
    LOOP
        EXECUTE format('ALTER TABLE "FinancialChecks" DROP CONSTRAINT %I', constraint_name);
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
          FROM pg_constraint
         WHERE conrelid = '"FinancialChecks"'::regclass
           AND conname = 'UQ_FinancialChecks_Type_Bank_Number'
    ) THEN
        ALTER TABLE "FinancialChecks"
            ADD CONSTRAINT "UQ_FinancialChecks_Type_Bank_Number"
            UNIQUE ("CheckType", "TreasuryAccountId", "CheckNumber");
    END IF;
END
$migration$;
