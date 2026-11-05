/* =========================================================================
   003 — تصحيح vw_TrialBalance
   المشكلة في السكريبت الأصلي: الـ JOIN على JournalEntries بعد الـ LEFT JOIN بيحوّله Inner Join،
   فأي حساب مالوش قيد Posted (حتى لو له رصيد افتتاحي) بيختفي من ميزان المراجعة.
   الحل: شرط Posted جوه الـ LEFT JOIN نفسه.
   ========================================================================= */
USE FinancialSystem;
GO

ALTER VIEW vw_TrialBalance AS
SELECT
    coa.AccountId,
    coa.AccountCode,
    coa.AccountNameAr,
    ac.NameAr                                            AS Classification,
    ac.StatementType,
    coa.OpeningDebit,
    coa.OpeningCredit,
    ISNULL(SUM(x.DebitAmount), 0)                         AS PeriodDebit,
    ISNULL(SUM(x.CreditAmount), 0)                        AS PeriodCredit,
    coa.OpeningDebit  + ISNULL(SUM(x.DebitAmount), 0)      AS TotalDebit,
    coa.OpeningCredit + ISNULL(SUM(x.CreditAmount), 0)     AS TotalCredit,
    CASE WHEN (coa.OpeningDebit  + ISNULL(SUM(x.DebitAmount),0))
            > (coa.OpeningCredit + ISNULL(SUM(x.CreditAmount),0))
         THEN (coa.OpeningDebit  + ISNULL(SUM(x.DebitAmount),0))
            - (coa.OpeningCredit + ISNULL(SUM(x.CreditAmount),0))
         ELSE 0 END                                        AS DebitBalance,
    CASE WHEN (coa.OpeningCredit + ISNULL(SUM(x.CreditAmount),0))
            > (coa.OpeningDebit  + ISNULL(SUM(x.DebitAmount),0))
         THEN (coa.OpeningCredit + ISNULL(SUM(x.CreditAmount),0))
            - (coa.OpeningDebit  + ISNULL(SUM(x.DebitAmount),0))
         ELSE 0 END                                        AS CreditBalance
FROM ChartOfAccounts coa
JOIN AccountClassifications ac ON ac.ClassificationId = coa.ClassificationId
LEFT JOIN (
    SELECT jed.AccountId, jed.DebitAmount, jed.CreditAmount
    FROM JournalEntryDetails jed
    JOIN JournalEntries je ON je.JournalEntryId = jed.JournalEntryId AND je.Status = 'Posted'
) x ON x.AccountId = coa.AccountId
GROUP BY coa.AccountId, coa.AccountCode, coa.AccountNameAr, ac.NameAr, ac.StatementType,
         coa.OpeningDebit, coa.OpeningCredit;
GO
