import { api, auth, login, userAvatarUrl } from "./api.js";
import { esc, toast, errText } from "./ui.js";
import { mountDataExchange } from "./data_exchange.js";
import { getLanguage, isEnglish, translate, applyLanguage } from "./i18n.js";

const root = document.getElementById("app");
let LANG = getLanguage();
const isEN = isEnglish;
const tr = translate;
// سجل الشاشات: route → وحدة الواجهة. أي شاشة جديدة تتضاف هنا.
const L = f => () => import(f);
const SCREENS = {
  "/checks/register": L("./pages/financial_checks.js?v=20261105-financial-checks-i18n-2"),
  "/financial-checks": L("./pages/financial_checks.js?v=20261105-financial-checks-i18n-2"),
  "/checks-register": L("./pages/financial_checks.js?v=20261105-financial-checks-i18n-2"),
  "/admin/users": L("./pages/admin.js?v=20261109-create-user-permissions-1"),
  "/admin/backup": L("./pages/backup.js?v=20261105-backup-i18n-2"),
  "/admin/reset": L("./pages/reset.js?v=20261107-safe-reset-1"),
  "/admin/company": L("./pages/company.js?v=20261105-company-i18n-1"),
  "/accounts": L("./pages/accounts.js?v=20261105-accounts-i18n-3"),
  "/projects": L("./pages/projects.js?v=20261105-projects-i18n-1"),
  "/journal": L("./pages/journal.js?v=20261105-journal-i18n-3"),
  "/trial-balance": L("./pages/trial_balance.js?v=20261105-trial-balance-data-i18n-1"),
  "/reports/balance-sheet": L("./pages/reports.js?v=20261105-reports-i18n-1"),
  "/reports/income-statement": L("./pages/reports.js?v=20261105-reports-i18n-1"),
  "/reports": L("./pages/reports_analytics.js?v=20261105-reports-analytics-i18n-3"),
  "/reports/financial-control": L("./pages/financial_control.js?v=20261105-financial-control-1"),
  "/contracts": L("./pages/contracts.js?v=20261109-flexible-vat-1"),
  "/contract-requests": L("./pages/contract_requests.js?v=20261105-auto-document-numbers-1"),
  "/settlements": L("./pages/settlements.js?v=20261109-flexible-vat-1"),
  "/settlements/technical": L("./pages/settlements.js?v=20261109-flexible-vat-1"),
  "/settlements/financial": L("./pages/settlements.js?v=20261109-flexible-vat-1"),
  "/settlements/manager-approval": L("./pages/settlements.js?v=20261109-flexible-vat-1"),
  "/inventory": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/receipts": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/items": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/warehouses": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/balances": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/movements": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/transfers": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/site-issues": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/stocktakes": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/inventory/returns": L("./pages/inventory.js?v=20261105-inventory-screens-2"),
  "/purchases": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/requisitions": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/quotations": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/orders": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/receipts": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/invoices": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/payments": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/purchases/reports": L("./pages/purchases.js?v=20261105-purchasing-nav-fix-2"),
  "/counterparties": L("./pages/counterparties.js?v=20261105-counterparty-names-i18n-2"),
  // Preserve the older type-specific links while using the unified party registry.
  "/customers": L("./pages/counterparties.js?v=20261105-counterparties-i18n-1"),
  "/contractors": L("./pages/counterparties.js?v=20261105-counterparties-i18n-1"),
  "/suppliers": L("./pages/counterparties.js?v=20261105-counterparties-i18n-1"),
  "/audit-logs": L("./pages/audit_logs.js?v=20261105-audit-i18n-2"),
  "/treasury/analysis": L("./pages/cash_analysis.js?v=20261105-cash-analysis-i18n-2"),
  "/treasury/reconciliation": L("./pages/reconciliation.js?v=20261105-reconciliation-i18n-2"),
  ...Object.fromEntries(["cib-egp", "cash-usd", "cash-egp", "cib-usd"].map(k => ["/treasury/" + k, L("./pages/treasury.js?v=20261109-ledger-reconciliation-6")])),
  ...Object.fromEntries(["cib", "cib-usd"].map(k => ["/checks/" + k, L("./pages/checks.js?v=20261109-fixed-cib-cheques-1")])),
};

// ---------------------------------------------------------------- أيقونات (SVG خطي بسيط)
const ICON = {
  home: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-5h4v5"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r="1"/><circle cx="3.5" cy="12" r="1"/><circle cx="3.5" cy="18" r="1"/>',
  book: '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
  scale: '<path d="M12 4v16M6 20h12M5 8h14"/><path d="M5 8l-3 6a3 3 0 0 0 6 0zM19 8l-3 6a3 3 0 0 0 6 0z"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
  bank: '<path d="M3 10 12 4l9 6M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 20h18"/>',
  card: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/>',
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M16 5.2a3 3 0 0 1 0 5.6M17.5 14.3c2.2.6 3.5 2.6 3.5 5.7"/>',
  cloud: '<path d="M7 18a4.5 4.5 0 0 1-.5-9A6 6 0 0 1 18 9.5 4 4 0 0 1 17.5 18"/><path d="M12 11v8M9 14l3-3 3 3"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  logout: '<path d="M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h5"/><path d="M15 8l4 4-4 4M19 12H9"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/>',
  moon: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
  dollar: '<circle cx="12" cy="12" r="9"/><path d="M14.5 9.2c-.4-1-1.4-1.6-2.6-1.6-1.5 0-2.6.8-2.6 2s1 1.7 2.7 2.1c1.7.4 2.7 1 2.7 2.2s-1.1 2-2.7 2c-1.3 0-2.3-.6-2.7-1.6M12 6v1.6M12 16.4V18"/>',
  swap: '<path d="M4 8h14l-3-3M20 16H6l3 3"/>',
  receipt: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
  target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".6"/>',
  pie: '<path d="M12 3v9h9"/><path d="M20.5 15A9 9 0 1 1 9 3.5"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/>',
  chevron: '<path d="M6 9l6 6 6-6"/>',
  file: '<path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
  refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
  printer: '<path d="M7 9V4h10v5M7 17H5a1 1 0 0 1-1-1v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5a1 1 0 0 1-1 1h-2"/><path d="M7 14h10v6H7z"/>',
  warehouse: '<path d="M3 10 12 4l9 6v10H3z"/><path d="M7 20v-6h4v6M15 13h2M15 16h2"/>',
  cart: '<circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/><path d="M2 3h2l2.5 12.5a2 2 0 0 0 2 1.5h9a2 2 0 0 0 2-1.6L21 8H5"/>',
  dot: '<circle cx="12" cy="12" r="2"/>',
};
const ico = (n, cls = "") => `<svg class="ico ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n] || ICON.dot}</svg>`;

