-- Migration PostgreSQL: سجل المراجعة والتحليلات
-- ينشئ جدول التدقيق إذا كان مفقودًا، دون التأثير على جدول موجود أو بياناته.
CREATE TABLE IF NOT EXISTS "AuditLog" (
    "AuditId" BIGSERIAL PRIMARY KEY,
    "UserId" INTEGER NULL REFERENCES "Users" ("UserId") ON DELETE SET NULL,
    "ActionType" VARCHAR(30) NOT NULL,
    "EntityName" VARCHAR(100) NOT NULL,
    "EntityId" VARCHAR(50) NULL,
    "OldValue" TEXT NULL,
    "NewValue" TEXT NULL,
    "Timestamp" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "IpAddress" VARCHAR(45) NULL
);

ALTER TABLE "AuditLog" ADD COLUMN IF NOT EXISTS "IpAddress" VARCHAR(45);
CREATE INDEX IF NOT EXISTS "IX_AuditLog_Timestamp_UserId" ON "AuditLog" ("Timestamp", "UserId");

-- إضافة الشاشتين إلى مجموعة التقارير؛ آمن عند إعادة التشغيل.
INSERT INTO "Sections" ("Code", "NameEn", "NameAr", "SortOrder", "IsActive")
SELECT 'REPORTS', 'Reports', 'التقارير', 2, TRUE
WHERE NOT EXISTS (SELECT 1 FROM "Sections" WHERE "Code"='REPORTS');

INSERT INTO "Screens" ("SectionId", "ScreenCode", "TitleEn", "TitleAr", "Route", "SortOrder", "IsActive")
SELECT s."SectionId", v.code, v.title_en, v.title_ar, v.route, v.sort_order, TRUE
FROM "Sections" s CROSS JOIN (VALUES
 ('AuditLogs','Audit Logs','سجل المراجعة والنشاطات','/audit-logs',20),
 ('AnalyticsReports','Reports & Analytics','التقارير والرسوم البيانية','/reports',30)
) AS v(code,title_en,title_ar,route,sort_order)
WHERE s."Code"='REPORTS' AND NOT EXISTS (SELECT 1 FROM "Screens" x WHERE x."ScreenCode"=v.code);

INSERT INTO "Permissions" ("ScreenCode", "ActionCode")
SELECT x.code, 'View' FROM (VALUES ('AuditLogs'),('AnalyticsReports')) AS x(code)
WHERE NOT EXISTS (SELECT 1 FROM "Permissions" p WHERE p."ScreenCode"=x.code AND p."ActionCode"='View');

-- مهم: منح صلاحية View للدور المناسب يتم حسب سياسة الشركة. لا تُمنح تلقائيًا لكل المستخدمين.
