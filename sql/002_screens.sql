/* =========================================================================
   002 — الأقسام والشاشات (مصدر بيانات الداشبورد)
   شغّله بعد financial_system_schema.sql
   ScreenCode هنا = نفس ScreenCode في جدول Permissions
   ========================================================================= */
USE FinancialSystem;
GO

CREATE TABLE Sections (
    SectionId   INT IDENTITY(1,1) PRIMARY KEY,
    Code        NVARCHAR(50)  NOT NULL UNIQUE,
    NameEn      NVARCHAR(150) NOT NULL,
    NameAr      NVARCHAR(150) NULL,
    SortOrder   INT NOT NULL DEFAULT 0,
    IsActive    BIT NOT NULL DEFAULT 1
);
GO

CREATE TABLE Screens (
    ScreenId    INT IDENTITY(1,1) PRIMARY KEY,
    SectionId   INT NOT NULL FOREIGN KEY REFERENCES Sections(SectionId),
    ScreenCode  NVARCHAR(50)  NOT NULL UNIQUE,
    TitleEn     NVARCHAR(150) NOT NULL,
    TitleAr     NVARCHAR(150) NULL,
    Route       NVARCHAR(200) NOT NULL,
    SortOrder   INT NOT NULL DEFAULT 0,
    IsActive    BIT NOT NULL DEFAULT 1
);
GO
CREATE INDEX IX_Screens_Section ON Screens(SectionId);
GO

-- أول شاشة (الباقي بيتضاف مع كل شاشة جديدة تتبني)
INSERT INTO Sections (Code, NameEn, NameAr, SortOrder) VALUES (N'ACCOUNTING', N'Accounting', N'الحسابات', 1);
INSERT INTO Screens (SectionId, ScreenCode, TitleEn, TitleAr, Route, SortOrder)
SELECT SectionId, N'ChartOfAccounts', N'Chart of Accounts', N'شجرة الحسابات', N'/accounts', 1
FROM Sections WHERE Code = N'ACCOUNTING';
GO