// ---------------------------------------------------------------- حالة الجلسة (بتتحمّل مرة بعد الدخول)
let NAV = null, IS_ADMIN = false, SUMMARY = null;
const resetSession = () => { NAV = null; IS_ADMIN = false; SUMMARY = null; };
async function ensureNav() {
  if (NAV) return;
  NAV = await api("/dashboard");
  try { IS_ADMIN = !!(await api("/admin/status")).is_admin; } catch { IS_ADMIN = false; }
  try { SUMMARY = await api("/dashboard/summary"); } catch { SUMMARY = null; }
}

// تنظيم القائمة حسب دورة العمل، مع الإبقاء على الشاشات والصلاحيات القادمة من الخادم.
const SEC_ORDER = ["ACCOUNTING", "REPORTS", "TREASURY", "CHECKS"];
const SCR_ORDER = ["ChartOfAccounts", "JournalBook", "TrialBalance", "CostCenters"];
const SCR_ICON = { ChartOfAccounts: "list", JournalBook: "book", TrialBalance: "scale", CostCenters: "target", BalanceSheet: "file", IncomeStatement: "chart", AnalyticsReports: "chart", AuditLogs: "receipt", CashAnalysis: "pie", BankReconciliation: "check" };
const tOf = x => isEN() ? (x.title_en || x.title_ar) : (x.title_ar || x.title_en);
const rank = (arr, v) => { const i = arr.indexOf(v); return i < 0 ? 99 : i; };
const isHrSection = s => /^(hr|human[_ -]?resources)$/i.test(String(s.code || "").trim())
  || /موارد\s*بشرية|human\s*resources/i.test(`${s.name_ar || ""} ${s.name_en || ""}`);
