--
-- PostgreSQL database dump
--

\restrict 1bEmt8DVo9JzELtefTKtuSZAAZjqNr1tQpNRWYqrM6e8E0UW23uVURpeCIQr6p5

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

-- Started on 2026-11-05 15:18:35

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 17968)
-- Name: AccountClassifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."AccountClassifications" (
    "ClassificationId" integer NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "StatementType" character varying(30) NOT NULL
);


--
-- TOC entry 223 (class 1259 OID 17967)
-- Name: AccountClassifications_ClassificationId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."AccountClassifications_ClassificationId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5631 (class 0 OID 0)
-- Dependencies: 223
-- Name: AccountClassifications_ClassificationId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."AccountClassifications_ClassificationId_seq" OWNED BY public."AccountClassifications"."ClassificationId";


--
-- TOC entry 247 (class 1259 OID 18119)
-- Name: AuditLog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."AuditLog" (
    "AuditId" bigint NOT NULL,
    "UserId" integer,
    "ActionType" character varying(30) NOT NULL,
    "EntityName" character varying(100) NOT NULL,
    "EntityId" character varying(50),
    "OldValue" text,
    "NewValue" text,
    "Timestamp" timestamp without time zone NOT NULL,
    "IpAddress" character varying(45)
);


--
-- TOC entry 246 (class 1259 OID 18118)
-- Name: AuditLog_AuditId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."AuditLog_AuditId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5632 (class 0 OID 0)
-- Dependencies: 246
-- Name: AuditLog_AuditId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."AuditLog_AuditId_seq" OWNED BY public."AuditLog"."AuditId";


--
-- TOC entry 293 (class 1259 OID 18664)
-- Name: BankReconciliationLines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."BankReconciliationLines" (
    "LineId" bigint NOT NULL,
    "ReconciliationId" integer NOT NULL,
    "TransactionDate" date,
    "Inflow" numeric(18,2) NOT NULL,
    "Outflow" numeric(18,2) NOT NULL,
    "Description" character varying(500),
    "CheckNo" character varying(30),
    "Status" character varying(30),
    "Recipient" character varying(200),
    "IsMatched" boolean NOT NULL
);


--
-- TOC entry 292 (class 1259 OID 18663)
-- Name: BankReconciliationLines_LineId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."BankReconciliationLines_LineId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5633 (class 0 OID 0)
-- Dependencies: 292
-- Name: BankReconciliationLines_LineId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."BankReconciliationLines_LineId_seq" OWNED BY public."BankReconciliationLines"."LineId";


--
-- TOC entry 271 (class 1259 OID 18378)
-- Name: BankReconciliations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."BankReconciliations" (
    "ReconciliationId" integer NOT NULL,
    "TreasuryAccountId" integer NOT NULL,
    "ReconciliationDate" date NOT NULL,
    "BookBalance" numeric(18,2) NOT NULL,
    "StatementBalance" numeric(18,2) NOT NULL,
    "Difference" numeric(18,2) GENERATED ALWAYS AS (("StatementBalance" - "BookBalance")) STORED NOT NULL,
    "PreparedBy" integer,
    "Notes" character varying(500),
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 270 (class 1259 OID 18377)
-- Name: BankReconciliations_ReconciliationId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."BankReconciliations_ReconciliationId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5634 (class 0 OID 0)
-- Dependencies: 270
-- Name: BankReconciliations_ReconciliationId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."BankReconciliations_ReconciliationId_seq" OWNED BY public."BankReconciliations"."ReconciliationId";


--
-- TOC entry 261 (class 1259 OID 18266)
-- Name: Beneficiaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Beneficiaries" (
    "BeneficiaryId" integer NOT NULL,
    "Code" character varying(30) NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "LinkedAccountId" integer,
    "DefaultProjectId" integer,
    "BankAccountNumber" character varying(50),
    "IsActive" boolean NOT NULL
);


--
-- TOC entry 260 (class 1259 OID 18265)
-- Name: Beneficiaries_BeneficiaryId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Beneficiaries_BeneficiaryId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5635 (class 0 OID 0)
-- Dependencies: 260
-- Name: Beneficiaries_BeneficiaryId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Beneficiaries_BeneficiaryId_seq" OWNED BY public."Beneficiaries"."BeneficiaryId";


--
-- TOC entry 318 (class 1259 OID 19242)
-- Name: CatalogItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."CatalogItems" (
    "CatalogItemId" integer NOT NULL,
    "Code" character varying(50) NOT NULL,
    "Name" character varying(250) NOT NULL,
    "Unit" character varying(30) NOT NULL,
    "Category" character varying(100),
    "DefaultUnitPrice" numeric(18,4) NOT NULL,
    "RevenueAccountId" integer,
    "ExpenseAccountId" integer,
    "InventoryAccountId" integer,
    "InventoryItemId" integer,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 317 (class 1259 OID 19241)
-- Name: CatalogItems_CatalogItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."CatalogItems_CatalogItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5636 (class 0 OID 0)
-- Dependencies: 317
-- Name: CatalogItems_CatalogItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."CatalogItems_CatalogItemId_seq" OWNED BY public."CatalogItems"."CatalogItemId";


--
-- TOC entry 242 (class 1259 OID 18055)
-- Name: ChartOfAccounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ChartOfAccounts" (
    "AccountId" integer NOT NULL,
    "AccountCode" character varying(30) NOT NULL,
    "AccountNameAr" character varying(300) NOT NULL,
    "ParentAccountId" integer,
    "ClassificationId" integer NOT NULL,
    "NormalBalance" character(2) NOT NULL,
    "OpeningDebit" numeric(18,2) NOT NULL,
    "OpeningCredit" numeric(18,2) NOT NULL,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "StatementType" character varying(30)
);


--
-- TOC entry 5637 (class 0 OID 0)
-- Dependencies: 242
-- Name: COLUMN "ChartOfAccounts"."StatementType"; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public."ChartOfAccounts"."StatementType" IS 'Per-account financial statement override: BalanceSheet, IncomeStatement, or empty string when unresolved; NULL inherits legacy classification type.';


--
-- TOC entry 241 (class 1259 OID 18054)
-- Name: ChartOfAccounts_AccountId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ChartOfAccounts_AccountId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5638 (class 0 OID 0)
-- Dependencies: 241
-- Name: ChartOfAccounts_AccountId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ChartOfAccounts_AccountId_seq" OWNED BY public."ChartOfAccounts"."AccountId";


--
-- TOC entry 277 (class 1259 OID 18457)
-- Name: CheckPrintTemplates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."CheckPrintTemplates" (
    "TemplateId" integer NOT NULL,
    "TreasuryAccountId" integer NOT NULL,
    "FieldName" character varying(50) NOT NULL,
    "PosX" numeric(10,2) NOT NULL,
    "PosY" numeric(10,2) NOT NULL,
    "FontSize" numeric(5,2) NOT NULL,
    "Alignment" character varying(10) NOT NULL,
    "SpellPiastres" boolean NOT NULL,
    "TextValue" character varying(200)
);


--
-- TOC entry 276 (class 1259 OID 18456)
-- Name: CheckPrintTemplates_TemplateId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."CheckPrintTemplates_TemplateId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5639 (class 0 OID 0)
-- Dependencies: 276
-- Name: CheckPrintTemplates_TemplateId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."CheckPrintTemplates_TemplateId_seq" OWNED BY public."CheckPrintTemplates"."TemplateId";


--
-- TOC entry 327 (class 1259 OID 19833)
-- Name: CheckSignatories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."CheckSignatories" (
    "SignatoryId" integer NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "JobTitle" character varying(150),
    "TreasuryAccountId" integer,
    "IsActive" boolean NOT NULL,
    "SortOrder" integer NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "UpdatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 326 (class 1259 OID 19832)
-- Name: CheckSignatories_SignatoryId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."CheckSignatories_SignatoryId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5640 (class 0 OID 0)
-- Dependencies: 326
-- Name: CheckSignatories_SignatoryId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."CheckSignatories_SignatoryId_seq" OWNED BY public."CheckSignatories"."SignatoryId";


--
-- TOC entry 295 (class 1259 OID 18678)
-- Name: CheckStatusHistory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."CheckStatusHistory" (
    "HistoryId" bigint NOT NULL,
    "CheckId" bigint NOT NULL,
    "OldStatus" character varying(20),
    "NewStatus" character varying(20) NOT NULL,
    "ChangedBy" integer,
    "ChangedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 294 (class 1259 OID 18677)
-- Name: CheckStatusHistory_HistoryId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."CheckStatusHistory_HistoryId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5641 (class 0 OID 0)
-- Dependencies: 294
-- Name: CheckStatusHistory_HistoryId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."CheckStatusHistory_HistoryId_seq" OWNED BY public."CheckStatusHistory"."HistoryId";


--
-- TOC entry 273 (class 1259 OID 18398)
-- Name: Checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Checks" (
    "CheckId" bigint NOT NULL,
    "TreasuryAccountId" integer NOT NULL,
    "CheckBookNo" character varying(20) NOT NULL,
    "SequenceNo" integer NOT NULL,
    "CheckNo" character varying(30),
    "CheckDate" date,
    "BeneficiaryId" integer NOT NULL,
    "Amount" numeric(18,2),
    "PurchaseOrderNo" character varying(50),
    "ProjectId" integer,
    "Description" character varying(500),
    "PrintDate" date,
    "DeliveryDate" date,
    "CashDate" date,
    "Status" character varying(20) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "SettlementId" integer
);


--
-- TOC entry 272 (class 1259 OID 18397)
-- Name: Checks_CheckId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Checks_CheckId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5642 (class 0 OID 0)
-- Dependencies: 272
-- Name: Checks_CheckId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Checks_CheckId_seq" OWNED BY public."Checks"."CheckId";


--
-- TOC entry 218 (class 1259 OID 17943)
-- Name: Companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Companies" (
    "CompanyId" integer NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "NameEn" character varying(200),
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "TaxNumber" character varying(50),
    "CommercialRegister" character varying(50),
    "AddressAr" character varying(500),
    "Phone" character varying(50),
    "Email" character varying(200),
    "Website" character varying(200),
    "LogoData" text
);


--
-- TOC entry 217 (class 1259 OID 17942)
-- Name: Companies_CompanyId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Companies_CompanyId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5643 (class 0 OID 0)
-- Dependencies: 217
-- Name: Companies_CompanyId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Companies_CompanyId_seq" OWNED BY public."Companies"."CompanyId";


--
-- TOC entry 287 (class 1259 OID 18550)
-- Name: ContractAccountingConfig; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractAccountingConfig" (
    "ConfigId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "SettlementSide" character varying(20) NOT NULL,
    "CompanyId" integer NOT NULL,
    "FiscalYearId" integer NOT NULL,
    "ControlAccountId" integer NOT NULL,
    "WorkAccountId" integer NOT NULL,
    "RetentionAccountId" integer,
    "AdvanceAccountId" integer,
    "TaxAccountId" integer,
    "VatAccountId" integer,
    "DefaultVatRate" numeric(9,4) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 286 (class 1259 OID 18549)
-- Name: ContractAccountingConfig_ConfigId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractAccountingConfig_ConfigId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5644 (class 0 OID 0)
-- Dependencies: 286
-- Name: ContractAccountingConfig_ConfigId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractAccountingConfig_ConfigId_seq" OWNED BY public."ContractAccountingConfig"."ConfigId";


--
-- TOC entry 279 (class 1259 OID 18471)
-- Name: ContractAddendums; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractAddendums" (
    "AddendumId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "AddendumNo" character varying(50) NOT NULL,
    "AddendumDate" date NOT NULL,
    "Description" character varying(500) NOT NULL,
    "ValueChange" numeric(18,2) NOT NULL,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 278 (class 1259 OID 18470)
-- Name: ContractAddendums_AddendumId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractAddendums_AddendumId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5645 (class 0 OID 0)
-- Dependencies: 278
-- Name: ContractAddendums_AddendumId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractAddendums_AddendumId_seq" OWNED BY public."ContractAddendums"."AddendumId";


--
-- TOC entry 299 (class 1259 OID 18717)
-- Name: ContractAttachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractAttachments" (
    "AttachmentId" integer NOT NULL,
    "ContractId" integer,
    "SettlementId" integer,
    "Category" character varying(80) NOT NULL,
    "OriginalFilename" character varying(255) NOT NULL,
    "ContentType" character varying(120) NOT NULL,
    "SizeBytes" integer NOT NULL,
    "FileContent" bytea NOT NULL,
    "Notes" character varying(500),
    "UploadedBy" integer,
    "UploadedAt" timestamp without time zone NOT NULL,
    CONSTRAINT "CK_ContractAttachments_OneParent" CHECK (((("ContractId" IS NOT NULL) AND ("SettlementId" IS NULL)) OR (("ContractId" IS NULL) AND ("SettlementId" IS NOT NULL))))
);


--
-- TOC entry 298 (class 1259 OID 18716)
-- Name: ContractAttachments_AttachmentId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractAttachments_AttachmentId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5646 (class 0 OID 0)
-- Dependencies: 298
-- Name: ContractAttachments_AttachmentId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractAttachments_AttachmentId_seq" OWNED BY public."ContractAttachments"."AttachmentId";


--
-- TOC entry 291 (class 1259 OID 18637)
-- Name: ContractChangeOrders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractChangeOrders" (
    "ChangeOrderId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "ChangeOrderNo" character varying(50) NOT NULL,
    "ChangeOrderDate" date NOT NULL,
    "Description" character varying(500) NOT NULL,
    "ValueChange" numeric(18,2) NOT NULL,
    "Status" character varying(20) NOT NULL,
    "CreatedBy" integer,
    "ApprovedBy" integer,
    "ApprovedAt" timestamp without time zone,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 290 (class 1259 OID 18636)
-- Name: ContractChangeOrders_ChangeOrderId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractChangeOrders_ChangeOrderId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5647 (class 0 OID 0)
-- Dependencies: 290
-- Name: ContractChangeOrders_ChangeOrderId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractChangeOrders_ChangeOrderId_seq" OWNED BY public."ContractChangeOrders"."ChangeOrderId";


--
-- TOC entry 285 (class 1259 OID 18529)
-- Name: ContractDeductionRules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractDeductionRules" (
    "RuleId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "SettlementSide" character varying(20) NOT NULL,
    "Code" character varying(50) NOT NULL,
    "NameAr" character varying(150) NOT NULL,
    "CalculationType" character varying(20) NOT NULL,
    "Rate" numeric(9,4) NOT NULL,
    "BaseType" character varying(30) NOT NULL,
    "PostingSide" character varying(10) NOT NULL,
    "CapAmount" numeric(18,2),
    "GLAccountId" integer,
    "IsActive" boolean NOT NULL,
    "SortOrder" integer NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    CONSTRAINT "CK_ContractDeductionRules_Rate" CHECK ((("Rate" >= (0)::numeric) AND (("CapAmount" IS NULL) OR ("CapAmount" >= (0)::numeric))))
);


--
-- TOC entry 284 (class 1259 OID 18528)
-- Name: ContractDeductionRules_RuleId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractDeductionRules_RuleId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5648 (class 0 OID 0)
-- Dependencies: 284
-- Name: ContractDeductionRules_RuleId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractDeductionRules_RuleId_seq" OWNED BY public."ContractDeductionRules"."RuleId";


--
-- TOC entry 283 (class 1259 OID 18511)
-- Name: ContractItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractItems" (
    "ItemId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "ItemNo" character varying(50) NOT NULL,
    "Description" character varying(500) NOT NULL,
    "Unit" character varying(30) NOT NULL,
    "Quantity" numeric(18,4) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CatalogItemId" integer,
    "AccountId" integer,
    "ProjectId" integer,
    CONSTRAINT "CK_ContractItems_NonNegative" CHECK ((("Quantity" >= (0)::numeric) AND ("UnitPrice" >= (0)::numeric)))
);


--
-- TOC entry 282 (class 1259 OID 18510)
-- Name: ContractItems_ItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractItems_ItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5649 (class 0 OID 0)
-- Dependencies: 282
-- Name: ContractItems_ItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractItems_ItemId_seq" OWNED BY public."ContractItems"."ItemId";


--
-- TOC entry 322 (class 1259 OID 19288)
-- Name: ContractRequestItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractRequestItems" (
    "RequestItemId" integer NOT NULL,
    "RequestId" integer NOT NULL,
    "CatalogItemId" integer,
    "ItemNo" character varying(50) NOT NULL,
    "Description" character varying(500) NOT NULL,
    "Unit" character varying(30) NOT NULL,
    "Quantity" numeric(18,4) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "AccountId" integer,
    "ProjectId" integer
);


--
-- TOC entry 321 (class 1259 OID 19287)
-- Name: ContractRequestItems_RequestItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractRequestItems_RequestItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5650 (class 0 OID 0)
-- Dependencies: 321
-- Name: ContractRequestItems_RequestItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractRequestItems_RequestItemId_seq" OWNED BY public."ContractRequestItems"."RequestItemId";


--
-- TOC entry 251 (class 1259 OID 18149)
-- Name: ContractRequests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractRequests" (
    "RequestId" integer NOT NULL,
    "RequestNo" character varying(50) NOT NULL,
    "RequestType" character varying(30) NOT NULL,
    "Title" character varying(250) NOT NULL,
    "CounterpartyName" character varying(200) NOT NULL,
    "ProjectId" integer,
    "EstimatedValue" numeric(18,2) NOT NULL,
    "Description" text,
    "Status" character varying(30) NOT NULL,
    "ReviewNotes" text,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "ReviewedBy" integer,
    "ReviewedAt" timestamp without time zone,
    "CounterpartyId" integer
);


--
-- TOC entry 250 (class 1259 OID 18148)
-- Name: ContractRequests_RequestId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractRequests_RequestId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5651 (class 0 OID 0)
-- Dependencies: 250
-- Name: ContractRequests_RequestId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractRequests_RequestId_seq" OWNED BY public."ContractRequests"."RequestId";


--
-- TOC entry 297 (class 1259 OID 18695)
-- Name: ContractSettlementItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractSettlementItems" (
    "SettlementItemId" integer NOT NULL,
    "SettlementId" integer NOT NULL,
    "ContractItemId" integer NOT NULL,
    "Quantity" numeric(18,4) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "Amount" numeric(18,2) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "AccountId" integer,
    "ProjectId" integer,
    CONSTRAINT "CK_ContractSettlementItems_Quantity" CHECK ((("Quantity" > (0)::numeric) AND ("UnitPrice" >= (0)::numeric)))
);


--
-- TOC entry 296 (class 1259 OID 18694)
-- Name: ContractSettlementItems_SettlementItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractSettlementItems_SettlementItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5652 (class 0 OID 0)
-- Dependencies: 296
-- Name: ContractSettlementItems_SettlementItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractSettlementItems_SettlementItemId_seq" OWNED BY public."ContractSettlementItems"."SettlementItemId";


--
-- TOC entry 289 (class 1259 OID 18605)
-- Name: ContractSettlements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ContractSettlements" (
    "SettlementId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "SettlementSide" character varying(20) NOT NULL,
    "SequenceNo" integer NOT NULL,
    "SettlementNo" character varying(50) NOT NULL,
    "SettlementDate" date NOT NULL,
    "CounterpartyName" character varying(200) NOT NULL,
    "WorkValue" numeric(18,2) NOT NULL,
    "CumulativeWorkValue" numeric(18,2) NOT NULL,
    "DeductionsJson" json NOT NULL,
    "VatAmount" numeric(18,2) NOT NULL,
    "NetAmount" numeric(18,2) NOT NULL,
    "Status" character varying(20) NOT NULL,
    "JournalEntryId" integer,
    "Notes" text,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CounterpartyId" integer,
    CONSTRAINT "CK_ContractSettlements_NonNegative" CHECK ((("WorkValue" >= (0)::numeric) AND ("NetAmount" >= (0)::numeric)))
);


--
-- TOC entry 288 (class 1259 OID 18604)
-- Name: ContractSettlements_SettlementId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ContractSettlements_SettlementId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5653 (class 0 OID 0)
-- Dependencies: 288
-- Name: ContractSettlements_SettlementId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ContractSettlements_SettlementId_seq" OWNED BY public."ContractSettlements"."SettlementId";


--
-- TOC entry 263 (class 1259 OID 18285)
-- Name: Contracts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Contracts" (
    "ContractId" integer NOT NULL,
    "RequestId" integer,
    "ContractNo" character varying(50) NOT NULL,
    "Title" character varying(250) NOT NULL,
    "ClientName" character varying(200) NOT NULL,
    "ProjectId" integer,
    "StartDate" date,
    "EndDate" date,
    "OriginalValue" numeric(18,2) NOT NULL,
    "Status" character varying(30) NOT NULL,
    "Notes" text,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CounterpartyId" integer
);


--
-- TOC entry 262 (class 1259 OID 18284)
-- Name: Contracts_ContractId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Contracts_ContractId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5654 (class 0 OID 0)
-- Dependencies: 262
-- Name: Contracts_ContractId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Contracts_ContractId_seq" OWNED BY public."Contracts"."ContractId";


--
-- TOC entry 308 (class 1259 OID 19050)
-- Name: Counterparties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Counterparties" (
    "CounterpartyId" integer NOT NULL,
    "Code" character varying(30) NOT NULL,
    "LegalName" character varying(250) NOT NULL,
    "PartyType" character varying(20) NOT NULL,
    "TaxNo" character varying(50),
    "CommercialRegistration" character varying(50),
    "Phone" character varying(50),
    "Email" character varying(200),
    "Address" character varying(500),
    "LinkedAccountId" integer,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "Name" character varying(250),
    "Roles" json,
    "AccountId" integer,
    "TaxNumber" character varying(50),
    "CommercialRegister" character varying(50),
    "Notes" text
);


--
-- TOC entry 307 (class 1259 OID 19049)
-- Name: Counterparties_CounterpartyId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Counterparties_CounterpartyId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5655 (class 0 OID 0)
-- Dependencies: 307
-- Name: Counterparties_CounterpartyId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Counterparties_CounterpartyId_seq" OWNED BY public."Counterparties"."CounterpartyId";


--
-- TOC entry 305 (class 1259 OID 19024)
-- Name: CounterpartyAliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."CounterpartyAliases" (
    "AliasId" integer NOT NULL,
    "AliasName" character varying(200) NOT NULL,
    "CanonicalName" character varying(200) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CounterpartyId" integer
);


--
-- TOC entry 304 (class 1259 OID 19023)
-- Name: CounterpartyAliases_AliasId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."CounterpartyAliases_AliasId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5656 (class 0 OID 0)
-- Dependencies: 304
-- Name: CounterpartyAliases_AliasId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."CounterpartyAliases_AliasId_seq" OWNED BY public."CounterpartyAliases"."AliasId";


--
-- TOC entry 222 (class 1259 OID 17959)
-- Name: ExchangeRates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ExchangeRates" (
    "ExchangeRateId" integer NOT NULL,
    "CurrencyCode" character varying(3) NOT NULL,
    "RateDate" date NOT NULL,
    "RateToEGP" numeric(18,6) NOT NULL
);


--
-- TOC entry 221 (class 1259 OID 17958)
-- Name: ExchangeRates_ExchangeRateId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ExchangeRates_ExchangeRateId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5657 (class 0 OID 0)
-- Dependencies: 221
-- Name: ExchangeRates_ExchangeRateId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ExchangeRates_ExchangeRateId_seq" OWNED BY public."ExchangeRates"."ExchangeRateId";


--
-- TOC entry 275 (class 1259 OID 18424)
-- Name: FinancialChecks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."FinancialChecks" (
    "CheckId" bigint NOT NULL,
    "CheckNumber" character varying(50) NOT NULL,
    "CheckType" character varying(20) NOT NULL,
    "Amount" numeric(18,2) NOT NULL,
    "DueDate" date NOT NULL,
    "DraweeBank" character varying(200),
    "ProjectBrand" character varying(50) NOT NULL,
    "Status" character varying(30) NOT NULL,
    "PartyAccountId" integer NOT NULL,
    "TreasuryAccountId" integer NOT NULL,
    "JournalEntryId" integer,
    "Description" character varying(500),
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "ProjectId" integer
);


--
-- TOC entry 274 (class 1259 OID 18423)
-- Name: FinancialChecks_CheckId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."FinancialChecks_CheckId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5658 (class 0 OID 0)
-- Dependencies: 274
-- Name: FinancialChecks_CheckId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."FinancialChecks_CheckId_seq" OWNED BY public."FinancialChecks"."CheckId";


--
-- TOC entry 240 (class 1259 OID 18043)
-- Name: FinancialStatementLines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."FinancialStatementLines" (
    "LineId" integer NOT NULL,
    "StatementType" character varying(30) NOT NULL,
    "CaptionAr" character varying(200) NOT NULL,
    "SortOrder" integer NOT NULL,
    "ClassificationId" integer,
    "IsSubtotal" boolean NOT NULL
);


--
-- TOC entry 239 (class 1259 OID 18042)
-- Name: FinancialStatementLines_LineId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."FinancialStatementLines_LineId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5659 (class 0 OID 0)
-- Dependencies: 239
-- Name: FinancialStatementLines_LineId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."FinancialStatementLines_LineId_seq" OWNED BY public."FinancialStatementLines"."LineId";


--
-- TOC entry 238 (class 1259 OID 18031)
-- Name: FiscalYears; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."FiscalYears" (
    "FiscalYearId" integer NOT NULL,
    "CompanyId" integer NOT NULL,
    "StartDate" date NOT NULL,
    "EndDate" date NOT NULL,
    "IsClosed" boolean NOT NULL
);


--
-- TOC entry 237 (class 1259 OID 18030)
-- Name: FiscalYears_FiscalYearId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."FiscalYears_FiscalYearId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5660 (class 0 OID 0)
-- Dependencies: 237
-- Name: FiscalYears_FiscalYearId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."FiscalYears_FiscalYearId_seq" OWNED BY public."FiscalYears"."FiscalYearId";


--
-- TOC entry 236 (class 1259 OID 18023)
-- Name: InventoryItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."InventoryItems" (
    "ItemId" integer NOT NULL,
    "Code" character varying(50) NOT NULL,
    "Name" character varying(250) NOT NULL,
    "Category" character varying(100),
    "Unit" character varying(30) NOT NULL,
    "MinQuantity" numeric(18,3) NOT NULL,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 235 (class 1259 OID 18022)
-- Name: InventoryItems_ItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."InventoryItems_ItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5661 (class 0 OID 0)
-- Dependencies: 235
-- Name: InventoryItems_ItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."InventoryItems_ItemId_seq" OWNED BY public."InventoryItems"."ItemId";


--
-- TOC entry 253 (class 1259 OID 18174)
-- Name: InventoryMovements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."InventoryMovements" (
    "MovementId" integer NOT NULL,
    "MovementNo" character varying(60) NOT NULL,
    "ItemId" integer NOT NULL,
    "WarehouseId" integer NOT NULL,
    "MovementDate" date NOT NULL,
    "MovementType" character varying(20) NOT NULL,
    "Quantity" numeric(18,3) NOT NULL,
    "UnitCost" numeric(18,4) NOT NULL,
    "Reference" character varying(100),
    "Notes" text,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "DocumentNo" character varying(60),
    "AccountId" integer,
    "ProjectId" integer,
    "CatalogItemId" integer
);


--
-- TOC entry 252 (class 1259 OID 18173)
-- Name: InventoryMovements_MovementId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."InventoryMovements_MovementId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5662 (class 0 OID 0)
-- Dependencies: 252
-- Name: InventoryMovements_MovementId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."InventoryMovements_MovementId_seq" OWNED BY public."InventoryMovements"."MovementId";


--
-- TOC entry 234 (class 1259 OID 18015)
-- Name: InventoryWarehouses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."InventoryWarehouses" (
    "WarehouseId" integer NOT NULL,
    "Code" character varying(40) NOT NULL,
    "Name" character varying(200) NOT NULL,
    "Location" character varying(250),
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 233 (class 1259 OID 18014)
-- Name: InventoryWarehouses_WarehouseId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."InventoryWarehouses_WarehouseId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5663 (class 0 OID 0)
-- Dependencies: 233
-- Name: InventoryWarehouses_WarehouseId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."InventoryWarehouses_WarehouseId_seq" OWNED BY public."InventoryWarehouses"."WarehouseId";


--
-- TOC entry 324 (class 1259 OID 19454)
-- Name: ItemCatalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ItemCatalog" (
    "CatalogItemId" integer NOT NULL,
    "Code" character varying(50) NOT NULL,
    "Name" character varying(250) NOT NULL,
    "Unit" character varying(30) NOT NULL,
    "AccountId" integer NOT NULL,
    "InventoryItemId" integer,
    "IsActive" boolean NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 323 (class 1259 OID 19453)
-- Name: ItemCatalog_CatalogItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ItemCatalog_CatalogItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5664 (class 0 OID 0)
-- Dependencies: 323
-- Name: ItemCatalog_CatalogItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ItemCatalog_CatalogItemId_seq" OWNED BY public."ItemCatalog"."CatalogItemId";


--
-- TOC entry 257 (class 1259 OID 18219)
-- Name: JournalEntries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."JournalEntries" (
    "JournalEntryId" integer NOT NULL,
    "EntryNo" character varying(30) NOT NULL,
    "EntryDate" date NOT NULL,
    "CompanyId" integer NOT NULL,
    "FiscalYearId" integer NOT NULL,
    "Description" character varying(500),
    "Status" character varying(20) NOT NULL,
    "CreatedBy" integer,
    "PostedBy" integer,
    "PostedAt" timestamp without time zone,
    "CreatedAt" timestamp without time zone NOT NULL,
    "SourceType" character varying(40),
    "SourceId" integer,
    "ReferenceNo" character varying(150),
    "SourceSettlementId" integer
);


--
-- TOC entry 256 (class 1259 OID 18218)
-- Name: JournalEntries_JournalEntryId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."JournalEntries_JournalEntryId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5665 (class 0 OID 0)
-- Dependencies: 256
-- Name: JournalEntries_JournalEntryId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."JournalEntries_JournalEntryId_seq" OWNED BY public."JournalEntries"."JournalEntryId";


--
-- TOC entry 267 (class 1259 OID 18330)
-- Name: JournalEntryDetails; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."JournalEntryDetails" (
    "DetailId" integer NOT NULL,
    "JournalEntryId" integer NOT NULL,
    "LineNo" integer NOT NULL,
    "AccountId" integer NOT NULL,
    "ProjectId" integer,
    "DebitAmount" numeric(18,2) NOT NULL,
    "CreditAmount" numeric(18,2) NOT NULL,
    "FcyAmount" numeric(18,2),
    "ExchangeRate" numeric(18,6),
    "Description" text
);


--
-- TOC entry 266 (class 1259 OID 18329)
-- Name: JournalEntryDetails_DetailId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."JournalEntryDetails_DetailId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5666 (class 0 OID 0)
-- Dependencies: 266
-- Name: JournalEntryDetails_DetailId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."JournalEntryDetails_DetailId_seq" OWNED BY public."JournalEntryDetails"."DetailId";


--
-- TOC entry 230 (class 1259 OID 17997)
-- Name: Permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Permissions" (
    "PermissionId" integer NOT NULL,
    "ScreenCode" character varying(50) NOT NULL,
    "ActionCode" character varying(30) NOT NULL
);


--
-- TOC entry 229 (class 1259 OID 17996)
-- Name: Permissions_PermissionId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Permissions_PermissionId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5667 (class 0 OID 0)
-- Dependencies: 229
-- Name: Permissions_PermissionId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Permissions_PermissionId_seq" OWNED BY public."Permissions"."PermissionId";


--
-- TOC entry 281 (class 1259 OID 18491)
-- Name: ProgressBillings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."ProgressBillings" (
    "BillingId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "BillingNo" character varying(50) NOT NULL,
    "BillingDate" date NOT NULL,
    "WorkValue" numeric(18,2) NOT NULL,
    "RetentionAmount" numeric(18,2) NOT NULL,
    "AdvanceDeduction" numeric(18,2) NOT NULL,
    "OtherDeductions" numeric(18,2) NOT NULL,
    "NetAmount" numeric(18,2) NOT NULL,
    "Status" character varying(30) NOT NULL,
    "Notes" text,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 280 (class 1259 OID 18490)
-- Name: ProgressBillings_BillingId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."ProgressBillings_BillingId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5668 (class 0 OID 0)
-- Dependencies: 280
-- Name: ProgressBillings_BillingId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."ProgressBillings_BillingId_seq" OWNED BY public."ProgressBillings"."BillingId";


--
-- TOC entry 220 (class 1259 OID 17950)
-- Name: Projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Projects" (
    "ProjectId" integer NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "NameEn" character varying(200),
    "IsHeadOffice" boolean NOT NULL,
    "IsActive" boolean NOT NULL
);


--
-- TOC entry 219 (class 1259 OID 17949)
-- Name: Projects_ProjectId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Projects_ProjectId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5669 (class 0 OID 0)
-- Dependencies: 219
-- Name: Projects_ProjectId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Projects_ProjectId_seq" OWNED BY public."Projects"."ProjectId";


--
-- TOC entry 265 (class 1259 OID 18312)
-- Name: PurchaseOrderLines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."PurchaseOrderLines" (
    "LineId" integer NOT NULL,
    "PurchaseOrderId" integer NOT NULL,
    "ItemId" integer NOT NULL,
    "Quantity" numeric(18,3) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "ReceivedQuantity" numeric(18,3) NOT NULL,
    "CatalogItemId" integer,
    "AccountId" integer,
    "ProjectId" integer
);


--
-- TOC entry 264 (class 1259 OID 18311)
-- Name: PurchaseOrderLines_LineId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."PurchaseOrderLines_LineId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5670 (class 0 OID 0)
-- Dependencies: 264
-- Name: PurchaseOrderLines_LineId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."PurchaseOrderLines_LineId_seq" OWNED BY public."PurchaseOrderLines"."LineId";


--
-- TOC entry 255 (class 1259 OID 18199)
-- Name: PurchaseOrders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."PurchaseOrders" (
    "PurchaseOrderId" integer NOT NULL,
    "OrderNo" character varying(60) NOT NULL,
    "OrderDate" date NOT NULL,
    "SupplierName" character varying(250) NOT NULL,
    "WarehouseId" integer NOT NULL,
    "Status" character varying(20) NOT NULL,
    "Notes" text,
    "TotalAmount" numeric(18,2) NOT NULL,
    "CreatedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CounterpartyId" integer,
    "ProjectId" integer
);


--
-- TOC entry 254 (class 1259 OID 18198)
-- Name: PurchaseOrders_PurchaseOrderId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."PurchaseOrders_PurchaseOrderId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5671 (class 0 OID 0)
-- Dependencies: 254
-- Name: PurchaseOrders_PurchaseOrderId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."PurchaseOrders_PurchaseOrderId_seq" OWNED BY public."PurchaseOrders"."PurchaseOrderId";


--
-- TOC entry 316 (class 1259 OID 19167)
-- Name: PurchaseReturnLines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."PurchaseReturnLines" (
    "LineId" integer NOT NULL,
    "ReturnId" integer NOT NULL,
    "InvoiceLineId" integer NOT NULL,
    "Quantity" numeric(18,3) NOT NULL,
    "NetAmount" numeric(18,2) NOT NULL,
    "TaxAmount" numeric(18,2) NOT NULL
);


--
-- TOC entry 315 (class 1259 OID 19166)
-- Name: PurchaseReturnLines_LineId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."PurchaseReturnLines_LineId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5672 (class 0 OID 0)
-- Dependencies: 315
-- Name: PurchaseReturnLines_LineId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."PurchaseReturnLines_LineId_seq" OWNED BY public."PurchaseReturnLines"."LineId";


--
-- TOC entry 314 (class 1259 OID 19133)
-- Name: PurchaseReturns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."PurchaseReturns" (
    "ReturnId" integer NOT NULL,
    "ReturnNo" character varying(60) NOT NULL,
    "InvoiceId" integer NOT NULL,
    "ReturnDate" date NOT NULL,
    "Reason" character varying(500) NOT NULL,
    "TotalAmount" numeric(18,2) NOT NULL,
    "Status" character varying(20) NOT NULL,
    "JournalEntryId" integer,
    "CreatedBy" integer,
    "ApprovedBy" integer,
    "CreatedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 313 (class 1259 OID 19132)
-- Name: PurchaseReturns_ReturnId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."PurchaseReturns_ReturnId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5673 (class 0 OID 0)
-- Dependencies: 313
-- Name: PurchaseReturns_ReturnId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."PurchaseReturns_ReturnId_seq" OWNED BY public."PurchaseReturns"."ReturnId";


--
-- TOC entry 320 (class 1259 OID 19272)
-- Name: RecordAttachments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."RecordAttachments" (
    "AttachmentId" integer NOT NULL,
    "RecordType" character varying(50) NOT NULL,
    "RecordId" integer NOT NULL,
    "OriginalFilename" character varying(255) NOT NULL,
    "ContentType" character varying(120) NOT NULL,
    "SizeBytes" integer NOT NULL,
    "FileContent" bytea NOT NULL,
    "Notes" character varying(500),
    "UploadedBy" integer,
    "UploadedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 319 (class 1259 OID 19271)
-- Name: RecordAttachments_AttachmentId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."RecordAttachments_AttachmentId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5674 (class 0 OID 0)
-- Dependencies: 319
-- Name: RecordAttachments_AttachmentId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."RecordAttachments_AttachmentId_seq" OWNED BY public."RecordAttachments"."AttachmentId";


--
-- TOC entry 243 (class 1259 OID 18073)
-- Name: RolePermissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."RolePermissions" (
    "RoleId" integer NOT NULL,
    "PermissionId" integer NOT NULL
);


--
-- TOC entry 228 (class 1259 OID 17988)
-- Name: Roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Roles" (
    "RoleId" integer NOT NULL,
    "RoleName" character varying(100) NOT NULL
);


--
-- TOC entry 227 (class 1259 OID 17987)
-- Name: Roles_RoleId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Roles_RoleId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5675 (class 0 OID 0)
-- Dependencies: 227
-- Name: Roles_RoleId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Roles_RoleId_seq" OWNED BY public."Roles"."RoleId";


--
-- TOC entry 306 (class 1259 OID 19044)
-- Name: SchemaMigrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."SchemaMigrations" (
    "MigrationId" character varying(80) NOT NULL,
    "AppliedAt" timestamp without time zone NOT NULL
);


--
-- TOC entry 249 (class 1259 OID 18133)
-- Name: Screens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Screens" (
    "ScreenId" integer NOT NULL,
    "SectionId" integer NOT NULL,
    "ScreenCode" character varying(50) NOT NULL,
    "TitleEn" character varying(150) NOT NULL,
    "TitleAr" character varying(150),
    "Route" character varying(200) NOT NULL,
    "SortOrder" integer NOT NULL,
    "IsActive" boolean NOT NULL
);


--
-- TOC entry 248 (class 1259 OID 18132)
-- Name: Screens_ScreenId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Screens_ScreenId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5676 (class 0 OID 0)
-- Dependencies: 248
-- Name: Screens_ScreenId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Screens_ScreenId_seq" OWNED BY public."Screens"."ScreenId";


--
-- TOC entry 232 (class 1259 OID 18006)
-- Name: Sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Sections" (
    "SectionId" integer NOT NULL,
    "Code" character varying(50) NOT NULL,
    "NameEn" character varying(150) NOT NULL,
    "NameAr" character varying(150),
    "SortOrder" integer NOT NULL,
    "IsActive" boolean NOT NULL
);


