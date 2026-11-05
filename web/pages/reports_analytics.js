import { esc, money, today, safe } from "../ui.js";
const EN = {
"المؤشرات المالية":"Financial indicators","كشف حساب أستاذ":"General ledger","التدفقات النقدية التفصيلية":"Detailed cash flow","التحليل المالي للمشروعات":"Project financial analysis","أعمار المستحقات":"Receivables & payables aging","العقود والمستخلصات والمدفوعات":"Contracts, statements & payments","الشيكات":"Cheques","المشتريات والاستلام":"Purchasing & receiving","الأصناف والأرصدة":"Items & balances","كشف طرف بالاسم المسجل":"Party statement (as registered)",
"الإيرادات والمصروفات وحركة النقدية والحسابات الأكثر حركة":"Revenue, expenses, cash movements and most active accounts","حركة حساب تفصيلي ورصيد أول وآخر الفترة":"Detailed account activity and opening/closing balances","تفاصيل المقبوضات والمدفوعات حسب الخزينة والبنك":"Receipts and payments by treasury and bank","الإيرادات والمصروفات وصافي نتيجة كل مشروع من القيود المرحلة":"Revenue, expenses and net result by project from posted entries","المبالغ المستحقة لنا وعلينا موزعة حسب عمر الرصيد":"Receivables and payables grouped by balance age","قيمة الأعمال والخصومات والصافي والمدفوع والمتبقي لكل مستخلص":"Work value, deductions, net, paid and remaining per statement","الشيكات حسب الفترة والحالة مع بيان المستخلص المرتبط والشيكات غير المربوطة":"Cheques by period and status, linked statements and unlinked cheques","أوامر الشراء والمورد والمخزن والكميات المطلوبة والمستلمة":"Purchase orders, suppliers, warehouses and ordered/received quantities","الأرصدة الحالية والتنبيه على الأصناف عند حد الطلب":"Current balances and reorder-level alerts","يعرض كل اسم كما ورد في سجلاته القديمة دون ربطه باسم موحد":"Shows each party name as originally recorded, without merging names",
"التاريخ":"Date","رقم القيد":"Journal entry No.","البيان":"Description","المشروع":"Project","مدين":"Debit","دائن":"Credit","الرصيد":"Balance","الخزينة / البنك":"Treasury / bank","رقم الإذن":"Voucher No.","المستفيد":"Beneficiary","وارد":"Inflow","منصرف":"Outflow","الصافي":"Net","الإيرادات":"Revenue","المصروفات":"Expenses","صافي النتيجة":"Net result","النوع":"Type","الطرف":"Party","رقم المستند":"Document No.","العمر بالأيام":"Age (days)","الفئة العمرية":"Age bucket","الرصيد المتبقي":"Remaining balance","رقم المستخلص":"Statement No.","رقم العقد":"Contract No.","العقد":"Contract","الطرف كما سُجل":"Party as registered","قيمة الأعمال":"Work value","الخصومات":"Deductions","الضريبة":"Tax","المدفوع":"Paid","المتبقي":"Remaining","الحالة":"Status","رقم الشيك":"Cheque No.","البنك":"Bank","المبلغ":"Amount","المستخلص المرتبط":"Linked statement","أمر الشراء":"Purchase order","المورد كما سُجل":"Supplier as registered","مركز التكلفة":"Cost center","المخزن":"Warehouse","الكمية المطلوبة":"Ordered quantity","الكمية المستلمة":"Received quantity","الإجمالي":"Total","كود الصنف":"Item code","الصنف":"Item","التصنيف":"Category","الوحدة":"Unit","الرصيد الحالي":"Current balance","حد الطلب":"Reorder level","تنبيه النقص":"Low stock alert",
"مسودة":"Draft","معتمد ماليًا":"Financially approved","مرحّل محاسبيًا":"Posted to accounting","تم الاستلام":"Received","ملغي":"Cancelled","تحت المراجعة":"Under review","معتمد هندسيًا":"Technically approved","نقص":"Low","طبيعي":"Normal","عميل":"Customer","مقاول باطن":"Subcontractor","لا توجد بيانات مطابقة للفلاتر":"No data matches the selected filters",
"حركة النقدية الشهرية":"Monthly cash flow","لا توجد حركات نقدية في الفترة المحددة.":"No cash movements in the selected period.","المصروفات حسب التصنيف":"Expenses by category","لا توجد مصروفات مصنفة في الفترة المحددة.":"No categorized expenses in the selected period.",
"مركز التقارير":"Reports Center","تقارير مالية وتشغيلية من بيانات النظام، مع فلاتر وطباعة وتصدير.":"Financial and operational reports from system data, with filters, print and export.","ميزان المراجعة":"Trial balance","المركز المالي":"Balance sheet","قائمة الدخل":"Income statement","الخزينة والبنوك":"Treasury & banks","دورة المشتريات":"Purchasing workflow","إدارة المخزون":"Inventory management","نوع التقرير":"Report type","من تاريخ":"From date","إلى تاريخ":"To date","نوع المستخلص":"Statement type","الكل":"All","العميل":"Customer","مقاول الباطن":"Subcontractor","كل المشروعات":"All projects","كل الحالات":"All statuses","الطرف — الاسم المسجل":"Party — registered name","اختر الاسم":"Select party","الحساب التفصيلي":"Ledger account","اكتب كود الحساب أو اسمه":"Type account code or name","ابحث عن الحساب":"Search account","الخزينة / البنك":"Treasury / bank","عرض التقرير":"Run report","تصدير CSV":"Export CSV","طباعة / PDF":"Print / PDF","تاريخ البداية يجب أن يكون قبل تاريخ النهاية":"Start date must be before end date","كل الفترات":"All periods","حتى اليوم":"To date","سجل":"records","إجمالي الإيرادات":"Total revenue","إجمالي المصروفات":"Total expenses","صافي الربح / الخسارة":"Net profit / loss","الشهر":"Month","الوارد":"Inflow","المنصرف":"Outflow","أكثر الحسابات حركة":"Most active accounts","الكود":"Code","الحساب":"Account","الطبيعة":"Nature","اختر الحساب التفصيلي لعرض كشف الأستاذ":"Select a ledger account to view its statement","عدد الحركات":"Transactions","إجمالي المقبوضات":"Total receipts","إجمالي المدفوعات":"Total payments","عدد المشروعات":"Projects","مستحق لنا":"Receivable","مستحق علينا":"Payable","أكثر من 90 يوم":"Over 90 days","حتى":"As of","المستخلصات":"Statements","صافي المستحق":"Net due","إجمالي القيمة":"Total value","المصروف":"Paid","غير مربوط بمستخلص":"Not linked to a statement","أوامر الشراء":"Purchase orders","إجمالي قيمة الأوامر":"Total order value","عدد الأصناف":"Items","أصناف عند حد الطلب أو أقل":"Items at or below reorder level","اختر الطرف المطلوب؛ القائمة تعرض الأسماء كما سُجلت دون توحيدها":"Select a party; the list shows names as originally recorded, without merging them","العقود":"Contracts","المستخلصات الفنية":"Technical statements","المستخلصات المالية":"Financial statements","صافي المستخلصات":"Net statements","كشف الطرف:":"Party statement:","لا يوجد حساب مطابق للاسم أو الكود":"No account matches the name or code"
};
const T = value => { try { return localStorage.getItem("fs_lang")==="en" ? (EN[value] || value) : value; } catch { return value; } };