const sectionsOrdered = () => (NAV?.sections || []).filter(s => !isHrSection(s)).slice().sort((a, b) => rank(SEC_ORDER, a.code) - rank(SEC_ORDER, b.code));
const screensOf = s => s.code === "ACCOUNTING" ? s.screens.slice().sort((a, b) => rank(SCR_ORDER, a.code) - rank(SCR_ORDER, b.code)) : s.screens;
const ADMIN_ITEMS = [
  { route: "/admin/company", title: "بيانات الشركة", title_en: "Company Profile", icon: "file" },
  { route: "/admin/users", title: "المستخدمون والصلاحيات", title_en: "Users & Permissions", icon: "users" },
  { route: "/admin/backup", title: "النسخ الاحتياطي", title_en: "Backup & Restore", icon: "cloud" },
  { route: "/admin/reset", title: "إعادة ضبط البيانات", title_en: "Reset System Data", icon: "refresh" },
];
const NAV_GROUPS = [
  { ar: "المشروعات والعقود", en: "Projects & Contracts", icon: "file", routes: ["/projects", "/contract-requests", "/contracts"] },
  { ar: "المستخلصات", en: "Settlements", icon: "receipt", routes: ["/settlements/technical", "/settlements/financial"] },
  { ar: "المشتريات والمخازن", en: "Purchasing & Inventory", icon: "receipt", routes: ["/purchases", "/inventory"] },
  { ar: "الإدارة المالية", en: "Financial Operations", icon: "bank", routes: ["/accounts", "/treasury/analysis", "/treasury/reconciliation", "/checks/register", "/financial-checks", "/checks-register"] },
  { ar: "الحسابات العامة", en: "General Accounting", icon: "book", sectionCodes: ["ACCOUNTING"] },
  { ar: "التقارير والرقابة", en: "Reports & Control", icon: "chart", sectionCodes: ["REPORTS"], routes: ["/reports", "/reports/financial-control"] },
  { ar: "الأطراف والبيانات الأساسية", en: "Parties & Master Data", icon: "users", routes: ["/counterparties", "/customers", "/contractors", "/suppliers"] },
  { ar: "الخزينة والشيكات", en: "Treasury & Cheques", icon: "card", sectionCodes: ["TREASURY", "CHECKS"] },
];
function navItems() {          // كل الوجهات (للبحث العام)
  const out = [{ route: "/", title: tr("الرئيسية", "Home"), sub: "Home" }];
  const dashboardScreens = (NAV?.sections || []).flatMap(section => section.screens || []);
  if (dashboardScreens.some(x => String(x.route || "").startsWith("/inventory")) || auth.can("PurchaseCycle", "View") || dashboardScreens.some(x => String(x.route || "").startsWith("/purchases")))
    out.push({ route: "/dashboard", title: tr("لوحة التحكم", "Dashboard"), sub: "Operational Dashboard" });
  for (const s of sectionsOrdered()) for (const x of screensOf(s)) out.push({ route: x.route, title: tOf(x), sub: x.title_en });
  if (auth.can("ContractSettlements", "View")) out.push(
    { route: "/settlements/technical", title: tr("المستخلصات الفنية", "Technical Settlements"), sub: tr("مراجعة هندسية", "Engineering review") },
    { route: "/settlements/financial", title: tr("المستخلصات المالية", "Financial Settlements"), sub: tr("مراجعة مالية وترحيل", "Finance review & posting") }
  );
  if (auth.can("AnalyticsReports", "View")) out.push({ route: "/reports/financial-control", title: tr("لوحة الرقابة المالية", "Financial Control"), sub: "Financial Control" });
  if (auth.can("PurchaseCycle", "View")) out.push(
    {route:"/purchases",title:tr("دورة المشتريات","Purchasing Cycle"),sub:"Purchasing"},
    {route:"/purchases/requisitions",title:tr("طلبات الشراء","Purchase Requisitions"),sub:"Purchasing"},
    {route:"/purchases/quotations",title:tr("عروض أسعار الموردين","Supplier Quotations"),sub:"Purchasing"},
    {route:"/purchases/orders",title:tr("أوامر الشراء","Purchase Orders"),sub:"Purchasing"},
    {route:"/purchases/receipts",title:tr("استلام التوريدات","Goods Receipts"),sub:"Purchasing"},
    {route:"/purchases/invoices",title:tr("فواتير الموردين","Supplier Invoices"),sub:"Purchasing"},
    {route:"/purchases/payments",title:tr("سداد الموردين","Supplier Payments"),sub:"Purchasing"},
    {route:"/purchases/reports",title:tr("تقارير الموردين","Supplier Reports"),sub:"Purchasing"}
  );
  if (IS_ADMIN) for (const a of ADMIN_ITEMS) out.push({ route: a.route, title: isEN() ? a.title_en : a.title, sub: "Admin" });
  return out;
}
function titleOf(path) {
  if (path === "/") return tr("الرئيسية", "Home");
  if (path === "/dashboard") return tr("لوحة التحكم", "Dashboard");
  if (path === "/customers") return tr("العملاء", "Customers");
  if (path === "/contractors") return tr("المقاولون", "Contractors");
  if (path === "/suppliers") return tr("الموردون", "Suppliers");
  if (["/checks/register", "/financial-checks", "/checks-register"].includes(path)) return tr("إدارة الشيكات المالية", "Financial Cheque Management");
  if (path === "/admin/users") return "";            // الصفحة نفسها فيها عنوانها
  if (path === "/admin/backup") return tr("النسخ الاحتياطي", "Backup & Restore");
  if (path === "/admin/company") return tr("بيانات الشركة", "Company Profile");
  if (path === "/audit-logs") return tr("سجل المراجعة والنشاطات", "Audit Log");
  if (path === "/reports") return tr("مركز التقارير", "Reports Center");
  if (path === "/reports/financial-control") return tr("لوحة الرقابة المالية", "Financial Control");
  if (path === "/contracts") return tr("العقود والمكتب الفني", "Contracts & Technical Office");
  if (path === "/contract-requests") return tr("طلبات التعاقد", "Contract Requests");
  if (["/settlements", "/settlements/technical"].includes(path)) return tr("المستخلصات الفنية", "Technical Settlements");
  if (path === "/settlements/financial") return tr("المستخلصات المالية", "Financial Settlements");
  if (path === "/settlements/manager-approval") return tr("اعتماد المستخلصات — المدير", "Settlement Manager Approval");
  if (path === "/inventory") return tr("إدارة المخزون", "Inventory Management");
  if (path === "/inventory/receipts") return tr("استلام التوريدات", "Goods Receipts");
  if (path === "/inventory/items") return tr("الأصناف", "Items");
  if (path === "/inventory/warehouses") return tr("المخازن", "Warehouses");
  if (path === "/inventory/balances") return tr("أرصدة المخزون", "Stock Balances");
  if (path === "/inventory/movements") return tr("حركة المخزون", "Stock Movements");
  if (path === "/inventory/transfers") return tr("التحويلات بين المخازن", "Warehouse Transfers");
  if (path === "/inventory/site-issues") return tr("طلبات صرف المواقع", "Site Issue Requests");
  if (path === "/inventory/stocktakes") return tr("الجرد والتسويات", "Stocktakes & Adjustments");
  if (path === "/inventory/returns") return tr("المرتجعات", "Inventory Returns");
  if (path === "/purchases") return tr("دورة المشتريات", "Purchasing Cycle");
  if (path === "/purchases/requisitions") return tr("طلبات الشراء", "Purchase Requisitions");
  if (path === "/purchases/quotations") return tr("عروض أسعار الموردين", "Supplier Quotations");
  if (path === "/purchases/orders") return tr("أوامر الشراء", "Purchase Orders");
  if (path === "/purchases/receipts") return tr("استلام التوريدات", "Goods Receipts");
  if (path === "/purchases/invoices") return tr("فواتير الموردين", "Supplier Invoices");
  if (path === "/purchases/payments") return tr("سداد الموردين", "Supplier Payments");
  if (path === "/purchases/reports") return tr("تقارير الموردين", "Supplier Reports");
  for (const s of sectionsOrdered()) for (const x of s.screens) if (x.route === path) return tOf(x);
  return "";
}

