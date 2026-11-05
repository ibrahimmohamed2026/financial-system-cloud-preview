/* 004 — ربط حسابات الخزينة/البنك بشاشاتها (إضافة أعمدة فقط، مفيش تعديل على الجداول الحالية) */
USE FinancialSystem;
GO
IF COL_LENGTH('dbo.TreasuryAccounts', 'ScreenCode') IS NULL
    ALTER TABLE dbo.TreasuryAccounts ADD ScreenCode NVARCHAR(50) NULL;       -- شاشة الحساب (BankCibEgp ...)
GO
IF COL_LENGTH('dbo.TreasuryAccounts', 'ChecksScreenCode') IS NULL
    ALTER TABLE dbo.TreasuryAccounts ADD ChecksScreenCode NVARCHAR(50) NULL; -- شاشة دفتر الشيكات (ChecksCib ...)
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_TreasuryAccounts_ScreenCode')
    EXEC('CREATE UNIQUE INDEX UX_TreasuryAccounts_ScreenCode ON dbo.TreasuryAccounts(ScreenCode) WHERE ScreenCode IS NOT NULL');
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_TreasuryAccounts_ChecksScreenCode')
    EXEC('CREATE UNIQUE INDEX UX_TreasuryAccounts_ChecksScreenCode ON dbo.TreasuryAccounts(ChecksScreenCode) WHERE ChecksScreenCode IS NOT NULL');
GO