--
-- TOC entry 231 (class 1259 OID 18005)
-- Name: Sections_SectionId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Sections_SectionId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5677 (class 0 OID 0)
-- Dependencies: 231
-- Name: Sections_SectionId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Sections_SectionId_seq" OWNED BY public."Sections"."SectionId";


--
-- TOC entry 312 (class 1259 OID 19110)
-- Name: SupplierInvoiceLines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."SupplierInvoiceLines" (
    "LineId" integer NOT NULL,
    "InvoiceId" integer NOT NULL,
    "PurchaseOrderLineId" integer NOT NULL,
    "AccountId" integer NOT NULL,
    "Quantity" numeric(18,3) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "NetAmount" numeric(18,2) NOT NULL,
    "TaxAmount" numeric(18,2) NOT NULL
);


--
-- TOC entry 311 (class 1259 OID 19109)
-- Name: SupplierInvoiceLines_LineId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."SupplierInvoiceLines_LineId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5678 (class 0 OID 0)
-- Dependencies: 311
-- Name: SupplierInvoiceLines_LineId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."SupplierInvoiceLines_LineId_seq" OWNED BY public."SupplierInvoiceLines"."LineId";


--
-- TOC entry 310 (class 1259 OID 19067)
-- Name: SupplierInvoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."SupplierInvoices" (
    "InvoiceId" integer NOT NULL,
    "SupplierId" integer NOT NULL,
    "PurchaseOrderId" integer NOT NULL,
    "InvoiceNo" character varying(60) NOT NULL,
    "InvoiceDate" date NOT NULL,
    "TaxAccountId" integer,
    "TaxAmount" numeric(18,2) NOT NULL,
    "TotalAmount" numeric(18,2) NOT NULL,
    "Status" character varying(20) NOT NULL,
    "CreatedBy" integer,
    "ApprovedBy" integer,
    "ApprovedAt" timestamp without time zone,
    "JournalEntryId" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "NetAmount" numeric(18,2) DEFAULT 0 NOT NULL,
    "ProjectId" integer
);


--
-- TOC entry 309 (class 1259 OID 19066)
-- Name: SupplierInvoices_InvoiceId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."SupplierInvoices_InvoiceId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5679 (class 0 OID 0)
-- Dependencies: 309
-- Name: SupplierInvoices_InvoiceId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."SupplierInvoices_InvoiceId_seq" OWNED BY public."SupplierInvoices"."InvoiceId";


--
-- TOC entry 303 (class 1259 OID 18846)
-- Name: TechnicalSettlementEstimateItems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."TechnicalSettlementEstimateItems" (
    "EstimateItemId" integer NOT NULL,
    "EstimateId" integer NOT NULL,
    "ContractItemId" integer NOT NULL,
    "PreviousQuantity" numeric(18,4) NOT NULL,
    "CurrentQuantity" numeric(18,4) NOT NULL,
    "UnitPrice" numeric(18,4) NOT NULL,
    "Amount" numeric(18,2) NOT NULL,
    "CreatedAt" timestamp without time zone NOT NULL,
    "AccountId" integer,
    "ProjectId" integer
);


--
-- TOC entry 302 (class 1259 OID 18845)
-- Name: TechnicalSettlementEstimateItems_EstimateItemId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."TechnicalSettlementEstimateItems_EstimateItemId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5680 (class 0 OID 0)
-- Dependencies: 302
-- Name: TechnicalSettlementEstimateItems_EstimateItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."TechnicalSettlementEstimateItems_EstimateItemId_seq" OWNED BY public."TechnicalSettlementEstimateItems"."EstimateItemId";


--
-- TOC entry 301 (class 1259 OID 18812)
-- Name: TechnicalSettlementEstimates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."TechnicalSettlementEstimates" (
    "EstimateId" integer NOT NULL,
    "ContractId" integer NOT NULL,
    "SettlementSide" character varying(20) NOT NULL,
    "EstimateNo" character varying(50) NOT NULL,
    "EstimateDate" date NOT NULL,
    "CounterpartyName" character varying(200) NOT NULL,
    "WorkValue" numeric(18,2) NOT NULL,
    "Status" character varying(30) NOT NULL,
    "Notes" text,
    "FinancialSettlementId" integer,
    "CreatedBy" integer,
    "ReviewedBy" integer,
    "ReviewedAt" timestamp without time zone,
    "CreatedAt" timestamp without time zone NOT NULL,
    "CounterpartyId" integer
);


--
-- TOC entry 300 (class 1259 OID 18811)
-- Name: TechnicalSettlementEstimates_EstimateId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."TechnicalSettlementEstimates_EstimateId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5681 (class 0 OID 0)
-- Dependencies: 300
-- Name: TechnicalSettlementEstimates_EstimateId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."TechnicalSettlementEstimates_EstimateId_seq" OWNED BY public."TechnicalSettlementEstimates"."EstimateId";


--
-- TOC entry 259 (class 1259 OID 18250)
-- Name: TreasuryAccounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."TreasuryAccounts" (
    "TreasuryAccountId" integer NOT NULL,
    "NameAr" character varying(200) NOT NULL,
    "AccountType" character varying(10) NOT NULL,
    "CurrencyCode" character varying(3) NOT NULL,
    "BankAccountNumber" character varying(50),
    "GLAccountId" integer NOT NULL,
    "IsActive" boolean NOT NULL,
    "ScreenCode" character varying(50),
    "ChecksScreenCode" character varying(50)
);


--
-- TOC entry 258 (class 1259 OID 18249)
-- Name: TreasuryAccounts_TreasuryAccountId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."TreasuryAccounts_TreasuryAccountId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5682 (class 0 OID 0)
-- Dependencies: 258
-- Name: TreasuryAccounts_TreasuryAccountId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."TreasuryAccounts_TreasuryAccountId_seq" OWNED BY public."TreasuryAccounts"."TreasuryAccountId";


--
-- TOC entry 269 (class 1259 OID 18354)
-- Name: TreasuryTransactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."TreasuryTransactions" (
    "TransactionId" bigint NOT NULL,
    "TreasuryAccountId" integer NOT NULL,
    "TransactionDate" date NOT NULL,
    "Inflow" numeric(18,2) NOT NULL,
    "Outflow" numeric(18,2) NOT NULL,
    "Description" character varying(500),
    "VoucherNo" character varying(50),
    "Status" character varying(30),
    "RecipientName" character varying(200),
    "ProjectId" integer,
    "JournalEntryId" integer,
    "CreatedAt" timestamp without time zone NOT NULL,
    "SettlementId" integer,
    "CounterpartyId" integer,
    "SupplierInvoiceId" integer
);


--
-- TOC entry 268 (class 1259 OID 18353)
-- Name: TreasuryTransactions_TransactionId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."TreasuryTransactions_TransactionId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5683 (class 0 OID 0)
-- Dependencies: 268
-- Name: TreasuryTransactions_TransactionId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."TreasuryTransactions_TransactionId_seq" OWNED BY public."TreasuryTransactions"."TransactionId";


--
-- TOC entry 325 (class 1259 OID 19651)
-- Name: UserAvatars; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."UserAvatars" (
    "UserId" integer NOT NULL,
    "ImageData" bytea NOT NULL,
    "MediaType" character varying(30) NOT NULL
);


--
-- TOC entry 245 (class 1259 OID 18103)
-- Name: UserPermissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."UserPermissions" (
    "UserId" integer NOT NULL,
    "PermissionId" integer NOT NULL,
    "IsAllowed" boolean NOT NULL
);


--
-- TOC entry 244 (class 1259 OID 18088)
-- Name: UserRoles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."UserRoles" (
    "UserId" integer NOT NULL,
    "RoleId" integer NOT NULL
);


--
-- TOC entry 226 (class 1259 OID 17977)
-- Name: Users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."Users" (
    "UserId" integer NOT NULL,
    "Username" character varying(50) NOT NULL,
    "PasswordHash" bytea NOT NULL,
    "FullName" character varying(150) NOT NULL,
    "IsActive" boolean NOT NULL,
    "LastLoginAt" timestamp without time zone,
    "FailedLoginCount" integer NOT NULL,
    "LockedUntil" timestamp without time zone,
    "CreatedAt" timestamp without time zone NOT NULL,
    "TokenVersion" integer,
    "AvatarUpdatedAt" timestamp without time zone
);


--
-- TOC entry 225 (class 1259 OID 17976)
-- Name: Users_UserId_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public."Users_UserId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 5684 (class 0 OID 0)
-- Dependencies: 225
-- Name: Users_UserId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public."Users_UserId_seq" OWNED BY public."Users"."UserId";


--
-- TOC entry 328 (class 1259 OID 19940)
-- Name: vw_EffectivePermissions; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public."vw_EffectivePermissions" AS
 SELECT u."UserId",
    p."PermissionId",
    p."ScreenCode",
    p."ActionCode",
        CASE
            WHEN (up."IsAllowed" IS NOT NULL) THEN
            CASE
                WHEN up."IsAllowed" THEN 1
                ELSE 0
            END
            WHEN (rp."PermissionId" IS NOT NULL) THEN 1
            ELSE 0
        END AS "IsAllowed"
   FROM ((((public."Users" u
     CROSS JOIN public."Permissions" p)
     LEFT JOIN public."UserRoles" ur ON ((ur."UserId" = u."UserId")))
     LEFT JOIN public."RolePermissions" rp ON (((rp."RoleId" = ur."RoleId") AND (rp."PermissionId" = p."PermissionId"))))
     LEFT JOIN public."UserPermissions" up ON (((up."UserId" = u."UserId") AND (up."PermissionId" = p."PermissionId"))));


--
-- TOC entry 4928 (class 2604 OID 17971)
-- Name: AccountClassifications ClassificationId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AccountClassifications" ALTER COLUMN "ClassificationId" SET DEFAULT nextval('public."AccountClassifications_ClassificationId_seq"'::regclass);


--
-- TOC entry 4938 (class 2604 OID 18122)
-- Name: AuditLog AuditId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AuditLog" ALTER COLUMN "AuditId" SET DEFAULT nextval('public."AuditLog_AuditId_seq"'::regclass);


--
-- TOC entry 4962 (class 2604 OID 18667)
-- Name: BankReconciliationLines LineId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliationLines" ALTER COLUMN "LineId" SET DEFAULT nextval('public."BankReconciliationLines_LineId_seq"'::regclass);


--
-- TOC entry 4950 (class 2604 OID 18381)
-- Name: BankReconciliations ReconciliationId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliations" ALTER COLUMN "ReconciliationId" SET DEFAULT nextval('public."BankReconciliations_ReconciliationId_seq"'::regclass);


--
-- TOC entry 4945 (class 2604 OID 18269)
-- Name: Beneficiaries BeneficiaryId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Beneficiaries" ALTER COLUMN "BeneficiaryId" SET DEFAULT nextval('public."Beneficiaries_BeneficiaryId_seq"'::regclass);


--
-- TOC entry 4975 (class 2604 OID 19245)
-- Name: CatalogItems CatalogItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems" ALTER COLUMN "CatalogItemId" SET DEFAULT nextval('public."CatalogItems_CatalogItemId_seq"'::regclass);


--
-- TOC entry 4937 (class 2604 OID 18058)
-- Name: ChartOfAccounts AccountId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ChartOfAccounts" ALTER COLUMN "AccountId" SET DEFAULT nextval('public."ChartOfAccounts_AccountId_seq"'::regclass);


--
-- TOC entry 4954 (class 2604 OID 18460)
-- Name: CheckPrintTemplates TemplateId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckPrintTemplates" ALTER COLUMN "TemplateId" SET DEFAULT nextval('public."CheckPrintTemplates_TemplateId_seq"'::regclass);


--
-- TOC entry 4979 (class 2604 OID 19836)
-- Name: CheckSignatories SignatoryId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckSignatories" ALTER COLUMN "SignatoryId" SET DEFAULT nextval('public."CheckSignatories_SignatoryId_seq"'::regclass);


--
-- TOC entry 4963 (class 2604 OID 18681)
-- Name: CheckStatusHistory HistoryId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckStatusHistory" ALTER COLUMN "HistoryId" SET DEFAULT nextval('public."CheckStatusHistory_HistoryId_seq"'::regclass);


--
-- TOC entry 4952 (class 2604 OID 18401)
-- Name: Checks CheckId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks" ALTER COLUMN "CheckId" SET DEFAULT nextval('public."Checks_CheckId_seq"'::regclass);


--
-- TOC entry 4925 (class 2604 OID 17946)
-- Name: Companies CompanyId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Companies" ALTER COLUMN "CompanyId" SET DEFAULT nextval('public."Companies_CompanyId_seq"'::regclass);


--
-- TOC entry 4959 (class 2604 OID 18553)
-- Name: ContractAccountingConfig ConfigId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig" ALTER COLUMN "ConfigId" SET DEFAULT nextval('public."ContractAccountingConfig_ConfigId_seq"'::regclass);


--
-- TOC entry 4955 (class 2604 OID 18474)
-- Name: ContractAddendums AddendumId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAddendums" ALTER COLUMN "AddendumId" SET DEFAULT nextval('public."ContractAddendums_AddendumId_seq"'::regclass);


--
-- TOC entry 4965 (class 2604 OID 18720)
-- Name: ContractAttachments AttachmentId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAttachments" ALTER COLUMN "AttachmentId" SET DEFAULT nextval('public."ContractAttachments_AttachmentId_seq"'::regclass);


--
-- TOC entry 4961 (class 2604 OID 18640)
-- Name: ContractChangeOrders ChangeOrderId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders" ALTER COLUMN "ChangeOrderId" SET DEFAULT nextval('public."ContractChangeOrders_ChangeOrderId_seq"'::regclass);


--
-- TOC entry 4958 (class 2604 OID 18532)
-- Name: ContractDeductionRules RuleId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractDeductionRules" ALTER COLUMN "RuleId" SET DEFAULT nextval('public."ContractDeductionRules_RuleId_seq"'::regclass);


--
-- TOC entry 4957 (class 2604 OID 18514)
-- Name: ContractItems ItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems" ALTER COLUMN "ItemId" SET DEFAULT nextval('public."ContractItems_ItemId_seq"'::regclass);


--
-- TOC entry 4977 (class 2604 OID 19291)
-- Name: ContractRequestItems RequestItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems" ALTER COLUMN "RequestItemId" SET DEFAULT nextval('public."ContractRequestItems_RequestItemId_seq"'::regclass);


--
-- TOC entry 4940 (class 2604 OID 18152)
-- Name: ContractRequests RequestId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests" ALTER COLUMN "RequestId" SET DEFAULT nextval('public."ContractRequests_RequestId_seq"'::regclass);


--
-- TOC entry 4964 (class 2604 OID 18698)
-- Name: ContractSettlementItems SettlementItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems" ALTER COLUMN "SettlementItemId" SET DEFAULT nextval('public."ContractSettlementItems_SettlementItemId_seq"'::regclass);


--
-- TOC entry 4960 (class 2604 OID 18608)
-- Name: ContractSettlements SettlementId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements" ALTER COLUMN "SettlementId" SET DEFAULT nextval('public."ContractSettlements_SettlementId_seq"'::regclass);


--
-- TOC entry 4946 (class 2604 OID 18288)
-- Name: Contracts ContractId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts" ALTER COLUMN "ContractId" SET DEFAULT nextval('public."Contracts_ContractId_seq"'::regclass);


--
-- TOC entry 4969 (class 2604 OID 19053)
-- Name: Counterparties CounterpartyId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Counterparties" ALTER COLUMN "CounterpartyId" SET DEFAULT nextval('public."Counterparties_CounterpartyId_seq"'::regclass);


--
-- TOC entry 4968 (class 2604 OID 19027)
-- Name: CounterpartyAliases AliasId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CounterpartyAliases" ALTER COLUMN "AliasId" SET DEFAULT nextval('public."CounterpartyAliases_AliasId_seq"'::regclass);


--
-- TOC entry 4927 (class 2604 OID 17962)
-- Name: ExchangeRates ExchangeRateId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ExchangeRates" ALTER COLUMN "ExchangeRateId" SET DEFAULT nextval('public."ExchangeRates_ExchangeRateId_seq"'::regclass);


--
-- TOC entry 4953 (class 2604 OID 18427)
-- Name: FinancialChecks CheckId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks" ALTER COLUMN "CheckId" SET DEFAULT nextval('public."FinancialChecks_CheckId_seq"'::regclass);


--
-- TOC entry 4936 (class 2604 OID 18046)
-- Name: FinancialStatementLines LineId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialStatementLines" ALTER COLUMN "LineId" SET DEFAULT nextval('public."FinancialStatementLines_LineId_seq"'::regclass);


--
-- TOC entry 4935 (class 2604 OID 18034)
-- Name: FiscalYears FiscalYearId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FiscalYears" ALTER COLUMN "FiscalYearId" SET DEFAULT nextval('public."FiscalYears_FiscalYearId_seq"'::regclass);


--
-- TOC entry 4934 (class 2604 OID 18026)
-- Name: InventoryItems ItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryItems" ALTER COLUMN "ItemId" SET DEFAULT nextval('public."InventoryItems_ItemId_seq"'::regclass);


--
-- TOC entry 4941 (class 2604 OID 18177)
-- Name: InventoryMovements MovementId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements" ALTER COLUMN "MovementId" SET DEFAULT nextval('public."InventoryMovements_MovementId_seq"'::regclass);


--
-- TOC entry 4933 (class 2604 OID 18018)
-- Name: InventoryWarehouses WarehouseId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryWarehouses" ALTER COLUMN "WarehouseId" SET DEFAULT nextval('public."InventoryWarehouses_WarehouseId_seq"'::regclass);


--
-- TOC entry 4978 (class 2604 OID 19457)
-- Name: ItemCatalog CatalogItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ItemCatalog" ALTER COLUMN "CatalogItemId" SET DEFAULT nextval('public."ItemCatalog_CatalogItemId_seq"'::regclass);


--
-- TOC entry 4943 (class 2604 OID 18222)
-- Name: JournalEntries JournalEntryId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries" ALTER COLUMN "JournalEntryId" SET DEFAULT nextval('public."JournalEntries_JournalEntryId_seq"'::regclass);


--
-- TOC entry 4948 (class 2604 OID 18333)
-- Name: JournalEntryDetails DetailId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntryDetails" ALTER COLUMN "DetailId" SET DEFAULT nextval('public."JournalEntryDetails_DetailId_seq"'::regclass);


--
-- TOC entry 4931 (class 2604 OID 18000)
-- Name: Permissions PermissionId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Permissions" ALTER COLUMN "PermissionId" SET DEFAULT nextval('public."Permissions_PermissionId_seq"'::regclass);


--
-- TOC entry 4956 (class 2604 OID 18494)
-- Name: ProgressBillings BillingId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ProgressBillings" ALTER COLUMN "BillingId" SET DEFAULT nextval('public."ProgressBillings_BillingId_seq"'::regclass);


--
-- TOC entry 4926 (class 2604 OID 17953)
-- Name: Projects ProjectId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Projects" ALTER COLUMN "ProjectId" SET DEFAULT nextval('public."Projects_ProjectId_seq"'::regclass);


--
-- TOC entry 4947 (class 2604 OID 18315)
-- Name: PurchaseOrderLines LineId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines" ALTER COLUMN "LineId" SET DEFAULT nextval('public."PurchaseOrderLines_LineId_seq"'::regclass);


--
-- TOC entry 4942 (class 2604 OID 18202)
-- Name: PurchaseOrders PurchaseOrderId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrders" ALTER COLUMN "PurchaseOrderId" SET DEFAULT nextval('public."PurchaseOrders_PurchaseOrderId_seq"'::regclass);


--
-- TOC entry 4974 (class 2604 OID 19170)
-- Name: PurchaseReturnLines LineId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturnLines" ALTER COLUMN "LineId" SET DEFAULT nextval('public."PurchaseReturnLines_LineId_seq"'::regclass);


--
-- TOC entry 4973 (class 2604 OID 19136)
-- Name: PurchaseReturns ReturnId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns" ALTER COLUMN "ReturnId" SET DEFAULT nextval('public."PurchaseReturns_ReturnId_seq"'::regclass);


--
-- TOC entry 4976 (class 2604 OID 19275)
-- Name: RecordAttachments AttachmentId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RecordAttachments" ALTER COLUMN "AttachmentId" SET DEFAULT nextval('public."RecordAttachments_AttachmentId_seq"'::regclass);


--
-- TOC entry 4930 (class 2604 OID 17991)
-- Name: Roles RoleId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Roles" ALTER COLUMN "RoleId" SET DEFAULT nextval('public."Roles_RoleId_seq"'::regclass);


--
-- TOC entry 4939 (class 2604 OID 18136)
-- Name: Screens ScreenId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Screens" ALTER COLUMN "ScreenId" SET DEFAULT nextval('public."Screens_ScreenId_seq"'::regclass);


--
-- TOC entry 4932 (class 2604 OID 18009)
-- Name: Sections SectionId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Sections" ALTER COLUMN "SectionId" SET DEFAULT nextval('public."Sections_SectionId_seq"'::regclass);


--
-- TOC entry 4972 (class 2604 OID 19113)
-- Name: SupplierInvoiceLines LineId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoiceLines" ALTER COLUMN "LineId" SET DEFAULT nextval('public."SupplierInvoiceLines_LineId_seq"'::regclass);


--
-- TOC entry 4970 (class 2604 OID 19070)
-- Name: SupplierInvoices InvoiceId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices" ALTER COLUMN "InvoiceId" SET DEFAULT nextval('public."SupplierInvoices_InvoiceId_seq"'::regclass);


--
-- TOC entry 4967 (class 2604 OID 18849)
-- Name: TechnicalSettlementEstimateItems EstimateItemId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems" ALTER COLUMN "EstimateItemId" SET DEFAULT nextval('public."TechnicalSettlementEstimateItems_EstimateItemId_seq"'::regclass);


--
-- TOC entry 4966 (class 2604 OID 18815)
-- Name: TechnicalSettlementEstimates EstimateId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates" ALTER COLUMN "EstimateId" SET DEFAULT nextval('public."TechnicalSettlementEstimates_EstimateId_seq"'::regclass);


--
-- TOC entry 4944 (class 2604 OID 18253)
-- Name: TreasuryAccounts TreasuryAccountId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryAccounts" ALTER COLUMN "TreasuryAccountId" SET DEFAULT nextval('public."TreasuryAccounts_TreasuryAccountId_seq"'::regclass);


--
-- TOC entry 4949 (class 2604 OID 18357)
-- Name: TreasuryTransactions TransactionId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions" ALTER COLUMN "TransactionId" SET DEFAULT nextval('public."TreasuryTransactions_TransactionId_seq"'::regclass);


--
-- TOC entry 4929 (class 2604 OID 17980)
-- Name: Users UserId; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Users" ALTER COLUMN "UserId" SET DEFAULT nextval('public."Users_UserId_seq"'::regclass);


--
-- TOC entry 5522 (class 0 OID 17968)
-- Dependencies: 224
-- Data for Name: AccountClassifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."AccountClassifications" ("ClassificationId", "NameAr", "StatementType") FROM stdin;
1	اصول ثابتة بالصافي	BalanceSheet
2	اصول غير ملموسه	BalanceSheet
3	استثمارات مالية بالقيمة العادلة	BalanceSheet
4	مخزون	BalanceSheet
5	اعمال تحت التنفيذ	BalanceSheet
6	نقدية بالصندوق و البنوك	BalanceSheet
7	مدينون و ارصدة مدينة اخرى	BalanceSheet
8	عملاء وأوراق قبض	BalanceSheet
9	مدينون و ارصدة مدينة أخرى	BalanceSheet
10	مستحق الى اطراف ذات علاقة	IncomeStatement
11	دفعات مقدمه موردون و مقاولون	BalanceSheet
12	اصول بحق الاستخدام	BalanceSheet
13	موردون و اوراق دفع	BalanceSheet
14	دائنون و ارصدة دائنة اخرى	BalanceSheet
15	دائنون و ارصدة دائنة أخرى	BalanceSheet
16	عملاء دفعات مقدمه	BalanceSheet
17	احتياطي قانوني	BalanceSheet
18	راس المال المصدر و المدفوع	BalanceSheet
19	الارباح / الخسائر المرحلة	BalanceSheet
20	التزامات ضريبيه مؤجله	BalanceSheet
21	التزامات تاجير تمويلى	BalanceSheet
22	مبيعات / إيرادات	BalanceSheet
23	ارباح / خسائر استثمارات مالية بالقيمة العادلة	BalanceSheet
24	فوائد دائنة	BalanceSheet
25	خسائر فروق عمله	BalanceSheet
26	مصروفات عمومية و ادارية	BalanceSheet
27	مصروفات عمومية و إدارية	BalanceSheet
28	اهلاك اصول	BalanceSheet
29	تكلفة المبيعات	BalanceSheet
30	فوائد التاجير التمويلى	BalanceSheet
\.


