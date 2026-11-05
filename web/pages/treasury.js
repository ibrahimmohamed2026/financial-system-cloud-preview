import { esc, money, toast, safe, formDialog, today, errText } from "../ui.js";
const CODE = { "cib-egp": "BankCibEgp", "cash-usd": "CashUsd", "cash-egp": "CashEgp", "cairo-egp": "BankCairoEgp", "hdb-usd": "BankHdbUsd", "hdb-egp": "BankHdbEgp", "cib-usd": "BankCibUsd" };

export async function render(main, { api, auth, route }) {
  const SC = CODE[route.split("/").pop()], can = a => auth.can(SC, a), base = "/treasury/" + SC;
  const info = await api(base + "/account");
  if (!info.account) return setup(info);
  const acc = info.account;
  const projs = await api("/projects/lookup").catch(() => []);
  main.innerHTML = `<h3 style="margin-top:0">${esc(acc.name_ar)} <small class="muted">${esc(acc.currency_code)} — ${esc(acc.gl_account)}</small> ${auth.can(SC,"Edit") || auth.can(SC,"Add") ? '<button class="btn sm" id="edit-gl-link">تصحيح ربط شجرة الحسابات</button>' : ""}</h3>
    <div class="toolbar"><div class="w" style="width:150px"><label>من</label><input type="date" id="df"></div><div class="w" style="width:150px"><label>إلى</label><input type="date" id="dt"></div>
    <div class="grow"><label>بحث</label><input id="q"></div>${can("Add") ? '<button class="btn primary" id="add">+ حركة</button>' : ""}</div>
    <div id="sum" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>التاريخ</th><th>وارد</th><th>منصرف</th><th>الرصيد</th><th>البيان</th><th>رقم الإذن</th><th>الحالة</th><th>المستلم</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s); let items = [];
  $("#edit-gl-link")?.addEventListener("click", safe(() => setup(info, true)));
  const load = async () => {
    const p = new URLSearchParams({ limit: 500 }); for (const [k, id] of [["date_from", "#df"], ["date_to", "#dt"], ["q", "#q"]]) if ($(id).value.trim()) p.set(k, $(id).value.trim());
    const r = await api(base + "/transactions?" + p); items = r.items;
    $("#sum").innerHTML = `رصيد أول الفترة: <b>${money(r.opening_balance) === "-" ? "0.00" : money(r.opening_balance)}</b> — وارد: <b>${money(r.total_inflow)}</b> — منصرف: <b>${money(r.total_outflow)}</b> — الرصيد الحالي: <b>${money(r.closing_balance) === "-" ? "0.00" : money(r.closing_balance)}</b>${r.total > 500 ? " — (معروض أول 500 حركة)" : ""}`;
    $("#rows").innerHTML = items.map(t => `<tr><td>${t.transaction_date}</td><td class="num">${money(t.inflow)}</td><td class="num">${money(t.outflow)}</td><td class="num">${money(t.balance) === "-" ? "0.00" : money(t.balance)}</td>
      <td>${esc(t.description)}</td><td>${esc(t.voucher_no)}</td><td>${esc(t.status)}</td><td>${esc(t.recipient_name)}</td>
      <td>${t.locked ? '<span class="tag">مرتبط بقيد</span>' : `${can("Edit") ? `<button class="btn sm" data-e="${t.transaction_id}">تعديل</button> ` : ""}${can("Delete") ? `<button class="btn sm danger" data-d="${t.transaction_id}">حذف</button>` : ""}`}</td></tr>`).join("")
      || `<tr><td colspan="9" class="muted">لا توجد حركات</td></tr>`;
  };
  const form = t => formDialog({
    title: t ? "تعديل حركة" : "حركة جديدة", values: t ? { ...t, inflow: +t.inflow || "", outflow: +t.outflow || "", project_id: t.project_id ?? "" } : { transaction_date: today() },
    fields: [{ name: "transaction_date", label: "التاريخ", type: "date", required: true }, { name: "voucher_no", label: "رقم الإذن" },
      { name: "inflow", label: "وارد", type: "number", step: "0.01", min: 0 }, { name: "outflow", label: "منصرف", type: "number", step: "0.01", min: 0 },
      { name: "description", label: "البيان", full: true }, { name: "status", label: "الحالة (مثال: تمويل)" }, { name: "recipient_name", label: "المستلم" },
      { name: "project_id", label: "مركز التكلفة", type: "select", optional: true, options: projs.map(p => [p.project_id, p.name_ar]), full: true }],
    onSubmit: async v => {
      await api(t ? `${base}/transactions/${t.transaction_id}` : base + "/transactions", { method: t ? "PUT" : "POST", json: {
        transaction_date: v.transaction_date, inflow: v.inflow || "0", outflow: v.outflow || "0", description: v.description || null, voucher_no: v.voucher_no || null,
        status: v.status || null, recipient_name: v.recipient_name || null, project_id: v.project_id ? +v.project_id : null } });
      toast("تم الحفظ"); await load();
    } });
  for (const id of ["#df", "#dt"]) $(id).onchange = safe(load);
  let tm; $("#q").oninput = () => { clearTimeout(tm); tm = setTimeout(safe(load), 300); };
  if (can("Add")) $("#add").onclick = () => form(null);
  $("#rows").onclick = safe(async ev => {
    const e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]");
    if (e) form(items.find(x => x.transaction_id == e.dataset.e));
    if (d && confirm("حذف الحركة؟")) { await api(`${base}/transactions/${d.dataset.d}`, { method: "DELETE" }); toast("تم الحذف"); await load(); }
  });
  await load();

  function setup(info, editExisting = false) {
    if (editExisting) {
      api(base + "/gl-accounts").then(gl => formDialog({
        title: `تصحيح ربط شجرة الحسابات — ${esc(info.account.name_ar)}`,
        values: { gl: String(info.account.gl_account_id) },
        fields: [{ name: "gl", label: "حساب الأستاذ (نقدية بالصندوق والبنوك)", type: "select", searchable: true,
          options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => {
          await api(base + "/account", { method: "PUT", json: { gl_account_id: Number(v.gl) } });
          toast("تم تصحيح ربط حساب البنك بشجرة الحسابات");
          main.innerHTML = ""; await render(main, { api, auth, route });
        }
      })).catch(e => toast(errText(e)));
      return;
    }
    main.innerHTML = `<div class="sec"><h3>تجهيز الحساب</h3><div style="padding:16px"><p class="muted">الشاشة دي لسه مش مربوطة بحساب خزينة/بنك. عند التسجيل تُحفظ البيانات في قاعدة بيانات النظام على الخادم، وتُربط بحساب فرعي نشط من شجرة الحسابات؛ لا تُحفظ كبيانات محلية في المتصفح.</p>${can("Add") ? '<button class="btn primary" id="go">تسجيل الحساب</button>' : "<p>اطلب من المسؤول تسجيل الحساب.</p>"}</div></div>`;
    main.querySelector("#go")?.addEventListener("click", safe(async () => {
      const gl = await api(base + "/gl-accounts"); const byLabel = Object.fromEntries(gl.map(g => [g.label, g.account_id]));
      const dlg = formDialog({ title: "تسجيل حساب الخزينة/البنك", values: { account_type: info.default_type, currency_code: info.default_currency },
        fields: [{ name: "name_ar", label: "الاسم", required: true, full: true },
          { name: "account_type", label: "النوع", type: "select", options: [["Bank", "بنك"], ["Cash", "خزينة"]] }, { name: "currency_code", label: "العملة", required: true },
          { name: "bank_account_number", label: "رقم الحساب البنكي" }, { name: "gl", label: "حساب الأستاذ (نقدية بالصندوق والبنوك)", type: "select", searchable: true,
            options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => { const id = Number(v.gl) || byLabel[v.gl]; if (!id) throw new Error("اختار حساب الأستاذ من القايمة");
          await api(base + "/account", { method: "POST", json: { name_ar: v.name_ar, account_type: v.account_type, currency_code: v.currency_code.toUpperCase(), bank_account_number: v.bank_account_number || null, gl_account_id: id } });
          toast("تم التسجيل"); main.innerHTML = ""; await render(main, { api, auth, route }); } });
    }));
  }
}
