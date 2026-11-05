/* =========================================================================
   نظام مالي ومحاسبي متكامل — سكريبت إنشاء قاعدة البيانات
   مبني على تحليل ملف "ميزانيه فارغه.xlsx" (17 شيت)
   SQL Server 2019+
   ========================================================================= */


USE FinancialSystem;
GO


/* =========================================================================
   1) الإعدادات الأساسية
   ========================================================================= */

CREATE TABLE Companies (
    CompanyId       INT IDENTITY(1,1) PRIMARY KEY,
    NameAr          NVARCHAR(200) NOT NULL,
    NameEn          NVARCHAR(200) NULL,
    TaxNumber       NVARCHAR(50) NULL,
    CommercialRegister NVARCHAR(50) NULL,
    AddressAr       NVARCHAR(500) NULL,
    Phone           NVARCHAR(50) NULL,
    Email           NVARCHAR(200) NULL,
    Website         NVARCHAR(200) NULL,
    LogoData        NVARCHAR(MAX) NULL,
    IsActive        BIT NOT NULL DEFAULT 1,
    CreatedAt       DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE FiscalYears (
    FiscalYearId    INT IDENTITY(1,1) PRIMARY KEY,
    CompanyId       INT NOT NULL FOREIGN KEY REFERENCES Companies(CompanyId),
    StartDate       DATE NOT NULL,
    EndDate         DATE NOT NULL,
    IsClosed        BIT NOT NULL DEFAULT 0,
    CONSTRAINT CK_FiscalYears_Dates CHECK (EndDate > StartDate)
);
GO

-- مراكز التكلفة / المشاريع (شيت "chart off account")
CREATE TABLE Projects (
    ProjectId       INT IDENTITY(1,1) PRIMARY KEY,
    NameAr          NVARCHAR(200) NOT NULL UNIQUE,
    NameEn          NVARCHAR(200) NULL,
    IsHeadOffice    BIT NOT NULL DEFAULT 0,
    IsActive        BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE ExchangeRates (
    ExchangeRateId  INT IDENTITY(1,1) PRIMARY KEY,
    CurrencyCode    NVARCHAR(3) NOT NULL,          -- EGP, USD, ...
    RateDate        DATE NOT NULL,
    RateToEGP       DECIMAL(18,6) NOT NULL,
    CONSTRAINT UQ_ExchangeRates UNIQUE (CurrencyCode, RateDate)
);
GO

/* =========================================================================
   2) الحسابات والقيود
   ========================================================================= */

-- تصنيفات القوائم المالية (موحّدة الإملاء — تحل مشكلة التكرار في الملف الأصلي)
CREATE TABLE AccountClassifications (
    ClassificationId INT IDENTITY(1,1) PRIMARY KEY,
    NameAr           NVARCHAR(200) NOT NULL UNIQUE,
    StatementType    NVARCHAR(30) NOT NULL          -- 'BalanceSheet' | 'IncomeStatement'
        CHECK (StatementType IN ('BalanceSheet','IncomeStatement'))
);
GO

-- بنود القوائم المالية (شيتات "قائمه المركز المالي" و"قائمه الدخل")
CREATE TABLE FinancialStatementLines (
    LineId           INT IDENTITY(1,1) PRIMARY KEY,
    StatementType    NVARCHAR(30) NOT NULL
        CHECK (StatementType IN ('BalanceSheet','IncomeStatement')),
    CaptionAr        NVARCHAR(200) NOT NULL,
    SortOrder        INT NOT NULL,
    ClassificationId INT NULL FOREIGN KEY REFERENCES AccountClassifications(ClassificationId),
    IsSubtotal       BIT NOT NULL DEFAULT 0
);
GO

-- شجرة الحسابات (شيت "Trial balance" — 594 حساب حاليًا)
CREATE TABLE ChartOfAccounts (
    AccountId        INT IDENTITY(1,1) PRIMARY KEY,
    AccountCode      NVARCHAR(30) NOT NULL UNIQUE,
    AccountNameAr    NVARCHAR(300) NOT NULL,
    ParentAccountId  INT NULL FOREIGN KEY REFERENCES ChartOfAccounts(AccountId),
    ClassificationId INT NOT NULL FOREIGN KEY REFERENCES AccountClassifications(ClassificationId),
    NormalBalance    CHAR(2) NOT NULL CHECK (NormalBalance IN ('DR','CR')),
    OpeningDebit     DECIMAL(18,2) NOT NULL DEFAULT 0,
    OpeningCredit    DECIMAL(18,2) NOT NULL DEFAULT 0,
    IsActive         BIT NOT NULL DEFAULT 1,
    CreatedAt        DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO
CREATE INDEX IX_ChartOfAccounts_Classification ON ChartOfAccounts(ClassificationId);
GO

-- رؤوس قيود اليومية (شيت "دفتر اليومية")
CREATE TABLE JournalEntries (
    JournalEntryId   INT IDENTITY(1,1) PRIMARY KEY,
    EntryNo          NVARCHAR(30) NOT NULL UNIQUE,
    EntryDate        DATE NOT NULL,
    CompanyId        INT NOT NULL FOREIGN KEY REFERENCES Companies(CompanyId),
    FiscalYearId     INT NOT NULL FOREIGN KEY REFERENCES FiscalYears(FiscalYearId),
    SourceSettlementId INT NULL,
    Description      NVARCHAR(500) NULL,
    Status           NVARCHAR(20) NOT NULL DEFAULT 'Draft'
        CHECK (Status IN ('Draft','Posted','Reversed')),
    CreatedBy        INT NULL,                       -- FK Users (يُضاف بعد إنشاء Users)
    PostedBy         INT NULL,
    PostedAt         DATETIME2 NULL,
    CreatedAt        DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_JournalEntries_SourceSettlementId ON JournalEntries(SourceSettlementId);
GO

-- تفاصيل قيود اليومية (مدين/دائن)
CREATE TABLE JournalEntryDetails (
    DetailId         INT IDENTITY(1,1) PRIMARY KEY,
    JournalEntryId   INT NOT NULL FOREIGN KEY REFERENCES JournalEntries(JournalEntryId),
    [LineNo]         INT NOT NULL,
    AccountId        INT NOT NULL FOREIGN KEY REFERENCES ChartOfAccounts(AccountId),
    ProjectId        INT NULL FOREIGN KEY REFERENCES Projects(ProjectId),
    DebitAmount      DECIMAL(18,2) NOT NULL DEFAULT 0,
    CreditAmount     DECIMAL(18,2) NOT NULL DEFAULT 0,
    FcyAmount        DECIMAL(18,2) NULL,
    ExchangeRate     DECIMAL(18,6) NULL,
    Description      NVARCHAR(MAX) NULL,
    CONSTRAINT CK_JED_OneSided CHECK (
        (DebitAmount > 0 AND CreditAmount = 0) OR
        (CreditAmount > 0 AND DebitAmount = 0)
    )
);
GO
CREATE INDEX IX_JED_Account ON JournalEntryDetails(AccountId);
CREATE INDEX IX_JED_Entry ON JournalEntryDetails(JournalEntryId);
GO

/* =========================================================================
   3) الخزائن والبنوك (توحيد الشيتات الستة: دمجت Bank/Cash في جدول واحد)
   ========================================================================= */

CREATE TABLE TreasuryAccounts (
    TreasuryAccountId INT IDENTITY(1,1) PRIMARY KEY,
    NameAr            NVARCHAR(200) NOT NULL,        -- مثال: "البنك التجاري جنيه مصري"
    AccountType       NVARCHAR(10) NOT NULL CHECK (AccountType IN ('Bank','Cash')),
    CurrencyCode      NVARCHAR(3) NOT NULL,
    BankAccountNumber NVARCHAR(50) NULL,
    GLAccountId       INT NOT NULL FOREIGN KEY REFERENCES ChartOfAccounts(AccountId),
    IsActive          BIT NOT NULL DEFAULT 1
);
GO

-- حركات الخزائن/البنوك (بديل الستة شيتات)
CREATE TABLE TreasuryTransactions (
    TransactionId     BIGINT IDENTITY(1,1) PRIMARY KEY,
    TreasuryAccountId INT NOT NULL FOREIGN KEY REFERENCES TreasuryAccounts(TreasuryAccountId),
    TransactionDate   DATE NOT NULL,
    Inflow            DECIMAL(18,2) NOT NULL DEFAULT 0,
    Outflow           DECIMAL(18,2) NOT NULL DEFAULT 0,
    Description       NVARCHAR(500) NULL,
    VoucherNo         NVARCHAR(50) NULL,
    Status            NVARCHAR(30) NULL,              -- مثال: "تمويل"
    RecipientName     NVARCHAR(200) NULL,
    ProjectId         INT NULL FOREIGN KEY REFERENCES Projects(ProjectId),
    JournalEntryId    INT NULL FOREIGN KEY REFERENCES JournalEntries(JournalEntryId),
    CreatedAt         DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO
CREATE INDEX IX_TreasuryTx_Account_Date ON TreasuryTransactions(TreasuryAccountId, TransactionDate);
GO

-- مذكرات تسوية البنك (رأس)
CREATE TABLE BankReconciliations (
    ReconciliationId  INT IDENTITY(1,1) PRIMARY KEY,
    TreasuryAccountId INT NOT NULL FOREIGN KEY REFERENCES TreasuryAccounts(TreasuryAccountId),
    ReconciliationDate DATE NOT NULL,
    BookBalance       DECIMAL(18,2) NOT NULL,
    StatementBalance  DECIMAL(18,2) NOT NULL,
    Difference        AS (StatementBalance - BookBalance) PERSISTED,
    PreparedBy        INT NULL,                        -- FK Users
    Notes             NVARCHAR(500) NULL,
    CreatedAt         DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

-- تفاصيل مذكرة التسوية (بنود كشف البنك)
CREATE TABLE BankReconciliationLines (
    LineId            BIGINT IDENTITY(1,1) PRIMARY KEY,
    ReconciliationId  INT NOT NULL FOREIGN KEY REFERENCES BankReconciliations(ReconciliationId),
    TransactionDate   DATE NULL,
    Inflow            DECIMAL(18,2) NOT NULL DEFAULT 0,
    Outflow           DECIMAL(18,2) NOT NULL DEFAULT 0,
    Description       NVARCHAR(500) NULL,
    CheckNo           NVARCHAR(30) NULL,
    Status            NVARCHAR(30) NULL,
    Recipient         NVARCHAR(200) NULL,
    IsMatched         BIT NOT NULL DEFAULT 0
);
GO

/* =========================================================================
   4) المستفيدون والشيكات
   ========================================================================= */

-- المستفيدون/الموردون (جدول جديد لدعم lookup باسم الحساب في شاشة الشيكات)
CREATE TABLE Beneficiaries (
    BeneficiaryId     INT IDENTITY(1,1) PRIMARY KEY,
    Code              NVARCHAR(30) NOT NULL UNIQUE,
    NameAr            NVARCHAR(200) NOT NULL,
    LinkedAccountId   INT NULL FOREIGN KEY REFERENCES ChartOfAccounts(AccountId),
    DefaultProjectId  INT NULL FOREIGN KEY REFERENCES Projects(ProjectId),
    BankAccountNumber NVARCHAR(50) NULL,
    IsActive          BIT NOT NULL DEFAULT 1
);
GO

-- سجل الشيكات (بديل الثلاثة شيتات)
CREATE TABLE Checks (
    CheckId           BIGINT IDENTITY(1,1) PRIMARY KEY,
    TreasuryAccountId INT NOT NULL FOREIGN KEY REFERENCES TreasuryAccounts(TreasuryAccountId),
    CheckBookNo       NVARCHAR(20) NOT NULL,
    SequenceNo        INT NOT NULL,
    CheckNo           NVARCHAR(30) NULL,
    CheckDate         DATE NULL,
    BeneficiaryId     INT NOT NULL FOREIGN KEY REFERENCES Beneficiaries(BeneficiaryId),
    Amount            DECIMAL(18,2) NULL,
    PurchaseOrderNo   NVARCHAR(50) NULL,
    ProjectId         INT NULL FOREIGN KEY REFERENCES Projects(ProjectId),
    Description       NVARCHAR(500) NULL,
    PrintDate         DATE NULL,
    DeliveryDate      DATE NULL,
    CashDate          DATE NULL,
    Status            NVARCHAR(20) NOT NULL DEFAULT N'جديد'
        CHECK (Status IN (N'جديد',N'مطبوع',N'تم التسليم',N'تم الصرف',N'ملغي',N'مرتد')),
    CreatedAt         DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT UQ_Checks_BankBook UNIQUE (TreasuryAccountId, CheckBookNo, SequenceNo)
);
GO
CREATE INDEX IX_Checks_Beneficiary ON Checks(BeneficiaryId);
GO

-- سجل تغييرات حالة الشيك
CREATE TABLE CheckStatusHistory (
    HistoryId   BIGINT IDENTITY(1,1) PRIMARY KEY,
    CheckId     BIGINT NOT NULL FOREIGN KEY REFERENCES Checks(CheckId),
    OldStatus   NVARCHAR(20) NULL,
    NewStatus   NVARCHAR(20) NOT NULL,
    ChangedBy   INT NULL,                              -- FK Users
    ChangedAt   DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

-- قوالب طباعة الشيكات (إحداثيات لكل بنك)
CREATE TABLE CheckPrintTemplates (
    TemplateId        INT IDENTITY(1,1) PRIMARY KEY,
    TreasuryAccountId INT NOT NULL FOREIGN KEY REFERENCES TreasuryAccounts(TreasuryAccountId),
    FieldName         NVARCHAR(50) NOT NULL,            -- BeneficiaryName, AmountNumeric, AmountInWords, Date...
    PosX              DECIMAL(10,2) NOT NULL,
    PosY              DECIMAL(10,2) NOT NULL,
    FontSize          DECIMAL(5,2) NOT NULL DEFAULT 11,
    Alignment         NVARCHAR(10) NOT NULL DEFAULT 'Left' CHECK (Alignment IN ('Left','Right','Center')),
    SpellPiastres     BIT NOT NULL DEFAULT 1,            -- قرار: القروش تُكتب بالحروف دايمًا ضمن سطر التفقيط
    CONSTRAINT UQ_CheckPrintTemplates UNIQUE (TreasuryAccountId, FieldName)
);
GO

/* =========================================================================
   5) المستخدمون والصلاحيات
   ========================================================================= */

CREATE TABLE Users (
    UserId           INT IDENTITY(1,1) PRIMARY KEY,
    Username         NVARCHAR(50) NOT NULL UNIQUE,
    PasswordHash     VARBINARY(256) NOT NULL,
    FullName         NVARCHAR(150) NOT NULL,
    IsActive         BIT NOT NULL DEFAULT 1,
    LastLoginAt      DATETIME2 NULL,
    FailedLoginCount INT NOT NULL DEFAULT 0,
    LockedUntil      DATETIME2 NULL,
    TokenVersion     INT NOT NULL DEFAULT 0,
    CreatedAt        DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE Roles (
    RoleId     INT IDENTITY(1,1) PRIMARY KEY,
    RoleName   NVARCHAR(100) NOT NULL UNIQUE
);
GO

-- مثال: (JournalEntries, Post) / (Checks, Print) / (BankReconciliations, Approve)
CREATE TABLE Permissions (
    PermissionId INT IDENTITY(1,1) PRIMARY KEY,
    ScreenCode   NVARCHAR(50) NOT NULL,
    ActionCode   NVARCHAR(30) NOT NULL,                -- View, Add, Edit, Delete, Post, Approve, Print
    CONSTRAINT UQ_Permissions UNIQUE (ScreenCode, ActionCode)
);
GO

CREATE TABLE RolePermissions (
    RoleId       INT NOT NULL FOREIGN KEY REFERENCES Roles(RoleId),
    PermissionId INT NOT NULL FOREIGN KEY REFERENCES Permissions(PermissionId),
    PRIMARY KEY (RoleId, PermissionId)
);
GO

CREATE TABLE UserRoles (
    UserId INT NOT NULL FOREIGN KEY REFERENCES Users(UserId),
    RoleId INT NOT NULL FOREIGN KEY REFERENCES Roles(RoleId),
    PRIMARY KEY (UserId, RoleId)
);
GO

-- تخصيص فردي فوق الدور: IsAllowed=1 يمنح صلاحية مش موجودة في الدور،
-- IsAllowed=0 يستثني المستخدم من صلاحية موجودة في دوره. صف غير موجود = اتبع الدور.
CREATE TABLE UserPermissions (
    UserId       INT NOT NULL FOREIGN KEY REFERENCES Users(UserId),
    PermissionId INT NOT NULL FOREIGN KEY REFERENCES Permissions(PermissionId),
    IsAllowed    BIT NOT NULL,
    PRIMARY KEY (UserId, PermissionId)
);
GO

CREATE TABLE AuditLog (
    AuditId     BIGINT IDENTITY(1,1) PRIMARY KEY,
    UserId      INT NULL FOREIGN KEY REFERENCES Users(UserId),
    ActionType  NVARCHAR(30) NOT NULL,                 -- Create, Update, Delete, Post, Approve, Print
    EntityName  NVARCHAR(100) NOT NULL,
    EntityId    NVARCHAR(50) NULL,
    OldValue    NVARCHAR(MAX) NULL,
    NewValue    NVARCHAR(MAX) NULL,
    Timestamp   DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

/* =========================================================================
   6) ربط JournalEntries بجدول Users بعد إنشائه
   ========================================================================= */

ALTER TABLE JournalEntries
    ADD CONSTRAINT FK_JournalEntries_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Users(UserId),
        CONSTRAINT FK_JournalEntries_PostedBy  FOREIGN KEY (PostedBy)  REFERENCES Users(UserId);
GO
ALTER TABLE BankReconciliations
    ADD CONSTRAINT FK_BankRecon_PreparedBy FOREIGN KEY (PreparedBy) REFERENCES Users(UserId);
GO
ALTER TABLE CheckStatusHistory
    ADD CONSTRAINT FK_CheckHistory_ChangedBy FOREIGN KEY (ChangedBy) REFERENCES Users(UserId);
GO

/* =========================================================================
   7) View أساسي: ميزان المراجعة (بديل شيتي Trial balance + ميزان مراجعة)
   ========================================================================= */

CREATE VIEW vw_TrialBalance AS
SELECT
    coa.AccountId,
    coa.AccountCode,
    coa.AccountNameAr,
    ac.NameAr                                            AS Classification,
    ac.StatementType,
    coa.OpeningDebit,
    coa.OpeningCredit,
    ISNULL(SUM(jed.DebitAmount), 0)                       AS PeriodDebit,
    ISNULL(SUM(jed.CreditAmount), 0)                      AS PeriodCredit,
    coa.OpeningDebit  + ISNULL(SUM(jed.DebitAmount), 0)    AS TotalDebit,
    coa.OpeningCredit + ISNULL(SUM(jed.CreditAmount), 0)   AS TotalCredit,
    CASE WHEN (coa.OpeningDebit  + ISNULL(SUM(jed.DebitAmount),0))
            > (coa.OpeningCredit + ISNULL(SUM(jed.CreditAmount),0))
         THEN (coa.OpeningDebit  + ISNULL(SUM(jed.DebitAmount),0))
            - (coa.OpeningCredit + ISNULL(SUM(jed.CreditAmount),0))
         ELSE 0 END                                        AS DebitBalance,
    CASE WHEN (coa.OpeningCredit + ISNULL(SUM(jed.CreditAmount),0))
            > (coa.OpeningDebit  + ISNULL(SUM(jed.DebitAmount),0))
         THEN (coa.OpeningCredit + ISNULL(SUM(jed.CreditAmount),0))
            - (coa.OpeningDebit  + ISNULL(SUM(jed.DebitAmount),0))
         ELSE 0 END                                        AS CreditBalance
FROM ChartOfAccounts coa
JOIN AccountClassifications ac ON ac.ClassificationId = coa.ClassificationId
LEFT JOIN JournalEntryDetails jed
       ON jed.AccountId = coa.AccountId
JOIN JournalEntries je ON je.JournalEntryId = jed.JournalEntryId AND je.Status = 'Posted'
GROUP BY coa.AccountId, coa.AccountCode, coa.AccountNameAr, ac.NameAr, ac.StatementType,
         coa.OpeningDebit, coa.OpeningCredit;
GO

/* =========================================================================
   View: الصلاحية الفعلية لكل مستخدم (الدور + التخصيص الفردي فوقه)
   ========================================================================= */

CREATE VIEW vw_EffectivePermissions AS
SELECT
    u.UserId,
    p.PermissionId,
    p.ScreenCode,
    p.ActionCode,
    CASE
        WHEN up.IsAllowed IS NOT NULL THEN up.IsAllowed   -- التخصيص الفردي أقوى لو موجود
        WHEN rp.PermissionId IS NOT NULL THEN CAST(1 AS BIT) -- وإلا اتبع الدور
        ELSE CAST(0 AS BIT)
    END AS IsAllowed
FROM Users u
CROSS JOIN Permissions p
LEFT JOIN UserRoles ur ON ur.UserId = u.UserId
LEFT JOIN RolePermissions rp ON rp.RoleId = ur.RoleId AND rp.PermissionId = p.PermissionId
LEFT JOIN UserPermissions up ON up.UserId = u.UserId AND up.PermissionId = p.PermissionId;
GO

/* =========================================================================
   ملاحظات تنفيذ:
   - شغّل السكريبت ده مرة واحدة فقط (CREATE DATABASE في الأول).
   - بعد التنفيذ: عبّي AccountClassifications وFinancialStatementLines يدويًا
     بالتصنيفات الموحّدة (بعد حل تكرار الإملاء في الملف الأصلي).
   - أداة الاستيراد من Excel (الخطوة الجاية) هتعبي Companies/FiscalYears مبدئيًا
     ثم ChartOfAccounts من شيت Trial balance ثم باقي الشيتات.
   ========================================================================= */
