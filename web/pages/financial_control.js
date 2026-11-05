import { esc, safe, toast } from "../ui.js";
import { downloadFile } from "../api.js";

const fmt = v => Number(v || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const labelSide = v => v === "Customer" ? "عميل / مستحقات" : "مقاول باطن / مستحقات";
const qs = main => {
  const p = new URLSearchParams();
  if (main.querySelector("#fc-from").value) p.set("date_from", main.querySelector("#fc-from").value);
  if (main.querySelector("#fc-to").value) p.set("date_to", main.querySelector("#fc-to").value);
  return p.toString();
};
const table = (headers, rows, empty = "لا توجد بيانات") => \`<div class="tbl-wrap"><table><thead><tr>\${headers.map(x => \`<th>\${x}</th>\`).join("")}</tr></thead><tbody>\${rows.length ? rows.join("") : \`<tr><td colspan="\${headers.length}" class="empty">\${empty}</td></tr>\`}</tbody></table></div>\`;
const card = (title, value, hint) => \`<article class="card" style="padding:16px"><small class="muted">\${title}</small><h2 style="margin:8px 0;direction:ltr;text-align:right">\${value}</h2><small class="muted">\${hint || ""}</small></article>\`;

export async function render(main, { api }) {
  main.innerHTML = \`
  <div class="fc-page" dir="rtl">
    <section class="card" style="padding:18px;margin-bottom:14px">
      <div style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap">
        <div><h2 style="margin:0 0 6px">لوحة الرقابة المالية</h2><p class="muted" style="margin:0">مؤشرات العقود والمستخلصات والمدفوعات والقيود — عرض فقط دون تعديل البيانات.</p></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn" id="fc-xlsx">تصدير Excel</button><button class="btn" id="fc-pdf">تصدير PDF</button><button class="btn primary" id="fc-refresh">تحديث</button>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:end;flex-wrap:wrap;margin-top:16px">
        <label>من تاريخ <input type="date" id="fc-from"></label>
        <label>إلى تاريخ <input type="date" id="fc-to"></label>
        <button class="btn" id="fc-apply">تطبيق الفترة</button>
      </div>
      <p class="muted" id="fc-period" style="margin:10px 0 0"></p>
    </section>
    <div id="fc-kpis" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-bottom:14px"></div>
    <section class="card" style="padding:16px;margin-bottom:14px">
      <h3>أعمار المستحقات</h3><p class="muted">الرصيد المتبقي للمستخلصات المعتمدة والمرحّلة. العمر محسوب من تاريخ المستخلص، ويُعد متأخراً بعد 30 يوماً.</p>
      <div id="fc-aging-buckets" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:12px 0"></div>
      <div id="fc-aging"></div>
    </section>
    <section class="card" style="padding:16px;margin-bottom:14px">
      <h3>تتبع دورة المستخلص</h3><p class="muted">من المستخلص الفني حتى الاعتماد المالي والترحيل والصرف.</p><div id="fc-lifecycle"></div>
    </section>
    <section class="card" style="padding:16px;margin-bottom:14px">
      <h3>مركز الإشعارات</h3><p class="muted">المستخلصات المنتظرة والشيكات التي يحين استحقاقها خلال 30 يوماً أو المتأخرة.</p><div id="fc-notifications"></div>
    </section>
    <section class="card" style="padding:16px">
      <h3>تقرير حركة الحساب</h3>
      <div style="display:flex;gap:8px;align-items:end;flex-wrap:wrap;margin:12px 0">
        <label style="min-width:260px;flex:1">الحساب <select id="fc-account" style="width:100%"><option value="">اختر الحساب</option></select></label>
        <button class="btn primary" id="fc-account-run">عرض الحركة</button>
      </div>
      <div id="fc-account-result"><p class="muted">اختر حساباً لعرض رصيد أول المدة والحركة المدينة والدائنة ورصيد آخر المدة.</p></div>
    </section>
  </div>\`;
  const $ = s => main.querySelector(s);
  let current = null;
  const params = () => qs(main);
  const get = async path => api(path);
  const load = async () => {
    const suffix = params();
    current = await get("/api/financial-control/overview" + (suffix ? "?" + suffix : ""));
    const k = current.kpis;
    $("#fc-period").textContent = "الفترة: " + current.date_from + " إلى " + current.date_to;
    $("#fc-kpis").innerHTML = [
      card("إجمالي العقود", fmt(k.contracts_value), k.contracts_count + " عقد — إجمالي القيمة التعاقدية"),
      card("صافي المستخلصات", fmt(k.settlements_net), k.settlements_count + " مستخلص ضمن الفترة"),
      card("المدفوع", fmt(k.paid_amount), "حركات خزينة مرتبطة بالمستخلصات"),
      card("المتبقي", fmt(k.outstanding_amount), "أرصدة مستحقات معتمدة ومرحّلة"),
      card("المتأخر", fmt(k.overdue_amount), "أكثر من 30 يوماً من تاريخ المستخلص"),
      card("القيود المرحلة", fmt(k.posted_entries_debit), k.posted_entries_count + " قيد مرحّل")
    ].join("");
    $("#fc-aging-buckets").innerHTML = current.aging.buckets.map(x => card(x.label + " يوم", fmt(x.amount), "الرصيد المتبقي")).join("");
    $("#fc-aging").innerHTML = table(
      ["المستخلص","العقد","الطرف","النوع","التاريخ","العمر","الصافي","المدفوع","المتبقي","الحالة"],
      current.aging.items.map(x => \`<tr><td>\${esc(x.settlement_no)}</td><td>\${esc(x.contract_no)}</td><td>\${esc(x.counterparty)}</td><td>\${esc(labelSide(x.side))}</td><td>\${esc(x.settlement_date)}</td><td>\${x.age_days}</td><td>\${fmt(x.net_amount)}</td><td>\${fmt(x.paid_amount)}</td><td><b>\${fmt(x.outstanding_amount)}</b></td><td>\${esc(x.status)}</td></tr>\`));
    $("#fc-lifecycle").innerHTML = table(
      ["فني","مالي","العقد","الطرف","تاريخ الإنشاء","الحالة الفنية","الحالة المالية","القيد","الصافي","المدفوع"],
      current.lifecycle.map(x => \`<tr><td>\${esc(x.technical_no || "—")}</td><td>\${esc(x.financial_no || "—")}</td><td>\${esc(x.contract_no)}</td><td>\${esc(x.counterparty)}</td><td>\${esc(x.created)}</td><td>\${esc(x.technical_status)}</td><td>\${esc(x.financial_status)}</td><td>\${esc(x.journal_status)}</td><td>\${fmt(x.net_amount)}</td><td>\${fmt(x.paid_amount)}</td></tr>\`));
    $("#fc-notifications").innerHTML = table(
      ["الأهمية","النوع","المرجع","الطرف / الحساب","التاريخ","التفاصيل"],
      current.notifications.map(x => \`<tr><td>\${x.severity === "danger" ? "متأخر" : "متابعة"}</td><td>\${esc(x.type)}</td><td>\${esc(x.reference)}</td><td>\${esc(x.party)}</td><td>\${esc(x.date)}</td><td>\${esc(x.message)}</td></tr>\`));
    const selected = $("#fc-account").value;
    $("#fc-account").innerHTML = '<option value="">اختر الحساب</option>' + current.accounts.map(a => \`<option value="\${a.account_id}">\${esc(a.code)} — \${esc(a.name)}</option>\`).join("");
    $("#fc-account").value = selected;
  };
  const showAccount = async () => {
    const id = $("#fc-account").value;
    if (!id) { toast("اختر الحساب أولاً"); return; }
    const p = new URLSearchParams(params());
    p.set("account_id", id);
    const d = await get("/api/financial-control/account-statement?" + p.toString());
    $("#fc-account-result").innerHTML = \`
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin:10px 0">
        \${card("رصيد أول المدة", fmt(d.opening_balance), d.account.code + " — " + esc(d.account.name))}
        \${card("إجمالي المدين", fmt(d.total_debit), "خلال الفترة")}
        \${card("إجمالي الدائن", fmt(d.total_credit), "خلال الفترة")}
        \${card("رصيد آخر المدة", fmt(d.closing_balance), "مدين موجب / دائن سالب")}
      </div>
      \${table(["التاريخ","رقم القيد","البيان","مدين","دائن","الرصيد الجاري"], d.items.map(x => \`<tr><td>\${esc(x.date)}</td><td>\${esc(x.entry_no)}</td><td>\${esc(x.description)}</td><td>\${fmt(x.debit)}</td><td>\${fmt(x.credit)}</td><td>\${fmt(x.balance)}</td></tr>\`))}
      \${d.truncated ? '<p class="muted">تم عرض أول 5000 حركة فقط.</p>' : ""}\`;
  };
  $("#fc-refresh").onclick = safe(load);
  $("#fc-apply").onclick = safe(async () => { await load(); $("#fc-account-result").innerHTML = '<p class="muted">اختر حساباً لعرض الحركة.</p>'; });
  const exportParams = () => { const p = new URLSearchParams(params()); if ($("#fc-account").value) p.set("account_id", $("#fc-account").value); return p.toString(); };
  $("#fc-xlsx").onclick = () => downloadFile("/api/financial-control/export.xlsx" + (exportParams() ? "?" + exportParams() : ""), "financial-control.xlsx").catch(e => toast(e.message || String(e)));
  $("#fc-pdf").onclick = () => downloadFile("/api/financial-control/export.pdf" + (exportParams() ? "?" + exportParams() : ""), "financial-control.pdf").catch(e => toast(e.message || String(e)));
  $("#fc-account-run").onclick = safe(showAccount);
  await safe(load)();
}