function navHtml(path) {
  const link = (it, sub = true) => `<a class="nav-i${it.route === path ? " on" : ""}${SCREENS[it.route] || it.route === "/" ? "" : " soon"}" href="#${esc(it.route)}">${sub ? "" : ico(it.icon)}<span>${esc(it.title)}</span></a>`;
  const all = sectionsOrdered().flatMap(s => screensOf(s).map(x => ({ ...x, _section: s.code }))).filter(x => x.route !== "/settlements");
  const used = new Set();
  let h = link({ route: "/", title: tr("الرئيسية", "Home"), icon: "home" }, false);
  const dashboardScreens = (NAV?.sections || []).flatMap(section => section.screens || []);
  if (dashboardScreens.some(x => String(x.route || "").startsWith("/inventory")) || auth.can("PurchaseCycle", "View") || dashboardScreens.some(x => String(x.route || "").startsWith("/purchases")))
    h += link({ route: "/dashboard", title: tr("لوحة التحكم", "Dashboard"), icon: "chart" }, false);
  const renderGroup = (title, icon, screens) => {
    const unique = screens.filter(x => x?.route && !used.has(x.route));
    if (!unique.length) return "";
    unique.forEach(x => used.add(x.route));
    const open = unique.some(x => x.route === path);
    return `<div class="nav-g${open ? " open" : ""}"><button class="nav-i nav-gh" type="button">${ico(icon)}<span>${esc(title)}</span>${ico("chevron", "chev")}</button><div class="nav-sub">${unique.map(x => link({ route: x.route, title: tOf(x) })).join("")}</div></div>`;
  };
  for (const g of NAV_GROUPS) {
    const screens = all.filter(x => (g.routes || []).includes(x.route) || (g.sectionCodes || []).includes(x._section));
    if (g.routes?.includes("/settlements/technical") && auth.can("ContractSettlements", "View")) screens.push(
      { route: "/settlements/technical", title_ar: "المستخلصات الفنية", title_en: "Technical Settlements" },
      { route: "/settlements/financial", title_ar: "المستخلصات المالية", title_en: "Financial Settlements" }
    );
    if ((g.routes || []).includes("/inventory") && screens.some(x => x.route === "/inventory")) screens.push({route:"/inventory/receipts",title_ar:"استلام التوريدات",title_en:"Goods Receipts"},{route:"/inventory/items",title_ar:"الأصناف",title_en:"Items"},{route:"/inventory/warehouses",title_ar:"المخازن",title_en:"Warehouses"},{route:"/inventory/balances",title_ar:"أرصدة المخزون",title_en:"Stock Balances"},{route:"/inventory/movements",title_ar:"حركة المخزون",title_en:"Stock Movements"},{route:"/inventory/transfers",title_ar:"التحويلات بين المخازن",title_en:"Warehouse Transfers"},{route:"/inventory/site-issues",title_ar:"طلبات صرف المواقع",title_en:"Site Issue Requests"},{route:"/inventory/stocktakes",title_ar:"الجرد والتسويات",title_en:"Stocktakes & Adjustments"},{route:"/inventory/returns",title_ar:"المرتجعات",title_en:"Inventory Returns"});
    if ((g.routes || []).includes("/purchases") && (screens.some(x => x.route === "/purchases") || auth.can("PurchaseCycle", "View"))) {
      if (!screens.some(x => x.route === "/purchases")) screens.push({route:"/purchases",title_ar:"دورة المشتريات",title_en:"Purchasing Cycle"});
      for (const item of [{route:"/purchases/requisitions",title_ar:"طلبات الشراء",title_en:"Purchase Requisitions"},{route:"/purchases/quotations",title_ar:"عروض أسعار الموردين",title_en:"Supplier Quotations"},{route:"/purchases/orders",title_ar:"أوامر الشراء",title_en:"Purchase Orders"},{route:"/purchases/receipts",title_ar:"استلام التوريدات",title_en:"Goods Receipts"},{route:"/purchases/invoices",title_ar:"فواتير الموردين",title_en:"Supplier Invoices"},{route:"/purchases/payments",title_ar:"سداد الموردين",title_en:"Supplier Payments"},{route:"/purchases/reports",title_ar:"تقارير الموردين",title_en:"Supplier Reports"}]) if (!screens.some(x => x.route === item.route)) screens.push(item);
    }
    h += renderGroup(isEN() ? g.en : g.ar, g.icon, screens);
  }
  for (const s of sectionsOrdered()) {
    const leftovers = all.filter(x => x._section === s.code && !used.has(x.route));
    h += renderGroup(isEN() ? (s.name_en || s.name_ar) : (s.name_ar || s.name_en), "list", leftovers);
  }
  if (auth.can("AnalyticsReports", "View") && !used.has("/reports/financial-control")) {
    h += renderGroup(tr("التقارير والرقابة", "Reports & Control"), "chart", [{ route: "/reports/financial-control", title_ar: "لوحة الرقابة المالية", title_en: "Financial Control" }]);
  }
  if (IS_ADMIN) h += `<div class="nav-sep"></div>` + renderGroup(tr("إدارة النظام", "System Administration"), "users", ADMIN_ITEMS.filter(a => a.route !== "/admin/reset").map(a => ({ ...a, title_ar: a.title, title_en: a.title_en })));
  // Keep the reset entry discoverable; the reset API still enforces IT system-admin authorization.
  h += renderGroup(tr("إدارة النظام", "System Administration"), "users", [{ route: "/admin/reset", title_ar: "إعادة ضبط البيانات", title_en: "Reset System Data" }]);
  return h;
}

// ---------------------------------------------------------------- الهيكل العام (قائمة جانبية + شريط علوي)
const curTheme = () => document.documentElement.dataset.theme === "light" ? "light" : "dark";
const draftCount = () => SUMMARY?.kpis?.draft_entries || 0;