const REPORTS = [
  ["overview", "المؤشرات المالية", "الإيرادات والمصروفات وحركة النقدية والحسابات الأكثر حركة", "◈"],
  ["account_ledger", "كشف حساب أستاذ", "حركة حساب تفصيلي ورصيد أول وآخر الفترة", "≡"],
  ["cash_flow", "التدفقات النقدية التفصيلية", "تفاصيل المقبوضات والمدفوعات حسب الخزينة والبنك", "⇄"],
  ["project_financials", "التحليل المالي للمشروعات", "الإيرادات والمصروفات وصافي نتيجة كل مشروع من القيود المرحلة", "⌂"],
  ["aging", "أعمار المستحقات", "المبالغ المستحقة لنا وعلينا موزعة حسب عمر الرصيد", "◷"],
  ["settlements", "العقود والمستخلصات والمدفوعات", "قيمة الأعمال والخصومات والصافي والمدفوع والمتبقي لكل مستخلص", "▤"],
  ["checks", "الشيكات", "الشيكات حسب الفترة والحالة مع بيان المستخلص المرتبط والشيكات غير المربوطة", "▣"],
  ["purchases", "المشتريات والاستلام", "أوامر الشراء والمورد والمخزن والكميات المطلوبة والمستلمة", "⇩"],
  ["inventory", "الأصناف والأرصدة", "الأرصدة الحالية والتنبيه على الأصناف عند حد الطلب", "▦"],
  ["contractor", "كشف طرف بالاسم المسجل", "يعرض كل اسم كما ورد في سجلاته القديمة دون ربطه باسم موحد", "♧"],
];