--
-- TOC entry 5545 (class 0 OID 18119)
-- Dependencies: 247
-- Data for Name: AuditLog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."AuditLog" ("AuditId", "UserId", "ActionType", "EntityName", "EntityId", "OldValue", "NewValue", "Timestamp", "IpAddress") FROM stdin;
1	1	Create	Contracts	1	\N	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22", "status": "Draft", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	2026-10-17 10:20:32.906273	\N
2	1	SubmitForApproval	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Draft", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "PendingApproval", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	2026-10-17 10:20:40.790779	\N
3	1	ReturnForChanges	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "PendingApproval", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Returned", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	2026-10-17 10:20:46.985885	\N
4	1	SubmitForApproval	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Returned", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "PendingApproval", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	2026-10-17 10:23:30.287311	\N
5	1	ApproveAndActivate	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "PendingApproval", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	2026-10-17 10:23:36.658054	\N
6	1	Update	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22", "status": "Draft", "notes": "ثرير"}	2026-10-17 10:28:37.487961	\N
7	1	Update	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22", "status": "Draft", "notes": "ثرير س سش "}	2026-10-17 10:28:58.710524	\N
8	1	Create	Contracts	2	\N	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000", "status": "Draft", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	2026-10-17 10:46:33.444561	\N
9	1	SubmitForApproval	Contracts	2	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "Draft", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	2026-10-17 10:46:41.494272	\N
10	1	ReturnForChanges	Contracts	2	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "Returned", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	2026-10-17 10:46:46.45788	\N
11	1	Create	Contracts	3	\N	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0", "status": "Draft", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	2026-10-17 11:44:50.139516	\N
12	1	Update	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "ؤ", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير س سش ", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_no": "2", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22", "status": "Draft", "notes": "ثرير س سش"}	2026-10-17 11:45:08.653206	\N
13	1	Create	ContractSettlements	1	\N	{"settlement_id": 1, "contract_id": 1, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-17", "counterparty_name": "لوكس", "work_value": "10.00", "cumulative_work_value": "10.00", "deductions": {}, "vat_amount": "2.50", "net_amount": "12.50", "status": "Draft", "journal_entry_id": null, "notes": "بلاقلا"}	2026-10-17 12:45:25.096578	\N
14	1	SubmitForApproval	Contracts	3	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0.00", "status": "Draft", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0.00", "status": "PendingApproval", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	2026-10-17 13:43:59.872432	\N
15	1	ApproveAndActivate	Contracts	3	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0.00", "status": "PendingApproval", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0.00", "status": "Active", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	2026-10-17 13:44:07.098973	\N
16	1	Create	ContractItems	1	\N	{"item_id": 1, "contract_id": 1, "item_no": "1", "description": "توريد", "unit": "طن", "quantity": "1000", "unit_price": "50", "total": "50000.00"}	2026-10-17 13:44:59.494848	\N
17	1	Approve	ContractSettlements	1	\N	{"settlement_id": 1, "contract_id": 1, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-17", "counterparty_name": "لوكس", "work_value": "10.00", "cumulative_work_value": "10.00", "deductions": {}, "vat_amount": "2.50", "net_amount": "12.50", "status": "Approved", "journal_entry_id": null, "notes": "بلاقلا"}	2026-10-17 13:45:56.414073	\N
18	1	Create	TechnicalSettlementEstimates	1	\N	{"estimate_no": "1", "work_value": "5000.00", "status": "UnderReview"}	2026-10-17 13:57:55.75948	\N
19	1	Approve	TechnicalSettlementEstimates	1	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 2, "work_value": "5000.00"}	2026-10-17 13:58:21.068806	\N
20	1	SubmitForApproval	Contracts	2	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "Returned", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	2026-10-17 15:46:10.81676	\N
21	1	ApproveAndActivate	Contracts	2	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "Active", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	2026-10-17 15:48:01.961866	\N
22	1	Update	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "2", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير س سش", "created_at": "2026-10-17 10:20:32.904112"}	{"contract_no": "2", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22", "status": "Draft", "notes": "ثرير س سش\\n\\n\\nعةةت\\nةظ\\nةظ\\nظ\\nة"}	2026-10-17 15:48:15.8139	\N
23	1	Create	TreasuryAccounts	1	\N	{"name_ar": "JV", "account_type": "Bank", "currency_code": "EGP", "bank_account_number": "100000000000", "gl_account_id": 2}	2026-10-17 16:05:14.185592	\N
24	1	Create	FinancialChecks	1	\N	{"check_number": "155", "check_type": "INCOMING", "amount": "5000", "due_date": "2026-10-23", "party_account_id": 1, "treasury_account_id": 1, "drawee_bank": "cib", "project_brand": "Lux", "description": "توريد"}	2026-10-17 16:05:51.981995	\N
25	1	Update	FinancialChecks	1	\N	{"status": "تحت التحصيل"}	2026-10-17 16:06:06.483726	\N
26	1	Create	ContractDeductionRules	1	\N	{"rule_id": 1, "contract_id": 3, "settlement_side": "Customer", "code": "retention_insurance", "name_ar": "تأمين محتجز", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 10}	2026-10-17 16:22:55.145759	\N
27	1	Create	ContractDeductionRules	2	\N	{"rule_id": 2, "contract_id": 3, "settlement_side": "Customer", "code": "final_insurance", "name_ar": "تأمين نهائي", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 20}	2026-10-17 16:22:55.149718	\N
28	1	Create	ContractDeductionRules	3	\N	{"rule_id": 3, "contract_id": 3, "settlement_side": "Customer", "code": "social_insurance", "name_ar": "تأمينات اجتماعية", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 30}	2026-10-17 16:22:55.152922	\N
29	1	Create	ContractDeductionRules	4	\N	{"rule_id": 4, "contract_id": 3, "settlement_side": "Customer", "code": "irregular_labor", "name_ar": "عمالة غير منتظمة", "calculation_type": "Percent", "rate": "0.6", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 40}	2026-10-17 16:22:55.156093	\N
30	1	Create	ContractDeductionRules	5	\N	{"rule_id": 5, "contract_id": 3, "settlement_side": "Customer", "code": "profit_tax", "name_ar": "ضريبة أرباح", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 50}	2026-10-17 16:22:55.159199	\N
31	1	Create	ContractDeductionRules	6	\N	{"rule_id": 6, "contract_id": 3, "settlement_side": "Customer", "code": "stamp_duty", "name_ar": "الدمغة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 60}	2026-10-17 16:22:55.162605	\N
32	1	Create	ContractDeductionRules	7	\N	{"rule_id": 7, "contract_id": 3, "settlement_side": "Customer", "code": "advance_payments", "name_ar": "الدفعات المقدمة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 70}	2026-10-17 16:22:55.165836	\N
33	1	Create	ContractDeductionRules	8	\N	{"rule_id": 8, "contract_id": 3, "settlement_side": "Customer", "code": "work_guarantee_hold", "name_ar": "حجز ضمان الأعمال", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 80}	2026-10-17 16:22:55.168514	\N
34	1	Create	ContractDeductionRules	9	\N	{"rule_id": 9, "contract_id": 3, "settlement_side": "Customer", "code": "store_withdrawals", "name_ar": "مسحوبات المخازن وخامات الموقع", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 90}	2026-10-17 16:22:55.171192	\N
35	1	Create	ContractDeductionRules	10	\N	{"rule_id": 10, "contract_id": 3, "settlement_side": "Subcontractor", "code": "3", "name_ar": "الحاجز", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": 2, "is_active": true, "sort_order": 3}	2026-10-17 19:03:14.349432	\N
36	1	Create	ContractDeductionRules	11	\N	{"rule_id": 11, "contract_id": 3, "settlement_side": "Subcontractor", "code": "retention_insurance", "name_ar": "تأمين محتجز", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 10}	2026-10-17 19:21:13.29194	\N
37	1	Create	ContractDeductionRules	12	\N	{"rule_id": 12, "contract_id": 3, "settlement_side": "Subcontractor", "code": "final_retention", "name_ar": "تأمين نهائي", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 20}	2026-10-17 19:21:13.325841	\N
38	1	Create	ContractDeductionRules	13	\N	{"rule_id": 13, "contract_id": 3, "settlement_side": "Subcontractor", "code": "social_insurance", "name_ar": "تأمينات اجتماعية", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 30}	2026-10-17 19:21:13.355806	\N
39	1	Create	ContractDeductionRules	14	\N	{"rule_id": 14, "contract_id": 3, "settlement_side": "Subcontractor", "code": "informal_labor", "name_ar": "عمالة غير منتظمة", "calculation_type": "Percent", "rate": "0.6", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 40}	2026-10-17 19:21:13.38604	\N
40	1	Create	ContractDeductionRules	15	\N	{"rule_id": 15, "contract_id": 3, "settlement_side": "Subcontractor", "code": "profit_tax", "name_ar": "ضريبة أرباح", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 50}	2026-10-17 19:21:13.415732	\N
42	1	Create	ContractDeductionRules	17	\N	{"rule_id": 17, "contract_id": 3, "settlement_side": "Subcontractor", "code": "advance_payment", "name_ar": "تسوية دفعات مقدمة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 70}	2026-10-17 19:21:13.462864	\N
41	1	Create	ContractDeductionRules	16	\N	{"rule_id": 16, "contract_id": 3, "settlement_side": "Subcontractor", "code": "stamp_duty", "name_ar": "دمغة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 60}	2026-10-17 19:21:13.440826	\N
43	1	Create	Contracts	4	\N	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000", "status": "Draft", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	2026-10-17 20:21:30.864391	\N
44	1	AutoLinkRules	Contracts	3	\N	{"linked": [{"code": "social_insurance", "name": "تأمينات اجتماعية", "side": "Customer", "account": "21405001 — تامينات اجتماعية - مقاولى باطن مشروع"}, {"code": "profit_tax", "name": "ضريبة أرباح", "side": "Customer", "account": "21402006 — جارى مصلحة الضرائب - ضريبة خصم واضافة"}, {"code": "stamp_duty", "name": "الدمغة", "side": "Customer", "account": "21402007 — دمغة هندسية ( 0.0045 )"}, {"code": "store_withdrawals", "name": "مسحوبات المخازن وخامات الموقع", "side": "Customer", "account": "15203049 — م . تشغيل - خامات دهانات ( اعمال تحت التنفيذ )"}, {"code": "social_insurance", "name": "تأمينات اجتماعية", "side": "Subcontractor", "account": "21405001 — تامينات اجتماعية - مقاولى باطن مشروع"}, {"code": "informal_labor", "name": "عمالة غير منتظمة", "side": "Subcontractor", "account": "15202005 — تكاليف - اعمال توريد عمالة ذاتى \\" عادى - فنى \\" ( اعمال تحت التنفيذ )"}, {"code": "profit_tax", "name": "ضريبة أرباح", "side": "Subcontractor", "account": "21402006 — جارى مصلحة الضرائب - ضريبة خصم واضافة"}, {"code": "stamp_duty", "name": "دمغة", "side": "Subcontractor", "account": "21402007 — دمغة هندسية ( 0.0045 )"}, {"code": "advance_payment", "name": "تسوية دفعات مقدمة", "side": "Subcontractor", "account": "21407001 — دفعات مقدمة من عميل/  شركة  المقاولون المتخصصون"}], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-17 20:23:21.109862	\N
45	1	AutoLinkRules	Contracts	3	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-17 20:23:29.528788	\N
46	1	AutoLinkRules	Contracts	3	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-17 20:23:31.16124	\N
47	1	AutoLinkRules	Contracts	3	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-17 20:23:31.812705	\N
48	1	AutoLinkRules	Contracts	3	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-17 20:23:37.097747	\N
49	1	Create	FiscalYears	1	\N	{"start_date": "2026-01-01", "end_date": "2026-12-31", "company_name": "JV"}	2026-10-17 20:27:42.913402	\N
50	1	Create	JournalEntries	1	\N	{"entry_no": "JE-2026-000001"}	2026-10-17 20:38:02.779504	\N
51	1	Create	Projects	1	\N	{"name_ar": "JV", "name_en": "JV", "is_head_office": false, "is_active": true}	2026-10-17 20:38:58.046181	\N
52	1	SubmitForApproval	Contracts	4	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000.00", "status": "Draft", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000.00", "status": "PendingApproval", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	2026-10-17 20:43:57.238934	\N
53	1	ApproveAndActivate	Contracts	4	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000.00", "status": "PendingApproval", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000.00", "status": "Active", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	2026-10-17 20:44:51.961785	\N
54	1	Delete	JournalEntries	1	{"entry_no": "JE-2026-000001"}	\N	2026-10-17 20:45:16.770195	\N
63	1	SubmitForApproval	Contracts	6	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000.00", "status": "Draft", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	2026-10-18 07:22:03.127207	\N
64	1	ApproveAndActivate	Contracts	6	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	2026-10-18 07:22:12.391849	\N
77	1	BackupCreate	Backup	-	\N	{"file": "financial_system_manual_20261018_125442.zip"}	2026-10-18 09:54:42.430583	\N
55	1	UpdateDeductions	ContractSettlements	2	{"deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "50.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "1.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.50", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "5000.00"}	{"deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "50.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "1.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.50", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.50", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.50", "net_amount": "4945.50"}	2026-10-18 06:40:43.785144	\N
56	1	Create	Contracts	5	\N	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000", "status": "Draft", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	2026-10-18 06:45:36.013158	\N
57	1	SubmitForApproval	Contracts	5	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Draft", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	2026-10-18 06:45:54.210613	\N
58	1	ApproveAndActivate	Contracts	5	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	2026-10-18 06:46:00.728884	\N
59	1	Create	ContractSettlements	3	\N	{"settlement_id": 3, "contract_id": 5, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "1999", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "10000.00", "cumulative_work_value": "10000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "10000.00", "status": "Draft", "journal_entry_id": null, "notes": null}	2026-10-18 06:47:17.975928	\N
60	1	Create	ContractSettlements	4	\N	{"settlement_id": 4, "contract_id": 5, "settlement_side": "Subcontractor", "sequence_no": 2, "settlement_no": "2", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "50.00", "cumulative_work_value": "50.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "50.00", "status": "Draft", "journal_entry_id": null, "notes": "50 طن بازلت "}	2026-10-18 06:54:57.651458	\N
61	1	Create	ContractItems	2	\N	{"item_id": 2, "contract_id": 5, "item_no": "1/49", "description": "كسر أحجار دلوميت  مقاس من (1-2) طن", "unit": "طن", "quantity": "3761.5", "unit_price": "415", "total": "1561022.50"}	2026-10-18 07:02:05.748189	\N
62	1	Create	Contracts	6	\N	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000", "status": "Draft", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	2026-10-18 07:21:50.614805	\N
75	1	AutoLinkRules	Contracts	7	\N	{"linked": [], "missing": []}	2026-10-18 08:44:17.330053	\N
76	1	AutoLinkRules	Contracts	7	\N	{"linked": [], "missing": []}	2026-10-18 08:44:27.21499	\N
78	1	Create	InventoryWarehouses	1	\N	{"code": "1", "name": "Network", "location": "1", "is_active": true}	2026-10-18 10:23:16.427297	\N
65	1	AdminPurge	ContractSettlements	4	{"settlement_id": 4, "contract_id": 5, "settlement_side": "Subcontractor", "sequence_no": 2, "settlement_no": "2", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "50.00", "cumulative_work_value": "50.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "50.00", "status": "Draft", "journal_entry_id": null, "notes": "50 طن بازلت ", "deleted_counts": {"settlements": 1, "technical_estimates": 0, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_105416.zip"}	2026-10-18 07:54:16.631652	\N
66	1	AdminPurge	ContractSettlements	3	{"settlement_id": 3, "contract_id": 5, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "1999", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "10000.00", "cumulative_work_value": "10000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "10000.00", "status": "Draft", "journal_entry_id": null, "notes": null, "deleted_counts": {"settlements": 1, "technical_estimates": 0, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_105427.zip"}	2026-10-18 07:54:28.070023	\N
67	1	AdminPurge	ContractSettlements	1	{"settlement_id": 1, "contract_id": 1, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-17", "counterparty_name": "لوكس", "work_value": "10.00", "cumulative_work_value": "10.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "2.50", "net_amount": "12.50", "status": "Approved", "journal_entry_id": null, "notes": "بلاقلا", "deleted_counts": {"settlements": 1, "technical_estimates": 0, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_105512.zip"}	2026-10-18 07:55:12.420639	\N
68	1	AdminPurge	TechnicalSettlementEstimates	1	{"estimate_no": "1", "status": "TechnicallyApproved", "financial_settlement_id": 2, "deleted_counts": {"settlements": 1, "technical_estimates": 1, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_105742.zip"}	2026-10-18 07:57:43.136702	\N
69	1	Create	Contracts	7	\N	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000", "status": "Draft", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	2026-10-18 08:10:54.959659	\N
70	1	SubmitForApproval	Contracts	7	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000.00", "status": "Draft", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	2026-10-18 08:11:02.444348	\N
71	1	ApproveAndActivate	Contracts	7	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	2026-10-18 08:11:03.99158	\N
72	1	Create	ContractItems	10	\N	{"item_id": 10, "contract_id": 7, "item_no": "1/49", "description": "بازلن", "unit": "طن", "quantity": "100", "unit_price": "20", "total": "2000.00"}	2026-10-18 08:21:33.312958	\N
73	1	Create	JournalEntries	2	\N	{"entry_no": "JE-2026-000001"}	2026-10-18 08:23:41.335886	\N
74	1	Post	JournalEntries	2	{"status": "Draft"}	{"status": "Posted"}	2026-10-18 08:24:09.143273	\N
79	1	Create	InventoryItems	1	\N	{"code": "1", "name": "محاسب", "category": "ق", "unit": "قطعة", "min_quantity": "5", "is_active": true}	2026-10-18 10:23:46.588739	\N
80	1	Create	Counterparties	5	\N	{"legal_name": "محمد", "party_type": "Supplier", "tax_no": "154", "commercial_registration": "582", "phone": "01158299866", "email": "himahero958@gmail.com", "address": "ش عباس علي عيسى بمتفرع من مدينة عامر بولاق الدكرور", "linked_account_id": null, "is_active": true}	2026-10-18 10:24:44.150615	\N
81	1	Create	Contracts	8	\N	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "counterparty_id": 1, "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000", "status": "Draft", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	2026-10-18 10:32:59.637131	\N
82	1	SubmitForApproval	Contracts	8	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "counterparty_id": 1, "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000.00", "status": "Draft", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "counterparty_id": 1, "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	2026-10-18 10:33:03.199021	\N
83	1	ApproveAndActivate	Contracts	8	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "counterparty_id": 1, "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "counterparty_id": 1, "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	2026-10-18 10:33:05.183648	\N
84	1	Create	ContractSettlements	5	\N	{"settlement_id": 5, "contract_id": 8, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "500.00", "cumulative_work_value": "500.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "500.00", "status": "Draft", "journal_entry_id": null, "notes": null}	2026-10-18 10:42:39.476324	\N
85	1	Create	ContractItems	11	\N	{"item_id": 11, "contract_id": 8, "catalog_item_id": null, "account_id": 60, "project_id": 1, "item_no": "1", "description": "توريد", "unit": "طن", "quantity": "1000", "unit_price": "50", "total": "50000.00"}	2026-10-18 10:46:37.967487	\N
86	1	Approve	ContractSettlements	5	\N	{"settlement_id": 5, "contract_id": 8, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "500.00", "cumulative_work_value": "500.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "500.00", "status": "Approved", "journal_entry_id": null, "notes": null}	2026-10-18 10:47:29.687107	\N
87	1	Create	ContractSettlements	6	\N	{"settlement_id": 6, "contract_id": 7, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "2000.00", "cumulative_work_value": "2000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "2000.00", "status": "Draft", "journal_entry_id": null, "notes": null}	2026-10-18 11:09:08.519781	\N
88	1	Approve	ContractSettlements	6	\N	{"settlement_id": 6, "contract_id": 7, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "2000.00", "cumulative_work_value": "2000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "2000.00", "status": "Approved", "journal_entry_id": null, "notes": null}	2026-10-18 11:09:31.315177	\N
89	1	BackupCreate	Backup	-	\N	{"file": "financial_system_manual_20261018_145036.zip"}	2026-10-18 11:50:36.613303	\N
90	1	AutoLinkRules	Contracts	3	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_insurance", "name": "تأمين نهائي", "side": "Customer"}, {"code": "irregular_labor", "name": "عمالة غير منتظمة", "side": "Customer"}, {"code": "advance_payments", "name": "الدفعات المقدمة", "side": "Customer"}, {"code": "work_guarantee_hold", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}]}	2026-10-18 11:52:32.255462	\N
91	1	AdminPurge	ContractSettlements	5	{"settlement_id": 5, "contract_id": 8, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "500.00", "cumulative_work_value": "500.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "500.00", "status": "Approved", "journal_entry_id": null, "notes": null, "deleted_counts": {"settlements": 1, "technical_estimates": 0, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_151938.zip"}	2026-10-18 12:19:38.764746	\N
92	1	AdminPurge	ContractSettlements	6	{"settlement_id": 6, "contract_id": 7, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "1", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "counterparty_id": 1, "work_value": "2000.00", "cumulative_work_value": "2000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "2000.00", "status": "Approved", "journal_entry_id": null, "notes": null, "deleted_counts": {"settlements": 1, "technical_estimates": 0, "payment_movements": 0, "journal_entries": 0}}	{"safety_backup": "financial_system_pre_restore_20261018_151942.zip"}	2026-10-18 12:19:42.825268	\N
93	1	Create	ContractDeductionRules	18	\N	{"rule_id": 18, "contract_id": 8, "settlement_side": "Customer", "code": "retention_insurance", "name_ar": "تأمين محتجز", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 10}	2026-10-18 12:44:10.639994	\N
94	1	Create	ContractDeductionRules	19	\N	{"rule_id": 19, "contract_id": 8, "settlement_side": "Customer", "code": "final_retention", "name_ar": "تأمين نهائي", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 20}	2026-10-18 12:44:10.670755	\N
95	1	Create	ContractDeductionRules	20	\N	{"rule_id": 20, "contract_id": 8, "settlement_side": "Customer", "code": "social_insurance", "name_ar": "تأمينات اجتماعية", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 30}	2026-10-18 12:44:10.696515	\N
96	1	Create	ContractDeductionRules	21	\N	{"rule_id": 21, "contract_id": 8, "settlement_side": "Customer", "code": "informal_labor", "name_ar": "عمالة غير منتظمة", "calculation_type": "Percent", "rate": "0.6", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 40}	2026-10-18 12:44:10.722038	\N
97	1	Create	ContractDeductionRules	22	\N	{"rule_id": 22, "contract_id": 8, "settlement_side": "Customer", "code": "profit_tax", "name_ar": "ضريبة أرباح", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 50}	2026-10-18 12:44:10.746096	\N
104	1	Create	ContractDeductionRules	29	\N	{"rule_id": 29, "contract_id": 8, "settlement_side": "Subcontractor", "code": "social_insurance", "name_ar": "تأمينات اجتماعية", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 30}	2026-10-18 12:44:10.931209	\N
109	1	Create	ContractDeductionRules	34	\N	{"rule_id": 34, "contract_id": 8, "settlement_side": "Subcontractor", "code": "works_guarantee", "name_ar": "حجز ضمان الأعمال", "calculation_type": "Percent", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 80}	2026-10-18 12:44:11.050996	\N
98	1	Create	ContractDeductionRules	23	\N	{"rule_id": 23, "contract_id": 8, "settlement_side": "Customer", "code": "stamp_duty", "name_ar": "دمغة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 60}	2026-10-18 12:44:10.770851	\N
105	1	Create	ContractDeductionRules	30	\N	{"rule_id": 30, "contract_id": 8, "settlement_side": "Subcontractor", "code": "informal_labor", "name_ar": "عمالة غير منتظمة", "calculation_type": "Percent", "rate": "0.6", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 40}	2026-10-18 12:44:10.95516	\N
110	1	Create	ContractDeductionRules	35	\N	{"rule_id": 35, "contract_id": 8, "settlement_side": "Subcontractor", "code": "store_withdrawals", "name_ar": "مسحوبات المخازن وخامات الموقع", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 90}	2026-10-18 12:44:11.073072	\N
334	1	Create	JournalEntries	9	\N	{"entry_no": "JE-2026-000008"}	2026-11-04 15:29:26.698895	127.0.0.1
335	1	Update	JournalEntries	9	{"journal_entry_id": 9, "entry_no": "JE-2026-000008", "entry_date": "2026-11-04", "description": null, "status": "Draft", "posted_at": null, "source_settlement_id": null, "line_descriptions": [{"line_no": 1, "description": "بالطن توريد ونقل كسر أحجار من أي نوع تحقق كثافة لا تقل عن 2.4  طن/م3   لزوم أعمال الحاجز المؤقت على ان يكون خالى من الشوائب و التشققات و التصدعات و العيوب طبقا للمواصفات الفنية والكود المصري والفئة تشمل التحميل من المحجر والنقل  لموقع التشوين والتفريغ بمشون المشروع والتسليم طبقا لتعليمات المهندس المشرف او من ينوب عنه بالموقع على ان تمم المحاسبة وفقا لاشعار بونات الميزان المعتمدة من المشروع ( الفئة لا تشمل التعتيق بمعدات المقاول فى المشروع )"}, {"line_no": 2, "description": "كسر أحجار دلوميت  مقاس من (1-2) طن"}], "total_debit": "154000.00", "total_credit": "154000.00", "lines": [{"line_no": 1, "account_id": 242, "account_code": "15409022", "account_name": "مقاولى باطن  /  شركة لوكس تو ايه", "project_id": null, "project_name": null, "debit_amount": "0.00", "credit_amount": "154000.00", "description": "بالطن توريد ونقل كسر أحجار من أي نوع تحقق كثافة لا تقل عن 2.4  طن/م3   لزوم أعمال الحاجز المؤقت على ان يكون خالى من الشوائب و التشققات و التصدعات و العيوب طبقا للمواصفات الفنية والكود المصري والفئة تشمل التحميل من المحجر والنقل  لموقع التشوين والتفريغ بمشون المشروع والتسليم طبقا لتعليمات المهندس المشرف او من ينوب عنه بالموقع على ان تمم المحاسبة وفقا لاشعار بونات الميزان المعتمدة من المشروع ( الفئة لا تشمل التعتيق بمعدات المقاول فى المشروع )"}, {"line_no": 2, "account_id": 134, "account_code": "15301001", "account_name": "الصندوق - خزينة  ( جنيه مصري )", "project_id": null, "project_name": null, "debit_amount": "154000.00", "credit_amount": "0.00", "description": "كسر أحجار دلوميت  مقاس من (1-2) طن"}]}	{"journal_entry_id": 9, "entry_no": "JE-2026-000008", "entry_date": "2026-11-04", "description": null, "status": "Draft", "posted_at": null, "source_settlement_id": null, "line_descriptions": [{"line_no": 1, "description": "بالطن توريد ونقل كسر أحجار من أي نوع تحقق كثافة لا تقل عن 2.4  طن/م3   لزوم أعمال الحاجز المؤقت على ان يكون خالى من الشوائب و التشققات و التصدعات و العيوب طبقا للمواصفات الفنية والكود المصري والفئة تشمل التحميل من المحجر والنقل  لموقع التشوين والتفريغ بمشون المشروع والتسليم طبقا لتعليمات المهندس المشرف او من ينوب عنه بالموقع على ان تمم المحاسبة وفقا لاشعار بونات الميزان المعتمدة من المشروع ( الفئة لا تشمل التعتيق بمعدات المقاول فى المشروع )"}, {"line_no": 2, "description": "كسر أحجار دلوميت  مقاس من (1-2) طن"}], "total_debit": "154000.00", "total_credit": "154000.00", "lines": [{"line_no": 1, "account_id": 242, "account_code": "15409022", "account_name": "مقاولى باطن  /  شركة لوكس تو ايه", "project_id": null, "project_name": null, "debit_amount": "0.00", "credit_amount": "154000.00", "description": "بالطن توريد ونقل كسر أحجار من أي نوع تحقق كثافة لا تقل عن 2.4  طن/م3   لزوم أعمال الحاجز المؤقت على ان يكون خالى من الشوائب و التشققات و التصدعات و العيوب طبقا للمواصفات الفنية والكود المصري والفئة تشمل التحميل من المحجر والنقل  لموقع التشوين والتفريغ بمشون المشروع والتسليم طبقا لتعليمات المهندس المشرف او من ينوب عنه بالموقع على ان تمم المحاسبة وفقا لاشعار بونات الميزان المعتمدة من المشروع ( الفئة لا تشمل التعتيق بمعدات المقاول فى المشروع )"}, {"line_no": 2, "account_id": 134, "account_code": "15301001", "account_name": "الصندوق - خزينة  ( جنيه مصري )", "project_id": null, "project_name": null, "debit_amount": "154000.00", "credit_amount": "0.00", "description": "كسر أحجار دلوميت  مقاس من (1-2) طن"}]}	2026-11-04 15:30:23.832566	127.0.0.1
336	1	Post	JournalEntries	9	{"status": "Draft"}	{"status": "Posted"}	2026-11-04 15:30:32.700796	127.0.0.1
337	1	Export	accounts	\N	\N	{"rows": 587, "format": "xlsx"}	2026-11-05 12:17:50.117187	127.0.0.1
339	1	BackupCreate	Backup	-	\N	{"file": "financial_system_manual_20261105_142935.zip"}	2026-11-05 12:29:36.19044	127.0.0.1
340	1	BackupCreate	Backup	-	\N	{"file": "financial_system_manual_20261105_143000.zip"}	2026-11-05 12:30:00.207251	127.0.0.1
99	1	Create	ContractDeductionRules	24	\N	{"rule_id": 24, "contract_id": 8, "settlement_side": "Customer", "code": "advance_payment", "name_ar": "تسوية دفعات مقدمة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 70}	2026-10-18 12:44:10.794127	\N
106	1	Create	ContractDeductionRules	31	\N	{"rule_id": 31, "contract_id": 8, "settlement_side": "Subcontractor", "code": "profit_tax", "name_ar": "ضريبة أرباح", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 50}	2026-10-18 12:44:10.979432	\N
111	1	AutoLinkRules	Contracts	8	\N	{"linked": [{"code": "social_insurance", "name": "تأمينات اجتماعية", "side": "Customer", "account": "21405001 — تامينات اجتماعية - مقاولى باطن مشروع"}, {"code": "informal_labor", "name": "عمالة غير منتظمة", "side": "Customer", "account": "15202005 — تكاليف - اعمال توريد عمالة ذاتى \\" عادى - فنى \\" ( اعمال تحت التنفيذ )"}, {"code": "profit_tax", "name": "ضريبة أرباح", "side": "Customer", "account": "21402006 — جارى مصلحة الضرائب - ضريبة خصم واضافة"}, {"code": "stamp_duty", "name": "دمغة", "side": "Customer", "account": "21402007 — دمغة هندسية ( 0.0045 )"}, {"code": "advance_payment", "name": "تسوية دفعات مقدمة", "side": "Customer", "account": "21407001 — دفعات مقدمة من عميل/  شركة  المقاولون المتخصصون"}, {"code": "store_withdrawals", "name": "مسحوبات المخازن وخامات الموقع", "side": "Customer", "account": "15203049 — م . تشغيل - خامات دهانات ( اعمال تحت التنفيذ )"}, {"code": "social_insurance", "name": "تأمينات اجتماعية", "side": "Subcontractor", "account": "21405001 — تامينات اجتماعية - مقاولى باطن مشروع"}, {"code": "informal_labor", "name": "عمالة غير منتظمة", "side": "Subcontractor", "account": "15202005 — تكاليف - اعمال توريد عمالة ذاتى \\" عادى - فنى \\" ( اعمال تحت التنفيذ )"}, {"code": "profit_tax", "name": "ضريبة أرباح", "side": "Subcontractor", "account": "21402006 — جارى مصلحة الضرائب - ضريبة خصم واضافة"}, {"code": "stamp_duty", "name": "دمغة", "side": "Subcontractor", "account": "21402007 — دمغة هندسية ( 0.0045 )"}, {"code": "advance_payment", "name": "تسوية دفعات مقدمة", "side": "Subcontractor", "account": "21407001 — دفعات مقدمة من عميل/  شركة  المقاولون المتخصصون"}, {"code": "store_withdrawals", "name": "مسحوبات المخازن وخامات الموقع", "side": "Subcontractor", "account": "15203049 — م . تشغيل - خامات دهانات ( اعمال تحت التنفيذ )"}], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Customer"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Subcontractor"}]}	2026-10-18 12:44:11.142098	\N
338	1	Export	accounts	\N	\N	{"rows": 587, "format": "csv"}	2026-11-05 12:24:19.545863	127.0.0.1
100	1	Create	ContractDeductionRules	25	\N	{"rule_id": 25, "contract_id": 8, "settlement_side": "Customer", "code": "works_guarantee", "name_ar": "حجز ضمان الأعمال", "calculation_type": "Percent", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 80}	2026-10-18 12:44:10.81903	\N
102	1	Create	ContractDeductionRules	27	\N	{"rule_id": 27, "contract_id": 8, "settlement_side": "Subcontractor", "code": "retention_insurance", "name_ar": "تأمين محتجز", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 10}	2026-10-18 12:44:10.885278	\N
107	1	Create	ContractDeductionRules	32	\N	{"rule_id": 32, "contract_id": 8, "settlement_side": "Subcontractor", "code": "stamp_duty", "name_ar": "دمغة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 60}	2026-10-18 12:44:11.006246	\N
341	1	BackupCreate	Backup	-	\N	{"file": "financial_system_manual_20261105_143001.zip"}	2026-11-05 12:30:00.438059	127.0.0.1
101	1	Create	ContractDeductionRules	26	\N	{"rule_id": 26, "contract_id": 8, "settlement_side": "Customer", "code": "store_withdrawals", "name_ar": "مسحوبات المخازن وخامات الموقع", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 90}	2026-10-18 12:44:10.843948	\N
103	1	Create	ContractDeductionRules	28	\N	{"rule_id": 28, "contract_id": 8, "settlement_side": "Subcontractor", "code": "final_retention", "name_ar": "تأمين نهائي", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 20}	2026-10-18 12:44:10.907662	\N
108	1	Create	ContractDeductionRules	33	\N	{"rule_id": 33, "contract_id": 8, "settlement_side": "Subcontractor", "code": "advance_payment", "name_ar": "تسوية دفعات مقدمة", "calculation_type": "Fixed", "rate": "0", "base_type": "CurrentWork", "posting_side": "Credit", "cap_amount": null, "gl_account_id": null, "is_active": true, "sort_order": 70}	2026-10-18 12:44:11.028486	\N
112	1	Create	ItemCatalog	1	\N	{"code": "11501003", "name": "توريد بازلت 50/100", "unit": "وحدة", "account_id": 3, "inventory_item_id": 1, "is_active": true}	2026-10-18 12:45:34.005197	\N
113	1	Create	ItemCatalog	5	\N	{"code": "200", "name": "توريد بازلت 50/100", "unit": "وحدة", "account_id": 46, "inventory_item_id": null, "is_active": true}	2026-10-18 13:13:47.916919	\N
114	1	AutoLinkRules	Contracts	8	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Customer"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Subcontractor"}]}	2026-10-18 13:16:12.996095	\N
115	1	Create	TechnicalSettlementEstimates	2	\N	{"estimate_no": "1", "work_value": "50000.00", "status": "UnderReview"}	2026-10-18 13:37:37.488229	\N
116	1	AutoLinkRules	Contracts	8	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Customer"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Subcontractor"}]}	2026-10-18 13:39:17.206947	\N
117	1	AutoLinkRules	Contracts	8	\N	{"linked": [], "missing": [{"code": "retention_insurance", "name": "تأمين محتجز", "side": "Customer"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Customer"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Customer"}, {"code": "retention_insurance", "name": "تأمين محتجز", "side": "Subcontractor"}, {"code": "final_retention", "name": "تأمين نهائي", "side": "Subcontractor"}, {"code": "works_guarantee", "name": "حجز ضمان الأعمال", "side": "Subcontractor"}]}	2026-10-18 13:39:45.914748	\N
118	1	Create	ItemCatalog	6	\N	{"code": "215", "name": "توريدحديد 50/100", "unit": "طن", "account_id": 48, "inventory_item_id": null, "is_active": true}	2026-10-18 13:41:35.997687	\N
119	1	Create	PurchaseOrders	1	\N	{"order_no": "123", "total_amount": "10"}	2026-10-18 13:47:47.517706	\N
120	1	Approve	PurchaseOrders	1	\N	{"status": "Approved"}	2026-10-18 13:47:50.928714	\N
121	1	Receive	PurchaseOrders	1	\N	{"status": "Received"}	2026-10-18 13:48:03.561191	\N
122	1	Create	PurchaseOrders	2	\N	{"order_no": "124", "total_amount": "15750"}	2026-10-18 15:03:31.544423	\N
123	1	Create	TechnicalSettlementEstimates	3	\N	{"estimate_no": "2", "work_value": "25000.00", "status": "UnderReview"}	2026-10-18 15:09:49.824512	\N
124	1	Approve	PurchaseOrders	2	\N	{"status": "Approved"}	2026-10-18 15:11:59.864968	\N
125	1	Receive	PurchaseOrders	2	\N	{"status": "Received"}	2026-10-18 15:12:23.040383	\N
126	1	Create	JournalEntries	3	\N	{"entry_no": "JE-2026-000002"}	2026-10-18 15:18:59.691751	\N
127	1	Create	Users	2	\N	{"username": "ahmed.saqr", "roles": [2]}	2026-10-18 15:20:35.398537	\N
128	1	Update	Users	2	\N	{"is_active": true}	2026-10-18 15:23:11.860238	\N
129	1	MapAlias	CounterpartyAliases	1	\N	{"alias_name": "لوكس", "canonical_name": "ابراهيم"}	2026-10-18 15:32:17.677619	\N
136	1	Post	JournalEntries	3	{"status": "Draft"}	{"status": "Posted"}	2026-10-18 15:34:45.157904	\N
137	1	Create	ChartOfAccounts	586	\N	{"account_code": "1500312", "account_name_ar": "اخري", "parent_account_id": 11, "classification_id": 4, "normal_balance": "CR", "opening_debit": "100000", "opening_credit": "0", "is_active": true}	2026-10-18 15:36:43.747883	\N
149	1	DeleteCascade	TechnicalSettlementEstimates	3	{"estimate_no": "2", "status": "UnderReview"}	\N	2026-10-18 15:45:38.780251	\N
150	1	DeleteCascade	TechnicalSettlementEstimates	2	{"estimate_no": "1", "status": "UnderReview"}	\N	2026-10-18 15:45:45.566229	\N
151	1	DeleteCascade	Contracts	8	{"contract_id": 8, "request_id": null, "contract_no": "1/50", "title": "1", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-18", "original_value": "500000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 10:32:59.633846"}	{"deleted_settlements": 0}	2026-10-18 15:46:55.001602	\N
152	1	DeleteCascade	Contracts	7	{"contract_id": 7, "request_id": null, "contract_no": "5", "title": "k", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "10000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 08:10:54.956421"}	{"deleted_settlements": 0}	2026-10-18 15:46:58.343105	\N
153	1	DeleteCascade	Contracts	6	{"contract_id": 6, "request_id": null, "contract_no": "2026", "title": "بازلت", "client_name": "ابراهيم", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-12-12", "original_value": "200000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 07:21:50.609376"}	{"deleted_settlements": 0}	2026-10-18 15:47:01.371519	\N
154	1	DeleteCascade	Contracts	5	{"contract_id": 5, "request_id": null, "contract_no": "1/49", "title": "تموين", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 06:45:36.009535"}	{"deleted_settlements": 0}	2026-10-18 15:47:04.651103	\N
155	1	DeleteCascade	Contracts	4	{"contract_id": 4, "request_id": null, "contract_no": "يي", "title": "JV", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-07", "original_value": "250000000.00", "status": "Active", "notes": "ي", "created_at": "2026-10-17 20:21:30.859146"}	{"deleted_settlements": 0}	2026-10-18 15:47:07.16262	\N
156	1	DeleteCascade	Contracts	3	{"contract_id": 3, "request_id": null, "contract_no": "1/48", "title": "c", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "0.00", "status": "Active", "notes": "توريد", "created_at": "2026-10-17 11:44:50.136388"}	{"deleted_settlements": 0}	2026-10-18 15:47:09.913339	\N
157	1	DeleteCascade	Contracts	2	{"contract_id": 2, "request_id": null, "contract_no": "1", "title": "بصس", "client_name": "يثس", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-10-23", "original_value": "5000.00", "status": "Active", "notes": "", "created_at": "2026-10-17 10:46:33.442603"}	{"deleted_settlements": 0}	2026-10-18 15:47:12.654334	\N
158	1	DeleteCascade	Contracts	1	{"contract_id": 1, "request_id": null, "contract_no": "2", "title": "ؤ", "client_name": "ؤص", "project_id": null, "start_date": "2026-10-17", "end_date": "2026-11-06", "original_value": "22.00", "status": "Active", "notes": "ثرير س سش\\n\\n\\nعةةت\\nةظ\\nةظ\\nظ\\nة", "created_at": "2026-10-17 10:20:32.904112"}	{"deleted_settlements": 0}	2026-10-18 15:47:17.042585	\N
159	1	Cancel	JournalEntries	3	{"status": "Posted"}	{"status": "Reversed"}	2026-10-18 15:49:18.403661	\N
160	1	Cancel	JournalEntries	2	{"status": "Posted"}	{"status": "Reversed"}	2026-10-18 15:49:24.913088	\N
161	1	Create	InventoryWarehouses	2	\N	{"code": "215", "name": "السولار", "location": "تحالف", "is_active": true}	2026-10-18 15:59:53.552759	\N
162	1	Create	InventoryItems	2	\N	{"code": "250", "name": "سولار", "category": "جاز", "unit": "لتر", "min_quantity": "0", "is_active": true}	2026-10-18 16:01:00.113643	\N
163	1	Create	PurchaseOrders	3	\N	{"order_no": "PO-2026-000003", "total_amount": "8000"}	2026-10-18 16:01:28.963832	\N
164	1	Approve	PurchaseOrders	3	\N	{"status": "Approved"}	2026-10-18 16:02:23.567953	\N
165	1	Receive	PurchaseOrders	3	\N	{"status": "Received"}	2026-10-18 16:02:45.995616	\N
166	1	Create	PurchaseOrders	4	\N	{"order_no": "PO-2026-000004", "total_amount": "225000"}	2026-10-18 16:12:29.57551	\N
167	1	Approve	PurchaseOrders	4	\N	{"status": "Approved"}	2026-10-18 16:12:33.405957	\N
168	1	Receive	PurchaseOrders	4	\N	{"status": "Received"}	2026-10-18 16:19:34.089323	\N
169	1	Create	Contracts	9	\N	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000", "status": "Draft", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	2026-10-18 16:24:54.838008	\N
170	1	SubmitForApproval	Contracts	9	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Draft", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "PendingApproval", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	2026-10-18 16:25:06.26246	\N
171	1	ApproveAndActivate	Contracts	9	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "PendingApproval", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Active", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	2026-10-18 16:25:40.92121	\N
172	1	Create	Contracts	10	\N	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000", "status": "Draft", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	2026-10-18 19:33:54.795895	127.0.0.1
173	1	Create	ContractItems	75	\N	{"contract_id": 10, "item_no": "1", "catalog_item_id": 1, "account_id": 3, "description": "توريد بازلت 50/100", "unit": "وحدة", "quantity": "500", "unit_price": "100"}	2026-10-18 19:33:54.810124	127.0.0.1
174	1	Create	ContractItems	76	\N	{"contract_id": 10, "item_no": "2", "catalog_item_id": 5, "account_id": 46, "description": "توريد بازلت 50/100", "unit": "وحدة", "quantity": "100", "unit_price": "300"}	2026-10-18 19:33:54.813255	127.0.0.1
175	1	SubmitForApproval	Contracts	10	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000.00", "status": "Draft", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	2026-10-18 19:34:12.182622	127.0.0.1
176	1	ApproveAndActivate	Contracts	10	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000.00", "status": "PendingApproval", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	2026-10-18 19:35:25.107656	127.0.0.1
177	1	Create	TechnicalSettlementEstimates	4	\N	{"estimate_no": "TE-0001", "work_value": "24000.00", "status": "UnderReview"}	2026-10-18 20:18:18.285612	127.0.0.1
178	1	Approve	TechnicalSettlementEstimates	4	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 7, "work_value": "24000.00"}	2026-10-18 20:18:23.791321	127.0.0.1
179	1	Approve	ContractSettlements	7	\N	{"settlement_id": 7, "contract_id": 10, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "FIN-000004", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "24000.00", "cumulative_work_value": "24000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "24000.00", "status": "Approved", "journal_entry_id": null, "notes": "تم إنشاؤه تلقائياً من المستخلص الفني TE-0001."}	2026-10-18 20:25:14.272052	127.0.0.1
180	1	Create	Contracts	11	\N	{"contract_id": 11, "request_id": null, "contract_no": "CT-2026-000011", "title": "عبد الرحمن", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2027-01-01", "original_value": "16000000", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-18 21:08:57.932289"}	2026-10-18 21:08:57.944147	127.0.0.1
181	1	Create	ContractDeductionRules	36	\N	{"contract_id": 11, "settlement_side": "Customer", "code": "retention_insurance", "name_ar": "تأمين محجوز", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": 56, "is_active": true, "sort_order": 10}	2026-10-18 21:08:57.976434	127.0.0.1
182	1	Create	ContractDeductionRules	37	\N	{"contract_id": 11, "settlement_side": "Customer", "code": "final_retention", "name_ar": "تأمين نهائي", "calculation_type": "Percent", "rate": "2", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": 56, "is_active": true, "sort_order": 20}	2026-10-18 21:08:57.980508	127.0.0.1
183	1	Create	ContractDeductionRules	38	\N	{"contract_id": 11, "settlement_side": "Customer", "code": "profit_tax", "name_ar": "ضريبة أرباح", "calculation_type": "Percent", "rate": "1", "base_type": "CurrentWork", "posting_side": "Debit", "cap_amount": null, "gl_account_id": 56, "is_active": true, "sort_order": 30}	2026-10-18 21:08:57.983057	127.0.0.1
184	1	ReturnForChanges	Contracts	11	{"contract_id": 11, "request_id": null, "contract_no": "CT-2026-000011", "title": "عبد الرحمن", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2027-01-01", "original_value": "16000000.00", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-18 21:08:57.932289"}	{"contract_id": 11, "request_id": null, "contract_no": "CT-2026-000011", "title": "عبد الرحمن", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2027-01-01", "original_value": "16000000.00", "status": "Returned", "notes": "", "created_at": "2026-10-18 21:08:57.932289"}	2026-10-18 21:09:08.454875	127.0.0.1
185	1	DeleteCascade	Contracts	11	{"contract_id": 11, "request_id": null, "contract_no": "CT-2026-000011", "title": "عبد الرحمن", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2027-01-01", "original_value": "16000000.00", "status": "Returned", "notes": "", "created_at": "2026-10-18 21:08:57.932289"}	{"deleted_settlements": 0}	2026-10-18 21:10:08.401979	127.0.0.1
186	1	Create	TechnicalSettlementEstimates	5	\N	{"estimate_no": "TE-0002", "work_value": "43000.00", "status": "UnderReview"}	2026-10-18 21:14:55.003655	127.0.0.1
187	1	Approve	TechnicalSettlementEstimates	5	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 8, "work_value": "43000.00"}	2026-10-18 21:15:46.764002	127.0.0.1
193	1	Create	TechnicalSettlementEstimates	6	\N	{"estimate_no": "TE-0003", "work_value": "13000.00", "status": "UnderReview"}	2026-10-18 21:20:56.464613	127.0.0.1
192	1	Approve	ContractSettlements	8	\N	{"settlement_id": 8, "contract_id": 10, "settlement_side": "Customer", "sequence_no": 2, "settlement_no": "FIN-000005", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "43000.00", "cumulative_work_value": "67000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "43000.00", "status": "Approved", "journal_entry_id": null, "notes": "تم إنشاؤه تلقائياً من المستخلص الفني TE-0002."}	2026-10-18 21:19:42.072443	127.0.0.1
194	1	Approve	TechnicalSettlementEstimates	6	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 9, "work_value": "13000.00"}	2026-10-18 21:21:12.100241	127.0.0.1
195	1	UpdateDeductions	ContractSettlements	9	{"deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "8500.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "3000.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "1000.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "1.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "13000.00"}	{"deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "8500.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "3000.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "1000.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "1.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "499.00"}	2026-10-18 21:22:15.376177	127.0.0.1
196	1	Approve	ContractSettlements	9	\N	{"settlement_id": 9, "contract_id": 10, "settlement_side": "Customer", "sequence_no": 3, "settlement_no": "FIN-000006", "settlement_date": "2026-10-18", "counterparty_name": "لوكس", "work_value": "13000.00", "cumulative_work_value": "80000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "499.00", "status": "Approved", "journal_entry_id": null, "notes": "تم إنشاؤه تلقائياً من المستخلص الفني TE-0003."}	2026-10-18 21:22:35.585952	127.0.0.1
209	1	Create	ContractItems	77	\N	{"item_id": 77, "contract_id": 9, "item_no": "1", "description": "توريد", "unit": "طن", "quantity": "300", "unit_price": "250", "total": "75000.00", "catalog_item_id": 1, "account_id": 3, "project_id": null}	2026-10-19 07:25:29.595246	127.0.0.1
210	1	Create	ContractItems	78	\N	{"item_id": 78, "contract_id": 9, "item_no": "2", "description": "توريد ", "unit": "وحده", "quantity": "3500", "unit_price": "160", "total": "560000.00", "catalog_item_id": 1, "account_id": 3, "project_id": null}	2026-10-19 07:27:04.934678	127.0.0.1
211	1	Create	TechnicalSettlementEstimates	7	\N	{"estimate_no": "TE-0001", "work_value": "357500.00", "status": "UnderReview"}	2026-10-19 07:27:51.017458	127.0.0.1
212	1	Approve	TechnicalSettlementEstimates	7	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 10, "work_value": "357500.00"}	2026-10-19 07:28:35.619242	127.0.0.1
213	1	Approve	ContractSettlements	10	\N	{"settlement_id": 10, "contract_id": 9, "settlement_side": "Customer", "sequence_no": 1, "settlement_no": "FIN-000007", "settlement_date": "2026-10-19", "counterparty_name": "لوكس", "work_value": "357500.00", "cumulative_work_value": "357500.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}, "vat_amount": "0.00", "net_amount": "357500.00", "status": "Approved", "journal_entry_id": null, "notes": "تم إنشاؤه تلقائياً من المستخلص الفني TE-0001."}	2026-10-19 07:29:21.710157	127.0.0.1
254	1	DeleteCascade	TechnicalSettlementEstimates	7	{"estimate_no": "TE-0001", "status": "TechnicallyApproved"}	\N	2026-10-19 07:49:30.116641	127.0.0.1
255	1	DeleteCascade	ContractSettlements	10	{"settlement_no": "FIN-000007", "status": "Approved", "journal_entry_id": null}	\N	2026-10-19 07:49:30.138431	127.0.0.1
256	1	DeleteCascade	TechnicalSettlementEstimates	6	{"estimate_no": "TE-0003", "status": "TechnicallyApproved"}	\N	2026-10-19 07:49:34.152096	127.0.0.1
257	1	DeleteCascade	ContractSettlements	9	{"settlement_no": "FIN-000006", "status": "Approved", "journal_entry_id": null}	\N	2026-10-19 07:49:34.161113	127.0.0.1
258	1	DeleteCascade	TechnicalSettlementEstimates	5	{"estimate_no": "TE-0002", "status": "TechnicallyApproved"}	\N	2026-10-19 07:49:35.91605	127.0.0.1
259	1	DeleteCascade	ContractSettlements	8	{"settlement_no": "FIN-000005", "status": "Approved", "journal_entry_id": null}	\N	2026-10-19 07:49:35.926066	127.0.0.1
260	1	DeleteCascade	TechnicalSettlementEstimates	4	{"estimate_no": "TE-0001", "status": "TechnicallyApproved"}	\N	2026-10-19 07:49:37.841574	127.0.0.1
261	1	DeleteCascade	ContractSettlements	7	{"settlement_no": "FIN-000004", "status": "Approved", "journal_entry_id": null}	\N	2026-10-19 07:49:37.851019	127.0.0.1
262	1	Create	TechnicalSettlementEstimates	8	\N	{"estimate_no": "TE-0001", "work_value": "35000.00", "status": "UnderReview"}	2026-10-19 07:50:52.821477	127.0.0.1
263	1	Approve	TechnicalSettlementEstimates	8	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 11, "work_value": "35000.00"}	2026-10-19 07:51:31.651252	127.0.0.1
264	1	Create	ChartOfAccounts	587	\N	{"account_code": "1990", "account_name_ar": "سامي", "parent_account_id": 267, "classification_id": 13, "normal_balance": "DR", "opening_debit": "25000", "opening_credit": "0", "is_active": true}	2026-10-19 09:50:07.518962	127.0.0.1
265	1	Approve	ContractSettlements	11	\N	{"settlement_id": 11, "contract_id": 10, "settlement_side": "Subcontractor", "sequence_no": 1, "settlement_no": "FIN-000008", "settlement_date": "2026-10-19", "counterparty_name": "لوكس", "work_value": "35000.00", "cumulative_work_value": "35000.00", "deductions": {"ADVANCE_PAYMENT": {"name": "دفعة مقدمة", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "RETENTION": {"name": "تأمين محجوز", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "FINAL_INSURANCE": {"name": "تأمين نهائي", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "PROFIT_TAX": {"name": "ضرائب أرباح", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ENGINEERING_STAMP": {"name": "دمغات هندسية", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "UNION_STAMP": {"name": "دمغات اتحاد", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "STORE_WITHDRAWALS": {"name": "مسحوبات ومصاريف مخازن", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "TRANSPORT": {"name": "نقل", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "DIESEL": {"name": "سولار", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "MEALS": {"name": "وجبات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}, "ADDITIONS": {"name": "تعليات", "amount": "0.00", "account_id": null, "posting_side": "Credit"}}, "vat_amount": "0.00", "net_amount": "35000.00", "status": "Approved", "journal_entry_id": null, "notes": "تم إنشاؤه تلقائياً من المستخلص الفني TE-0001."}	2026-10-19 10:22:37.656545	127.0.0.1
266	1	DeleteCascade	TechnicalSettlementEstimates	8	{"estimate_no": "TE-0001", "status": "TechnicallyApproved"}	\N	2026-10-19 10:23:26.814984	127.0.0.1
267	1	DeleteCascade	ContractSettlements	11	{"settlement_no": "FIN-000008", "status": "Approved", "journal_entry_id": null}	\N	2026-10-19 10:23:26.827206	127.0.0.1
268	1	Create	Contracts	12	\N	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	2026-10-19 10:25:44.386731	127.0.0.1
269	1	Create	ContractItems	79	\N	{"contract_id": 12, "item_no": "1", "catalog_item_id": 5, "account_id": 46, "description": "توريد بازلت 50/100", "unit": "وحدة", "quantity": "200", "unit_price": "300"}	2026-10-19 10:25:44.395717	127.0.0.1
270	1	EngineeringApprove	Contracts	12	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "PendingFinancial", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	2026-10-19 10:25:59.961732	127.0.0.1
271	1	ReturnForChanges	Contracts	12	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "PendingFinancial", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "Returned", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	2026-10-19 10:26:11.913164	127.0.0.1
272	1	SubmitForApproval	Contracts	12	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "Returned", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	2026-10-19 10:26:15.111793	127.0.0.1
273	1	DeleteCascade	Contracts	12	{"contract_id": 12, "request_id": null, "contract_no": "CT-2026-000012", "title": "يث", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "60000.00", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:25:44.384936"}	{"deleted_settlements": 0}	2026-10-19 10:26:21.752757	127.0.0.1
274	1	Create	Contracts	13	\N	{"contract_id": 13, "request_id": null, "contract_no": "CT-2026-000013", "title": "ي", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "20000", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:27:17.561264"}	2026-10-19 10:27:17.563567	127.0.0.1
275	1	Create	ContractItems	80	\N	{"contract_id": 13, "item_no": "1", "catalog_item_id": 5, "account_id": 46, "description": "توريد بازلت 50/100", "unit": "وحدة", "quantity": "200", "unit_price": "100"}	2026-10-19 10:27:17.56773	127.0.0.1
276	1	EngineeringApprove	Contracts	13	{"contract_id": 13, "request_id": null, "contract_no": "CT-2026-000013", "title": "ي", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "20000.00", "status": "PendingEngineering", "notes": "", "created_at": "2026-10-19 10:27:17.561264"}	{"contract_id": 13, "request_id": null, "contract_no": "CT-2026-000013", "title": "ي", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "20000.00", "status": "PendingFinancial", "notes": "", "created_at": "2026-10-19 10:27:17.561264"}	2026-10-19 10:27:20.942941	127.0.0.1
277	1	ApproveAndActivate	Contracts	13	{"contract_id": 13, "request_id": null, "contract_no": "CT-2026-000013", "title": "ي", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "20000.00", "status": "PendingFinancial", "notes": "", "created_at": "2026-10-19 10:27:17.561264"}	{"contract_id": 13, "request_id": null, "contract_no": "CT-2026-000013", "title": "ي", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-19", "end_date": "2026-11-07", "original_value": "20000.00", "status": "Active", "notes": "", "created_at": "2026-10-19 10:27:17.561264"}	2026-10-19 10:27:41.749515	127.0.0.1
278	1	Create	TechnicalSettlementEstimates	9	\N	{"estimate_no": "TE-0001", "work_value": "10000.00", "status": "UnderReview"}	2026-10-19 10:28:26.752368	127.0.0.1
279	1	Approve	TechnicalSettlementEstimates	9	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 12, "work_value": "10000.00"}	2026-10-19 10:28:31.710437	127.0.0.1
281	1	Approve	TechnicalSettlementEstimates	10	\N	{"status": "TechnicallyApproved", "financial_settlement_id": 13, "work_value": "10000.00"}	2026-10-19 10:29:18.050643	127.0.0.1
280	1	Create	TechnicalSettlementEstimates	10	\N	{"estimate_no": "TE-0002", "work_value": "10000.00", "status": "UnderReview"}	2026-10-19 10:29:16.144372	127.0.0.1
282	1	Update	FinancialChecks	1	\N	{"status": "مُرتجع"}	2026-10-19 12:07:26.044813	127.0.0.1
283	1	Update	TreasuryAccounts	1	{"name_ar": "JV", "gl_account_id": 2, "gl_account_code": "11501002"}	{"name_ar": "البنك التجاري الدولي CIB (جنيه مصري)", "gl_account_id": 140, "gl_account_code": "15302005"}	2026-10-22 07:35:17.667938	127.0.0.1
284	1	Update	TreasuryAccounts	1	\N	{"checks": "ChecksCib"}	2026-10-22 07:35:27.249405	127.0.0.1
285	1	Create	FinancialChecks	2	\N	{"check_number": "1666", "check_type": "OUTGOING", "amount": "25000", "due_date": "2026-11-07", "party_account_id": 1, "treasury_account_id": 1, "drawee_bank": "25000", "project_brand": "عام", "description": "توريد"}	2026-10-22 08:07:36.018867	127.0.0.1
286	1	Create	Beneficiaries	1	\N	{"code": "21", "name_ar": "محمد", "bank_account_number": "100000000000"}	2026-10-22 08:09:27.683863	127.0.0.1
287	1	Create	Checks	1	\N	{"check_book_no": "1", "sequence_no": 1, "check_no": "158", "check_date": "2026-10-22", "beneficiary_id": 1, "amount": "25685220", "purchase_order_no": "120", "project_id": 1, "settlement_id": null, "description": "توريد"}	2026-10-22 08:20:40.382187	127.0.0.1
288	1	Update	FinancialChecks	2	\N	{"status": "مُرتجع"}	2026-10-23 18:10:02.764866	127.0.0.1
289	1	Create	JournalEntries	4	\N	{"entry_no": "JE-2026-000003"}	2026-11-03 21:27:45.387068	127.0.0.1
290	1	Post	JournalEntries	4	{"status": "Draft"}	{"status": "Posted"}	2026-11-03 21:28:04.162628	127.0.0.1
291	1	Create	JournalEntries	5	\N	{"entry_no": "JE-2026-000004"}	2026-11-03 21:32:04.65438	127.0.0.1
292	1	Post	JournalEntries	5	{"status": "Draft"}	{"status": "Posted"}	2026-11-03 21:32:14.456176	127.0.0.1
293	1	Update	ChartOfAccounts	242	{"account_code": "15409022", "account_name_ar": "مقاولى باطن - دفعات مقدمه /  شركة", "parent_account_id": null, "classification_id": 11, "normal_balance": "DR", "opening_debit": "0.00", "opening_credit": "0.00", "is_active": true}	{"account_code": "15409022", "account_name_ar": "مقاولى باطن  /  شركة لوكس تو ايه", "parent_account_id": null, "classification_id": 11, "normal_balance": "DR", "opening_debit": "0.00", "opening_credit": "0.00", "is_active": true}	2026-11-03 21:44:43.214157	127.0.0.1
294	1	Create	JournalEntries	6	\N	{"entry_no": "JE-2026-000005"}	2026-11-03 21:45:48.614886	127.0.0.1
295	1	Post	JournalEntries	6	{"status": "Draft"}	{"status": "Posted"}	2026-11-03 21:45:55.591434	127.0.0.1
296	1	Create	JournalEntries	7	\N	{"entry_no": "JE-2026-000006"}	2026-11-03 21:47:10.214052	127.0.0.1
297	1	Post	JournalEntries	7	{"status": "Draft"}	{"status": "Posted"}	2026-11-03 21:47:15.939152	127.0.0.1
298	1	Create	JournalEntries	8	\N	{"entry_no": "JE-2026-000007"}	2026-11-03 21:50:13.962236	127.0.0.1
299	1	Post	JournalEntries	8	{"status": "Draft"}	{"status": "Posted"}	2026-11-03 21:50:21.214001	127.0.0.1
306	1	DeleteCascade	Contracts	10	{"contract_id": 10, "request_id": null, "contract_no": "CT-2026-000010", "title": "اول عقد", "client_name": "لوكس", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-18", "original_value": "80000.00", "status": "Active", "notes": "", "created_at": "2026-10-18 19:33:54.790207"}	{"deleted_settlements": 0}	2026-11-04 14:03:02.24837	127.0.0.1
313	1	DeleteCascade	Contracts	9	{"contract_id": 9, "request_id": null, "contract_no": "1-50", "title": "domas", "client_name": "doma", "project_id": null, "start_date": "2026-10-18", "end_date": "2026-11-07", "original_value": "1000000.00", "status": "Active", "notes": "توريد", "created_at": "2026-10-18 16:24:54.834612"}	{"deleted_settlements": 0}	2026-11-04 14:03:08.657433	127.0.0.1
\.


--
-- TOC entry 5591 (class 0 OID 18664)
-- Dependencies: 293
-- Data for Name: BankReconciliationLines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."BankReconciliationLines" ("LineId", "ReconciliationId", "TransactionDate", "Inflow", "Outflow", "Description", "CheckNo", "Status", "Recipient", "IsMatched") FROM stdin;
\.


--
-- TOC entry 5569 (class 0 OID 18378)
-- Dependencies: 271
-- Data for Name: BankReconciliations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."BankReconciliations" ("ReconciliationId", "TreasuryAccountId", "ReconciliationDate", "BookBalance", "StatementBalance", "PreparedBy", "Notes", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5559 (class 0 OID 18266)
-- Dependencies: 261
-- Data for Name: Beneficiaries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Beneficiaries" ("BeneficiaryId", "Code", "NameAr", "LinkedAccountId", "DefaultProjectId", "BankAccountNumber", "IsActive") FROM stdin;
1	21	محمد	\N	\N	100000000000	t
\.


--
-- TOC entry 5616 (class 0 OID 19242)
-- Dependencies: 318
-- Data for Name: CatalogItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."CatalogItems" ("CatalogItemId", "Code", "Name", "Unit", "Category", "DefaultUnitPrice", "RevenueAccountId", "ExpenseAccountId", "InventoryAccountId", "InventoryItemId", "IsActive", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5540 (class 0 OID 18055)
-- Dependencies: 242
-- Data for Name: ChartOfAccounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ChartOfAccounts" ("AccountId", "AccountCode", "AccountNameAr", "ParentAccountId", "ClassificationId", "NormalBalance", "OpeningDebit", "OpeningCredit", "IsActive", "CreatedAt", "StatementType") FROM stdin;
1	11301001	اصول ثابتة - الالآت و المعدات	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
2	11501002	عدد و اداوات و قوالب - شدات معدنيه	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
3	11501003	اصول ثابتة - كرفانات واكشاك امن وحراسه	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
4	11501004	اصول ثابتة - ميزان بسكول	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
5	11601001	اثاث و مفروشات	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
6	11601002	اجهزة كمبيوتر وملحقاتها	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
7	11601003	اجهزة كهربائية	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
8	11601004	سيارات - ملاكي	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
9	11601005	أجهزة مساحة ورصد و GPS	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
10	11701001	سيارات - خلاطة خرسانة	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
11	11801001	برامج - سوفت	\N	2	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
12	11901001	اصول ثابتة - تجهيزات وتشطيبات	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
13	12301001	مجمع الاهلاكات - الالآت والمعدات - AA	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
14	12401001	مجمع الاهلاكات - عدد و اداوات و قوالب - شدات معدنية	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
15	12501001	مجمع الاهلاكات - عدد و اداوات و قوالب - AA	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
16	12601001	مجمع الاهلاكات - اجهزه كمبيوتر وملحقاتها فرعى	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
17	12701001	مجمع الاهلاكات - اثاث ومفروشات فرعى	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
18	12801001	مجمع الاهلاكات - اجهزه كهربائيه فرعى	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
19	12801002	مجمع الاهلاكات -  ميزان بسكول	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
20	12801003	مجمع الاهلاكات -  تجهيزات وتشطيبات	\N	1	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
21	12901001	مجمع الاهلاكات - اصول غير ملموسه فرعى	\N	2	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
22	14101001	استثمارات ماليه	\N	3	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
23	15101001	مخزون موقع	\N	4	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
24	15201001	م . اجور و مرتبات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
25	15201002	م . مكافاة - منح للعاملين ( اعمال تحت النفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
26	15201003	اجور عماله ذاتيه ( سراكى ) ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
27	15202001	تكاليف - اعمال تجهيزات المواقع ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
28	15202002	تكاليف - اعمال مبانى ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
29	15202003	تكاليف - اعمال كهرباء ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
30	15202004	تكاليف - اعمال مساحة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
31	15202005	تكاليف - اعمال توريد عمالة ذاتى " عادى - فنى " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
32	15202006	تكاليف - اعمال حفر وانشاء احواض الترسيب  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
33	15202007	تكاليف - اعمال تعتيق وفرز احجار ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
34	15202008	تكاليف - اعمال توريد مياه -( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
35	15202009	تكاليف - اعمال مصنعيات خرسانة بالمتر المكعب ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
36	15202010	تكاليف - اعمال صب وتوريد خرسانة بالمتر المكعب ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
37	15202011	تكاليف - اعمال مصنعيات صب وفرمجة كتل خرسانة الحماية البحرية  ( تترا بودز ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
38	15202012	تكاليف اعمال - تشوينات رمل ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
39	15202013	تكاليف اعمال - تشوينات سن ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
40	15202014	تكاليف اعمال - متكامله ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
41	15202015	تكاليف - اعمال صحى وسباكه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
42	15202016	تكاليف - اعمال دهانات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
43	15202017	تكاليف - اعمال توريد ومصنعيات تركيب سيراميك ورخام وجرانيت ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
44	15202018	تكاليف - اعمال مدنيه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
45	15202020	تكاليف اعمال - اخرى ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
46	15202021	تكاليف - اعمال عزل ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
47	15202022	تكاليف - اعمال زراعه ولاند سكيب( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
48	15202023	تكاليف - اعمال طرق ورصف ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
49	15202024	تكاليف - اعمال تكييف وحريق ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
138	15302003	البنك - بنك العقاري المصري ( جنيه مصري )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
50	15202025	تكاليف - اعمال الكتروميكانيكال ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
51	15202026	تكاليف - اعمال نحاته وخزف وديكور ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
52	15202027	تكاليف - اعمال نجاره ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
53	15202028	تكاليف - اعمال خوازيق  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
54	15202029	تكاليف - اعمال ترابية - طبقات اساس  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
55	15202030	تكاليف - اعمال تكسير ونحاته  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
56	15202031	تكاليف - اعمال توريد ومصنعيات حديد واعمال خرسانة والبردورة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
57	15202032	تكاليف - اعمال السلامة والصحة المهنية ( HSE ) ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
58	15202033	تكاليف - اعمال مصنعيات تشكيل حديد تسليح ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
59	15202034	تكاليف - اعمال مصنعيات تركيب بارتشنات للمكاتب بالساندوتش بانلز ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
60	15202035	تكاليف - اعمال انشاء وتنفيذ الحاجز المؤقت   ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
61	15203001	مصاريف مطبوعات وتصميمات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
62	15203002	م . تشغيل - تجهيز موقع ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
63	15203003	م . تشغيل - رسوم ومصاريف ادارية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
64	15203004	م . تشغيل - مصاريف علاج ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
65	15203005	م . تشغيل - م . يفط و لوحات اعلانية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
66	15203006	م . تشغيل - م .نقل مخلفات بانواعها  " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
67	15203007	م . تشغيل - م . انتقالات داخلية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
68	15203009	م . تشغيل - م . ايجار سيارت " ملاكى - سنجل - دوبل كابينة " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
69	15203010	م . تشغيل - م . استشارات هندسية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
70	15203011	م . تشغيل - م . قطع غيار ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
71	15203012	م . تشغيل - م . مستلزمات أمن صناعى ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
72	15203013	م . تشغيل - اقامات ( اعمال تحت التنفيذ)	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
73	15203014	م . تشغيل - م . كارتات طرق و موازين ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
74	15203015	م . تشغيل - م . ايجار معدات - مولدات كهربائية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
75	15203016	م . تشغيل - م . اعمال نظافة و مكافحة حشرات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
76	15203017	م . تشغيل - م . ضيافة و بوفيه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
77	15203018	م . تشغيل - م . وجبات غذائية للعاملين بالمواقع ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
78	15203019	م . تشغيل - م . اداوات مكتبية و كتابية للمواقع واحبار ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
79	15203020	م . تشغيل - م . ايجار نقل ثقيل " تريلا - كساحات " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
80	15203021	م . تشغيل - م . عدد و اداوات و قوالب - اداوات مساعدة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
81	15203022	م . تشغيل - م . وقود " سولار " للمعدات و السيارت ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
82	15203023	م . تشغيل - م . وقود " بنزين" للسيارت ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
83	15203024	م . تشغيل - " م . زيوت و شحوم و غسيل " للمعدات و السيارت ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
84	15203025	م . تشغيل - اكرامية - " اكراميات - عمولات - سمسرة " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
85	15203026	م . تشغيل - م . ايجار " سكن العاملين - مقر ادارى - ... غيره " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
86	15203027	م . تشغيل - م . نت - تليفون ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
87	15203028	م . تشغيل - م . مستلزمات كمبيوتر ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
88	15203029	م . تشغيل - م . استهلاكات سكن العاملين " مياه - كهرباء - غاز " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
89	15203030	م . تشغيل - م .اصلاح و صيانة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
90	15203031	م . تشغيل - م . عدد و اداوات صغيرة " مساعدة للعمل " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
91	15203032	م . تشغيل - م . مستلزمات كهربائية " كشافات - انارة " ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
207	15405015	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
92	15203033	م . تشغيل - مادة خرسانية - المحطة الخرسانية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
93	15203034	م . تشغيل - مادة مانع تسريب- محطة المياه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
94	15203035	م . تشغيل - م . توريد عمالة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
95	15203036	م . تشغيل - م.زيارة و معاينة شراء سيارات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
96	15203037	م . تشغيل - م.بدل سفر ( اعمال تحت التنفيذ)	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
97	15203038	م . تشغيل - شراء حديد مسلح ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
98	15203039	م . تشغيل - شراء اسمنت ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
99	15203040	م . تشغيل - شراء طوب و حجر ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
100	15203041	م . تشغيل - مشتريات متنوعة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
101	15203042	م . تشغيل - م . شحن ونقل ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
102	15203043	م . تشغيل - م . حراسة و امن المواقع ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
103	15203044	م . تشغيل م . تراخيص سيارات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
104	15203045	م . تشغيل م . مستلزمات صحى وسباكه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
105	15203046	م . تشغيل م . مستلزمات معدنيه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
106	15203047	م . تشغيل م . سيراميك ورخام ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
107	15203048	م . تشغيل م . اخشاب والوميتال ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
108	15203049	م . تشغيل - خامات دهانات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
109	15203050	م . تشغيل - خامات عزل ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
110	15203051	م . تشغيل - خامات بيتومين ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
111	15203052	م . تشغيل - تامين طبي ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
112	15203053	م . تشغيل - تجارب معمل  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
113	15203054	م . تشغيل - توريد احجار دلوميت  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
114	15203055	م . تشغيل - م .اصلاح و صيانة سيارات ملاكي وجراج ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
115	15203056	م . تشغيل - م .نقل كتل خرسانية شامل التريلات والاوناش والمعدات الازمة ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
116	15203057	م . تشغيل - م . نثريات (مخالفات مرورية وخلافه ) ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
117	15203058	م . تشغيل - توريد احجار بازلت  ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
118	15204001	مصروف اهلاك الالات والمعدات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
119	15204002	مصروف اهلاك العدد والادوات والشدة المعدنية ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
120	15204003	مصروف اهلاك كرفانات واكشاك امن وحراسه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
121	15204004	مصروف اهلاك الاثاث والمفروشات ( اعمال تحت التنفيذ)	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
122	15204005	مصروف اهلاك اجهزه كهربائيه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
123	15204006	مصروف اهلاك اجهزه كمبيوتر وملحقاتها ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
124	15204007	مصروف اهلاك ميزان بسكول ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
125	15204008	مصروف اهلاك تجهيزات وتشطيبات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
126	15205001	تكاليف - ضرائب القيمه المضافه الخاصه بمحطه الخرسانه ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
127	15205002	م . بنكيه - تحصيل شيكات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
128	15205003	م . بنكيه - خطابات ضمان ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
129	15205004	تكاليف - استقطاعات المستخلصات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
130	15205005	م . تشغيل - غرامات ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
131	15205006	مصروفات تامينات اجتماعيه عملاء ( اعمال تحت التنفيذ)	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
132	15205007	م . وثائق تامين ( اعمال تحت التنفيذ)	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
133	15205008	م . تشغيل - سكن فندقي ( اعمال تحت التنفيذ )	\N	5	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
134	15301001	الصندوق - خزينة  ( جنيه مصري )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
135	15301002	الصندوق - خزينة  ( دولار امريكي )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
136	15302001	البنك - بنك القاهرة ( جنيه مصري )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
137	15302002	البنك - بنك القاهرة (  دولار امريكي )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
208	15405016	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
139	15302004	البنك - بنك العقاري المصري (  دولار امريكي )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
140	15302005	البنك - بنك التجاري الدولي CIB  ( جنيه مصري )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
141	15302006	البنك - بنك التجاري الدولي  (  دولار امريكي )	\N	6	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
142	15311001	اعتماد مستندي رقم	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
143	15321001	خطاب ضمان	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
144	15401001	عملاء - شركة المقاولون المتخصصون	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
145	15401002	عملاء - شركة المقاولون المتخصصون	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
146	15401003	عملاء -	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
147	15402001	اوراق القبض	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
148	15403001	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
149	15403002	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
150	15403003	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
151	15403004	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
152	15403005	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
153	15403006	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
154	15403007	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
155	15403008	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
156	15403009	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
157	15403010	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
158	15403011	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
159	15403012	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
160	15403013	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
161	15403014	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
162	15403015	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
163	15403016	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
164	15403017	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
165	15403018	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
166	15403019	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
167	15403020	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
168	15403021	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
169	15403022	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
170	15403023	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
171	15403024	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
172	15403025	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
173	15403026	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
174	15403027	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
175	15403028	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
176	15403029	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
177	15403030	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
178	15403031	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
179	15403032	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
180	15403033	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
181	15403034	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
182	15403035	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
183	15403036	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
184	15403037	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
185	15403038	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
186	15403039	تأمينات لدى الغير -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
187	15404001	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
188	15404002	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
189	15404003	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
190	15404004	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
191	15404005	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
192	15404006	السلف - أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
193	15405001	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
194	15405002	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
195	15405003	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
196	15405004	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
197	15405005	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
198	15405006	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
199	15405007	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
200	15405008	العهد -  أ /	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
201	15405009	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
202	15405010	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
203	15405011	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
204	15405012	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
205	15405013	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
206	15405014	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
209	15405017	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
210	15405018	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
211	15405019	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
212	15405020	العهد -  أ /	\N	9	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
213	15406001	شركة ابناء رجب للمقاولات	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
214	15406002	شركة السعداء	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
215	15406003	شركة المقاولون المتخصصون	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
216	15406004	شركة	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
217	15407001	تأمين اعمال ابتدائى - مشروع	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
218	15407002	تأمين اعمال ابتدائى - مشروع	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
219	15408001	تأمين اعمال نهائى - مشروع	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
220	15408002	تأمين اعمال نهائى - مشروع	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
221	15409001	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
222	15409002	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
223	15409003	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
224	15409004	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
225	15409005	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
226	15409006	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
227	15409007	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
228	15409008	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
229	15409009	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
230	15409010	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
231	15409011	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
232	15409012	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
233	15409013	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
234	15409014	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
235	15409015	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
236	15409016	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
237	15409017	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
238	15409018	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
239	15409019	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
240	15409020	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
241	15409021	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
243	15409023	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
244	15409024	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
245	15409025	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
246	15409026	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
247	15409027	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
248	15409028	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
249	15409029	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
250	15409030	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
251	15409031	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
252	15409032	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
253	15409033	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
254	15409034	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
255	15409035	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
256	15409036	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
257	15409037	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
258	15409038	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
259	15409039	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
260	15409040	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
261	15409041	مقاولى باطن - دفعات مقدمه /  شركة	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
262	15410001	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
263	15410002	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
264	15410003	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
265	15410004	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	BalanceSheet
266	15410005	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
267	15410006	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
268	15410007	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
269	15410008	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
270	15410009	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
271	15410010	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
272	15410011	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
273	15410012	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
274	15410013	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
275	15410014	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
276	15410015	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
277	15410016	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
278	15410017	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
279	15410018	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
280	15410019	موردين دفعات مقدمه - شركة /	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
281	15411001	حساب التعليات - مشروع	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
282	15411002	حساب التعليات - مشروع	\N	8	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
283	15503001	مصروفات مدفوعة مقدمة - ايجارات	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
284	15503002	مصروفات مدفوعة مقدمة -	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
285	15504001	ضرائب خصم من المنبع	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
286	15504002	ضريبة مشتروات - قيمة مضافة	\N	7	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
287	16101001	اصول مؤجره - المبنى الادارى	\N	12	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
288	21101001	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
289	21101002	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
290	21101003	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
291	21101004	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
292	21101005	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
293	21102001	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
294	21102002	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
295	21102003	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
296	21102004	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
297	21102005	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
298	21102006	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
299	21102007	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
300	21102008	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
301	21102009	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
302	21102010	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
303	21102011	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
304	21102012	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
305	21102013	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
306	21102014	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
307	21102015	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
308	21102016	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
309	21102017	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
310	21102018	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
311	21102019	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
312	21102020	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
313	21102021	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
314	21102022	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
315	21102023	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
316	21102024	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
317	21102025	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
318	21102026	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
319	21102027	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
320	21102028	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
321	21102029	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
322	21102030	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
323	21102031	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
324	21102032	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
325	21102033	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
326	21102034	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
327	21102035	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
328	21102036	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
329	21102037	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
330	21102038	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
331	21102039	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
332	21102040	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
333	21102041	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
334	21102042	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
335	21102043	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
336	21102044	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
337	21102045	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
338	21102046	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
339	21102047	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
340	21102048	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
341	21102049	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
342	21102050	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
343	21102051	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
344	21102052	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
345	21102053	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
346	21102054	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
347	21102055	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
348	21102056	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
349	21102057	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
350	21102058	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
351	21102059	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
352	21102060	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
353	21102061	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
354	21102062	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
355	21102063	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
356	21102064	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
357	21102065	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
358	21102066	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
359	21102067	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
360	21102068	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
361	21102069	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
362	21102070	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
363	21102071	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
364	21102072	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
365	21102073	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
366	21102074	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
367	21102075	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
368	21102076	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
369	21102077	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
370	21102078	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
371	21102079	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
372	21102080	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
373	21102081	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
374	21102082	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
375	21102083	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
376	21102084	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
377	21102085	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
378	21102086	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
379	21102087	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
380	21102088	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
381	21102089	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
382	21102090	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
383	21102091	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
384	21102092	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
385	21102093	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
386	21102094	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
387	21102095	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
388	21102096	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
389	21102097	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
390	21102098	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
391	21102099	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
392	21102100	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
393	21102101	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
394	21102102	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
395	21102103	مورد نشاط - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
396	21201001	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
397	21201002	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
398	21201003	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
399	21201004	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
400	21201005	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
401	21201006	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
402	21201007	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
403	21201008	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
404	21201009	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
405	21201010	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
406	21201011	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
407	21201012	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
408	21201013	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
409	21201014	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
410	21201015	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
411	21201016	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
412	21201017	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
413	21201018	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
414	21201019	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
415	21201020	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
416	21201021	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
417	21201022	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
418	21201023	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
419	21201024	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
420	21201025	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
421	21201026	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
422	21201027	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
423	21201028	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
424	21201029	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
425	21201030	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
426	21201031	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
427	21201032	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
428	21201033	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
429	21201034	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
430	21201035	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
431	21201036	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
432	21201037	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
433	21201038	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
434	21201039	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
435	21201040	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
436	21201041	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
437	21201042	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
438	21201043	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
439	21201044	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
440	21201045	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
441	21201046	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
442	21201047	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
443	21201048	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
444	21201049	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
445	21201050	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
446	21201051	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
447	21201052	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
448	21201053	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
449	21201054	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
450	21201055	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
451	21201056	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
452	21201057	مقاول باطن - شركة /	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
453	21301001	اوراق الدفع - بنك القاهرة ( جنيه مصري )	\N	13	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
454	21401001	تأمينات للغير - المقاول / شركة /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
455	21401002	تأمينات للغير - المقاول / شركة /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
456	21401003	تأمينات للغير - المقاول / شركة /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
457	21401004	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
458	21401005	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
459	21401006	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
460	21401007	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
461	21401008	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
462	21401009	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
463	21401010	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
464	21401011	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
465	21401012	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
466	21401013	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
467	21401014	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
468	21401015	تأمينات للغير - المقاول / شركة /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
469	21402001	جارى هيئة التأمينات الاجتماعية	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
470	21402002	جارى مصلحه الضرائب - ضريبة مضافة مشتريات	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
471	21402003	جارى مصلحة الضرائب - ض.القيمة المضافة ( 14 % )	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
472	21402004	جارى مصلحة الضرائب - صندوق الشهداء	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
473	21402005	جارى مصلحة الضرائب - ضريبة كسب العمل	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
474	21402006	جارى مصلحة الضرائب - ضريبة خصم واضافة	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
475	21402007	دمغة هندسية ( 0.0045 )	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
476	21402008	دمغة الاتحاد ( 0.0005 )	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
477	21404001	جارى مساهمين - ابناء رجب	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
478	21404002	جارى مساهمين - ابراهيم جمعة سالم	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
479	21405001	تامينات اجتماعية - مقاولى باطن مشروع	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
480	21405002	تامينات اجتماعية - مقاولى باطن مشروع	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
481	21406001	عماله غير منتظمه - مقاولى باطن - مشروع	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
482	21406002	عماله غير منتظمه - مقاولى باطن - مشروع	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
483	21407001	دفعات مقدمة من عميل/  شركة  المقاولون المتخصصون	\N	16	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
484	21407002	دفعات مقدمة من عميل/      - مشروع /	\N	16	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
485	21407003	دفعات مقدمة من عميل/      - مشروع /	\N	16	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
486	21408001	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
487	21408002	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
488	21408003	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
489	21408004	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
490	21408005	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
491	21408006	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
492	21408007	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
493	21408008	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
494	21408009	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
495	21408010	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
496	21408011	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
497	21408012	تعليات مقاولى باطن -  المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
498	21409001	تأمينات للغير " تأمين نهائى " - المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
499	21409002	تأمينات للغير " تأمين نهائى " - المقاول /	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
500	21409003	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
501	21409004	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
502	21409005	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
503	21409006	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
504	21409007	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
505	21409008	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
506	21409009	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
507	21409010	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
508	21409011	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
509	21409012	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
510	21409013	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
511	21409014	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
512	21409015	تأمينات للغير " تأمين نهائى " - المقاول /	\N	15	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
513	22101001	مصروفات مستحقة - اجور مستحقة	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
514	22101002	مصروفات مستحقة - فواتير تحت التسوية	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
515	22101003	مصروفات مستحقة - مستخلصات تحت التسويه	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
516	22101004	مصروفات مستحقة - تخليصات جمركية	\N	14	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
517	23011001	احتياطي قانوني	\N	17	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
518	25101001	راس المال المدفوع - ابناء رجب	\N	18	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
519	25201001	ارباح وخسائر مرحلة	\N	19	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
520	26101001	حساب التزامات ضريبيه مؤجله	\N	20	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
521	27101001	التزامات اصول مؤجره	\N	21	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
522	31101001	ايرادات النشاط - مشروع	\N	22	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
523	31101002	ايرادات النشاط - مشروع	\N	22	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
524	31101003	ايرادات النشاط - مشروع	\N	22	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
525	31101004	ايرادات النشاط - مشروع	\N	22	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
526	32101001	ايرادات اوراق مالية	\N	23	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
527	32101002	فوائد دائنة - بنكية	\N	24	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
528	32102001	ارباح فروق تقييم عمله - محقق	\N	25	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
529	41101001	م . اجور و مرتبات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
530	41101002	م . مكافاة - منح للعاملين	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
531	43101001	عمومية - اتعاب مهنية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
532	43101002	عمومية - استشارات قانونية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
533	43101003	عموميه  - ايجار مقر	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
534	43101004	عمومية - مصاريف بنكية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
535	43101005	عمومية - تصميمات وديكورات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
536	43101006	عمومية - رسوم ودمغات و م. حكومية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
537	43101007	عمومية - تصاريح سفر واقامة	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
538	43101008	عمومية - مصاريف وادوات مكتبية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
539	43101009	عمومية - مصاريف بوفية و ضيافة	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
540	43101010	عمومية - م . انتقالات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
541	43101011	عمومية - م . اكرامية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
542	43101012	عمومية - مصاريف كهرباء ومياه	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
543	43101013	عمومية - م . تراخيص سيارات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
544	43101014	عمومية - م . وقود و زيوت و شحوم	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
545	43101015	عمومية - م . مستلزمات كمبيوتر	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
546	43101016	عمومية - م . بدل سفر	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
547	43101017	عمومية - م . مطبوعات وتصميمات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
548	43101018	عمومية - م . علاج	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
549	43101019	عمومية - م . اصلاح وصيانه سياراة	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
550	43101020	عمومية - م . دعايه واعلان	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
551	43101021	عمومية - م . بنزين	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
552	43101022	عمومية - م . تليفون ونت	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
553	43101023	عمومية - تصاريح عمل	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
554	43101024	عمومية - تامينات اجتماعية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
555	43101025	عمومية - بدل اقامة للعاملين	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
556	43101026	عمومية - تامين طبي	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
557	43101027	عمومية - وثائق تامين سيارات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
558	43101028	عمومية - تذاكر سفر	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
559	43101029	عمومية - تعويضات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
560	43101030	عمومية - م . اعمال نظافة و مكافحة حشرات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
561	43101031	عمومية - عمولات وسمسرة	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
562	43101032	عمومية - مصروفات تأسيس	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
563	43101033	عمومية - رسوم تسجيل وتصاريح	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
564	43101034	عمومية - مصاريف اقامة وفنادق	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
565	43101035	مصروف ضريبة الدخل	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
566	43101036	عمومية - مصاريف مناقصات	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
567	43101037	عمومية - بدل انتقال	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
568	43101038	عمومية - بدل سكن	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
569	43101039	عمومية - مصاريف خطابات ضمان	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
570	43101040	عمومية - ايجار سيارات ملاكي - المركز الرئيسي	\N	27	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
571	45201001	مصروف اهلاك الالات والمعدات فرعي	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
572	45301001	مصروف اهلاك وسائل نقل فرعي	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
573	45501001	مصروف اهلاك الاثاث والمعدات فرعي	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
574	45601001	مصروف اهلاك اجهزه كهربائيه فرعى	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
575	45701001	مصروف اهلاك اجهزه كمبيوتر وملحقاتها فرعى	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
576	45801001	مصروف اهلاك سيارات	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
577	45901001	مصروف اهلاك اصول غير ملموسه فرعى	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
578	45101001	اهلاك اصول مؤجره - المبنى الادارى	\N	28	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
579	46101001	تكلفه اعمال مشروع	\N	29	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
580	46101002	تكلفه اعمال مشروع	\N	29	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
581	46101003	تكلفه اعمال مشروع	\N	29	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
582	47101001	خسائر فروق عمله - محقق	\N	25	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
583	48101001	فوائد مدينه	\N	30	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
584	48101002	فوائد مدينه بنكية	\N	26	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
585	21404003	جارى مساهمين -	\N	10	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	
586	1500312	اخري	11	4	CR	100000.00	0.00	t	2026-10-18 15:36:43.74261	\N
587	1990	سامي	267	13	DR	25000.00	0.00	t	2026-10-19 09:50:07.50715	\N
242	15409022	مقاولى باطن  /  شركة لوكس تو ايه	\N	11	DR	0.00	0.00	t	2026-10-17 09:59:53.918338	IncomeStatement
\.


--
-- TOC entry 5575 (class 0 OID 18457)
-- Dependencies: 277
-- Data for Name: CheckPrintTemplates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."CheckPrintTemplates" ("TemplateId", "TreasuryAccountId", "FieldName", "PosX", "PosY", "FontSize", "Alignment", "SpellPiastres", "TextValue") FROM stdin;
\.


--
-- TOC entry 5625 (class 0 OID 19833)
-- Dependencies: 327
-- Data for Name: CheckSignatories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."CheckSignatories" ("SignatoryId", "NameAr", "JobTitle", "TreasuryAccountId", "IsActive", "SortOrder", "CreatedAt", "UpdatedAt") FROM stdin;
\.


--
-- TOC entry 5593 (class 0 OID 18678)
-- Dependencies: 295
-- Data for Name: CheckStatusHistory; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."CheckStatusHistory" ("HistoryId", "CheckId", "OldStatus", "NewStatus", "ChangedBy", "ChangedAt") FROM stdin;
1	1	\N	جديد	1	2026-10-22 08:20:40.385263
\.


--
-- TOC entry 5571 (class 0 OID 18398)
-- Dependencies: 273
-- Data for Name: Checks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Checks" ("CheckId", "TreasuryAccountId", "CheckBookNo", "SequenceNo", "CheckNo", "CheckDate", "BeneficiaryId", "Amount", "PurchaseOrderNo", "ProjectId", "Description", "PrintDate", "DeliveryDate", "CashDate", "Status", "CreatedAt", "SettlementId") FROM stdin;
1	1	1	1	158	2026-10-22	1	25685220.00	120	1	توريد	\N	\N	\N	جديد	2026-10-22 08:20:40.377131	\N
\.


--
-- TOC entry 5516 (class 0 OID 17943)
-- Dependencies: 218
-- Data for Name: Companies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Companies" ("CompanyId", "NameAr", "NameEn", "IsActive", "CreatedAt", "TaxNumber", "CommercialRegister", "AddressAr", "Phone", "Email", "Website", "LogoData") FROM stdin;
1	JV	\N	t	2026-10-17 20:27:42.906672	\N	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 5585 (class 0 OID 18550)
-- Dependencies: 287
-- Data for Name: ContractAccountingConfig; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractAccountingConfig" ("ConfigId", "ContractId", "SettlementSide", "CompanyId", "FiscalYearId", "ControlAccountId", "WorkAccountId", "RetentionAccountId", "AdvanceAccountId", "TaxAccountId", "VatAccountId", "DefaultVatRate", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5577 (class 0 OID 18471)
-- Dependencies: 279
-- Data for Name: ContractAddendums; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractAddendums" ("AddendumId", "ContractId", "AddendumNo", "AddendumDate", "Description", "ValueChange", "CreatedBy", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5597 (class 0 OID 18717)
-- Dependencies: 299
-- Data for Name: ContractAttachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractAttachments" ("AttachmentId", "ContractId", "SettlementId", "Category", "OriginalFilename", "ContentType", "SizeBytes", "FileContent", "Notes", "UploadedBy", "UploadedAt") FROM stdin;
\.


--
-- TOC entry 5589 (class 0 OID 18637)
-- Dependencies: 291
-- Data for Name: ContractChangeOrders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractChangeOrders" ("ChangeOrderId", "ContractId", "ChangeOrderNo", "ChangeOrderDate", "Description", "ValueChange", "Status", "CreatedBy", "ApprovedBy", "ApprovedAt", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5583 (class 0 OID 18529)
-- Dependencies: 285
-- Data for Name: ContractDeductionRules; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractDeductionRules" ("RuleId", "ContractId", "SettlementSide", "Code", "NameAr", "CalculationType", "Rate", "BaseType", "PostingSide", "CapAmount", "GLAccountId", "IsActive", "SortOrder", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5581 (class 0 OID 18511)
-- Dependencies: 283
-- Data for Name: ContractItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractItems" ("ItemId", "ContractId", "ItemNo", "Description", "Unit", "Quantity", "UnitPrice", "CreatedAt", "CatalogItemId", "AccountId", "ProjectId") FROM stdin;
80	13	1	توريد بازلت 50/100	وحدة	200.0000	100.0000	2026-10-19 10:27:17.56587	5	46	\N
\.


--
-- TOC entry 5620 (class 0 OID 19288)
-- Dependencies: 322
-- Data for Name: ContractRequestItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractRequestItems" ("RequestItemId", "RequestId", "CatalogItemId", "ItemNo", "Description", "Unit", "Quantity", "UnitPrice", "AccountId", "ProjectId") FROM stdin;
\.


--
-- TOC entry 5549 (class 0 OID 18149)
-- Dependencies: 251
-- Data for Name: ContractRequests; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractRequests" ("RequestId", "RequestNo", "RequestType", "Title", "CounterpartyName", "ProjectId", "EstimatedValue", "Description", "Status", "ReviewNotes", "CreatedBy", "CreatedAt", "ReviewedBy", "ReviewedAt", "CounterpartyId") FROM stdin;
\.


--
-- TOC entry 5595 (class 0 OID 18695)
-- Dependencies: 297
-- Data for Name: ContractSettlementItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractSettlementItems" ("SettlementItemId", "SettlementId", "ContractItemId", "Quantity", "UnitPrice", "Amount", "CreatedAt", "AccountId", "ProjectId") FROM stdin;
13	12	80	100.0000	100.0000	10000.00	2026-10-19 10:28:31.712788	\N	\N
14	13	80	100.0000	100.0000	10000.00	2026-10-19 10:29:18.051438	\N	\N
\.


--
-- TOC entry 5587 (class 0 OID 18605)
-- Dependencies: 289
-- Data for Name: ContractSettlements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ContractSettlements" ("SettlementId", "ContractId", "SettlementSide", "SequenceNo", "SettlementNo", "SettlementDate", "CounterpartyName", "WorkValue", "CumulativeWorkValue", "DeductionsJson", "VatAmount", "NetAmount", "Status", "JournalEntryId", "Notes", "CreatedBy", "CreatedAt", "CounterpartyId") FROM stdin;
13	13	Customer	2	FIN-000010	2026-10-19	لوكس	10000.00	20000.00	{"ADVANCE_PAYMENT": {"name": "\\u062f\\u0641\\u0639\\u0629 \\u0645\\u0642\\u062f\\u0645\\u0629", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "\\u062a\\u0623\\u0645\\u064a\\u0646 \\u0645\\u062d\\u062c\\u0648\\u0632", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "\\u062a\\u0623\\u0645\\u064a\\u0646 \\u0646\\u0647\\u0627\\u0626\\u064a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "\\u0636\\u0631\\u0627\\u0626\\u0628 \\u0623\\u0631\\u0628\\u0627\\u062d", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "\\u062f\\u0645\\u063a\\u0627\\u062a \\u0647\\u0646\\u062f\\u0633\\u064a\\u0629", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "\\u062f\\u0645\\u063a\\u0627\\u062a \\u0627\\u062a\\u062d\\u0627\\u062f", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "\\u0645\\u0633\\u062d\\u0648\\u0628\\u0627\\u062a \\u0648\\u0645\\u0635\\u0627\\u0631\\u064a\\u0641 \\u0645\\u062e\\u0627\\u0632\\u0646", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "\\u0646\\u0642\\u0644", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "\\u0633\\u0648\\u0644\\u0627\\u0631", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "\\u0648\\u062c\\u0628\\u0627\\u062a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "\\u062a\\u0639\\u0644\\u064a\\u0627\\u062a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}	0.00	10000.00	Draft	\N	تم إنشاؤه تلقائياً من المستخلص الفني TE-0002.	1	2026-10-19 10:29:18.04875	1
12	13	Customer	1	FIN-000009	2026-10-19	لوكس	10000.00	10000.00	{"ADVANCE_PAYMENT": {"name": "\\u062f\\u0641\\u0639\\u0629 \\u0645\\u0642\\u062f\\u0645\\u0629", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "RETENTION": {"name": "\\u062a\\u0623\\u0645\\u064a\\u0646 \\u0645\\u062d\\u062c\\u0648\\u0632", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "FINAL_INSURANCE": {"name": "\\u062a\\u0623\\u0645\\u064a\\u0646 \\u0646\\u0647\\u0627\\u0626\\u064a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "PROFIT_TAX": {"name": "\\u0636\\u0631\\u0627\\u0626\\u0628 \\u0623\\u0631\\u0628\\u0627\\u062d", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ENGINEERING_STAMP": {"name": "\\u062f\\u0645\\u063a\\u0627\\u062a \\u0647\\u0646\\u062f\\u0633\\u064a\\u0629", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "UNION_STAMP": {"name": "\\u062f\\u0645\\u063a\\u0627\\u062a \\u0627\\u062a\\u062d\\u0627\\u062f", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "STORE_WITHDRAWALS": {"name": "\\u0645\\u0633\\u062d\\u0648\\u0628\\u0627\\u062a \\u0648\\u0645\\u0635\\u0627\\u0631\\u064a\\u0641 \\u0645\\u062e\\u0627\\u0632\\u0646", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "TRANSPORT": {"name": "\\u0646\\u0642\\u0644", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "DIESEL": {"name": "\\u0633\\u0648\\u0644\\u0627\\u0631", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "MEALS": {"name": "\\u0648\\u062c\\u0628\\u0627\\u062a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}, "ADDITIONS": {"name": "\\u062a\\u0639\\u0644\\u064a\\u0627\\u062a", "amount": "0.00", "account_id": null, "posting_side": "Debit"}}	0.00	10000.00	Draft	\N	تم إنشاؤه تلقائياً من المستخلص الفني TE-0001.	1	2026-10-19 10:28:31.702977	1
\.


--
-- TOC entry 5561 (class 0 OID 18285)
-- Dependencies: 263
-- Data for Name: Contracts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Contracts" ("ContractId", "RequestId", "ContractNo", "Title", "ClientName", "ProjectId", "StartDate", "EndDate", "OriginalValue", "Status", "Notes", "CreatedBy", "CreatedAt", "CounterpartyId") FROM stdin;
13	\N	CT-2026-000013	ي	لوكس	\N	2026-10-19	2026-11-07	20000.00	Active		1	2026-10-19 10:27:17.561264	1
\.


--
-- TOC entry 5606 (class 0 OID 19050)
-- Dependencies: 308
-- Data for Name: Counterparties; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Counterparties" ("CounterpartyId", "Code", "LegalName", "PartyType", "TaxNo", "CommercialRegistration", "Phone", "Email", "Address", "LinkedAccountId", "IsActive", "CreatedAt", "Name", "Roles", "AccountId", "TaxNumber", "CommercialRegister", "Notes") FROM stdin;
2	CP-000002	يثس	Customer	\N	\N	\N	\N	\N	\N	t	2026-10-18 09:41:47.36762	يثس	[]	\N	\N	\N	\N
3	CP-000003	ؤص	Customer	\N	\N	\N	\N	\N	\N	t	2026-10-18 09:41:47.371341	ؤص	[]	\N	\N	\N	\N
5	CP-000005	محمد	Supplier	154	582	01158299866	himahero958@gmail.com	ش عباس علي عيسى بمتفرع من مدينة عامر بولاق الدكرور	\N	t	2026-10-18 10:24:44.149249	محمد	[]	\N	\N	\N	\N
1	CP-000001	لوكس	Mixed	\N	\N	\N	\N	\N	\N	t	2026-10-18 09:41:47.35843	لوكس	[]	\N	\N	\N	\N
6	CP-000006	علي	Supplier	\N	\N	\N	\N	\N	\N	t	2026-10-18 15:15:44.71213	علي	["Supplier"]	\N	\N	\N	\N
4	CP-000004	ابراهيم	Mixed	\N	\N	\N	\N	\N	\N	t	2026-10-18 09:41:47.378947	ابراهيم	[]	\N	\N	\N	\N
7	CP-000007	هاني	Supplier	\N	\N	\N	\N	\N	\N	t	2026-10-18 16:18:40.579969	هاني	["Supplier"]	\N	\N	\N	\N
8	CP-000008	doma	Customer	\N	\N	\N	\N	\N	\N	t	2026-10-18 16:27:41.841763	doma	["Customer"]	\N	\N	\N	\N
\.


--
-- TOC entry 5603 (class 0 OID 19024)
-- Dependencies: 305
-- Data for Name: CounterpartyAliases; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."CounterpartyAliases" ("AliasId", "AliasName", "CanonicalName", "CreatedAt", "CounterpartyId") FROM stdin;
1	لوكس	ابراهيم	2026-10-18 15:32:17.662999	4
\.


--
-- TOC entry 5520 (class 0 OID 17959)
-- Dependencies: 222
-- Data for Name: ExchangeRates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ExchangeRates" ("ExchangeRateId", "CurrencyCode", "RateDate", "RateToEGP") FROM stdin;
\.


--
-- TOC entry 5573 (class 0 OID 18424)
-- Dependencies: 275
-- Data for Name: FinancialChecks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."FinancialChecks" ("CheckId", "CheckNumber", "CheckType", "Amount", "DueDate", "DraweeBank", "ProjectBrand", "Status", "PartyAccountId", "TreasuryAccountId", "JournalEntryId", "Description", "CreatedBy", "CreatedAt", "ProjectId") FROM stdin;
1	155	INCOMING	5000.00	2026-10-23	cib	Lux	مُرتجع	1	1	\N	توريد	1	2026-10-17 16:05:51.969568	\N
2	1666	OUTGOING	25000.00	2026-11-07	25000	عام	مُرتجع	1	1	\N	توريد	1	2026-10-22 08:07:36.003596	\N
\.


--
-- TOC entry 5538 (class 0 OID 18043)
-- Dependencies: 240
-- Data for Name: FinancialStatementLines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."FinancialStatementLines" ("LineId", "StatementType", "CaptionAr", "SortOrder", "ClassificationId", "IsSubtotal") FROM stdin;
\.


--
-- TOC entry 5536 (class 0 OID 18031)
-- Dependencies: 238
-- Data for Name: FiscalYears; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."FiscalYears" ("FiscalYearId", "CompanyId", "StartDate", "EndDate", "IsClosed") FROM stdin;
1	1	2026-01-01	2026-12-31	f
\.


--
-- TOC entry 5534 (class 0 OID 18023)
-- Dependencies: 236
-- Data for Name: InventoryItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."InventoryItems" ("ItemId", "Code", "Name", "Category", "Unit", "MinQuantity", "IsActive", "CreatedAt") FROM stdin;
1	1	محاسب	ق	قطعة	5.000	t	2026-10-18 10:23:46.585548
2	250	سولار	جاز	لتر	0.000	t	2026-10-18 16:01:00.111369
\.


--
-- TOC entry 5551 (class 0 OID 18174)
-- Dependencies: 253
-- Data for Name: InventoryMovements; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."InventoryMovements" ("MovementId", "MovementNo", "ItemId", "WarehouseId", "MovementDate", "MovementType", "Quantity", "UnitCost", "Reference", "Notes", "CreatedBy", "CreatedAt", "DocumentNo", "AccountId", "ProjectId", "CatalogItemId") FROM stdin;
1	PO-123-1	1	1	2026-10-18	IN	1.000	10.0000	123	استلام أمر شراء	1	2026-10-18 13:48:03.564789	\N	\N	\N	\N
2	PO-124-2	1	1	2026-10-18	IN	45.000	350.0000	124	استلام أمر شراء	1	2026-10-18 15:12:23.044763	\N	\N	\N	\N
3	PO-PO-2026-000003-3	2	2	2026-10-18	IN	25.000	320.0000	PO-2026-000003	استلام أمر شراء	1	2026-10-18 16:02:45.997677	\N	\N	\N	\N
4	PO-PO-2026-000004-4	2	2	2026-10-18	IN	500.000	450.0000	PO-2026-000004	استلام أمر شراء	1	2026-10-18 16:19:34.096691	\N	\N	\N	\N
\.


--
-- TOC entry 5532 (class 0 OID 18015)
-- Dependencies: 234
-- Data for Name: InventoryWarehouses; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."InventoryWarehouses" ("WarehouseId", "Code", "Name", "Location", "IsActive", "CreatedAt") FROM stdin;
1	1	Network	1	t	2026-10-18 10:23:16.423907
2	215	السولار	تحالف	t	2026-10-18 15:59:53.550485
\.


--
-- TOC entry 5622 (class 0 OID 19454)
-- Dependencies: 324
-- Data for Name: ItemCatalog; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ItemCatalog" ("CatalogItemId", "Code", "Name", "Unit", "AccountId", "InventoryItemId", "IsActive", "CreatedAt") FROM stdin;
1	11501003	توريد بازلت 50/100	وحدة	3	1	t	2026-10-18 12:45:34.001708
5	200	توريد بازلت 50/100	وحدة	46	\N	t	2026-10-18 13:13:47.912305
6	215	توريدحديد 50/100	طن	48	\N	t	2026-10-18 13:41:35.996386
\.


--
-- TOC entry 5555 (class 0 OID 18219)
-- Dependencies: 257
-- Data for Name: JournalEntries; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."JournalEntries" ("JournalEntryId", "EntryNo", "EntryDate", "CompanyId", "FiscalYearId", "Description", "Status", "CreatedBy", "PostedBy", "PostedAt", "CreatedAt", "SourceType", "SourceId", "ReferenceNo", "SourceSettlementId") FROM stdin;
3	JE-2026-000002	2026-10-18	1	1	\N	Reversed	1	1	2026-10-18 15:34:45.154998	2026-10-18 15:18:59.674296	\N	\N	\N	\N
2	JE-2026-000001	2026-10-18	1	1	\N	Reversed	1	1	2026-10-18 08:24:09.142091	2026-10-18 08:23:41.322645	\N	\N	\N	\N
4	JE-2026-000003	2026-11-03	1	1	\N	Posted	1	1	2026-11-03 21:28:04.161216	2026-11-03 21:27:45.359649	\N	\N	\N	\N
5	JE-2026-000004	2026-11-03	1	1	\N	Posted	1	1	2026-11-03 21:32:14.455288	2026-11-03 21:32:04.646422	\N	\N	\N	\N
6	JE-2026-000005	2026-11-03	1	1	\N	Posted	1	1	2026-11-03 21:45:55.590366	2026-11-03 21:45:48.60839	\N	\N	\N	\N
7	JE-2026-000006	2026-11-03	1	1	\N	Posted	1	1	2026-11-03 21:47:15.938036	2026-11-03 21:47:10.206875	\N	\N	\N	\N
8	JE-2026-000007	2026-11-03	1	1	\N	Posted	1	1	2026-11-03 21:50:21.212931	2026-11-03 21:50:13.957841	\N	\N	\N	\N
9	JE-2026-000008	2026-11-04	1	1	\N	Posted	1	1	2026-11-04 15:30:32.700377	2026-11-04 15:29:26.691207	\N	\N	\N	\N
\.


--
-- TOC entry 5565 (class 0 OID 18330)
-- Dependencies: 267
-- Data for Name: JournalEntryDetails; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."JournalEntryDetails" ("DetailId", "JournalEntryId", "LineNo", "AccountId", "ProjectId", "DebitAmount", "CreditAmount", "FcyAmount", "ExchangeRate", "Description") FROM stdin;
3	2	1	1	\N	100.00	0.00	\N	\N	\N
4	2	2	140	\N	0.00	100.00	\N	\N	\N
5	3	1	6	1	4500.00	0.00	\N	\N	\N
6	3	2	140	1	0.00	4500.00	\N	\N	\N
7	4	1	538	\N	100.00	0.00	\N	\N	\N
8	4	2	134	\N	0.00	100.00	\N	\N	\N
9	5	1	538	\N	1000.00	0.00	\N	\N	\N
10	5	2	134	\N	0.00	1000.00	\N	\N	\N
11	6	1	113	1	100000.00	0.00	\N	\N	\N
12	6	2	242	1	0.00	100000.00	\N	\N	\N
13	7	1	113	1	500000.00	0.00	\N	\N	\N
14	7	2	242	1	0.00	500000.00	\N	\N	\N
15	8	1	242	\N	1200000.00	0.00	\N	\N	\N
16	8	2	140	\N	0.00	1200000.00	\N	\N	\N
19	9	1	242	\N	0.00	154000.00	\N	\N	بالطن توريد ونقل كسر أحجار من أي نوع تحقق كثافة لا تقل عن 2.4  طن/م3   لزوم أعمال الحاجز المؤقت على ان يكون خالى من الشوائب و التشققات و التصدعات و العيوب طبقا للمواصفات الفنية والكود المصري والفئة تشمل التحميل من المحجر والنقل  لموقع التشوين والتفريغ بمشون المشروع والتسليم طبقا لتعليمات المهندس المشرف او من ينوب عنه بالموقع على ان تمم المحاسبة وفقا لاشعار بونات الميزان المعتمدة من المشروع ( الفئة لا تشمل التعتيق بمعدات المقاول فى المشروع )
20	9	2	134	\N	154000.00	0.00	\N	\N	كسر أحجار دلوميت  مقاس من (1-2) طن
\.


--
-- TOC entry 5528 (class 0 OID 17997)
-- Dependencies: 230
-- Data for Name: Permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Permissions" ("PermissionId", "ScreenCode", "ActionCode") FROM stdin;
1	AuditLogs	View
2	AnalyticsReports	View
3	Contracts	View
4	Contracts	Add
5	Contracts	Edit
6	Contracts	Delete
7	Contracts	Print
8	ContractSettlements	View
9	ContractSettlements	Add
10	ContractSettlements	Edit
11	ContractSettlements	Approve
12	ContractSettlements	Post
13	AuditLogs	Add
14	AuditLogs	Edit
15	AuditLogs	Delete
16	AuditLogs	Post
17	AuditLogs	Approve
18	AuditLogs	Print
19	AnalyticsReports	Add
20	AnalyticsReports	Edit
21	AnalyticsReports	Delete
22	AnalyticsReports	Post
23	AnalyticsReports	Approve
24	AnalyticsReports	Print
25	JournalBook	View
26	JournalBook	Add
27	JournalBook	Edit
28	JournalBook	Delete
29	JournalBook	Post
30	JournalBook	Approve
31	JournalBook	Print
32	CostCenters	View
33	CostCenters	Add
34	CostCenters	Edit
35	CostCenters	Delete
36	CostCenters	Post
37	CostCenters	Approve
38	CostCenters	Print
39	ChartOfAccounts	View
40	ChartOfAccounts	Add
41	ChartOfAccounts	Edit
42	ChartOfAccounts	Delete
43	ChartOfAccounts	Post
44	ChartOfAccounts	Approve
45	ChartOfAccounts	Print
46	TrialBalance	View
47	TrialBalance	Add
48	TrialBalance	Edit
49	TrialBalance	Delete
50	TrialBalance	Post
51	TrialBalance	Approve
52	TrialBalance	Print
53	BalanceSheet	View
54	BalanceSheet	Add
55	BalanceSheet	Edit
56	BalanceSheet	Delete
57	BalanceSheet	Post
58	BalanceSheet	Approve
59	BalanceSheet	Print
60	IncomeStatement	View
61	IncomeStatement	Add
62	IncomeStatement	Edit
63	IncomeStatement	Delete
64	IncomeStatement	Post
65	IncomeStatement	Approve
66	IncomeStatement	Print
67	CashAnalysis	View
68	CashAnalysis	Add
69	CashAnalysis	Edit
70	CashAnalysis	Delete
71	CashAnalysis	Post
72	CashAnalysis	Approve
73	CashAnalysis	Print
74	BankCibEgp	View
75	BankCibEgp	Add
76	BankCibEgp	Edit
77	BankCibEgp	Delete
78	BankCibEgp	Post
79	BankCibEgp	Approve
80	BankCibEgp	Print
81	ChecksCib	View
82	ChecksCib	Add
83	ChecksCib	Edit
84	ChecksCib	Delete
85	ChecksCib	Post
86	ChecksCib	Approve
87	ChecksCib	Print
88	BankReconciliation	View
89	BankReconciliation	Add
90	BankReconciliation	Edit
91	BankReconciliation	Delete
92	BankReconciliation	Post
93	BankReconciliation	Approve
94	BankReconciliation	Print
95	CashUsd	View
96	CashUsd	Add
97	CashUsd	Edit
98	CashUsd	Delete
99	CashUsd	Post
100	CashUsd	Approve
101	CashUsd	Print
102	BankCairoEgp	View
103	BankCairoEgp	Add
104	BankCairoEgp	Edit
105	BankCairoEgp	Delete
106	BankCairoEgp	Post
107	BankCairoEgp	Approve
108	BankCairoEgp	Print
109	BankHdbUsd	View
110	BankHdbUsd	Add
111	BankHdbUsd	Edit
112	BankHdbUsd	Delete
113	BankHdbUsd	Post
114	BankHdbUsd	Approve
115	BankHdbUsd	Print
116	BankHdbEgp	View
117	BankHdbEgp	Add
118	BankHdbEgp	Edit
119	BankHdbEgp	Delete
120	BankHdbEgp	Post
121	BankHdbEgp	Approve
122	BankHdbEgp	Print
123	BankCibUsd	View
124	BankCibUsd	Add
125	BankCibUsd	Edit
126	BankCibUsd	Delete
127	BankCibUsd	Post
128	BankCibUsd	Approve
129	BankCibUsd	Print
130	ChecksCairoEgp	View
131	ChecksCairoEgp	Add
132	ChecksCairoEgp	Edit
133	ChecksCairoEgp	Delete
134	ChecksCairoEgp	Post
135	ChecksCairoEgp	Approve
136	ChecksCairoEgp	Print
137	ChecksCairoUsd	View
138	ChecksCairoUsd	Add
139	ChecksCairoUsd	Edit
140	ChecksCairoUsd	Delete
141	ChecksCairoUsd	Post
142	ChecksCairoUsd	Approve
143	ChecksCairoUsd	Print
144	FinancialChecks	View
145	FinancialChecks	Add
146	FinancialChecks	Edit
147	FinancialChecks	Delete
148	FinancialChecks	Post
149	FinancialChecks	Approve
150	FinancialChecks	Print
151	Contracts	Post
152	Contracts	Approve
153	ContractRequests	View
154	ContractRequests	Add
155	ContractRequests	Edit
156	ContractRequests	Delete
157	ContractRequests	Post
158	ContractRequests	Approve
159	ContractRequests	Print
160	ContractSettlements	Delete
161	ContractSettlements	Print
162	InventoryManagement	View
163	InventoryManagement	Add
164	InventoryManagement	Edit
165	InventoryManagement	Delete
166	InventoryManagement	Post
167	InventoryManagement	Approve
168	InventoryManagement	Print
169	PurchaseCycle	View
170	PurchaseCycle	Add
171	PurchaseCycle	Edit
172	PurchaseCycle	Delete
173	PurchaseCycle	Post
174	PurchaseCycle	Approve
175	PurchaseCycle	Print
176	HumanResources	View
177	HumanResources	Add
178	HumanResources	Edit
179	HumanResources	Delete
180	HumanResources	Post
181	HumanResources	Approve
182	HumanResources	Print
183	Counterparties	View
184	Counterparties	Add
185	Counterparties	Edit
186	Counterparties	Delete
187	Counterparties	Post
188	Counterparties	Approve
189	Counterparties	Print
352	AuditLogs	EngineeringApprove
353	AuditLogs	FinancialApprove
354	JournalBook	EngineeringApprove
355	JournalBook	FinancialApprove
356	ChartOfAccounts	EngineeringApprove
357	ChartOfAccounts	FinancialApprove
358	TrialBalance	EngineeringApprove
359	TrialBalance	FinancialApprove
360	BalanceSheet	EngineeringApprove
361	BalanceSheet	FinancialApprove
362	IncomeStatement	EngineeringApprove
363	IncomeStatement	FinancialApprove
364	CashAnalysis	EngineeringApprove
365	CashAnalysis	FinancialApprove
366	BankCibEgp	EngineeringApprove
367	BankCibEgp	FinancialApprove
368	ChecksCib	EngineeringApprove
369	ChecksCib	FinancialApprove
370	BankReconciliation	EngineeringApprove
371	BankReconciliation	FinancialApprove
372	CashUsd	EngineeringApprove
373	CashUsd	FinancialApprove
374	BankCairoEgp	EngineeringApprove
375	BankCairoEgp	FinancialApprove
376	BankHdbUsd	EngineeringApprove
377	BankHdbUsd	FinancialApprove
378	BankHdbEgp	EngineeringApprove
379	BankHdbEgp	FinancialApprove
380	BankCibUsd	EngineeringApprove
381	BankCibUsd	FinancialApprove
382	ChecksCairoEgp	EngineeringApprove
383	ChecksCairoEgp	FinancialApprove
384	ChecksCairoUsd	EngineeringApprove
385	ChecksCairoUsd	FinancialApprove
386	FinancialChecks	EngineeringApprove
387	FinancialChecks	FinancialApprove
388	CostCenters	EngineeringApprove
389	CostCenters	FinancialApprove
390	Contracts	EngineeringApprove
391	Contracts	FinancialApprove
392	ContractRequests	EngineeringApprove
393	ContractRequests	FinancialApprove
394	ContractSettlements	EngineeringApprove
395	ContractSettlements	FinancialApprove
396	InventoryManagement	EngineeringApprove
397	InventoryManagement	FinancialApprove
398	PurchaseCycle	EngineeringApprove
399	PurchaseCycle	FinancialApprove
400	HumanResources	EngineeringApprove
401	HumanResources	FinancialApprove
402	Counterparties	EngineeringApprove
403	Counterparties	FinancialApprove
404	AnalyticsReports	EngineeringApprove
405	AnalyticsReports	FinancialApprove
406	CustomerRegistry	View
407	CustomerRegistry	Add
408	CustomerRegistry	Edit
409	CustomerRegistry	Delete
410	CustomerRegistry	Post
411	CustomerRegistry	Approve
412	CustomerRegistry	EngineeringApprove
413	CustomerRegistry	FinancialApprove
414	CustomerRegistry	Print
415	ContractorRegistry	View
416	ContractorRegistry	Add
417	ContractorRegistry	Edit
418	ContractorRegistry	Delete
419	ContractorRegistry	Post
420	ContractorRegistry	Approve
421	ContractorRegistry	EngineeringApprove
422	ContractorRegistry	FinancialApprove
423	ContractorRegistry	Print
424	SupplierRegistry	View
425	SupplierRegistry	Add
426	SupplierRegistry	Edit
427	SupplierRegistry	Delete
428	SupplierRegistry	Post
429	SupplierRegistry	Approve
430	SupplierRegistry	EngineeringApprove
431	SupplierRegistry	FinancialApprove
432	SupplierRegistry	Print
433	CashEgp	View
434	CashEgp	Add
435	CashEgp	Edit
436	CashEgp	Delete
437	CashEgp	Post
438	CashEgp	Approve
439	CashEgp	EngineeringApprove
440	CashEgp	FinancialApprove
441	CashEgp	Print
\.


--
-- TOC entry 5579 (class 0 OID 18491)
-- Dependencies: 281
-- Data for Name: ProgressBillings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."ProgressBillings" ("BillingId", "ContractId", "BillingNo", "BillingDate", "WorkValue", "RetentionAmount", "AdvanceDeduction", "OtherDeductions", "NetAmount", "Status", "Notes", "CreatedBy", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5518 (class 0 OID 17950)
-- Dependencies: 220
-- Data for Name: Projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Projects" ("ProjectId", "NameAr", "NameEn", "IsHeadOffice", "IsActive") FROM stdin;
1	JV	JV	f	t
\.


--
-- TOC entry 5563 (class 0 OID 18312)
-- Dependencies: 265
-- Data for Name: PurchaseOrderLines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."PurchaseOrderLines" ("LineId", "PurchaseOrderId", "ItemId", "Quantity", "UnitPrice", "ReceivedQuantity", "CatalogItemId", "AccountId", "ProjectId") FROM stdin;
1	1	1	1.000	10.0000	1.000	\N	\N	\N
2	2	1	45.000	350.0000	45.000	\N	\N	\N
3	3	2	25.000	320.0000	25.000	\N	\N	\N
4	4	2	500.000	450.0000	500.000	\N	\N	\N
\.


--
-- TOC entry 5553 (class 0 OID 18199)
-- Dependencies: 255
-- Data for Name: PurchaseOrders; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."PurchaseOrders" ("PurchaseOrderId", "OrderNo", "OrderDate", "SupplierName", "WarehouseId", "Status", "Notes", "TotalAmount", "CreatedBy", "CreatedAt", "CounterpartyId", "ProjectId") FROM stdin;
1	123	2026-10-18	علي	1	Received	\N	10.00	1	2026-10-18 13:47:47.513274	6	\N
2	124	2026-10-18	علي	1	Received	\N	15750.00	1	2026-10-18 15:03:31.540424	6	\N
3	PO-2026-000003	2026-10-18	ابراهيم	2	Received	\N	8000.00	1	2026-10-18 16:01:28.961592	4	\N
4	PO-2026-000004	2026-10-18	هاني	2	Received	\N	225000.00	1	2026-10-18 16:12:29.572678	7	\N
\.


--
-- TOC entry 5614 (class 0 OID 19167)
-- Dependencies: 316
-- Data for Name: PurchaseReturnLines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."PurchaseReturnLines" ("LineId", "ReturnId", "InvoiceLineId", "Quantity", "NetAmount", "TaxAmount") FROM stdin;
\.


--
-- TOC entry 5612 (class 0 OID 19133)
-- Dependencies: 314
-- Data for Name: PurchaseReturns; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."PurchaseReturns" ("ReturnId", "ReturnNo", "InvoiceId", "ReturnDate", "Reason", "TotalAmount", "Status", "JournalEntryId", "CreatedBy", "ApprovedBy", "CreatedAt") FROM stdin;
\.


--
-- TOC entry 5618 (class 0 OID 19272)
-- Dependencies: 320
-- Data for Name: RecordAttachments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."RecordAttachments" ("AttachmentId", "RecordType", "RecordId", "OriginalFilename", "ContentType", "SizeBytes", "FileContent", "Notes", "UploadedBy", "UploadedAt") FROM stdin;
\.


--
-- TOC entry 5541 (class 0 OID 18073)
-- Dependencies: 243
-- Data for Name: RolePermissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."RolePermissions" ("RoleId", "PermissionId") FROM stdin;
1	1
1	2
1	3
1	4
1	5
1	6
1	7
1	8
1	9
1	10
1	11
1	12
1	13
1	14
1	15
1	16
1	17
1	18
1	19
1	20
1	21
1	22
1	23
1	24
1	25
1	26
1	27
1	28
1	29
1	30
1	31
1	32
1	33
1	34
1	35
1	36
1	37
1	38
1	39
1	40
1	41
1	42
1	43
1	44
1	45
1	46
1	47
1	48
1	49
1	50
1	51
1	52
1	53
1	54
1	55
1	56
1	57
1	58
1	59
1	60
1	61
1	62
1	63
1	64
1	65
1	66
1	67
1	68
1	69
1	70
1	71
1	72
1	73
1	74
1	75
1	76
1	77
1	78
1	79
1	80
1	81
1	82
1	83
1	84
1	85
1	86
1	87
1	88
1	89
1	90
1	91
1	92
1	93
1	94
1	95
1	96
1	97
1	98
1	99
1	100
1	101
1	102
1	103
1	104
1	105
1	106
1	107
1	108
1	109
1	110
1	111
1	112
1	113
1	114
1	115
1	116
1	117
1	118
1	119
1	120
1	121
1	122
1	123
1	124
1	125
1	126
1	127
1	128
1	129
1	130
1	131
1	132
1	133
1	134
1	135
1	136
1	137
1	138
1	139
1	140
1	141
1	142
1	143
1	144
1	145
1	146
1	147
1	148
1	149
1	150
1	151
1	152
1	153
1	154
1	155
1	156
1	157
1	158
1	159
1	160
1	161
1	162
1	163
1	164
1	165
1	166
1	167
1	168
1	169
1	170
1	171
1	172
1	173
1	174
1	175
1	176
1	177
1	178
1	179
1	180
1	181
1	182
2	2
2	24
2	1
2	18
2	53
2	59
2	102
2	108
2	74
2	80
2	123
2	129
2	116
2	122
2	109
2	115
2	88
2	94
2	67
2	73
2	95
2	101
2	39
2	45
2	130
2	136
2	137
2	143
2	81
2	87
2	153
2	159
2	8
2	161
2	3
2	7
2	32
2	38
2	144
2	150
2	176
2	182
2	60
2	66
2	162
2	168
2	25
2	31
2	169
2	175
2	46
2	52
3	39
3	40
3	41
3	45
3	25
3	26
3	27
3	29
3	31
3	46
3	52
3	53
3	59
3	60
3	66
3	2
3	24
3	32
3	33
3	34
4	74
4	75
4	76
4	80
4	123
4	124
4	125
4	129
4	102
4	103
4	104
4	108
4	116
4	117
4	118
4	122
4	109
4	110
4	111
4	115
4	95
4	96
4	97
4	101
4	88
4	89
4	90
4	94
4	67
4	73
4	81
4	82
4	83
4	87
4	130
4	131
4	132
4	136
4	137
4	138
4	139
4	143
4	144
4	145
4	146
4	150
5	32
5	3
5	4
5	5
5	7
5	153
5	154
5	155
5	159
5	8
5	9
5	10
5	161
6	169
6	170
6	171
6	175
6	162
6	168
7	162
7	163
7	164
7	168
7	169
7	173
7	175
8	176
8	177
8	178
8	182
1	183
1	184
1	185
1	186
1	187
1	188
1	189
1	390
1	391
1	352
1	353
1	354
1	355
1	356
1	357
1	358
1	359
1	360
1	361
1	362
1	363
1	364
1	365
1	366
1	367
1	368
1	369
1	370
1	371
1	372
1	373
1	374
1	375
1	376
1	377
1	378
1	379
1	380
1	381
1	382
1	383
1	384
1	385
1	386
1	387
1	388
1	389
1	392
1	393
1	394
1	395
1	396
1	397
1	398
1	399
1	400
1	401
1	402
1	403
1	404
1	405
1	406
1	407
1	408
1	409
1	410
1	411
1	412
1	413
1	414
1	415
1	416
1	417
1	418
1	419
1	420
1	421
1	422
1	423
1	424
1	425
1	426
1	427
1	428
1	429
1	430
1	431
1	432
1	433
1	434
1	435
1	436
1	437
1	438
1	439
1	440
1	441
\.


--
-- TOC entry 5526 (class 0 OID 17988)
-- Dependencies: 228
-- Data for Name: Roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Roles" ("RoleId", "RoleName") FROM stdin;
1	Admin
2	Auditor
3	Accountant
4	Treasurer
5	Technical Office
6	Procurement
7	Store Keeper
8	HR
\.


--
-- TOC entry 5604 (class 0 OID 19044)
-- Dependencies: 306
-- Data for Name: SchemaMigrations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."SchemaMigrations" ("MigrationId", "AppliedAt") FROM stdin;
001_counterparty_master	2026-10-18 09:41:47.390805
002_purchase_invoices	2026-10-18 09:41:47.404733
003_catalog_lines_attachments	2026-10-18 10:14:19.929352
\.


--
-- TOC entry 5547 (class 0 OID 18133)
-- Dependencies: 249
-- Data for Name: Screens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Screens" ("ScreenId", "SectionId", "ScreenCode", "TitleEn", "TitleAr", "Route", "SortOrder", "IsActive") FROM stdin;
1	1	AuditLogs	Audit Logs	سجل المراجعة والنشاطات	/audit-logs	20	t
3	2	JournalBook	General Journal	دفتر اليومية	/journal	1	t
5	2	ChartOfAccounts	Chart of Accounts	شجرة الحسابات	/accounts	3	t
6	2	TrialBalance	Trial Balance	ميزان المراجعة	/trial-balance	4	t
7	1	BalanceSheet	Balance Sheet	قائمة المركز المالي	/reports/balance-sheet	5	t
8	1	IncomeStatement	Income Statement	قائمة الدخل	/reports/income-statement	6	t
9	3	CashAnalysis	Cash Analysis	تحليل النقدية	/treasury/analysis	7	t
10	3	BankCibEgp	CIB Bank - EGP	البنك التجاري جنيه مصري	/treasury/cib-egp	8	t
11	4	ChecksCib	CIB Checks	أرقام شيكات بنك CIB	/checks/cib	9	t
12	3	BankReconciliation	Bank Reconciliation	مذكرة تسوية البنك	/treasury/reconciliation	10	t
13	3	CashUsd	Cash - USD	خزينة دولار	/treasury/cash-usd	11	t
14	3	BankCairoEgp	Banque du Caire - EGP	بنك القاهرة جنيه مصري	/treasury/cairo-egp	12	t
15	3	BankHdbUsd	Real Estate Bank - USD	البنك العقاري المصري دولار	/treasury/hdb-usd	13	t
16	3	BankHdbEgp	Real Estate Bank - EGP	البنك العقاري جنيه مصري	/treasury/hdb-egp	14	t
17	3	BankCibUsd	CIB Bank - USD	البنك التجاري دولار	/treasury/cib-usd	15	t
18	4	ChecksCairoEgp	Banque du Caire Checks - EGP	أرقام شيكات بنك القاهرة جنيه	/checks/cairo-egp	16	t
19	4	ChecksCairoUsd	Banque du Caire Checks - USD	أرقام شيكات بنك القاهرة دولار	/checks/cairo-usd	17	t
20	4	FinancialChecks	Financial Checks Register	إدارة الشيكات المالية	/checks/register	18	t
4	5	CostCenters	Cost Centers	مراكز التكلفة والمشروعات	/projects	1	t
21	5	Contracts	Contracts & Technical Office	العقود والمكتب الفني	/contracts	2	t
22	5	ContractRequests	Contract Requests	طلبات التعاقد	/contract-requests	3	t
23	5	ContractSettlements	Contract Settlements	مستخلصات العملاء ومقاولي الباطن	/settlements	4	t
24	6	InventoryManagement	Inventory Management	إدارة المخزون	/inventory	2	t
25	6	PurchaseCycle	Purchase Cycle	دورة المشتريات	/purchases	1	t
26	7	HumanResources	Human Resources	الموارد البشرية	/hr	1	t
2	1	AnalyticsReports	Reports & Analytics	التقارير والرسوم البيانية	/reports	30	t
28	2	CustomerRegistry	Customers	العملاء	/customers	26	t
29	2	ContractorRegistry	Contractors	المقاولون	/contractors	27	t
30	2	SupplierRegistry	Suppliers	الموردون	/suppliers	28	t
27	2	Counterparties	Counterparties	المقاولون والموردون والعملاء	/counterparties	26	t
31	3	CashEgp	Cash - EGP	صندوق خزينة الجنيه المصري	/treasury/cash-egp	12	t
\.


--
-- TOC entry 5530 (class 0 OID 18006)
-- Dependencies: 232
-- Data for Name: Sections; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Sections" ("SectionId", "Code", "NameEn", "NameAr", "SortOrder", "IsActive") FROM stdin;
1	REPORTS	Reports	التقارير	2	t
2	ACCOUNTING	Accounting	الحسابات	1	t
3	TREASURY	Treasury & Banks	الخزائن والبنوك	2	t
4	CHECKS	Checks	الشيكات	3	t
5	PROJECTS	Projects & Contracts	المشروعات والعقود	5	t
6	PROCUREMENT	Procurement & Inventory	المشتريات والمخازن	6	t
7	HR	Human Resources	الموارد البشرية	7	t
\.


--
-- TOC entry 5610 (class 0 OID 19110)
-- Dependencies: 312
-- Data for Name: SupplierInvoiceLines; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."SupplierInvoiceLines" ("LineId", "InvoiceId", "PurchaseOrderLineId", "AccountId", "Quantity", "UnitPrice", "NetAmount", "TaxAmount") FROM stdin;
\.


--
-- TOC entry 5608 (class 0 OID 19067)
-- Dependencies: 310
-- Data for Name: SupplierInvoices; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."SupplierInvoices" ("InvoiceId", "SupplierId", "PurchaseOrderId", "InvoiceNo", "InvoiceDate", "TaxAccountId", "TaxAmount", "TotalAmount", "Status", "CreatedBy", "ApprovedBy", "ApprovedAt", "JournalEntryId", "CreatedAt", "NetAmount", "ProjectId") FROM stdin;
\.


--
-- TOC entry 5601 (class 0 OID 18846)
-- Dependencies: 303
-- Data for Name: TechnicalSettlementEstimateItems; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."TechnicalSettlementEstimateItems" ("EstimateItemId", "EstimateId", "ContractItemId", "PreviousQuantity", "CurrentQuantity", "UnitPrice", "Amount", "CreatedAt", "AccountId", "ProjectId") FROM stdin;
14	9	80	0.0000	100.0000	100.0000	10000.00	2026-10-19 10:28:26.754268	\N	\N
15	10	80	100.0000	100.0000	100.0000	10000.00	2026-10-19 10:29:16.145568	\N	\N
\.


--
-- TOC entry 5599 (class 0 OID 18812)
-- Dependencies: 301
-- Data for Name: TechnicalSettlementEstimates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."TechnicalSettlementEstimates" ("EstimateId", "ContractId", "SettlementSide", "EstimateNo", "EstimateDate", "CounterpartyName", "WorkValue", "Status", "Notes", "FinancialSettlementId", "CreatedBy", "ReviewedBy", "ReviewedAt", "CreatedAt", "CounterpartyId") FROM stdin;
9	13	Customer	TE-0001	2026-10-19	لوكس	10000.00	TechnicallyApproved	\N	12	1	1	2026-10-19 10:28:31.709896	2026-10-19 10:28:26.750023	1
10	13	Customer	TE-0002	2026-10-19	لوكس	10000.00	TechnicallyApproved	\N	13	1	1	2026-10-19 10:29:18.050263	2026-10-19 10:29:16.142094	1
\.


--
-- TOC entry 5557 (class 0 OID 18250)
-- Dependencies: 259
-- Data for Name: TreasuryAccounts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."TreasuryAccounts" ("TreasuryAccountId", "NameAr", "AccountType", "CurrencyCode", "BankAccountNumber", "GLAccountId", "IsActive", "ScreenCode", "ChecksScreenCode") FROM stdin;
1	البنك التجاري الدولي CIB (جنيه مصري)	Bank	EGP	100000000000	140	t	BankCibEgp	ChecksCib
\.


--
-- TOC entry 5567 (class 0 OID 18354)
-- Dependencies: 269
-- Data for Name: TreasuryTransactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."TreasuryTransactions" ("TransactionId", "TreasuryAccountId", "TransactionDate", "Inflow", "Outflow", "Description", "VoucherNo", "Status", "RecipientName", "ProjectId", "JournalEntryId", "CreatedAt", "SettlementId", "CounterpartyId", "SupplierInvoiceId") FROM stdin;
\.


--
-- TOC entry 5623 (class 0 OID 19651)
-- Dependencies: 325
-- Data for Name: UserAvatars; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."UserAvatars" ("UserId", "ImageData", "MediaType") FROM stdin;
\.


--
-- TOC entry 5543 (class 0 OID 18103)
-- Dependencies: 245
-- Data for Name: UserPermissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."UserPermissions" ("UserId", "PermissionId", "IsAllowed") FROM stdin;
\.


--
-- TOC entry 5542 (class 0 OID 18088)
-- Dependencies: 244
-- Data for Name: UserRoles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."UserRoles" ("UserId", "RoleId") FROM stdin;
1	1
2	2
\.


--
-- TOC entry 5524 (class 0 OID 17977)
-- Dependencies: 226
-- Data for Name: Users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."Users" ("UserId", "Username", "PasswordHash", "FullName", "IsActive", "LastLoginAt", "FailedLoginCount", "LockedUntil", "CreatedAt", "TokenVersion", "AvatarUpdatedAt") FROM stdin;
2	ahmed.saqr	\\x24326224313224354275306b6a624e6c695a6f714a69374f4230593475753155624e374656334f534b3275393443306b364936504f63634372714b79	احمد محمد صقر	t	2026-10-18 15:23:29.806065	0	\N	2026-10-18 15:20:35.395776	0	\N
1	admin	\\x24326224313224683775783465364d33624477474e4e356c6b4357654f3174566347764974444564555233523167792f71326b2f674e6f53422e484f	System Admin	t	2026-11-05 12:16:48.016612	0	\N	2026-10-17 07:51:06.054814	2	\N
\.


--
-- TOC entry 5685 (class 0 OID 0)
-- Dependencies: 223
-- Name: AccountClassifications_ClassificationId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."AccountClassifications_ClassificationId_seq"', 30, true);


--
-- TOC entry 5686 (class 0 OID 0)
-- Dependencies: 246
-- Name: AuditLog_AuditId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."AuditLog_AuditId_seq"', 341, true);


--
-- TOC entry 5687 (class 0 OID 0)
-- Dependencies: 292
-- Name: BankReconciliationLines_LineId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."BankReconciliationLines_LineId_seq"', 1, false);


--
-- TOC entry 5688 (class 0 OID 0)
-- Dependencies: 270
-- Name: BankReconciliations_ReconciliationId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."BankReconciliations_ReconciliationId_seq"', 1, false);


--
-- TOC entry 5689 (class 0 OID 0)
-- Dependencies: 260
-- Name: Beneficiaries_BeneficiaryId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Beneficiaries_BeneficiaryId_seq"', 1, true);


--
-- TOC entry 5690 (class 0 OID 0)
-- Dependencies: 317
-- Name: CatalogItems_CatalogItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."CatalogItems_CatalogItemId_seq"', 1, false);


--
-- TOC entry 5691 (class 0 OID 0)
-- Dependencies: 241
-- Name: ChartOfAccounts_AccountId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ChartOfAccounts_AccountId_seq"', 587, true);


--
-- TOC entry 5692 (class 0 OID 0)
-- Dependencies: 276
-- Name: CheckPrintTemplates_TemplateId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."CheckPrintTemplates_TemplateId_seq"', 1, false);


--
-- TOC entry 5693 (class 0 OID 0)
-- Dependencies: 326
-- Name: CheckSignatories_SignatoryId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."CheckSignatories_SignatoryId_seq"', 1, false);


--
-- TOC entry 5694 (class 0 OID 0)
-- Dependencies: 294
-- Name: CheckStatusHistory_HistoryId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."CheckStatusHistory_HistoryId_seq"', 1, true);


--
-- TOC entry 5695 (class 0 OID 0)
-- Dependencies: 272
-- Name: Checks_CheckId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Checks_CheckId_seq"', 1, true);


--
-- TOC entry 5696 (class 0 OID 0)
-- Dependencies: 217
-- Name: Companies_CompanyId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Companies_CompanyId_seq"', 1, true);


--
-- TOC entry 5697 (class 0 OID 0)
-- Dependencies: 286
-- Name: ContractAccountingConfig_ConfigId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractAccountingConfig_ConfigId_seq"', 1, false);


--
-- TOC entry 5698 (class 0 OID 0)
-- Dependencies: 278
-- Name: ContractAddendums_AddendumId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractAddendums_AddendumId_seq"', 1, false);


--
-- TOC entry 5699 (class 0 OID 0)
-- Dependencies: 298
-- Name: ContractAttachments_AttachmentId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractAttachments_AttachmentId_seq"', 1, false);


--
-- TOC entry 5700 (class 0 OID 0)
-- Dependencies: 290
-- Name: ContractChangeOrders_ChangeOrderId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractChangeOrders_ChangeOrderId_seq"', 1, false);


--
-- TOC entry 5701 (class 0 OID 0)
-- Dependencies: 284
-- Name: ContractDeductionRules_RuleId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractDeductionRules_RuleId_seq"', 38, true);


--
-- TOC entry 5702 (class 0 OID 0)
-- Dependencies: 282
-- Name: ContractItems_ItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractItems_ItemId_seq"', 80, true);


--
-- TOC entry 5703 (class 0 OID 0)
-- Dependencies: 321
-- Name: ContractRequestItems_RequestItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractRequestItems_RequestItemId_seq"', 1, false);


--
-- TOC entry 5704 (class 0 OID 0)
-- Dependencies: 250
-- Name: ContractRequests_RequestId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractRequests_RequestId_seq"', 1, true);


--
-- TOC entry 5705 (class 0 OID 0)
-- Dependencies: 296
-- Name: ContractSettlementItems_SettlementItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractSettlementItems_SettlementItemId_seq"', 14, true);


--
-- TOC entry 5706 (class 0 OID 0)
-- Dependencies: 288
-- Name: ContractSettlements_SettlementId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ContractSettlements_SettlementId_seq"', 13, true);


--
-- TOC entry 5707 (class 0 OID 0)
-- Dependencies: 262
-- Name: Contracts_ContractId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Contracts_ContractId_seq"', 13, true);


--
-- TOC entry 5708 (class 0 OID 0)
-- Dependencies: 307
-- Name: Counterparties_CounterpartyId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Counterparties_CounterpartyId_seq"', 8, true);


--
-- TOC entry 5709 (class 0 OID 0)
-- Dependencies: 304
-- Name: CounterpartyAliases_AliasId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."CounterpartyAliases_AliasId_seq"', 1, true);


--
-- TOC entry 5710 (class 0 OID 0)
-- Dependencies: 221
-- Name: ExchangeRates_ExchangeRateId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ExchangeRates_ExchangeRateId_seq"', 1, false);


--
-- TOC entry 5711 (class 0 OID 0)
-- Dependencies: 274
-- Name: FinancialChecks_CheckId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."FinancialChecks_CheckId_seq"', 2, true);


--
-- TOC entry 5712 (class 0 OID 0)
-- Dependencies: 239
-- Name: FinancialStatementLines_LineId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."FinancialStatementLines_LineId_seq"', 1, false);


--
-- TOC entry 5713 (class 0 OID 0)
-- Dependencies: 237
-- Name: FiscalYears_FiscalYearId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."FiscalYears_FiscalYearId_seq"', 1, true);


--
-- TOC entry 5714 (class 0 OID 0)
-- Dependencies: 235
-- Name: InventoryItems_ItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."InventoryItems_ItemId_seq"', 2, true);


--
-- TOC entry 5715 (class 0 OID 0)
-- Dependencies: 252
-- Name: InventoryMovements_MovementId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."InventoryMovements_MovementId_seq"', 4, true);


--
-- TOC entry 5716 (class 0 OID 0)
-- Dependencies: 233
-- Name: InventoryWarehouses_WarehouseId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."InventoryWarehouses_WarehouseId_seq"', 2, true);


--
-- TOC entry 5717 (class 0 OID 0)
-- Dependencies: 323
-- Name: ItemCatalog_CatalogItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ItemCatalog_CatalogItemId_seq"', 6, true);


--
-- TOC entry 5718 (class 0 OID 0)
-- Dependencies: 256
-- Name: JournalEntries_JournalEntryId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."JournalEntries_JournalEntryId_seq"', 9, true);


--
-- TOC entry 5719 (class 0 OID 0)
-- Dependencies: 266
-- Name: JournalEntryDetails_DetailId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."JournalEntryDetails_DetailId_seq"', 20, true);


--
-- TOC entry 5720 (class 0 OID 0)
-- Dependencies: 229
-- Name: Permissions_PermissionId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Permissions_PermissionId_seq"', 441, true);


--
-- TOC entry 5721 (class 0 OID 0)
-- Dependencies: 280
-- Name: ProgressBillings_BillingId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."ProgressBillings_BillingId_seq"', 1, false);


--
-- TOC entry 5722 (class 0 OID 0)
-- Dependencies: 219
-- Name: Projects_ProjectId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Projects_ProjectId_seq"', 1, true);


--
-- TOC entry 5723 (class 0 OID 0)
-- Dependencies: 264
-- Name: PurchaseOrderLines_LineId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."PurchaseOrderLines_LineId_seq"', 4, true);


--
-- TOC entry 5724 (class 0 OID 0)
-- Dependencies: 254
-- Name: PurchaseOrders_PurchaseOrderId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."PurchaseOrders_PurchaseOrderId_seq"', 4, true);


--
-- TOC entry 5725 (class 0 OID 0)
-- Dependencies: 315
-- Name: PurchaseReturnLines_LineId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."PurchaseReturnLines_LineId_seq"', 1, false);


--
-- TOC entry 5726 (class 0 OID 0)
-- Dependencies: 313
-- Name: PurchaseReturns_ReturnId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."PurchaseReturns_ReturnId_seq"', 1, false);


--
-- TOC entry 5727 (class 0 OID 0)
-- Dependencies: 319
-- Name: RecordAttachments_AttachmentId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."RecordAttachments_AttachmentId_seq"', 1, false);


--
-- TOC entry 5728 (class 0 OID 0)
-- Dependencies: 227
-- Name: Roles_RoleId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Roles_RoleId_seq"', 8, true);


--
-- TOC entry 5729 (class 0 OID 0)
-- Dependencies: 248
-- Name: Screens_ScreenId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Screens_ScreenId_seq"', 31, true);


--
-- TOC entry 5730 (class 0 OID 0)
-- Dependencies: 231
-- Name: Sections_SectionId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Sections_SectionId_seq"', 7, true);


--
-- TOC entry 5731 (class 0 OID 0)
-- Dependencies: 311
-- Name: SupplierInvoiceLines_LineId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."SupplierInvoiceLines_LineId_seq"', 1, false);


--
-- TOC entry 5732 (class 0 OID 0)
-- Dependencies: 309
-- Name: SupplierInvoices_InvoiceId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."SupplierInvoices_InvoiceId_seq"', 1, false);


--
-- TOC entry 5733 (class 0 OID 0)
-- Dependencies: 302
-- Name: TechnicalSettlementEstimateItems_EstimateItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."TechnicalSettlementEstimateItems_EstimateItemId_seq"', 15, true);


--
-- TOC entry 5734 (class 0 OID 0)
-- Dependencies: 300
-- Name: TechnicalSettlementEstimates_EstimateId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."TechnicalSettlementEstimates_EstimateId_seq"', 10, true);


--
-- TOC entry 5735 (class 0 OID 0)
-- Dependencies: 258
-- Name: TreasuryAccounts_TreasuryAccountId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."TreasuryAccounts_TreasuryAccountId_seq"', 1, true);


--
-- TOC entry 5736 (class 0 OID 0)
-- Dependencies: 268
-- Name: TreasuryTransactions_TransactionId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."TreasuryTransactions_TransactionId_seq"', 1, false);


--
-- TOC entry 5737 (class 0 OID 0)
-- Dependencies: 225
-- Name: Users_UserId_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public."Users_UserId_seq"', 2, true);


--
-- TOC entry 4996 (class 2606 OID 17975)
-- Name: AccountClassifications AccountClassifications_NameAr_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AccountClassifications"
    ADD CONSTRAINT "AccountClassifications_NameAr_key" UNIQUE ("NameAr");


--
-- TOC entry 4998 (class 2606 OID 17973)
-- Name: AccountClassifications AccountClassifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AccountClassifications"
    ADD CONSTRAINT "AccountClassifications_pkey" PRIMARY KEY ("ClassificationId");


--
-- TOC entry 5036 (class 2606 OID 18126)
-- Name: AuditLog AuditLog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AuditLog"
    ADD CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("AuditId");


--
-- TOC entry 5149 (class 2606 OID 18671)
-- Name: BankReconciliationLines BankReconciliationLines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliationLines"
    ADD CONSTRAINT "BankReconciliationLines_pkey" PRIMARY KEY ("LineId");


--
-- TOC entry 5089 (class 2606 OID 18386)
-- Name: BankReconciliations BankReconciliations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliations"
    ADD CONSTRAINT "BankReconciliations_pkey" PRIMARY KEY ("ReconciliationId");


--
-- TOC entry 5068 (class 2606 OID 18273)
-- Name: Beneficiaries Beneficiaries_Code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Beneficiaries"
    ADD CONSTRAINT "Beneficiaries_Code_key" UNIQUE ("Code");


--
-- TOC entry 5070 (class 2606 OID 18271)
-- Name: Beneficiaries Beneficiaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Beneficiaries"
    ADD CONSTRAINT "Beneficiaries_pkey" PRIMARY KEY ("BeneficiaryId");


--
-- TOC entry 5211 (class 2606 OID 19249)
-- Name: CatalogItems CatalogItems_InventoryItemId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_InventoryItemId_key" UNIQUE ("InventoryItemId");


--
-- TOC entry 5213 (class 2606 OID 19247)
-- Name: CatalogItems CatalogItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_pkey" PRIMARY KEY ("CatalogItemId");


--
-- TOC entry 5026 (class 2606 OID 18062)
-- Name: ChartOfAccounts ChartOfAccounts_AccountCode_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ChartOfAccounts"
    ADD CONSTRAINT "ChartOfAccounts_AccountCode_key" UNIQUE ("AccountCode");


--
-- TOC entry 5028 (class 2606 OID 18060)
-- Name: ChartOfAccounts ChartOfAccounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ChartOfAccounts"
    ADD CONSTRAINT "ChartOfAccounts_pkey" PRIMARY KEY ("AccountId");


--
-- TOC entry 5103 (class 2606 OID 18462)
-- Name: CheckPrintTemplates CheckPrintTemplates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckPrintTemplates"
    ADD CONSTRAINT "CheckPrintTemplates_pkey" PRIMARY KEY ("TemplateId");


--
-- TOC entry 5231 (class 2606 OID 19838)
-- Name: CheckSignatories CheckSignatories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckSignatories"
    ADD CONSTRAINT "CheckSignatories_pkey" PRIMARY KEY ("SignatoryId");


--
-- TOC entry 5151 (class 2606 OID 18683)
-- Name: CheckStatusHistory CheckStatusHistory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckStatusHistory"
    ADD CONSTRAINT "CheckStatusHistory_pkey" PRIMARY KEY ("HistoryId");


--
-- TOC entry 5091 (class 2606 OID 18405)
-- Name: Checks Checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks"
    ADD CONSTRAINT "Checks_pkey" PRIMARY KEY ("CheckId");


--
-- TOC entry 4986 (class 2606 OID 17948)
-- Name: Companies Companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Companies"
    ADD CONSTRAINT "Companies_pkey" PRIMARY KEY ("CompanyId");


--
-- TOC entry 5127 (class 2606 OID 18555)
-- Name: ContractAccountingConfig ContractAccountingConfig_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_pkey" PRIMARY KEY ("ConfigId");


--
-- TOC entry 5107 (class 2606 OID 18478)
-- Name: ContractAddendums ContractAddendums_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAddendums"
    ADD CONSTRAINT "ContractAddendums_pkey" PRIMARY KEY ("AddendumId");


--
-- TOC entry 5161 (class 2606 OID 18725)
-- Name: ContractAttachments ContractAttachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAttachments"
    ADD CONSTRAINT "ContractAttachments_pkey" PRIMARY KEY ("AttachmentId");


--
-- TOC entry 5143 (class 2606 OID 18644)
-- Name: ContractChangeOrders ContractChangeOrders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders"
    ADD CONSTRAINT "ContractChangeOrders_pkey" PRIMARY KEY ("ChangeOrderId");


--
-- TOC entry 5121 (class 2606 OID 18535)
-- Name: ContractDeductionRules ContractDeductionRules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractDeductionRules"
    ADD CONSTRAINT "ContractDeductionRules_pkey" PRIMARY KEY ("RuleId");


--
-- TOC entry 5115 (class 2606 OID 18519)
-- Name: ContractItems ContractItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "ContractItems_pkey" PRIMARY KEY ("ItemId");


--
-- TOC entry 5220 (class 2606 OID 19295)
-- Name: ContractRequestItems ContractRequestItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems"
    ADD CONSTRAINT "ContractRequestItems_pkey" PRIMARY KEY ("RequestItemId");


--
-- TOC entry 5044 (class 2606 OID 18156)
-- Name: ContractRequests ContractRequests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests"
    ADD CONSTRAINT "ContractRequests_pkey" PRIMARY KEY ("RequestId");


--
-- TOC entry 5153 (class 2606 OID 18701)
-- Name: ContractSettlementItems ContractSettlementItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "ContractSettlementItems_pkey" PRIMARY KEY ("SettlementItemId");


--
-- TOC entry 5132 (class 2606 OID 18619)
-- Name: ContractSettlements ContractSettlements_JournalEntryId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_JournalEntryId_key" UNIQUE ("JournalEntryId");


--
-- TOC entry 5134 (class 2606 OID 18613)
-- Name: ContractSettlements ContractSettlements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_pkey" PRIMARY KEY ("SettlementId");


--
-- TOC entry 5072 (class 2606 OID 18294)
-- Name: Contracts Contracts_RequestId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_RequestId_key" UNIQUE ("RequestId");


--
-- TOC entry 5074 (class 2606 OID 18292)
-- Name: Contracts Contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_pkey" PRIMARY KEY ("ContractId");


--
-- TOC entry 5185 (class 2606 OID 19057)
-- Name: Counterparties Counterparties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Counterparties"
    ADD CONSTRAINT "Counterparties_pkey" PRIMARY KEY ("CounterpartyId");


--
-- TOC entry 5179 (class 2606 OID 19029)
-- Name: CounterpartyAliases CounterpartyAliases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CounterpartyAliases"
    ADD CONSTRAINT "CounterpartyAliases_pkey" PRIMARY KEY ("AliasId");


--
-- TOC entry 4992 (class 2606 OID 17964)
-- Name: ExchangeRates ExchangeRates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ExchangeRates"
    ADD CONSTRAINT "ExchangeRates_pkey" PRIMARY KEY ("ExchangeRateId");


--
-- TOC entry 5096 (class 2606 OID 18433)
-- Name: FinancialChecks FinancialChecks_CheckNumber_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_CheckNumber_key" UNIQUE ("CheckNumber");


--
-- TOC entry 5098 (class 2606 OID 18435)
-- Name: FinancialChecks FinancialChecks_JournalEntryId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_JournalEntryId_key" UNIQUE ("JournalEntryId");


--
-- TOC entry 5100 (class 2606 OID 18431)
-- Name: FinancialChecks FinancialChecks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_pkey" PRIMARY KEY ("CheckId");


--
-- TOC entry 5024 (class 2606 OID 18048)
-- Name: FinancialStatementLines FinancialStatementLines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialStatementLines"
    ADD CONSTRAINT "FinancialStatementLines_pkey" PRIMARY KEY ("LineId");


--
-- TOC entry 5022 (class 2606 OID 18036)
-- Name: FiscalYears FiscalYears_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FiscalYears"
    ADD CONSTRAINT "FiscalYears_pkey" PRIMARY KEY ("FiscalYearId");


--
-- TOC entry 5019 (class 2606 OID 18028)
-- Name: InventoryItems InventoryItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryItems"
    ADD CONSTRAINT "InventoryItems_pkey" PRIMARY KEY ("ItemId");


--
-- TOC entry 5049 (class 2606 OID 18181)
-- Name: InventoryMovements InventoryMovements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_pkey" PRIMARY KEY ("MovementId");


--
-- TOC entry 5016 (class 2606 OID 18020)
-- Name: InventoryWarehouses InventoryWarehouses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryWarehouses"
    ADD CONSTRAINT "InventoryWarehouses_pkey" PRIMARY KEY ("WarehouseId");


--
-- TOC entry 5223 (class 2606 OID 19461)
-- Name: ItemCatalog ItemCatalog_InventoryItemId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ItemCatalog"
    ADD CONSTRAINT "ItemCatalog_InventoryItemId_key" UNIQUE ("InventoryItemId");


--
-- TOC entry 5225 (class 2606 OID 19459)
-- Name: ItemCatalog ItemCatalog_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ItemCatalog"
    ADD CONSTRAINT "ItemCatalog_pkey" PRIMARY KEY ("CatalogItemId");


--
-- TOC entry 5057 (class 2606 OID 18228)
-- Name: JournalEntries JournalEntries_EntryNo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_EntryNo_key" UNIQUE ("EntryNo");


--
-- TOC entry 5059 (class 2606 OID 18226)
-- Name: JournalEntries JournalEntries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_pkey" PRIMARY KEY ("JournalEntryId");


--
-- TOC entry 5081 (class 2606 OID 18337)
-- Name: JournalEntryDetails JournalEntryDetails_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntryDetails"
    ADD CONSTRAINT "JournalEntryDetails_pkey" PRIMARY KEY ("DetailId");


--
-- TOC entry 5008 (class 2606 OID 18002)
-- Name: Permissions Permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Permissions"
    ADD CONSTRAINT "Permissions_pkey" PRIMARY KEY ("PermissionId");


--
-- TOC entry 5112 (class 2606 OID 18498)
-- Name: ProgressBillings ProgressBillings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ProgressBillings"
    ADD CONSTRAINT "ProgressBillings_pkey" PRIMARY KEY ("BillingId");


--
-- TOC entry 4988 (class 2606 OID 17957)
-- Name: Projects Projects_NameAr_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Projects"
    ADD CONSTRAINT "Projects_NameAr_key" UNIQUE ("NameAr");


--
-- TOC entry 4990 (class 2606 OID 17955)
-- Name: Projects Projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Projects"
    ADD CONSTRAINT "Projects_pkey" PRIMARY KEY ("ProjectId");


--
-- TOC entry 5078 (class 2606 OID 18317)
-- Name: PurchaseOrderLines PurchaseOrderLines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_pkey" PRIMARY KEY ("LineId");


--
-- TOC entry 5053 (class 2606 OID 18206)
-- Name: PurchaseOrders PurchaseOrders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrders"
    ADD CONSTRAINT "PurchaseOrders_pkey" PRIMARY KEY ("PurchaseOrderId");


--
-- TOC entry 5208 (class 2606 OID 19172)
-- Name: PurchaseReturnLines PurchaseReturnLines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturnLines"
    ADD CONSTRAINT "PurchaseReturnLines_pkey" PRIMARY KEY ("LineId");


--
-- TOC entry 5201 (class 2606 OID 19144)
-- Name: PurchaseReturns PurchaseReturns_JournalEntryId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_JournalEntryId_key" UNIQUE ("JournalEntryId");


--
-- TOC entry 5203 (class 2606 OID 19142)
-- Name: PurchaseReturns PurchaseReturns_ReturnNo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_ReturnNo_key" UNIQUE ("ReturnNo");


--
-- TOC entry 5205 (class 2606 OID 19140)
-- Name: PurchaseReturns PurchaseReturns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_pkey" PRIMARY KEY ("ReturnId");


--
-- TOC entry 5216 (class 2606 OID 19279)
-- Name: RecordAttachments RecordAttachments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RecordAttachments"
    ADD CONSTRAINT "RecordAttachments_pkey" PRIMARY KEY ("AttachmentId");


--
-- TOC entry 5030 (class 2606 OID 18077)
-- Name: RolePermissions RolePermissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RolePermissions"
    ADD CONSTRAINT "RolePermissions_pkey" PRIMARY KEY ("RoleId", "PermissionId");


--
-- TOC entry 5004 (class 2606 OID 17995)
-- Name: Roles Roles_RoleName_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Roles"
    ADD CONSTRAINT "Roles_RoleName_key" UNIQUE ("RoleName");


--
-- TOC entry 5006 (class 2606 OID 17993)
-- Name: Roles Roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Roles"
    ADD CONSTRAINT "Roles_pkey" PRIMARY KEY ("RoleId");


--
-- TOC entry 5183 (class 2606 OID 19048)
-- Name: SchemaMigrations SchemaMigrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SchemaMigrations"
    ADD CONSTRAINT "SchemaMigrations_pkey" PRIMARY KEY ("MigrationId");


--
-- TOC entry 5039 (class 2606 OID 18142)
-- Name: Screens Screens_ScreenCode_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Screens"
    ADD CONSTRAINT "Screens_ScreenCode_key" UNIQUE ("ScreenCode");


--
-- TOC entry 5041 (class 2606 OID 18140)
-- Name: Screens Screens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Screens"
    ADD CONSTRAINT "Screens_pkey" PRIMARY KEY ("ScreenId");


--
-- TOC entry 5012 (class 2606 OID 18013)
-- Name: Sections Sections_Code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Sections"
    ADD CONSTRAINT "Sections_Code_key" UNIQUE ("Code");


--
-- TOC entry 5014 (class 2606 OID 18011)
-- Name: Sections Sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Sections"
    ADD CONSTRAINT "Sections_pkey" PRIMARY KEY ("SectionId");


--
-- TOC entry 5198 (class 2606 OID 19115)
-- Name: SupplierInvoiceLines SupplierInvoiceLines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoiceLines"
    ADD CONSTRAINT "SupplierInvoiceLines_pkey" PRIMARY KEY ("LineId");


--
-- TOC entry 5190 (class 2606 OID 19076)
-- Name: SupplierInvoices SupplierInvoices_JournalEntryId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_JournalEntryId_key" UNIQUE ("JournalEntryId");


--
-- TOC entry 5192 (class 2606 OID 19072)
-- Name: SupplierInvoices SupplierInvoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_pkey" PRIMARY KEY ("InvoiceId");


--
-- TOC entry 5173 (class 2606 OID 18851)
-- Name: TechnicalSettlementEstimateItems TechnicalSettlementEstimateItems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "TechnicalSettlementEstimateItems_pkey" PRIMARY KEY ("EstimateItemId");


--
-- TOC entry 5166 (class 2606 OID 18823)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_FinancialSettlementId_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_FinancialSettlementId_key" UNIQUE ("FinancialSettlementId");


--
-- TOC entry 5168 (class 2606 OID 18819)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_pkey" PRIMARY KEY ("EstimateId");


--
-- TOC entry 5062 (class 2606 OID 18259)
-- Name: TreasuryAccounts TreasuryAccounts_ChecksScreenCode_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryAccounts"
    ADD CONSTRAINT "TreasuryAccounts_ChecksScreenCode_key" UNIQUE ("ChecksScreenCode");


--
-- TOC entry 5064 (class 2606 OID 18257)
-- Name: TreasuryAccounts TreasuryAccounts_ScreenCode_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryAccounts"
    ADD CONSTRAINT "TreasuryAccounts_ScreenCode_key" UNIQUE ("ScreenCode");


--
-- TOC entry 5066 (class 2606 OID 18255)
-- Name: TreasuryAccounts TreasuryAccounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryAccounts"
    ADD CONSTRAINT "TreasuryAccounts_pkey" PRIMARY KEY ("TreasuryAccountId");


--
-- TOC entry 5086 (class 2606 OID 18361)
-- Name: TreasuryTransactions TreasuryTransactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_pkey" PRIMARY KEY ("TransactionId");


--
-- TOC entry 5105 (class 2606 OID 18464)
-- Name: CheckPrintTemplates UQ_CheckPrintTemplates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckPrintTemplates"
    ADD CONSTRAINT "UQ_CheckPrintTemplates" UNIQUE ("TreasuryAccountId", "FieldName");


--
-- TOC entry 5094 (class 2606 OID 18407)
-- Name: Checks UQ_Checks_BankBook; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks"
    ADD CONSTRAINT "UQ_Checks_BankBook" UNIQUE ("TreasuryAccountId", "CheckBookNo", "SequenceNo");


--
-- TOC entry 5129 (class 2606 OID 18557)
-- Name: ContractAccountingConfig UQ_ContractAccountingConfig_Contract_Side; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "UQ_ContractAccountingConfig_Contract_Side" UNIQUE ("ContractId", "SettlementSide");


--
-- TOC entry 5146 (class 2606 OID 18646)
-- Name: ContractChangeOrders UQ_ContractChangeOrders_Number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders"
    ADD CONSTRAINT "UQ_ContractChangeOrders_Number" UNIQUE ("ContractId", "ChangeOrderNo");


--
-- TOC entry 5124 (class 2606 OID 18537)
-- Name: ContractDeductionRules UQ_ContractDeductionRules_Code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractDeductionRules"
    ADD CONSTRAINT "UQ_ContractDeductionRules_Code" UNIQUE ("ContractId", "SettlementSide", "Code");


--
-- TOC entry 5118 (class 2606 OID 18521)
-- Name: ContractItems UQ_ContractItems_Contract_ItemNo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "UQ_ContractItems_Contract_ItemNo" UNIQUE ("ContractId", "ItemNo");


--
-- TOC entry 5157 (class 2606 OID 18703)
-- Name: ContractSettlementItems UQ_ContractSettlementItems_Line; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "UQ_ContractSettlementItems_Line" UNIQUE ("SettlementId", "ContractItemId");


--
-- TOC entry 5138 (class 2606 OID 18617)
-- Name: ContractSettlements UQ_ContractSettlements_Number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "UQ_ContractSettlements_Number" UNIQUE ("ContractId", "SettlementSide", "SettlementNo");


--
-- TOC entry 5140 (class 2606 OID 18615)
-- Name: ContractSettlements UQ_ContractSettlements_Sequence; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "UQ_ContractSettlements_Sequence" UNIQUE ("ContractId", "SettlementSide", "SequenceNo");


--
-- TOC entry 4994 (class 2606 OID 17966)
-- Name: ExchangeRates UQ_ExchangeRates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ExchangeRates"
    ADD CONSTRAINT "UQ_ExchangeRates" UNIQUE ("CurrencyCode", "RateDate");


--
-- TOC entry 5010 (class 2606 OID 18004)
-- Name: Permissions UQ_Permissions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Permissions"
    ADD CONSTRAINT "UQ_Permissions" UNIQUE ("ScreenCode", "ActionCode");


--
-- TOC entry 5194 (class 2606 OID 19074)
-- Name: SupplierInvoices UQ_SupplierInvoices_SupplierNumber; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "UQ_SupplierInvoices_SupplierNumber" UNIQUE ("SupplierId", "InvoiceNo");


--
-- TOC entry 5175 (class 2606 OID 18853)
-- Name: TechnicalSettlementEstimateItems UQ_TechnicalSettlementEstimateItems_Line; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "UQ_TechnicalSettlementEstimateItems_Line" UNIQUE ("EstimateId", "ContractItemId");


--
-- TOC entry 5170 (class 2606 OID 18821)
-- Name: TechnicalSettlementEstimates UQ_TechnicalSettlementEstimates_Number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "UQ_TechnicalSettlementEstimates_Number" UNIQUE ("ContractId", "SettlementSide", "EstimateNo");


--
-- TOC entry 5229 (class 2606 OID 19657)
-- Name: UserAvatars UserAvatars_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserAvatars"
    ADD CONSTRAINT "UserAvatars_pkey" PRIMARY KEY ("UserId");


--
-- TOC entry 5034 (class 2606 OID 18107)
-- Name: UserPermissions UserPermissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserPermissions"
    ADD CONSTRAINT "UserPermissions_pkey" PRIMARY KEY ("UserId", "PermissionId");


--
-- TOC entry 5032 (class 2606 OID 18092)
-- Name: UserRoles UserRoles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserRoles"
    ADD CONSTRAINT "UserRoles_pkey" PRIMARY KEY ("UserId", "RoleId");


--
-- TOC entry 5000 (class 2606 OID 17986)
-- Name: Users Users_Username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_Username_key" UNIQUE ("Username");


--
-- TOC entry 5002 (class 2606 OID 17984)
-- Name: Users Users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY ("UserId");


--
-- TOC entry 5037 (class 1259 OID 18749)
-- Name: IX_AuditLog_Timestamp_UserId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_AuditLog_Timestamp_UserId" ON public."AuditLog" USING btree ("Timestamp", "UserId");


--
-- TOC entry 5092 (class 1259 OID 19866)
-- Name: IX_Checks_SettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_Checks_SettlementId" ON public."Checks" USING btree ("SettlementId");


--
-- TOC entry 5108 (class 1259 OID 18750)
-- Name: IX_ContractAddendums_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractAddendums_ContractId" ON public."ContractAddendums" USING btree ("ContractId");


--
-- TOC entry 5144 (class 1259 OID 18755)
-- Name: IX_ContractChangeOrders_ContractStatus; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractChangeOrders_ContractStatus" ON public."ContractChangeOrders" USING btree ("ContractId", "Status");


--
-- TOC entry 5122 (class 1259 OID 18753)
-- Name: IX_ContractDeductionRules_ContractSide; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractDeductionRules_ContractSide" ON public."ContractDeductionRules" USING btree ("ContractId", "SettlementSide");


--
-- TOC entry 5116 (class 1259 OID 18752)
-- Name: IX_ContractItems_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractItems_ContractId" ON public."ContractItems" USING btree ("ContractId");


--
-- TOC entry 5045 (class 1259 OID 19189)
-- Name: IX_ContractRequests_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractRequests_CounterpartyId" ON public."ContractRequests" USING btree ("CounterpartyId");


--
-- TOC entry 5154 (class 1259 OID 18757)
-- Name: IX_ContractSettlementItems_ContractItemId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractSettlementItems_ContractItemId" ON public."ContractSettlementItems" USING btree ("ContractItemId");


--
-- TOC entry 5155 (class 1259 OID 18756)
-- Name: IX_ContractSettlementItems_SettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractSettlementItems_SettlementId" ON public."ContractSettlementItems" USING btree ("SettlementId");


--
-- TOC entry 5135 (class 1259 OID 18754)
-- Name: IX_ContractSettlements_ContractSideDate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractSettlements_ContractSideDate" ON public."ContractSettlements" USING btree ("ContractId", "SettlementSide", "SettlementDate");


--
-- TOC entry 5136 (class 1259 OID 19201)
-- Name: IX_ContractSettlements_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ContractSettlements_CounterpartyId" ON public."ContractSettlements" USING btree ("CounterpartyId");


--
-- TOC entry 5075 (class 1259 OID 19195)
-- Name: IX_Contracts_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_Contracts_CounterpartyId" ON public."Contracts" USING btree ("CounterpartyId");


--
-- TOC entry 5101 (class 1259 OID 18764)
-- Name: IX_FinancialChecks_ProjectBrand_Status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_FinancialChecks_ProjectBrand_Status" ON public."FinancialChecks" USING btree ("ProjectBrand", "Status");


--
-- TOC entry 5047 (class 1259 OID 19382)
-- Name: IX_InventoryMovements_DocumentNo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_InventoryMovements_DocumentNo" ON public."InventoryMovements" USING btree ("DocumentNo");


--
-- TOC entry 5055 (class 1259 OID 19924)
-- Name: IX_JournalEntries_SourceSettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_JournalEntries_SourceSettlementId" ON public."JournalEntries" USING btree ("SourceSettlementId");


--
-- TOC entry 5110 (class 1259 OID 18751)
-- Name: IX_ProgressBillings_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_ProgressBillings_ContractId" ON public."ProgressBillings" USING btree ("ContractId");


--
-- TOC entry 5051 (class 1259 OID 19219)
-- Name: IX_PurchaseOrders_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_PurchaseOrders_CounterpartyId" ON public."PurchaseOrders" USING btree ("CounterpartyId");


--
-- TOC entry 5164 (class 1259 OID 19207)
-- Name: IX_TechnicalSettlementEstimates_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_TechnicalSettlementEstimates_CounterpartyId" ON public."TechnicalSettlementEstimates" USING btree ("CounterpartyId");


--
-- TOC entry 5082 (class 1259 OID 19213)
-- Name: IX_TreasuryTransactions_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_TreasuryTransactions_CounterpartyId" ON public."TreasuryTransactions" USING btree ("CounterpartyId");


--
-- TOC entry 5083 (class 1259 OID 19037)
-- Name: IX_TreasuryTransactions_SettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_TreasuryTransactions_SettlementId" ON public."TreasuryTransactions" USING btree ("SettlementId");


--
-- TOC entry 5084 (class 1259 OID 19230)
-- Name: IX_TreasuryTransactions_SupplierInvoiceId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "IX_TreasuryTransactions_SupplierInvoiceId" ON public."TreasuryTransactions" USING btree ("SupplierInvoiceId");


--
-- TOC entry 5060 (class 1259 OID 19714)
-- Name: UQ_JournalEntries_Source; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "UQ_JournalEntries_Source" ON public."JournalEntries" USING btree ("SourceType", "SourceId");


--
-- TOC entry 5042 (class 1259 OID 18931)
-- Name: UX_Screens_ActiveRoute; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "UX_Screens_ActiveRoute" ON public."Screens" USING btree (lower(("Route")::text)) WHERE "IsActive";


--
-- TOC entry 5087 (class 1259 OID 18748)
-- Name: UX_TreasuryTransactions_CheckVoucher; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "UX_TreasuryTransactions_CheckVoucher" ON public."TreasuryTransactions" USING btree ("VoucherNo") WHERE (("VoucherNo")::text ~~ 'CHK-%'::text);


--
-- TOC entry 5214 (class 1259 OID 19270)
-- Name: ix_CatalogItems_Code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_CatalogItems_Code" ON public."CatalogItems" USING btree ("Code");


--
-- TOC entry 5232 (class 1259 OID 19845)
-- Name: ix_CheckSignatories_NameAr; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_CheckSignatories_NameAr" ON public."CheckSignatories" USING btree ("NameAr");


--
-- TOC entry 5233 (class 1259 OID 19844)
-- Name: ix_CheckSignatories_TreasuryAccountId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_CheckSignatories_TreasuryAccountId" ON public."CheckSignatories" USING btree ("TreasuryAccountId");


--
-- TOC entry 5130 (class 1259 OID 18603)
-- Name: ix_ContractAccountingConfig_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractAccountingConfig_ContractId" ON public."ContractAccountingConfig" USING btree ("ContractId");


--
-- TOC entry 5109 (class 1259 OID 18489)
-- Name: ix_ContractAddendums_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractAddendums_ContractId" ON public."ContractAddendums" USING btree ("ContractId");


--
-- TOC entry 5162 (class 1259 OID 18742)
-- Name: ix_ContractAttachments_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractAttachments_ContractId" ON public."ContractAttachments" USING btree ("ContractId");


--
-- TOC entry 5163 (class 1259 OID 18741)
-- Name: ix_ContractAttachments_SettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractAttachments_SettlementId" ON public."ContractAttachments" USING btree ("SettlementId");


--
-- TOC entry 5147 (class 1259 OID 18662)
-- Name: ix_ContractChangeOrders_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractChangeOrders_ContractId" ON public."ContractChangeOrders" USING btree ("ContractId");


--
-- TOC entry 5125 (class 1259 OID 18548)
-- Name: ix_ContractDeductionRules_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractDeductionRules_ContractId" ON public."ContractDeductionRules" USING btree ("ContractId");


--
-- TOC entry 5119 (class 1259 OID 18527)
-- Name: ix_ContractItems_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractItems_ContractId" ON public."ContractItems" USING btree ("ContractId");


--
-- TOC entry 5221 (class 1259 OID 19316)
-- Name: ix_ContractRequestItems_RequestId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractRequestItems_RequestId" ON public."ContractRequestItems" USING btree ("RequestId");


--
-- TOC entry 5046 (class 1259 OID 18172)
-- Name: ix_ContractRequests_RequestNo; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_ContractRequests_RequestNo" ON public."ContractRequests" USING btree ("RequestNo");


--
-- TOC entry 5158 (class 1259 OID 18714)
-- Name: ix_ContractSettlementItems_ContractItemId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractSettlementItems_ContractItemId" ON public."ContractSettlementItems" USING btree ("ContractItemId");


--
-- TOC entry 5159 (class 1259 OID 18715)
-- Name: ix_ContractSettlementItems_SettlementId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractSettlementItems_SettlementId" ON public."ContractSettlementItems" USING btree ("SettlementId");


--
-- TOC entry 5141 (class 1259 OID 18635)
-- Name: ix_ContractSettlements_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ContractSettlements_ContractId" ON public."ContractSettlements" USING btree ("ContractId");


--
-- TOC entry 5076 (class 1259 OID 18310)
-- Name: ix_Contracts_ContractNo; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_Contracts_ContractNo" ON public."Contracts" USING btree ("ContractNo");


--
-- TOC entry 5186 (class 1259 OID 19064)
-- Name: ix_Counterparties_Code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_Counterparties_Code" ON public."Counterparties" USING btree ("Code");


--
-- TOC entry 5187 (class 1259 OID 19063)
-- Name: ix_Counterparties_LegalName; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_Counterparties_LegalName" ON public."Counterparties" USING btree ("LegalName");


--
-- TOC entry 5188 (class 1259 OID 19065)
-- Name: ix_Counterparties_PartyType; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_Counterparties_PartyType" ON public."Counterparties" USING btree ("PartyType");


--
-- TOC entry 5180 (class 1259 OID 19031)
-- Name: ix_CounterpartyAliases_AliasName; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_CounterpartyAliases_AliasName" ON public."CounterpartyAliases" USING btree ("AliasName");


--
-- TOC entry 5181 (class 1259 OID 19030)
-- Name: ix_CounterpartyAliases_CanonicalName; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_CounterpartyAliases_CanonicalName" ON public."CounterpartyAliases" USING btree ("CanonicalName");


--
-- TOC entry 5020 (class 1259 OID 18029)
-- Name: ix_InventoryItems_Code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_InventoryItems_Code" ON public."InventoryItems" USING btree ("Code");


--
-- TOC entry 5050 (class 1259 OID 18197)
-- Name: ix_InventoryMovements_MovementNo; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_InventoryMovements_MovementNo" ON public."InventoryMovements" USING btree ("MovementNo");


--
-- TOC entry 5017 (class 1259 OID 18021)
-- Name: ix_InventoryWarehouses_Code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_InventoryWarehouses_Code" ON public."InventoryWarehouses" USING btree ("Code");


--
-- TOC entry 5226 (class 1259 OID 19472)
-- Name: ix_ItemCatalog_AccountId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ItemCatalog_AccountId" ON public."ItemCatalog" USING btree ("AccountId");


--
-- TOC entry 5227 (class 1259 OID 19473)
-- Name: ix_ItemCatalog_Code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_ItemCatalog_Code" ON public."ItemCatalog" USING btree ("Code");


--
-- TOC entry 5113 (class 1259 OID 18509)
-- Name: ix_ProgressBillings_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_ProgressBillings_ContractId" ON public."ProgressBillings" USING btree ("ContractId");


--
-- TOC entry 5079 (class 1259 OID 18328)
-- Name: ix_PurchaseOrderLines_PurchaseOrderId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_PurchaseOrderLines_PurchaseOrderId" ON public."PurchaseOrderLines" USING btree ("PurchaseOrderId");


--
-- TOC entry 5054 (class 1259 OID 18217)
-- Name: ix_PurchaseOrders_OrderNo; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX "ix_PurchaseOrders_OrderNo" ON public."PurchaseOrders" USING btree ("OrderNo");


--
-- TOC entry 5209 (class 1259 OID 19183)
-- Name: ix_PurchaseReturnLines_ReturnId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_PurchaseReturnLines_ReturnId" ON public."PurchaseReturnLines" USING btree ("ReturnId");


--
-- TOC entry 5206 (class 1259 OID 19165)
-- Name: ix_PurchaseReturns_InvoiceId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_PurchaseReturns_InvoiceId" ON public."PurchaseReturns" USING btree ("InvoiceId");


--
-- TOC entry 5217 (class 1259 OID 19286)
-- Name: ix_RecordAttachments_RecordId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_RecordAttachments_RecordId" ON public."RecordAttachments" USING btree ("RecordId");


--
-- TOC entry 5218 (class 1259 OID 19285)
-- Name: ix_RecordAttachments_RecordType; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_RecordAttachments_RecordType" ON public."RecordAttachments" USING btree ("RecordType");


--
-- TOC entry 5199 (class 1259 OID 19131)
-- Name: ix_SupplierInvoiceLines_InvoiceId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_SupplierInvoiceLines_InvoiceId" ON public."SupplierInvoiceLines" USING btree ("InvoiceId");


--
-- TOC entry 5195 (class 1259 OID 19108)
-- Name: ix_SupplierInvoices_CounterpartyId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_SupplierInvoices_CounterpartyId" ON public."SupplierInvoices" USING btree ("SupplierId");


--
-- TOC entry 5196 (class 1259 OID 19107)
-- Name: ix_SupplierInvoices_PurchaseOrderId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_SupplierInvoices_PurchaseOrderId" ON public."SupplierInvoices" USING btree ("PurchaseOrderId");


--
-- TOC entry 5176 (class 1259 OID 18864)
-- Name: ix_TechnicalSettlementEstimateItems_ContractItemId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_TechnicalSettlementEstimateItems_ContractItemId" ON public."TechnicalSettlementEstimateItems" USING btree ("ContractItemId");


--
-- TOC entry 5177 (class 1259 OID 18865)
-- Name: ix_TechnicalSettlementEstimateItems_EstimateId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_TechnicalSettlementEstimateItems_EstimateId" ON public."TechnicalSettlementEstimateItems" USING btree ("EstimateId");


--
-- TOC entry 5171 (class 1259 OID 18844)
-- Name: ix_TechnicalSettlementEstimates_ContractId; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX "ix_TechnicalSettlementEstimates_ContractId" ON public."TechnicalSettlementEstimates" USING btree ("ContractId");


--
-- TOC entry 5244 (class 2606 OID 18127)
-- Name: AuditLog AuditLog_UserId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."AuditLog"
    ADD CONSTRAINT "AuditLog_UserId_fkey" FOREIGN KEY ("UserId") REFERENCES public."Users"("UserId");


--
-- TOC entry 5320 (class 2606 OID 18672)
-- Name: BankReconciliationLines BankReconciliationLines_ReconciliationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliationLines"
    ADD CONSTRAINT "BankReconciliationLines_ReconciliationId_fkey" FOREIGN KEY ("ReconciliationId") REFERENCES public."BankReconciliations"("ReconciliationId");


--
-- TOC entry 5284 (class 2606 OID 18392)
-- Name: BankReconciliations BankReconciliations_PreparedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliations"
    ADD CONSTRAINT "BankReconciliations_PreparedBy_fkey" FOREIGN KEY ("PreparedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5285 (class 2606 OID 18387)
-- Name: BankReconciliations BankReconciliations_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."BankReconciliations"
    ADD CONSTRAINT "BankReconciliations_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5264 (class 2606 OID 18279)
-- Name: Beneficiaries Beneficiaries_DefaultProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Beneficiaries"
    ADD CONSTRAINT "Beneficiaries_DefaultProjectId_fkey" FOREIGN KEY ("DefaultProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5265 (class 2606 OID 18274)
-- Name: Beneficiaries Beneficiaries_LinkedAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Beneficiaries"
    ADD CONSTRAINT "Beneficiaries_LinkedAccountId_fkey" FOREIGN KEY ("LinkedAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5356 (class 2606 OID 19255)
-- Name: CatalogItems CatalogItems_ExpenseAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_ExpenseAccountId_fkey" FOREIGN KEY ("ExpenseAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5357 (class 2606 OID 19260)
-- Name: CatalogItems CatalogItems_InventoryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_InventoryAccountId_fkey" FOREIGN KEY ("InventoryAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5358 (class 2606 OID 19265)
-- Name: CatalogItems CatalogItems_InventoryItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_InventoryItemId_fkey" FOREIGN KEY ("InventoryItemId") REFERENCES public."InventoryItems"("ItemId");


--
-- TOC entry 5359 (class 2606 OID 19250)
-- Name: CatalogItems CatalogItems_RevenueAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CatalogItems"
    ADD CONSTRAINT "CatalogItems_RevenueAccountId_fkey" FOREIGN KEY ("RevenueAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5236 (class 2606 OID 18068)
-- Name: ChartOfAccounts ChartOfAccounts_ClassificationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ChartOfAccounts"
    ADD CONSTRAINT "ChartOfAccounts_ClassificationId_fkey" FOREIGN KEY ("ClassificationId") REFERENCES public."AccountClassifications"("ClassificationId");


--
-- TOC entry 5237 (class 2606 OID 18063)
-- Name: ChartOfAccounts ChartOfAccounts_ParentAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ChartOfAccounts"
    ADD CONSTRAINT "ChartOfAccounts_ParentAccountId_fkey" FOREIGN KEY ("ParentAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5293 (class 2606 OID 18465)
-- Name: CheckPrintTemplates CheckPrintTemplates_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckPrintTemplates"
    ADD CONSTRAINT "CheckPrintTemplates_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5368 (class 2606 OID 19839)
-- Name: CheckSignatories CheckSignatories_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckSignatories"
    ADD CONSTRAINT "CheckSignatories_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5321 (class 2606 OID 18689)
-- Name: CheckStatusHistory CheckStatusHistory_ChangedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckStatusHistory"
    ADD CONSTRAINT "CheckStatusHistory_ChangedBy_fkey" FOREIGN KEY ("ChangedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5322 (class 2606 OID 18684)
-- Name: CheckStatusHistory CheckStatusHistory_CheckId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CheckStatusHistory"
    ADD CONSTRAINT "CheckStatusHistory_CheckId_fkey" FOREIGN KEY ("CheckId") REFERENCES public."Checks"("CheckId");


--
-- TOC entry 5286 (class 2606 OID 18413)
-- Name: Checks Checks_BeneficiaryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks"
    ADD CONSTRAINT "Checks_BeneficiaryId_fkey" FOREIGN KEY ("BeneficiaryId") REFERENCES public."Beneficiaries"("BeneficiaryId");


--
-- TOC entry 5287 (class 2606 OID 18418)
-- Name: Checks Checks_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks"
    ADD CONSTRAINT "Checks_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5288 (class 2606 OID 18408)
-- Name: Checks Checks_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Checks"
    ADD CONSTRAINT "Checks_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5304 (class 2606 OID 18588)
-- Name: ContractAccountingConfig ContractAccountingConfig_AdvanceAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_AdvanceAccountId_fkey" FOREIGN KEY ("AdvanceAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5305 (class 2606 OID 18563)
-- Name: ContractAccountingConfig ContractAccountingConfig_CompanyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_CompanyId_fkey" FOREIGN KEY ("CompanyId") REFERENCES public."Companies"("CompanyId");


--
-- TOC entry 5306 (class 2606 OID 18558)
-- Name: ContractAccountingConfig ContractAccountingConfig_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5307 (class 2606 OID 18573)
-- Name: ContractAccountingConfig ContractAccountingConfig_ControlAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_ControlAccountId_fkey" FOREIGN KEY ("ControlAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5308 (class 2606 OID 18568)
-- Name: ContractAccountingConfig ContractAccountingConfig_FiscalYearId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_FiscalYearId_fkey" FOREIGN KEY ("FiscalYearId") REFERENCES public."FiscalYears"("FiscalYearId");


--
-- TOC entry 5309 (class 2606 OID 18583)
-- Name: ContractAccountingConfig ContractAccountingConfig_RetentionAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_RetentionAccountId_fkey" FOREIGN KEY ("RetentionAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5310 (class 2606 OID 18593)
-- Name: ContractAccountingConfig ContractAccountingConfig_TaxAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_TaxAccountId_fkey" FOREIGN KEY ("TaxAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5311 (class 2606 OID 18598)
-- Name: ContractAccountingConfig ContractAccountingConfig_VatAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_VatAccountId_fkey" FOREIGN KEY ("VatAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5312 (class 2606 OID 18578)
-- Name: ContractAccountingConfig ContractAccountingConfig_WorkAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAccountingConfig"
    ADD CONSTRAINT "ContractAccountingConfig_WorkAccountId_fkey" FOREIGN KEY ("WorkAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5294 (class 2606 OID 18479)
-- Name: ContractAddendums ContractAddendums_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAddendums"
    ADD CONSTRAINT "ContractAddendums_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5295 (class 2606 OID 18484)
-- Name: ContractAddendums ContractAddendums_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAddendums"
    ADD CONSTRAINT "ContractAddendums_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5327 (class 2606 OID 18726)
-- Name: ContractAttachments ContractAttachments_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAttachments"
    ADD CONSTRAINT "ContractAttachments_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5328 (class 2606 OID 18731)
-- Name: ContractAttachments ContractAttachments_SettlementId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAttachments"
    ADD CONSTRAINT "ContractAttachments_SettlementId_fkey" FOREIGN KEY ("SettlementId") REFERENCES public."ContractSettlements"("SettlementId") ON DELETE CASCADE;


--
-- TOC entry 5329 (class 2606 OID 18736)
-- Name: ContractAttachments ContractAttachments_UploadedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractAttachments"
    ADD CONSTRAINT "ContractAttachments_UploadedBy_fkey" FOREIGN KEY ("UploadedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5317 (class 2606 OID 18657)
-- Name: ContractChangeOrders ContractChangeOrders_ApprovedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders"
    ADD CONSTRAINT "ContractChangeOrders_ApprovedBy_fkey" FOREIGN KEY ("ApprovedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5318 (class 2606 OID 18647)
-- Name: ContractChangeOrders ContractChangeOrders_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders"
    ADD CONSTRAINT "ContractChangeOrders_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5319 (class 2606 OID 18652)
-- Name: ContractChangeOrders ContractChangeOrders_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractChangeOrders"
    ADD CONSTRAINT "ContractChangeOrders_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5302 (class 2606 OID 18538)
-- Name: ContractDeductionRules ContractDeductionRules_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractDeductionRules"
    ADD CONSTRAINT "ContractDeductionRules_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5303 (class 2606 OID 18543)
-- Name: ContractDeductionRules ContractDeductionRules_GLAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractDeductionRules"
    ADD CONSTRAINT "ContractDeductionRules_GLAccountId_fkey" FOREIGN KEY ("GLAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5298 (class 2606 OID 19322)
-- Name: ContractItems ContractItems_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "ContractItems_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5299 (class 2606 OID 18522)
-- Name: ContractItems ContractItems_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "ContractItems_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5300 (class 2606 OID 19327)
-- Name: ContractItems ContractItems_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "ContractItems_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5361 (class 2606 OID 19306)
-- Name: ContractRequestItems ContractRequestItems_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems"
    ADD CONSTRAINT "ContractRequestItems_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5362 (class 2606 OID 19301)
-- Name: ContractRequestItems ContractRequestItems_CatalogItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems"
    ADD CONSTRAINT "ContractRequestItems_CatalogItemId_fkey" FOREIGN KEY ("CatalogItemId") REFERENCES public."CatalogItems"("CatalogItemId");


--
-- TOC entry 5363 (class 2606 OID 19311)
-- Name: ContractRequestItems ContractRequestItems_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems"
    ADD CONSTRAINT "ContractRequestItems_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5364 (class 2606 OID 19296)
-- Name: ContractRequestItems ContractRequestItems_RequestId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequestItems"
    ADD CONSTRAINT "ContractRequestItems_RequestId_fkey" FOREIGN KEY ("RequestId") REFERENCES public."ContractRequests"("RequestId") ON DELETE CASCADE;


--
-- TOC entry 5246 (class 2606 OID 19184)
-- Name: ContractRequests ContractRequests_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests"
    ADD CONSTRAINT "ContractRequests_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5247 (class 2606 OID 18162)
-- Name: ContractRequests ContractRequests_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests"
    ADD CONSTRAINT "ContractRequests_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5248 (class 2606 OID 18157)
-- Name: ContractRequests ContractRequests_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests"
    ADD CONSTRAINT "ContractRequests_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5249 (class 2606 OID 18167)
-- Name: ContractRequests ContractRequests_ReviewedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractRequests"
    ADD CONSTRAINT "ContractRequests_ReviewedBy_fkey" FOREIGN KEY ("ReviewedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5323 (class 2606 OID 19332)
-- Name: ContractSettlementItems ContractSettlementItems_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "ContractSettlementItems_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5324 (class 2606 OID 18709)
-- Name: ContractSettlementItems ContractSettlementItems_ContractItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "ContractSettlementItems_ContractItemId_fkey" FOREIGN KEY ("ContractItemId") REFERENCES public."ContractItems"("ItemId");


--
-- TOC entry 5325 (class 2606 OID 19337)
-- Name: ContractSettlementItems ContractSettlementItems_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "ContractSettlementItems_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5326 (class 2606 OID 18704)
-- Name: ContractSettlementItems ContractSettlementItems_SettlementId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlementItems"
    ADD CONSTRAINT "ContractSettlementItems_SettlementId_fkey" FOREIGN KEY ("SettlementId") REFERENCES public."ContractSettlements"("SettlementId") ON DELETE CASCADE;


--
-- TOC entry 5313 (class 2606 OID 18620)
-- Name: ContractSettlements ContractSettlements_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5314 (class 2606 OID 19196)
-- Name: ContractSettlements ContractSettlements_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5315 (class 2606 OID 18630)
-- Name: ContractSettlements ContractSettlements_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5316 (class 2606 OID 18625)
-- Name: ContractSettlements ContractSettlements_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractSettlements"
    ADD CONSTRAINT "ContractSettlements_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5266 (class 2606 OID 19190)
-- Name: Contracts Contracts_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5267 (class 2606 OID 18305)
-- Name: Contracts Contracts_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5268 (class 2606 OID 18300)
-- Name: Contracts Contracts_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5269 (class 2606 OID 18295)
-- Name: Contracts Contracts_RequestId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Contracts"
    ADD CONSTRAINT "Contracts_RequestId_fkey" FOREIGN KEY ("RequestId") REFERENCES public."ContractRequests"("RequestId");


--
-- TOC entry 5340 (class 2606 OID 19058)
-- Name: Counterparties Counterparties_LinkedAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Counterparties"
    ADD CONSTRAINT "Counterparties_LinkedAccountId_fkey" FOREIGN KEY ("LinkedAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5339 (class 2606 OID 19220)
-- Name: CounterpartyAliases CounterpartyAliases_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."CounterpartyAliases"
    ADD CONSTRAINT "CounterpartyAliases_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5301 (class 2606 OID 19581)
-- Name: ContractItems FK_ContractItems_ItemCatalog_CatalogItemId; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ContractItems"
    ADD CONSTRAINT "FK_ContractItems_ItemCatalog_CatalogItemId" FOREIGN KEY ("CatalogItemId") REFERENCES public."ItemCatalog"("CatalogItemId");


--
-- TOC entry 5289 (class 2606 OID 18451)
-- Name: FinancialChecks FinancialChecks_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5290 (class 2606 OID 18446)
-- Name: FinancialChecks FinancialChecks_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5291 (class 2606 OID 18436)
-- Name: FinancialChecks FinancialChecks_PartyAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_PartyAccountId_fkey" FOREIGN KEY ("PartyAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5292 (class 2606 OID 18441)
-- Name: FinancialChecks FinancialChecks_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialChecks"
    ADD CONSTRAINT "FinancialChecks_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5235 (class 2606 OID 18049)
-- Name: FinancialStatementLines FinancialStatementLines_ClassificationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FinancialStatementLines"
    ADD CONSTRAINT "FinancialStatementLines_ClassificationId_fkey" FOREIGN KEY ("ClassificationId") REFERENCES public."AccountClassifications"("ClassificationId");


--
-- TOC entry 5234 (class 2606 OID 18037)
-- Name: FiscalYears FiscalYears_CompanyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."FiscalYears"
    ADD CONSTRAINT "FiscalYears_CompanyId_fkey" FOREIGN KEY ("CompanyId") REFERENCES public."Companies"("CompanyId");


--
-- TOC entry 5250 (class 2606 OID 19352)
-- Name: InventoryMovements InventoryMovements_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5251 (class 2606 OID 19362)
-- Name: InventoryMovements InventoryMovements_CatalogItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_CatalogItemId_fkey" FOREIGN KEY ("CatalogItemId") REFERENCES public."CatalogItems"("CatalogItemId");


--
-- TOC entry 5252 (class 2606 OID 18192)
-- Name: InventoryMovements InventoryMovements_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5253 (class 2606 OID 18182)
-- Name: InventoryMovements InventoryMovements_ItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_ItemId_fkey" FOREIGN KEY ("ItemId") REFERENCES public."InventoryItems"("ItemId");


--
-- TOC entry 5254 (class 2606 OID 19357)
-- Name: InventoryMovements InventoryMovements_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5255 (class 2606 OID 18187)
-- Name: InventoryMovements InventoryMovements_WarehouseId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."InventoryMovements"
    ADD CONSTRAINT "InventoryMovements_WarehouseId_fkey" FOREIGN KEY ("WarehouseId") REFERENCES public."InventoryWarehouses"("WarehouseId");


--
-- TOC entry 5365 (class 2606 OID 19462)
-- Name: ItemCatalog ItemCatalog_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ItemCatalog"
    ADD CONSTRAINT "ItemCatalog_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5366 (class 2606 OID 19467)
-- Name: ItemCatalog ItemCatalog_InventoryItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ItemCatalog"
    ADD CONSTRAINT "ItemCatalog_InventoryItemId_fkey" FOREIGN KEY ("InventoryItemId") REFERENCES public."InventoryItems"("ItemId");


--
-- TOC entry 5259 (class 2606 OID 18229)
-- Name: JournalEntries JournalEntries_CompanyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_CompanyId_fkey" FOREIGN KEY ("CompanyId") REFERENCES public."Companies"("CompanyId");


--
-- TOC entry 5260 (class 2606 OID 18239)
-- Name: JournalEntries JournalEntries_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5261 (class 2606 OID 18234)
-- Name: JournalEntries JournalEntries_FiscalYearId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_FiscalYearId_fkey" FOREIGN KEY ("FiscalYearId") REFERENCES public."FiscalYears"("FiscalYearId");


--
-- TOC entry 5262 (class 2606 OID 18244)
-- Name: JournalEntries JournalEntries_PostedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntries"
    ADD CONSTRAINT "JournalEntries_PostedBy_fkey" FOREIGN KEY ("PostedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5275 (class 2606 OID 18343)
-- Name: JournalEntryDetails JournalEntryDetails_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntryDetails"
    ADD CONSTRAINT "JournalEntryDetails_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5276 (class 2606 OID 18338)
-- Name: JournalEntryDetails JournalEntryDetails_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntryDetails"
    ADD CONSTRAINT "JournalEntryDetails_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5277 (class 2606 OID 18348)
-- Name: JournalEntryDetails JournalEntryDetails_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."JournalEntryDetails"
    ADD CONSTRAINT "JournalEntryDetails_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5296 (class 2606 OID 18499)
-- Name: ProgressBillings ProgressBillings_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ProgressBillings"
    ADD CONSTRAINT "ProgressBillings_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5297 (class 2606 OID 18504)
-- Name: ProgressBillings ProgressBillings_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."ProgressBillings"
    ADD CONSTRAINT "ProgressBillings_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5270 (class 2606 OID 19372)
-- Name: PurchaseOrderLines PurchaseOrderLines_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5271 (class 2606 OID 19367)
-- Name: PurchaseOrderLines PurchaseOrderLines_CatalogItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_CatalogItemId_fkey" FOREIGN KEY ("CatalogItemId") REFERENCES public."CatalogItems"("CatalogItemId");


--
-- TOC entry 5272 (class 2606 OID 18323)
-- Name: PurchaseOrderLines PurchaseOrderLines_ItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_ItemId_fkey" FOREIGN KEY ("ItemId") REFERENCES public."InventoryItems"("ItemId");


--
-- TOC entry 5273 (class 2606 OID 19377)
-- Name: PurchaseOrderLines PurchaseOrderLines_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5274 (class 2606 OID 18318)
-- Name: PurchaseOrderLines PurchaseOrderLines_PurchaseOrderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrderLines"
    ADD CONSTRAINT "PurchaseOrderLines_PurchaseOrderId_fkey" FOREIGN KEY ("PurchaseOrderId") REFERENCES public."PurchaseOrders"("PurchaseOrderId") ON DELETE CASCADE;


--
-- TOC entry 5256 (class 2606 OID 19214)
-- Name: PurchaseOrders PurchaseOrders_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrders"
    ADD CONSTRAINT "PurchaseOrders_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5257 (class 2606 OID 18212)
-- Name: PurchaseOrders PurchaseOrders_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrders"
    ADD CONSTRAINT "PurchaseOrders_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5258 (class 2606 OID 18207)
-- Name: PurchaseOrders PurchaseOrders_WarehouseId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseOrders"
    ADD CONSTRAINT "PurchaseOrders_WarehouseId_fkey" FOREIGN KEY ("WarehouseId") REFERENCES public."InventoryWarehouses"("WarehouseId");


--
-- TOC entry 5354 (class 2606 OID 19178)
-- Name: PurchaseReturnLines PurchaseReturnLines_InvoiceLineId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturnLines"
    ADD CONSTRAINT "PurchaseReturnLines_InvoiceLineId_fkey" FOREIGN KEY ("InvoiceLineId") REFERENCES public."SupplierInvoiceLines"("LineId");


--
-- TOC entry 5355 (class 2606 OID 19173)
-- Name: PurchaseReturnLines PurchaseReturnLines_ReturnId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturnLines"
    ADD CONSTRAINT "PurchaseReturnLines_ReturnId_fkey" FOREIGN KEY ("ReturnId") REFERENCES public."PurchaseReturns"("ReturnId") ON DELETE CASCADE;


--
-- TOC entry 5350 (class 2606 OID 19160)
-- Name: PurchaseReturns PurchaseReturns_ApprovedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_ApprovedBy_fkey" FOREIGN KEY ("ApprovedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5351 (class 2606 OID 19155)
-- Name: PurchaseReturns PurchaseReturns_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5352 (class 2606 OID 19145)
-- Name: PurchaseReturns PurchaseReturns_InvoiceId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_InvoiceId_fkey" FOREIGN KEY ("InvoiceId") REFERENCES public."SupplierInvoices"("InvoiceId");


--
-- TOC entry 5353 (class 2606 OID 19150)
-- Name: PurchaseReturns PurchaseReturns_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."PurchaseReturns"
    ADD CONSTRAINT "PurchaseReturns_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5360 (class 2606 OID 19280)
-- Name: RecordAttachments RecordAttachments_UploadedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RecordAttachments"
    ADD CONSTRAINT "RecordAttachments_UploadedBy_fkey" FOREIGN KEY ("UploadedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5238 (class 2606 OID 18083)
-- Name: RolePermissions RolePermissions_PermissionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RolePermissions"
    ADD CONSTRAINT "RolePermissions_PermissionId_fkey" FOREIGN KEY ("PermissionId") REFERENCES public."Permissions"("PermissionId");


--
-- TOC entry 5239 (class 2606 OID 18078)
-- Name: RolePermissions RolePermissions_RoleId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."RolePermissions"
    ADD CONSTRAINT "RolePermissions_RoleId_fkey" FOREIGN KEY ("RoleId") REFERENCES public."Roles"("RoleId");


--
-- TOC entry 5245 (class 2606 OID 18143)
-- Name: Screens Screens_SectionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."Screens"
    ADD CONSTRAINT "Screens_SectionId_fkey" FOREIGN KEY ("SectionId") REFERENCES public."Sections"("SectionId");


--
-- TOC entry 5347 (class 2606 OID 19126)
-- Name: SupplierInvoiceLines SupplierInvoiceLines_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoiceLines"
    ADD CONSTRAINT "SupplierInvoiceLines_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5348 (class 2606 OID 19116)
-- Name: SupplierInvoiceLines SupplierInvoiceLines_InvoiceId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoiceLines"
    ADD CONSTRAINT "SupplierInvoiceLines_InvoiceId_fkey" FOREIGN KEY ("InvoiceId") REFERENCES public."SupplierInvoices"("InvoiceId") ON DELETE CASCADE;


--
-- TOC entry 5349 (class 2606 OID 19121)
-- Name: SupplierInvoiceLines SupplierInvoiceLines_PurchaseOrderLineId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoiceLines"
    ADD CONSTRAINT "SupplierInvoiceLines_PurchaseOrderLineId_fkey" FOREIGN KEY ("PurchaseOrderLineId") REFERENCES public."PurchaseOrderLines"("LineId");


--
-- TOC entry 5341 (class 2606 OID 19097)
-- Name: SupplierInvoices SupplierInvoices_ApprovedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_ApprovedBy_fkey" FOREIGN KEY ("ApprovedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5342 (class 2606 OID 19077)
-- Name: SupplierInvoices SupplierInvoices_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_CounterpartyId_fkey" FOREIGN KEY ("SupplierId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5343 (class 2606 OID 19092)
-- Name: SupplierInvoices SupplierInvoices_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5344 (class 2606 OID 19102)
-- Name: SupplierInvoices SupplierInvoices_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5345 (class 2606 OID 19082)
-- Name: SupplierInvoices SupplierInvoices_PurchaseOrderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_PurchaseOrderId_fkey" FOREIGN KEY ("PurchaseOrderId") REFERENCES public."PurchaseOrders"("PurchaseOrderId");


--
-- TOC entry 5346 (class 2606 OID 19087)
-- Name: SupplierInvoices SupplierInvoices_TaxAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."SupplierInvoices"
    ADD CONSTRAINT "SupplierInvoices_TaxAccountId_fkey" FOREIGN KEY ("TaxAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5335 (class 2606 OID 19342)
-- Name: TechnicalSettlementEstimateItems TechnicalSettlementEstimateItems_AccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "TechnicalSettlementEstimateItems_AccountId_fkey" FOREIGN KEY ("AccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5336 (class 2606 OID 18859)
-- Name: TechnicalSettlementEstimateItems TechnicalSettlementEstimateItems_ContractItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "TechnicalSettlementEstimateItems_ContractItemId_fkey" FOREIGN KEY ("ContractItemId") REFERENCES public."ContractItems"("ItemId");


--
-- TOC entry 5337 (class 2606 OID 18854)
-- Name: TechnicalSettlementEstimateItems TechnicalSettlementEstimateItems_EstimateId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "TechnicalSettlementEstimateItems_EstimateId_fkey" FOREIGN KEY ("EstimateId") REFERENCES public."TechnicalSettlementEstimates"("EstimateId") ON DELETE CASCADE;


--
-- TOC entry 5338 (class 2606 OID 19347)
-- Name: TechnicalSettlementEstimateItems TechnicalSettlementEstimateItems_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimateItems"
    ADD CONSTRAINT "TechnicalSettlementEstimateItems_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5330 (class 2606 OID 18824)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_ContractId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_ContractId_fkey" FOREIGN KEY ("ContractId") REFERENCES public."Contracts"("ContractId") ON DELETE CASCADE;


--
-- TOC entry 5331 (class 2606 OID 19202)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5332 (class 2606 OID 18834)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_CreatedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_CreatedBy_fkey" FOREIGN KEY ("CreatedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5333 (class 2606 OID 18829)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_FinancialSettlementId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_FinancialSettlementId_fkey" FOREIGN KEY ("FinancialSettlementId") REFERENCES public."ContractSettlements"("SettlementId");


--
-- TOC entry 5334 (class 2606 OID 18839)
-- Name: TechnicalSettlementEstimates TechnicalSettlementEstimates_ReviewedBy_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TechnicalSettlementEstimates"
    ADD CONSTRAINT "TechnicalSettlementEstimates_ReviewedBy_fkey" FOREIGN KEY ("ReviewedBy") REFERENCES public."Users"("UserId");


--
-- TOC entry 5263 (class 2606 OID 18260)
-- Name: TreasuryAccounts TreasuryAccounts_GLAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryAccounts"
    ADD CONSTRAINT "TreasuryAccounts_GLAccountId_fkey" FOREIGN KEY ("GLAccountId") REFERENCES public."ChartOfAccounts"("AccountId");


--
-- TOC entry 5278 (class 2606 OID 19208)
-- Name: TreasuryTransactions TreasuryTransactions_CounterpartyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_CounterpartyId_fkey" FOREIGN KEY ("CounterpartyId") REFERENCES public."Counterparties"("CounterpartyId");


--
-- TOC entry 5279 (class 2606 OID 18372)
-- Name: TreasuryTransactions TreasuryTransactions_JournalEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_JournalEntryId_fkey" FOREIGN KEY ("JournalEntryId") REFERENCES public."JournalEntries"("JournalEntryId");


--
-- TOC entry 5280 (class 2606 OID 18367)
-- Name: TreasuryTransactions TreasuryTransactions_ProjectId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_ProjectId_fkey" FOREIGN KEY ("ProjectId") REFERENCES public."Projects"("ProjectId");


--
-- TOC entry 5281 (class 2606 OID 19032)
-- Name: TreasuryTransactions TreasuryTransactions_SettlementId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_SettlementId_fkey" FOREIGN KEY ("SettlementId") REFERENCES public."ContractSettlements"("SettlementId");


--
-- TOC entry 5282 (class 2606 OID 19225)
-- Name: TreasuryTransactions TreasuryTransactions_SupplierInvoiceId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_SupplierInvoiceId_fkey" FOREIGN KEY ("SupplierInvoiceId") REFERENCES public."SupplierInvoices"("InvoiceId");


--
-- TOC entry 5283 (class 2606 OID 18362)
-- Name: TreasuryTransactions TreasuryTransactions_TreasuryAccountId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."TreasuryTransactions"
    ADD CONSTRAINT "TreasuryTransactions_TreasuryAccountId_fkey" FOREIGN KEY ("TreasuryAccountId") REFERENCES public."TreasuryAccounts"("TreasuryAccountId");


--
-- TOC entry 5367 (class 2606 OID 19658)
-- Name: UserAvatars UserAvatars_UserId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserAvatars"
    ADD CONSTRAINT "UserAvatars_UserId_fkey" FOREIGN KEY ("UserId") REFERENCES public."Users"("UserId") ON DELETE CASCADE;


--
-- TOC entry 5242 (class 2606 OID 18113)
-- Name: UserPermissions UserPermissions_PermissionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserPermissions"
    ADD CONSTRAINT "UserPermissions_PermissionId_fkey" FOREIGN KEY ("PermissionId") REFERENCES public."Permissions"("PermissionId");


--
-- TOC entry 5243 (class 2606 OID 18108)
-- Name: UserPermissions UserPermissions_UserId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserPermissions"
    ADD CONSTRAINT "UserPermissions_UserId_fkey" FOREIGN KEY ("UserId") REFERENCES public."Users"("UserId");


--
-- TOC entry 5240 (class 2606 OID 18098)
-- Name: UserRoles UserRoles_RoleId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserRoles"
    ADD CONSTRAINT "UserRoles_RoleId_fkey" FOREIGN KEY ("RoleId") REFERENCES public."Roles"("RoleId");


--
-- TOC entry 5241 (class 2606 OID 18093)
-- Name: UserRoles UserRoles_UserId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."UserRoles"
    ADD CONSTRAINT "UserRoles_UserId_fkey" FOREIGN KEY ("UserId") REFERENCES public."Users"("UserId");


-- Completed on 2026-11-05 15:18:36

--
-- PostgreSQL database dump complete
--

\unrestrict 1bEmt8DVo9JzELtefTKtuSZAAZjqNr1tQpNRWYqrM6e8E0UW23uVURpeCIQr6p5