function shell(title, path = "") {
  applyLanguage();
  document.body.classList.remove("login-mode");
  const name = auth.user?.full_name || auth.user?.username || "";
  const initial = [...name.trim()][0] || "؟";
  root.innerHTML = `<div class="app">
    <aside class="sidebar" aria-label="${tr("القائمة الرئيسية", "Main navigation")}">
      <a class="brand" href="#/"><img src="/static/company-logos.png?v=20261017" alt="شعارات الشركات"><div class="brand-t">ADEX ERP</div><small class="brand-sub">ENTERPRISE MANAGEMENT</small></a>
      ${navHtml(path)}
    </aside>
    <div class="content">
      <header class="hdr">
        <button class="icon-btn menu" id="menubtn" type="button" aria-label="القائمة">${ico("menu")}</button>
        <div class="gsearch"><input id="gs" placeholder="${tr("البحث العام", "Search")}" autocomplete="off" aria-label="${tr("البحث العام", "Search")}"><span class="gs-ico">${ico("search")}</span><div class="gs-res" id="gsr" hidden></div></div>
        <span class="sp"></span>
        <button class="btn sm" id="langbtn" type="button" title="${tr("تغيير اللغة", "Change language")}">${isEN() ? "العربية" : "English"}</button>
        <button class="icon-btn" id="themebtn" type="button" title="تبديل الوضع الفاتح/الداكن" aria-label="تبديل الوضع">${ico(curTheme() === "dark" ? "sun" : "moon")}</button>
        <button class="icon-btn" id="bell" type="button" title="القيود غير المرحّلة" aria-label="الإشعارات">${ico("bell")}${draftCount() > 0 ? '<i class="dot"></i>' : ""}</button>
        <span class="avatar" id="profile-avatar" title="${esc(name)}">${esc(initial)}</span><span class="who">${esc(name)}</span>
        <button class="btn sm" id="out" type="button">${ico("logout")}<span>${tr("خروج", "Logout")}</span></button>
      </header>
      <div class="print-head" id="printhead"></div>
      <div class="pagebar">${title ? `<h2>${esc(title)}</h2>` : ""}<span class="sp"></span><span id="pageact"></span><button class="btn sm" id="printbtn" type="button" hidden>${ico("printer")}<span>${tr("طباعة الشاشة", "Print screen")}</span></button></div>
      <main class="wrap"></main>
    </div>
    <div class="scrim"></div></div>`;
  const $ = s => root.querySelector(s);
  if (auth.user?.avatar_updated_at) userAvatarUrl(auth.user.user_id, auth.user.avatar_updated_at).then(url => {
    const el = $("#profile-avatar"); if (el && url) el.innerHTML = `<img src="${url}" alt="الصورة الشخصية">`;
  }).catch(() => {});
  api("/company-profile").then(company => {
    const logo = $(".brand img");
    if (logo && company?.logo_data) logo.src = company.logo_data;
    if (company?.logo_data) root.querySelectorAll(".alliance-logo").forEach(img => { img.src = company.logo_data; });
  }).catch(() => {});
  const app = $(".app");
  root.querySelectorAll(".nav-gh").forEach(b => b.onclick = () => b.parentElement.classList.toggle("open"));
  $("#menubtn").onclick = () => app.classList.toggle("open");
  $(".scrim").onclick = () => app.classList.remove("open");
  $("#printbtn").onclick = () => window.print();
  $("#langbtn").onclick = async () => { LANG = isEN() ? "ar" : "en"; try { localStorage.setItem("fs_lang", LANG); } catch {} applyLanguage(); route(); if (auth.loggedIn) { try { await api("/auth/language", { method: "PUT", json: { language: LANG } }); auth.updateUser({ preferred_language: LANG }); } catch (e) { toast(errText(e)); } } };
  $("#out").onclick = async () => { try { await api("/auth/logout", { method: "POST" }); } catch {} auth.clear(); resetSession(); location.hash = "#/login"; };
  $("#bell").onclick = () => draftCount() > 0 ? (location.hash = "#/journal") : toast(tr("لا توجد قيود غير مرحّلة", "No unposted journal entries"));
  $("#themebtn").onclick = () => {
    const t = curTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem("fs_theme", t); } catch {}
    $("#themebtn").innerHTML = ico(t === "dark" ? "sun" : "moon");
  };
  // البحث العام في الشاشات
  const gs = $("#gs"), gr = $("#gsr"), items = navItems();
  gs.oninput = () => {
    const q = gs.value.trim().toLowerCase();
    if (!q) { gr.hidden = true; return; }
    const hits = items.filter(i => (i.title + " " + i.sub).toLowerCase().includes(q)).slice(0, 8);
    gr.innerHTML = hits.length ? hits.map(h => `<a href="#${esc(h.route)}">${esc(h.title)}<small>${esc(h.sub)}</small></a>`).join("") : `<div class="empty">لا توجد نتائج</div>`;
    gr.hidden = false;
  };
  gs.onkeydown = ev => {
    if (ev.key === "Escape") { gr.hidden = true; return; }
    if (ev.key !== "Enter") return;
    const a = gr.querySelector("a");
    if (a) { location.hash = a.getAttribute("href"); gs.value = ""; gr.hidden = true; }
  };
  gs.onblur = () => setTimeout(() => (gr.hidden = true), 150);
  return $("main");
}

function loginPage() {
  applyLanguage();
  resetSession();
  document.body.classList.add("login-mode");
  root.innerHTML = `<form class="login"><div class="adex-login-brand"><strong>ADEX</strong><small>ENTERPRISE RESOURCE PLANNING</small></div><div style="display:flex;justify-content:flex-end"><button class="btn sm" id="loginlang" type="button">${isEN() ? "العربية" : "English"}</button></div><h2>${tr("تسجيل الدخول", "Sign in")}</h2>
    <div class="f"><label>${tr("اسم المستخدم", "Username")}</label><input name="u" autocomplete="username" required autofocus></div>
    <div class="f"><label>${tr("كلمة المرور", "Password")}</label><input name="p" type="password" autocomplete="current-password" required></div>
    <div class="err" id="e"></div><button class="btn primary" style="width:100%">${tr("دخول", "Sign in")}</button></form>`;
  root.querySelector("#loginlang").onclick = () => { LANG = isEN() ? "ar" : "en"; try { localStorage.setItem("fs_lang", LANG); localStorage.setItem("fs_lang_manual", "1"); } catch {} applyLanguage(); loginPage(); };
  const f = root.querySelector("form");
  f.onsubmit = async ev => {
    ev.preventDefault(); const b = f.querySelector("button"); b.disabled = true;
    try { await login(f.u.value.trim(), f.p.value); location.hash = "#/"; }
    catch (e) { f.querySelector("#e").textContent = errText(e); b.disabled = false; }
  };
}