const csvCell = value => {
  let text = String(value ?? "");
  if (/^[=+@\-\t\r\n]/.test(text)) text = "'" + text;
  return `"${text.replaceAll('"', '""')}"`;
};
const csvDownload = (filename, keys, labels, rows) => {
  const csv = "\ufeff" + [labels, ...rows.map(row => keys.map(key => row[key]))]
    .map(row => row.map(csvCell).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
const columns = {
  account_ledger: [["date", "التاريخ"], ["entry_no", "رقم القيد"], ["description", "البيان"], ["project", "المشروع"], ["debit", "مدين"], ["credit", "دائن"], ["balance", "الرصيد" ]],
  cash_flow: [["date", "التاريخ"], ["account", "الخزينة / البنك"], ["voucher_no", "رقم الإذن"], ["description", "البيان"], ["recipient", "المستفيد"], ["project", "المشروع"], ["inflow", "وارد"], ["outflow", "منصرف"], ["net", "الصافي"]],
  project_financials: [["project", "المشروع"], ["revenue", "الإيرادات"], ["expenses", "المصروفات"], ["net", "صافي النتيجة"]],
  aging: [["kind", "النوع"], ["party", "الطرف"], ["document_no", "رقم المستند"], ["document_date", "التاريخ"], ["age_days", "العمر بالأيام"], ["bucket", "الفئة العمرية"], ["balance", "الرصيد المتبقي"], ["project", "المشروع"]],
  settlements: [["settlement_no", "رقم المستخلص"], ["settlement_date", "التاريخ"], ["settlement_side", "النوع"], ["contract_no", "رقم العقد"], ["contract_title", "العقد"], ["project", "المشروع"], ["counterparty_name", "الطرف كما سُجل"], ["work_value", "قيمة الأعمال"], ["deductions", "الخصومات"], ["vat_amount", "الضريبة"], ["net_amount", "الصافي"], ["paid_amount", "المدفوع"], ["remaining_amount", "المتبقي"], ["status", "الحالة"]],
  checks: [["check_no", "رقم الشيك"], ["check_date", "التاريخ"], ["bank", "البنك"], ["beneficiary", "المستفيد"], ["project", "المشروع"], ["amount", "المبلغ"], ["settlement_no", "المستخلص المرتبط"], ["status", "الحالة"], ["description", "البيان"]],
  purchases: [["order_no", "أمر الشراء"], ["order_date", "التاريخ"], ["supplier", "المورد كما سُجل"], ["project", "مركز التكلفة"], ["warehouse", "المخزن"], ["ordered_quantity", "الكمية المطلوبة"], ["received_quantity", "الكمية المستلمة"], ["total_amount", "الإجمالي"], ["status", "الحالة"]],
  inventory: [["code", "كود الصنف"], ["name", "الصنف"], ["category", "التصنيف"], ["unit", "الوحدة"], ["balance", "الرصيد الحالي"], ["minimum", "حد الطلب"], ["low_stock", "تنبيه النقص"]],
  contractor: [["date", "التاريخ"], ["kind", "النوع"], ["number", "رقم المستخلص"], ["contract_no", "رقم العقد"], ["contract_title", "العقد"], ["counterparty_name", "الطرف كما سُجل"], ["status", "الحالة"], ["work_value", "قيمة الأعمال"], ["deductions", "الخصومات"], ["vat", "الضريبة"], ["net", "الصافي"], ["paid", "المدفوع"], ["outstanding", "المتبقي"]],
};
const statusLabel = value => T(({ Draft: "مسودة", Approved: "معتمد ماليًا", Posted: "مرحّل محاسبيًا", Received: "تم الاستلام", Cancelled: "ملغي", UnderReview: "تحت المراجعة", TechnicallyApproved: "معتمد هندسيًا", "جديد":"جديد", "مطبوع":"مطبوع", "تم التسليم":"تم التسليم", "تم الصرف":"تم الصرف", "مرتد":"مرتد" })[value] || value);

const kpis = entries => `<div class="kpis">${entries.map(([label, value]) => `<div class="kpi"><div class="kpi-h">${esc(T(label))}</div><div class="kpi-v">${esc(value)}</div></div>`).join("")}</div>`;
const dataTable = (key, items) => {
  const cols = columns[key];
  return `<div class="tbl-wrap"><table><thead><tr>${cols.map(([, label]) => `<th>${esc(T(label))}</th>`).join("")}</tr></thead><tbody>${items.map(item => `<tr>${cols.map(([field]) => {
    const value = item[field];
    const formatted = ["work_value", "deductions", "vat_amount", "net_amount", "paid_amount", "remaining_amount", "amount", "total_amount", "vat", "net", "paid", "outstanding", "debit", "credit", "balance", "revenue", "expenses", "inflow", "outflow", "opening_balance", "closing_balance"].includes(field) && value !== "" && value != null ? money(value) : field === "low_stock" ? (value ? T("نقص") : T("طبيعي")) : field === "settlement_side" ? (value === "Customer" ? T("عميل") : value === "Subcontractor" ? T("مقاول باطن") : value) : field === "status" ? statusLabel(value) : value;
    return `<td>${esc(formatted ?? "—")}</td>`;
  }).join("")}</tr>`).join("") || `<tr><td class="muted" colspan="${cols.length}">${T("لا توجد بيانات مطابقة للفلاتر")}</td></tr>`}</tbody></table></div>`;
};
const chartNum = value => { const n = Number(value || 0); return Number.isFinite(n) ? n : 0; };
const monthlyCashChart = items => {
  const rows = items || [], width = 960, height = 310, left = 94, right = 18, top = 22, bottom = 58;
  if (!rows.some(x => chartNum(x.inflow) || chartNum(x.outflow))) return '<section class="report-chart"><h4>حركة النقدية الشهرية</h4><p class="muted">لا توجد حركات نقدية في الفترة المحددة.</p></section>';
  const plotW = width - left - right, plotH = height - top - bottom;
  const max = Math.max(1, ...rows.flatMap(x => [chartNum(x.inflow), chartNum(x.outflow)]));
  const axis = Array.from({ length: 5 }, (_, i) => { const value = max * (4 - i) / 4, y = top + plotH * i / 4;
    return `<line x1="${left}" y1="${y}" x2="${width - right}" y2="${y}" stroke="#94a3b8" stroke-opacity=".22"/><text x="${left - 10}" y="${y + 4}" text-anchor="end" class="report-chart-label">${esc(Number(value).toLocaleString("ar-EG", { notation: "compact", maximumFractionDigits: 1 }))}</text>`;
  }).join("");
  const slot = plotW / Math.max(rows.length, 1), barW = Math.min(20, slot * .28), gap = Math.min(5, slot * .08);
  const bars = rows.map((x, i) => {
    const center = left + slot * (i + .5), inflow = chartNum(x.inflow), outflow = chartNum(x.outflow);
    const hi = inflow / max * plotH, ho = outflow / max * plotH;
    const label = String(x.month || "");
    return `<rect x="${center - gap / 2 - barW}" y="${top + plotH - hi}" width="${barW}" height="${hi}" rx="3" fill="#35c27a"><title>${esc(`${label} — ${T("وارد")} ${money(inflow)}`)}</title></rect><rect x="${center + gap / 2}" y="${top + plotH - ho}" width="${barW}" height="${ho}" rx="3" fill="#ef6a62"><title>${esc(`${label} — ${T("منصرف")} ${money(outflow)}`)}</title></rect><text x="${center}" y="${top + plotH + 22}" text-anchor="middle" class="report-chart-label">${esc(label)}</text>`;
  }).join("");
  return `<section class="report-chart"><div class="report-chart-head"><h4>${T("حركة النقدية الشهرية")}</h4><div class="report-legend"><span><i class="in"></i>${T("وارد")}</span><span><i class="out"></i>${T("منصرف")}</span></div></div><div class="report-chart-scroll"><svg class="report-monthly-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${T("حركة النقدية الشهرية")}">${axis}${bars}</svg></div></section>`;
};
const expenseBreakdownChart = items => {
  const rows = (items || []).slice(0, 8), max = Math.max(1, ...rows.map(x => chartNum(x.amount)));
  const body = rows.length ? rows.map(x => `<div class="expense-chart-row"><span class="expense-chart-name" title="${esc(x.category)}">${esc(x.category)}</span><div class="expense-chart-track"><i style="width:${Math.max(0, Math.min(100, chartNum(x.amount) / max * 100))}%"></i></div><b>${money(x.amount)}</b></div>`).join("") : `<p class="muted">${T("لا توجد مصروفات مصنفة في الفترة المحددة.")}</p>`;
  return `<section class="report-chart"><h4>${T("المصروفات حسب التصنيف")}</h4><div class="expense-chart-list">${body}</div></section>`;
};

export async function render(main, { api }) {
  main.innerHTML = `<header class="reports-head no-print"><div><h2>${T("مركز التقارير")}</h2><p class="muted">${T("تقارير مالية وتشغيلية من بيانات النظام، مع فلاتر وطباعة وتصدير.")}</p></div><div class="reports-links"><a class="btn" href="#/trial-balance">ميزان المراجعة</a><a class="btn" href="#/reports/balance-sheet">المركز المالي</a><a class="btn" href="#/reports/income-statement">قائمة الدخل</a><a class="btn" href="#/treasury/analysis">الخزينة والبنوك</a><a class="btn" href="#/purchases">دورة المشتريات</a><a class="btn" href="#/inventory">إدارة المخزون</a></div></header>
    <section class="panel reports-panel no-print"><div class="reports-cards">${REPORTS.map(([id, title, desc, icon]) => `<button type="button" class="report-card" data-select="${id}"><span class="report-icon">${icon}</span><span><b>${T(title)}</b><small>${T(desc)}</small></span></button>`).join("")}</div>
      <div class="toolbar reports-toolbar"><div class="w"><label>${T("نوع التقرير")}</label><select id="kind">${REPORTS.map(([id, title]) => `<option value="${id}">${title}</option>`).join("")}</select></div>
        <div class="w date-filter"><label>${T("من تاريخ")}</label><input type="date" id="from" value="${new Date().getFullYear()}-01-01"></div><div class="w date-filter"><label>${T("إلى تاريخ")}</label><input type="date" id="to" value="${today()}"></div>
        <div class="w" id="side-wrap"><label>${T("نوع المستخلص")}</label><select id="side"><option value="">${T("الكل")}</option><option value="Customer">${T("العميل")}</option><option value="Subcontractor">${T("مقاول الباطن")}</option></select></div>
        <div class="w" id="project-wrap" hidden><label>${T("المشروع")}</label><select id="project"><option value="">${T("كل المشروعات")}</option></select></div>
        <div class="w" id="status-wrap" hidden><label>${T("الحالة")}</label><select id="status"><option value="">${T("كل الحالات")}</option></select></div>
        <div class="w" id="party-wrap" hidden><label>${T("الطرف — الاسم المسجل")}</label><select id="party"><option value="">${T("اختر الاسم")}</option></select></div>
        <div class="w" id="account-wrap" hidden><label>${T("الحساب التفصيلي")}</label><div class="report-account-picker"><input id="account-search" type="search" placeholder="${T("اكتب كود الحساب أو اسمه")}" autocomplete="off" aria-label="${T("ابحث عن الحساب")}"><input id="account" type="hidden" value=""><div id="account-options" class="journal-account-options" role="listbox" hidden></div></div></div>
        <div class="w" id="treasury-wrap" hidden><label>${T("الخزينة / البنك")}</label><select id="treasury"><option value="">${T("الكل")}</option></select></div>
        <button class="btn primary" id="run">${T("عرض التقرير")}</button><button class="btn" id="csv" disabled>${T("تصدير CSV")}</button><button class="btn" id="print" disabled>${T("طباعة / PDF")}</button></div></section>
      <div id="report-output"></div>`;
  const $ = selector => main.querySelector(selector), out = $("#report-output");
  let currentRows = [], currentColumns = [], currentLabels = [], currentTitle = "";
  const setStatuses = values => { $("#status").innerHTML = '<option value="">كل الحالات</option>' + values.map(v => `<option value="${esc(v)}">${esc(statusLabel(v))}</option>`).join(""); };
  const updateFilters = () => {
    const kind = $("#kind").value;
    $("#side-wrap").hidden = kind !== "settlements";
    $("#project-wrap").hidden = !["settlements", "checks", "purchases", "account_ledger", "project_financials", "aging"].includes(kind);
    $("#status-wrap").hidden = !["checks", "purchases", "settlements"].includes(kind);
    $("#party-wrap").hidden = kind !== "contractor";
    $("#account-wrap").hidden = kind !== "account_ledger";
    $("#treasury-wrap").hidden = kind !== "cash_flow";
    main.querySelectorAll(".date-filter").forEach(e => e.hidden = kind === "inventory");
    if (kind === "aging") $("#from").closest(".date-filter").hidden = true;
    if (kind === "checks") setStatuses(["جديد", "مطبوع", "تم التسليم", "تم الصرف", "ملغي", "مرتد"]);
    if (kind === "purchases") setStatuses(["Draft", "Approved", "Received", "Cancelled"]);
    if (kind === "settlements") setStatuses(["Draft", "PendingApproval", "UnderReview", "TechnicallyApproved", "Approved", "Posted", "Rejected", "Cancelled"]);
    if (!["checks", "purchases", "settlements"].includes(kind)) $("#status").value = "";
  };
  const dates = () => {
    const from = $("#kind").value === "aging" ? "" : $("#from").value, to = $("#to").value;
    if (from && to && from > to) throw new Error(T("تاريخ البداية يجب أن يكون قبل تاريخ النهاية"));
    return { ...(from ? { date_from: from } : {}), ...(to ? { date_to: to } : {}) };
  };
  const formatReport = (title, rows, summary, cols, period = `${$("#from").value || T("كل الفترات")} — ${$("#to").value || T("حتى اليوم")}`) => {
    currentRows = rows; currentColumns = cols.map(([key]) => key); currentLabels = cols.map(([, label]) => T(label)); currentTitle = T(title);
    out.innerHTML = `<section class="panel reports-result"><div class="reports-result-head"><div><h3>${esc(T(title))}</h3><p class="muted">${esc(T(period))}</p></div><span class="tag">${rows.length.toLocaleString(T("Date")==="Date"?"en-US":"ar-EG")} ${T("سجل")}</span></div>${summary}${dataTable(cols === columns.contractor ? "contractor" : Object.keys(columns).find(k => columns[k] === cols) || "settlements", rows)}</section>`;
    $("#csv").disabled = $("#print").disabled = false;
  };
  const run = async () => {
    const kind = $("#kind").value, dateParams = dates();
    if (kind === "overview") {
      const p = new URLSearchParams(dateParams), r = await api(`/api/reports/data?${p}`);
      const summary = kpis([["إجمالي الإيرادات", money(r.kpis.total_revenue)], ["إجمالي المصروفات", money(r.kpis.total_expenses)], ["صافي الربح / الخسارة", money(r.kpis.net_profit)]]);
      currentRows = [...(r.cash_flow_monthly || []).map(x => ({ period: x.month, inflow: x.inflow, outflow: x.outflow, net: Number(x.inflow) - Number(x.outflow) }))];
      currentColumns = ["period", "inflow", "outflow", "net"]; currentLabels = ["الشهر", "الوارد", "المنصرف", "الصافي"]; currentTitle = "المؤشرات المالية";
      out.innerHTML = `<section class="panel reports-result"><h3>المؤشرات المالية</h3><p class="muted">${esc(`${r.date_from} — ${r.date_to}`)}</p>${summary}<div class="reports-charts">${monthlyCashChart(r.cash_flow_monthly)}${expenseBreakdownChart(r.expenses_breakdown)}</div><h4>حركة النقدية الشهرية</h4><div class="tbl-wrap"><table><thead><tr><th>الشهر</th><th>الوارد</th><th>المنصرف</th><th>الصافي</th></tr></thead><tbody>${currentRows.map(x => `<tr><td>${esc(x.period)}</td><td class="num">${money(x.inflow)}</td><td class="num">${money(x.outflow)}</td><td class="num">${money(x.net)}</td></tr>`).join("")}</tbody></table></div><h4>أكثر الحسابات حركة</h4><div class="tbl-wrap"><table><thead><tr><th>الكود</th><th>الحساب</th><th>الرصيد</th><th>الطبيعة</th><th>الحالة</th></tr></thead><tbody>${(r.top_accounts || []).map(x => `<tr><td>${esc(x.account_code)}</td><td>${esc(x.account_name)}</td><td>${money(x.closing_balance)}</td><td>${esc(x.side)}</td><td>${esc(x.status)}</td></tr>`).join("") || '<tr><td colspan="5">لا توجد بيانات</td></tr>'}</tbody></table></div></section>`;
      $("#csv").disabled = $("#print").disabled = false; return;
    }
    if (kind === "account_ledger") {
      if (!$("#account").value) throw new Error("اختر الحساب التفصيلي لعرض كشف الأستاذ");
      const p = new URLSearchParams(dateParams);p.set("account_id", $("#account").value);if($("#project").value)p.set("project_id",$("#project").value);
      const r=await api(`/api/reports/account-ledger?${p}`),a=r.account;
      const summary=kpis([["الحساب",`${a.code} — ${a.name}`],["رصيد أول المدة",money(r.opening_balance)],["إجمالي المدين",money(r.total_debit)],["إجمالي الدائن",money(r.total_credit)],["رصيد آخر المدة",money(r.closing_balance)]]);
      return formatReport("كشف حساب الأستاذ",r.items||[],summary,columns.account_ledger);
    }
    if (kind === "cash_flow") {
      const p=new URLSearchParams(dateParams);if($("#treasury").value)p.set("treasury_account_id",$("#treasury").value);
      const r=await api(`/api/reports/cash-flow?${p}`),s=r.summary;
      const summary=kpis([["عدد الحركات",s.count],["إجمالي المقبوضات",money(s.inflow)],["إجمالي المدفوعات",money(s.outflow)],["صافي الحركة",money(s.net)]]);
      return formatReport("تقرير التدفقات النقدية التفصيلي",r.items||[],summary,columns.cash_flow);
    }
    if (kind === "project_financials") {
      const p=new URLSearchParams(dateParams);if($("#project").value)p.set("project_id",$("#project").value);
      const r=await api(`/api/reports/project-financials?${p}`),s=r.summary;
      const summary=kpis([["عدد المشروعات",s.project_count],["الإيرادات",money(s.revenue)],["المصروفات",money(s.expenses)],["صافي النتيجة",money(s.net)]]);
      return formatReport("التحليل المالي للمشروعات",r.items||[],summary,columns.project_financials);
    }
    if (kind === "aging") {
      const p=new URLSearchParams({as_of:$("#to").value||today()});if($("#project").value)p.set("project_id",$("#project").value);
      const r=await api(`/api/reports/aging?${p}`),s=r.summary;
      const buckets=s.buckets||{};
      const summary=kpis([["مستحق لنا",money(s.receivable)],["مستحق علينا",money(s.payable)],["0–30 يوم",money(buckets["0-30"])],["31–60 يوم",money(buckets["31-60"])],["61–90 يوم",money(buckets["61-90"])],["أكثر من 90 يوم",money(buckets["90+"])]]);
      return formatReport("تقرير أعمار المستحقات",r.items||[],summary,columns.aging,`حتى ${$("#to").value||today()}`);
    }
    if (kind === "settlements") {
      const p = new URLSearchParams(dateParams); if ($("#side").value) p.set("settlement_side", $("#side").value); if ($("#project").value) p.set("project_id", $("#project").value); if ($("#status").value) p.set("status", $("#status").value);
      const r = await api(`/api/reports/settlements?${p}`), summary = kpis([["المستخلصات", r.summary.count], ["قيمة الأعمال", money(r.summary.work_value)], ["الخصومات", money(r.summary.deductions)], ["صافي المستحق", money(r.summary.net_amount)], ["المدفوع", money(r.summary.paid_amount)], ["المتبقي", money(r.summary.remaining_amount)]]);
      return formatReport("كشف العقود والمستخلصات والمدفوعات", r.items || [], summary, columns.settlements);
    }
    if (kind === "checks") {
      const p = new URLSearchParams(dateParams); if ($("#status").value) p.set("status", $("#status").value); if ($("#project").value) p.set("project_id", $("#project").value);
      const r = await api(`/api/reports/checks?${p}`), summary = kpis([["عدد الشيكات", r.summary.count], ["إجمالي القيمة", money(r.summary.amount)], ["المصروف", money(r.summary.paid_amount)], ["غير مربوط بمستخلص", r.summary.unlinked_count]]);
      return formatReport("تقرير الشيكات", r.items || [], summary, columns.checks);
    }
    if (kind === "purchases") {
      const p = new URLSearchParams(dateParams); if ($("#status").value) p.set("status", $("#status").value); if ($("#project").value) p.set("project_id", $("#project").value);
      const r = await api(`/api/reports/purchases?${p}`), summary = kpis([["أوامر الشراء", r.summary.count], ["إجمالي قيمة الأوامر", money(r.summary.total_amount)]]);
      return formatReport("تقرير المشتريات والاستلام", r.items || [], summary, columns.purchases);
    }
    if (kind === "inventory") {
      const r = await api("/api/reports/inventory"), summary = kpis([["عدد الأصناف", r.summary.count], ["أصناف عند حد الطلب أو أقل", r.summary.low_stock_count]]);
      return formatReport("تقرير الأصناف والأرصدة", r.items || [], summary, columns.inventory);
    }
    const party = $("#party").value; if (!party) throw new Error("اختر الطرف المطلوب؛ القائمة تعرض الأسماء كما سُجلت دون توحيدها");
    const p = new URLSearchParams({ counterparty_name: party, ...dateParams }), r = await api(`/api/reports/contractor?${p}`);
    const rows = (r.settlements || []).map(x => ({ ...x, counterparty_name: party }));
    const summary = kpis([["العقود", r.summary.contract_count], ["المستخلصات الفنية", r.summary.technical_count], ["المستخلصات المالية", r.summary.financial_count], ["صافي المستخلصات", money(r.summary.approved_net_settlements)], ["المدفوع", money(r.summary.paid_amount)], ["المتبقي", money(r.summary.outstanding_amount)]]);
    formatReport(`كشف الطرف: ${party}`, rows, summary, columns.contractor);
  };
  const [parties, projects, lookups] = await Promise.all([api("/api/reports/contractors"), api("/api/reports/projects"), api("/api/reports/financial-lookups")]);
  $("#party").innerHTML += (parties.items || []).map(x => `<option value="${esc(x.name)}">${esc(x.name)}</option>`).join("");
  $("#project").innerHTML += (projects.items || []).map(x => `<option value="${x.project_id}">${esc(x.name)}</option>`).join("");
  const accounts = lookups.accounts || [];
  const accountLabel = a => `${a.code} — ${a.name}`;
  const selectAccount = id => { const a = accounts.find(x => x.account_id === id); if (!a) return; $("#account").value = a.account_id; $("#account-search").value = accountLabel(a); $("#account-options").hidden = true; };
  const accountOptions = (term = "", showAll = false) => {
    const box = $("#account-options"), input = $("#account-search"), needle = term.trim().toLocaleLowerCase();
    if (!needle && !showAll) { box.hidden = true; box.innerHTML = ""; return; }
    const matches = needle ? accounts.filter(a => accountLabel(a).toLocaleLowerCase().includes(needle)) : accounts;
    box.innerHTML = (matches.length ? matches.map(a => `<button type="button" class="journal-account-option" role="option" data-report-account-id="${a.account_id}">${esc(accountLabel(a))}</button>`).join("") : '<div class="journal-account-empty">لا يوجد حساب مطابق للاسم أو الكود</div>');
    box.hidden = false;
    const rect = input.getBoundingClientRect(), width = Math.min(Math.max(rect.width, 360), window.innerWidth - 24);
    box.style.width = `${width}px`; box.style.left = `${Math.max(12, Math.min(rect.left, window.innerWidth - width - 12))}px`;
    const height = Math.min(window.innerHeight * .42, 360), below = rect.bottom + height <= window.innerHeight - 12;
    box.style.maxHeight = `${Math.max(54, Math.min(height, below ? window.innerHeight - rect.bottom - 16 : rect.top - 16))}px`;
    box.style.top = `${below ? rect.bottom + 4 : Math.max(12, rect.top - height - 4)}px`;
  };
  $("#account-search").oninput = ev => { $("#account").value = ""; accountOptions(ev.target.value); };
  $("#account-search").onfocus = () => accountOptions("", true);
  $("#account-search").onclick = () => accountOptions("", true);
  $("#account-search").onkeydown = ev => {
    if (ev.key === "ArrowDown") { const first = $("#account-options .journal-account-option"); if (first) { ev.preventDefault(); first.focus(); } }
    if (ev.key === "Enter") { const opts = [...$("#account-options").querySelectorAll(".journal-account-option")], exact = accounts.find(a => accountLabel(a).toLocaleLowerCase() === ev.target.value.trim().toLocaleLowerCase()); if (exact || opts.length === 1) { ev.preventDefault(); selectAccount(exact?.account_id || +opts[0].dataset.reportAccountId); } else if (opts.length) { ev.preventDefault(); opts[0].focus(); } }
    if (ev.key === "Escape") $("#account-options").hidden = true;
  };
  $("#account-options").onmousedown = ev => { const option = ev.target.closest("[data-report-account-id]"); if (!option) return; ev.preventDefault(); selectAccount(+option.dataset.reportAccountId); };
  $("#account-options").onkeydown = ev => { const option = ev.target.closest(".journal-account-option"); if (!option) return; if (ev.key === "ArrowDown" || ev.key === "ArrowUp") { ev.preventDefault(); const opts = [...$("#account-options").querySelectorAll(".journal-account-option")], n = opts.indexOf(option) + (ev.key === "ArrowDown" ? 1 : -1); (opts[n] || (ev.key === "ArrowUp" ? $("#account-search") : opts[0]))?.focus(); } else if (ev.key === "Enter") { ev.preventDefault(); selectAccount(+option.dataset.reportAccountId); $("#account-search").focus(); } else if (ev.key === "Escape") { $("#account-options").hidden = true; $("#account-search").focus(); } };
  main.addEventListener("focusout", ev => { if (ev.target.id === "account-search" || ev.target.closest?.("#account-options")) setTimeout(() => { if (!$("#account-wrap").contains(document.activeElement)) $("#account-options").hidden = true; }, 0); });
  $("#treasury").innerHTML += (lookups.treasury_accounts || []).map(x => `<option value="${x.treasury_account_id}">${esc(x.name)} — ${esc(x.currency)}</option>`).join("");
  $("#kind").onchange = updateFilters; updateFilters();
  main.querySelectorAll("[data-select]").forEach(button => button.onclick = () => { $("#kind").value = button.dataset.select; updateFilters(); if (button.dataset.select !== "contractor") safe(run)(); });
  $("#run").onclick = safe(run); $("#from").onchange = $("#to").onchange = () => {};
  $("#print").onclick = () => window.print();
  $("#csv").onclick = () => currentRows.length && csvDownload("report.csv", currentColumns, currentLabels, currentRows);
  await safe(run)();
}