// ---------------------------------------------------------------- الشاشة الرئيسية
const fmt0 = v => Number(v).toLocaleString(isEN() ? "en-US" : "ar-EG", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtDate = d => String(d || "").split("-").reverse().join("/");
const compact = v => {
  const a = Math.abs(v);
  const s = a >= 1e9 ? (a / 1e9).toFixed(1) + "B" : a >= 1e6 ? (a / 1e6).toFixed(1) + "M" : a >= 1e3 ? (a / 1e3).toFixed(1) + "K" : String(Math.round(a));
  return (v < 0 ? "-" : "") + s.replace(".0", "");
};
const MONTHS = ["ينا", "فبر", "مار", "أبر", "ماي", "يون", "يول", "أغس", "سبت", "أكت", "نوف", "ديس"];
const ST = { Posted: [tr("مرحّل", "Posted"), "ok"], Draft: [tr("مسودة", "Draft"), "warn"], Reversed: [tr("ملغي", "Reversed"), "bad"] };

function niceTicks(min, max, n = 4) {
  if (min === max) { if (min === 0) max = 1; else { min = Math.min(0, min); max = Math.max(0, max); } }
  const raw = (max - min) / n, pow = 10 ** Math.floor(Math.log10(raw)), f = raw / pow;
  const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * pow;
  const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, ticks = [];
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(+v.toFixed(6));
  return { lo, hi, ticks };
}

function lineChart(series) {      // [{year, month, balance}]
  const W = 640, H = 300, Lm = 92, Rm = 18, T = 30, B = 34;
  const vals = series.map(p => +p.balance);
  const { lo, hi, ticks } = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals));
  const x = i => Lm + i * (W - Lm - Rm) / Math.max(1, series.length - 1);
  const y = v => T + (hi - v) / (hi - lo) * (H - T - B);
  const pts = vals.map((v, i) => [x(i), y(v)]);
  const r = n => n.toFixed(1);
  let d = `M${r(pts[0][0])},${r(pts[0][1])}`;
  for (let i = 0; i < pts.length - 1; i++) {      // منحنى ناعم (Catmull-Rom → Bezier)
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    d += ` C${r(p1[0] + (p2[0] - p0[0]) / 6)},${r(p1[1] + (p2[1] - p0[1]) / 6)} ${r(p2[0] - (p3[0] - p1[0]) / 6)},${r(p2[1] - (p3[1] - p1[1]) / 6)} ${r(p2[0])},${r(p2[1])}`;
  }
  const bottom = y(lo);
  const area = `${d} L${r(pts.at(-1)[0])},${r(bottom)} L${r(pts[0][0])},${r(bottom)} Z`;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="رصيد الخزينة الشهري">
    <defs><linearGradient id="chg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--brand);stop-opacity:.45"/><stop offset="1" style="stop-color:var(--brand);stop-opacity:.02"/></linearGradient></defs>
    ${ticks.map(t => `<line class="ch-grid" x1="${Lm}" x2="${W - Rm}" y1="${r(y(t))}" y2="${r(y(t))}"/><text class="ch-ax" x="${Lm - 8}" y="${r(y(t) + 4)}" text-anchor="end">${fmt0(t)}</text>`).join("")}
    <path d="${area}" fill="url(#chg)"/><path class="ch-line" d="${d}"/>
    ${pts.map((p, i) => `<circle class="ch-pt" cx="${r(p[0])}" cy="${r(p[1])}" r="3.5"><title>${MONTHS[series[i].month - 1]} ${series[i].year}: ${fmt0(vals[i])}</title></circle><text class="ch-val" x="${r(p[0])}" y="${r(p[1] - 9)}" text-anchor="middle">${compact(vals[i])}</text>`).join("")}
    ${series.map((p, i) => `<text class="ch-ax" x="${r(x(i))}" y="${H - 10}" text-anchor="middle">${MONTHS[p.month - 1]}</text>`).join("")}
  </svg>`;
}

const kpi = (label, icon, val, cls, sub) => `<article class="kpi home-kpi"><div class="kpi-top"><div class="kpi-h">${ico(icon)}<span>${label}</span></div><span class="kpi-mark">${ico(icon)}</span></div><div class="kpi-v ${cls || ""}"><bdi dir="ltr">${val}</bdi></div><div class="kpi-s">${sub || ""}</div></article>`;

function homeHtml(s) {
  const k = s.kpis || {}, cards = [];

  if (k.total_debit != null) cards.push(kpi(tr("إجمالي المدين", "Total Debit"), "dollar", fmt0(k.total_debit), "", tr("القيود المرحّلة", "Posted entries")));
  if (k.treasury_balance != null) {
    const v = +k.treasury_balance;
    const others = (s.other_balances || []).map(o => `${esc(o.currency)} ${fmt0(o.balance)}`).join(" · ");
    cards.push(kpi(tr("رصيد الخزينة", "Treasury Balance"), "bank", (v > 0 ? "+" : "") + fmt0(v), v > 0 ? "pos" : v < 0 ? "neg" : "", esc(s.currency) + (others ? " · " + others : "")));
  }
  if (k.total_credit != null) cards.push(kpi(tr("إجمالي الدائن", "Total Credit"), "swap", fmt0(k.total_credit), "", tr("القيود المرحّلة", "Posted entries")));
  if (k.draft_entries != null) cards.push(kpi(tr("قيود غير مرحّلة", "Unposted Entries"), "receipt", fmt0(k.draft_entries), "", tr("مسودات تنتظر الترحيل", "Drafts awaiting posting")));
  const table = s.latest_entries == null ? "" : `<section class="card home-panel home-recent"><div class="card-h"><div><span class="home-eyebrow">${tr("الحركة المحاسبية", "ACCOUNTING ACTIVITY")}</span><h3>${tr("آخر القيود", "Recent Journal Entries")}</h3></div>
      <div class="seg"><button class="btn sm primary" type="button" data-f="all">${tr("الكل", "All")}</button><button class="btn sm" type="button" data-f="Draft">${tr("مسودة", "Draft")}</button></div></div>
      <div class="tbl-wrap"><table><thead><tr><th>${tr("رقم القيد", "Entry No.")}</th><th>${tr("التاريخ", "Date")}</th><th>${tr("البيان", "Description")}</th><th>${tr("الحالة", "Status")}</th></tr></thead><tbody id="lastrows"></tbody></table></div>
      <div class="home-panel-foot">${tr("اضغط على أي قيد للانتقال إلى دفتر اليومية", "Select an entry to open the journal")}</div></section>`;
  const chart = s.cash_series == null ? "" : `<section class="card home-panel home-chart"><div class="card-h"><div><span class="home-eyebrow">${tr("الموقف النقدي", "CASH POSITION")}</span><h3>${tr("حركة رصيد الخزينة", "Treasury Balance Trend")}</h3></div><span class="home-period">${tr("آخر 12 شهر", "Last 12 months")}</span></div>${s.cash_series.length ? `<div class="chart">${lineChart(s.cash_series)}</div>` : `<div class="home-empty">${tr("لا توجد حركة خزينة مسجلة خلال الفترة", "No treasury activity recorded for this period")}</div>`}<div class="home-panel-foot">${tr("الرصيد التراكمي بعملة", "Cumulative balance in")} ${esc(s.currency || "")}</div></section>`;
  if (!cards.length && !table && !chart) return `<p class="empty">${tr("لا توجد بيانات متاحة لصلاحياتك — استخدم القائمة الجانبية للتنقل.", "No data is available for your permissions. Use the sidebar to navigate.")}</p>`;
  const dateLabel = new Date().toLocaleDateString(isEN() ? "en-US" : "ar-EG", {weekday:"long",year:"numeric",month:"long",day:"numeric"});
  return `<section class="home-hero"><div class="alliance-heading"><img class="alliance-logo" src="/static/company-logos.png?v=20261017" alt="شعار التحالف"><div class="alliance-copy"><strong>تحالف شركات</strong><span>المقاولون العرب (عثمان احمد عثمان وشركاه)</span><span>الغرابلي للأعمال الهندسية المتكاملة</span><span>أبناء سيناء للتشييد والبناء</span></div></div><div class="home-heading"><span class="home-eyebrow">${tr("نظرة عامة", "OVERVIEW")}</span><h1>${tr("لوحة تحكم ADEX", "ADEX Dashboard")}</h1><p>${tr("ملخص سريع لأهم الأرصدة والحركة المحاسبية في النظام.", "A concise view of key balances and accounting activity.")}</p><div class="home-date">${ico("calendar")}<span>${dateLabel}</span></div></div></section>
    <div class="home-section-title"><div><h2>${tr("المؤشرات الرئيسية", "Key Financial Indicators")}</h2><p>${tr("القيم المعروضة حسب البيانات والصلاحيات المتاحة", "Figures based on available data and permissions")}</p></div></div>
    <div class="kpis home-kpis">${cards.join("")}</div><div class="home-section-title home-activity-title"><div><h2>${tr("ملخص النشاط", "Activity Overview")}</h2><p>${tr("تابع أحدث القيود واتجاه رصيد الخزينة", "Review recent entries and treasury trends")}</p></div></div>
    <div class="dash home-dash">${table}${chart}</div>`;
}
async function modulesDashboard() {
  const main = shell(tr("لوحة التحكم", "Dashboard"), "/dashboard");
  const screens = (NAV?.sections || []).flatMap(section => section.screens || []);
  const hasInventoryAccess = screens.some(x => String(x.route || "").startsWith("/inventory"));
  const hasPurchasesAccess = auth.can("PurchaseCycle", "View") || screens.some(x => String(x.route || "").startsWith("/purchases"));
  const cards = `
    <section class="home-hero">
      <div class="home-heading">
        <span class="home-eyebrow">${tr("إدارة العمليات", "OPERATIONS")}</span>
        <h1>${tr("لوحة التحكم التشغيلية", "Operational Dashboard")}</h1>
        <p>${tr("اختر الوحدة التي تريد العمل عليها. لكل وحدة شاشاتها وإجراءاتها المستقلة.", "Choose a module. Each module has its own screens and workflows.")}</p>
      </div>
    </section>
    <section class="home-modules" aria-label="${tr("الوحدات التشغيلية", "Operational modules")}">
      ${hasInventoryAccess ? `<a class="home-module-card inventory" href="#/inventory" aria-label="${tr("فتح إدارة المخازن", "Open Inventory Management")}">
        <span class="home-module-icon">${ico("warehouse")}</span><span class="home-module-copy"><strong>${tr("إدارة المخازن", "Inventory Management")}</strong><small>${tr("الأصناف والأرصدة والاستلام والصرف والتحويلات والجرد", "Items, balances, receipts, issues, transfers and stocktakes")}</small><em>${tr("دخول إلى المخازن", "Open Inventory")} <b>←</b></em></span>
      </a>` : ""}
      ${hasPurchasesAccess ? `<a class="home-module-card purchasing" href="#/purchases" aria-label="${tr("فتح إدارة المشتريات", "Open Purchasing Management")}">
        <span class="home-module-icon">${ico("cart")}</span><span class="home-module-copy"><strong>${tr("إدارة المشتريات", "Purchasing Management")}</strong><small>${tr("طلبات الشراء وعروض الأسعار وأوامر الشراء وفواتير الموردين والسداد", "Requisitions, quotations, purchase orders, supplier invoices and payments")}</small><em>${tr("دخول إلى المشتريات", "Open Purchasing")} <b>←</b></em></span>
      </a>` : ""}
    </section>`;
  main.innerHTML = hasInventoryAccess || hasPurchasesAccess ? cards : `<p class="empty">${tr("لا توجد وحدات تشغيلية متاحة حسب صلاحيات المستخدم.", "No operational modules are available for this user.")}</p>`;
}

function drawRows(main, entries, only) {
  const tb = main.querySelector("#lastrows"); if (!tb) return;
  const rows = entries.filter(e => only === "all" || e.status === only).slice(0, 8);
  tb.innerHTML = rows.length ? rows.map(e => { const [t, c] = ST[e.status] || [e.status, ""]; return `<tr data-id="${e.journal_entry_id}"><td>${esc(e.entry_no)}</td><td>${fmtDate(e.entry_date)}</td><td>${esc(e.description || "")}</td><td><span class="tag ${c}">${esc(t)}</span></td></tr>`; }).join("")
    : `<tr><td colspan="4" class="empty">${tr("لا توجد قيود", "No entries")}</td></tr>`;
  tb.querySelectorAll("tr[data-id]").forEach(tr => tr.onclick = () => (location.hash = "#/journal"));
}

async function dashboard() {
  const main = shell(tr("الرئيسية", "Home"), "/");
  root.querySelector("#pageact").innerHTML = `<button class="btn primary sm" id="refresh" type="button">${ico("refresh")}<span>${tr("تحديث", "Refresh")}</span></button>`;
  main.innerHTML = `<p class="muted">جاري التحميل…</p>`;
  const draw = async () => {
    const s = await api("/dashboard/summary");
    SUMMARY = s;
    const dot = root.querySelector("#bell .dot");
    if (draftCount() > 0 && !dot) root.querySelector("#bell").insertAdjacentHTML("beforeend", '<i class="dot"></i>');
    if (draftCount() === 0 && dot) dot.remove();
    main.innerHTML = homeHtml(s);
    let only = "all";
    drawRows(main, s.latest_entries || [], only);
    main.querySelectorAll(".seg [data-f]").forEach(b => b.onclick = () => {
      only = b.dataset.f;
      main.querySelectorAll(".seg [data-f]").forEach(x => x.classList.toggle("primary", x === b));
      drawRows(main, s.latest_entries || [], only);
    });
  };
  root.querySelector("#refresh").onclick = () => draw().catch(e => toast(errText(e)));
  await draw();
}

// ---------------------------------------------------------------- التوجيه
async function route() {
  let path = (location.hash.replace(/^#/, "") || "/").replace(/\/+$/, "") || "/";
  // توافق مع المسارات القديمة/المختلفة التي قد تكون محفوظة في قاعدة البيانات.
  const routeAliases = { "/financial-checks": "/checks/register", "/checks-register": "/checks/register", "/purchase-cycle": "/purchases", "/purchasing": "/purchases", "/purchase": "/purchases", "/accounting/purchases": "/purchases", "/accounting/purchase-cycle": "/purchases", "/purchase-orders": "/purchases", "/purchase-order": "/purchases" };
  if (routeAliases[path] || /\/(purchase|purchases|purchasing|purchase-cycle|purchase-order|purchase-orders)$/i.test(path)) {
    path = routeAliases[path] || "/purchases";
    history.replaceState(null, "", "#" + path);
  }
  if (path === "/login") return loginPage();
  if (!auth.loggedIn) return (location.hash = "#/login");
  try {
    await ensureNav();
    if (path === "/") return await dashboard();
    if (path === "/dashboard") return await modulesDashboard();
    const loader = SCREENS[path];
    if (!loader) { shell(titleOf(path), path).innerHTML = `<p>هذه الشاشة قيد التنفيذ.</p><button class="btn" onclick="location.hash='#/'">رجوع</button>`; return; }
    const mod = await loader();
    const main = shell(titleOf(path), path);
    await mod.render(main, { api, auth, route: path });
    mountDataExchange(main, api, path);
    root.querySelector("#printbtn").hidden = false;     // طباعة أي شاشة (الرئيسية والدخول مالهمش طباعة)
  } catch (e) { toast(errText(e)); }
}
addEventListener("hashchange", route);
route();

// ترويسة الطباعة: اسم الشاشة + التاريخ + المستخدم (بتظهر في الورق بس)
addEventListener("beforeprint", () => {
  const h = document.getElementById("printhead"); if (!h) return;
  const t = document.querySelector(".pagebar h2, main .pagehead h2, main h2, main .sec > h3, main h3")?.textContent?.trim() || document.title;
  h.innerHTML = `<div class="print-alliance"><img src="${document.querySelector(".brand img")?.src || "/static/company-logos.png"}" alt="شعار التحالف"><div><b>تحالف شركات</b><strong>المقاولون العرب (عثمان احمد عثمان وشركاه)</strong><strong>الغرابلي للأعمال الهندسية المتكاملة</strong><strong>أبناء سيناء للتشييد والبناء</strong></div></div><div class="print-meta"><b>${esc(t)}</b><span>${esc(new Date().toLocaleString("ar-EG"))}${auth.user?.full_name ? " — " + esc(auth.user.full_name) : ""}</span></div>`;
});
