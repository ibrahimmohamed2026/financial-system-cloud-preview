import { esc, money, toast, safe, formDialog, today, errText } from "../ui.js";
import { translate as tr } from "../i18n.js";
const CODE = { "cib-egp": "BankCibEgp", "cash-usd": "CashUsd", "cash-egp": "CashEgp", "cairo-egp": "BankCairoEgp", "hdb-usd": "BankHdbUsd", "hdb-egp": "BankHdbEgp", "cib-usd": "BankCibUsd" };

export async function render(main, { api, auth, route }) {
  const SC = CODE[route.split("/").pop()], can = a => auth.can(SC, a), base = "/treasury/" + SC;
  const info = await api(base + "/account");
  if (!info.account) return setup(info);
  const acc = info.account;
  const projs = await api("/projects/lookup").catch(() => []);
  main.innerHTML = `<h3 style="margin-top:0">${esc(localStorage.getItem("fs_lang")==="en"?(acc.name_en||acc.name_ar):acc.name_ar)} <small class="muted">${esc(acc.currency_code)} — ${esc(acc.gl_account)}</small> ${auth.can(SC,"Edit") || auth.can(SC,"Add") ? `<button class="btn sm" id="edit-gl-link">${tr("تصحيح ربط شجرة الحسابات","Fix chart of accounts link")}</button>` : ""}</h3>
    <div class="toolbar"><div class="w" style="width:150px"><label>${tr("من","From")}</label><input type="date" id="df"></div><div class="w" style="width:150px"><label>${tr("إلى","To")}</label><input type="date" id="dt"></div>
    <div class="grow"><label>${tr("بحث","Search")}</label><input id="q"></div>${can("Add") ? `<button class="btn primary" id="add">+ ${tr("حركة","Transaction")}</button>` : ""}</div>
    <div id="sum" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>${tr("التاريخ","Date")}</th><th>${tr("وارد","Inflow")}</th><th>${tr("منصرف","Outflow")}</th><th>${tr("الرصيد","Balance")}</th><th>${tr("البيان","Description")}</th>${acc.currency_code === "USD" ? `<th>${tr("سعر الصرف","Exchange rate")}</th>` : ""}<th>${tr("رقم الإذن","Voucher No.")}</th><th>${tr("الحالة","Status")}</th><th>${tr("المستلم","Recipient")}</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s); let items = [];
  $("#edit-gl-link")?.addEventListener("click", safe(() => setup(info, true)));
  const load = async () => {
    const p = new URLSearchParams({ limit: 500 }); for (const [k, id] of [["date_from", "#df"], ["date_to", "#dt"], ["q", "#q"]]) if ($(id).value.trim()) p.set(k, $(id).value.trim());
    const r = await api(base + "/transactions?" + p); items = r.items;
    $("#sum").innerHTML = `${tr("رصيد أول الفترة:","Opening balance:")} <b>${money(r.opening_balance) === "-" ? "0.00" : money(r.opening_balance)}</b> — ${tr("وارد:","Inflow:")} <b>${money(r.total_inflow)}</b> — ${tr("منصرف:","Outflow:")} <b>${money(r.total_outflow)}</b> — ${tr("الرصيد الحالي:","Current balance:")} <b>${money(r.closing_balance) === "-" ? "0.00" : money(r.closing_balance)}</b>${r.total > 500 ? ` — (${tr("معروض أول 500 حركة","First 500 transactions shown")})` : ""}`;
    $("#rows").innerHTML = items.map(t => `<tr><td>${t.transaction_date}</td><td class="num">${money(t.inflow)}</td><td class="num">${money(t.outflow)}</td><td class="num">${money(t.balance) === "-" ? "0.00" : money(t.balance)}</td>
      <td>${esc(t.description)}</td>${acc.currency_code === "USD" ? `<td class="num">${t.exchange_rate ? Number(t.exchange_rate).toFixed(6) : "—"}</td>` : ""}<td>${esc(t.voucher_no)}</td><td>${esc(t.status)}</td><td>${esc(t.recipient_name)}</td>
      <td>${t.locked ? `<span class="tag">${tr("مرتبط بقيد","Linked to journal entry")}</span>` : `${can("Edit") ? `<button class="btn sm" data-e="${t.transaction_id}">${tr("تعديل","Edit")}</button> ` : ""}${can("Delete") ? `<button class="btn sm danger" data-d="${t.transaction_id}">${tr("حذف","Delete")}</button>` : ""}`}</td></tr>`).join("")
      || `<tr><td colspan="${acc.currency_code === "USD" ? 10 : 9}" class="muted">${tr("لا توجد حركات","No transactions")}</td></tr>`;
  };
  const form = async t => {
    const initialDirection = t ? (+t.inflow > 0 ? "inflow" : "outflow") : "inflow";
    const initialCounterparts = acc.currency_code === "USD"
      ? await api(base + "/counterpart-accounts?direction=" + initialDirection).catch(() => []) : [];
    return formDialog({
    title: t ? tr("تعديل حركة","Edit transaction") : tr("حركة جديدة","New transaction"), values: t ? { ...t, inflow: +t.inflow || "", outflow: +t.outflow || "", project_id: t.project_id ?? "" } : { transaction_date: today() },
    fields: [{ name: "transaction_date", label: tr("التاريخ","Date"), type: "date", required: true },
      ...(acc.currency_code === "USD" ? [
        { name: "exchange_rate", label: tr("سعر الدولار مقابل الجنيه","USD exchange rate to EGP"), type: "number", step: "0.000001", min: "0.000001", required: true },
        { name: "counterpart_account_id", label: tr("حساب الطرف المقابل","Counterpart account"), type: "select", searchable: true, options: initialCounterparts.map(a => [String(a.account_id), a.label]), required: true, full: true }
      ] : []),
      { name: "voucher_no", label: tr("رقم الإذن","Voucher No.") }, { name: "inflow", label: tr("وارد","Inflow"), type: "number", step: "0.01", min: 0 }, { name: "outflow", label: tr("منصرف","Outflow"), type: "number", step: "0.01", min: 0 },
      { name: "description", label: tr("البيان","Description"), full: true }, { name: "status", label: tr("الحالة (مثال: تمويل)","Status (e.g. Funding)") }, { name: "recipient_name", label: tr("المستلم","Recipient") },
      { name: "project_id", label: tr("مركز التكلفة","Cost center"), type: "select", optional: true, options: projs.map(p => [p.project_id, p.name_ar]), full: true }],
    onSubmit: async v => {
      const saved = await api(t ? `${base}/transactions/${t.transaction_id}` : base + "/transactions", { method: t ? "PUT" : "POST", json: {
        transaction_date: v.transaction_date, inflow: v.inflow || "0", outflow: v.outflow || "0", description: v.description || null, voucher_no: v.voucher_no || null,
        status: v.status || null, recipient_name: v.recipient_name || null, project_id: v.project_id ? +v.project_id : null,
        exchange_rate: acc.currency_code === "USD" ? v.exchange_rate : null,
        counterpart_account_id: acc.currency_code === "USD" ? Number(v.counterpart_account_id) : null } });
      toast(acc.currency_code === "USD" ? `${tr("تم الحفظ وإنشاء القيد كمسودة","Saved; draft journal created")}: ${saved.journal_entry_no || "—"}` : tr("تم الحفظ","Saved")); await load();
    },
    onOpen: (dlg, formEl) => {
      if (acc.currency_code !== "USD") return;
      const directionSelect = formEl.elements.namedItem("counterpart_account_id");
      const refreshCounterparts = async direction => {
        const selected = directionSelect.value;
        directionSelect.disabled = true;
        try {
          const options = await api(base + "/counterpart-accounts?direction=" + direction);
          directionSelect.innerHTML = '<option value="">—</option>' + options.map(a =>
            `<option value="${String(a.account_id)}">${esc(a.label)}</option>`).join("");
          if (options.some(a => String(a.account_id) === selected)) directionSelect.value = selected;
        } finally { directionSelect.disabled = false; }
      };
      const inflow = formEl.elements.namedItem("inflow"), outflow = formEl.elements.namedItem("outflow");
      inflow.addEventListener("input", () => { if (+inflow.value > 0) refreshCounterparts("inflow"); });
      outflow.addEventListener("input", () => { if (+outflow.value > 0) refreshCounterparts("outflow"); });
      const sideHint = document.createElement("small");
      sideHint.className = "muted";
      sideHint.textContent = (+inflow.value > 0 || (!+outflow.value && !+inflow.value))
        ? "الوارد: حساب الطرف المقابل يظهر في الجانب الدائن من القيد."
        : "المنصرف: حساب الطرف المقابل يظهر في الجانب المدين من القيد.";
      directionSelect.parentElement.appendChild(sideHint);
      const updateHint = () => { sideHint.textContent = +inflow.value > 0
        ? "الوارد: حساب الطرف المقابل يظهر في الجانب الدائن من القيد."
        : "المنصرف: حساب الطرف المقابل يظهر في الجانب المدين من القيد."; };
      inflow.addEventListener("input", updateHint); outflow.addEventListener("input", updateHint);
    } });
  };
  for (const id of ["#df", "#dt"]) $(id).onchange = safe(load);
  let tm; $("#q").oninput = () => { clearTimeout(tm); tm = setTimeout(safe(load), 300); };
  if (can("Add")) $("#add").onclick = safe(() => form(null));
  $("#rows").onclick = safe(async ev => {
    const e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]");
    if (e) await form(items.find(x => x.transaction_id == e.dataset.e));
    if (d && confirm(tr("حذف الحركة؟","Delete this transaction?"))) { await api(`${base}/transactions/${d.dataset.d}`, { method: "DELETE" }); toast(tr("تم الحذف","Deleted")); await load(); }
  });
  await load();

  function setup(info, editExisting = false) {
    if (editExisting) {
      api(base + "/gl-accounts").then(gl => formDialog({
        title: `${tr("تصحيح ربط شجرة الحسابات","Fix chart of accounts link")} — ${esc(info.account.name_en||info.account.name_ar)}`,
        values: { gl: String(info.account.gl_account_id) },
        fields: [{ name: "gl", label: tr("حساب الأستاذ (نقدية بالصندوق والبنوك)","Ledger account (cash on hand and at banks)"), type: "select", searchable: true,
          options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => {
          await api(base + "/account", { method: "PUT", json: { gl_account_id: Number(v.gl) } });
          toast(tr("تم تصحيح ربط حساب البنك بشجرة الحسابات","Bank account link updated"));
          main.innerHTML = ""; await render(main, { api, auth, route });
        }
      })).catch(e => toast(errText(e)));
      return;
    }
    main.innerHTML = `<div class="sec"><h3>${tr("تجهيز الحساب","Account setup")}</h3><div style="padding:16px"><p class="muted">${tr("الشاشة دي لسه مش مربوطة بحساب خزينة/بنك. عند التسجيل تُحفظ البيانات في قاعدة بيانات النظام على الخادم، وتُربط بحساب فرعي نشط من شجرة الحسابات؛ لا تُحفظ كبيانات محلية في المتصفح.","This screen is not yet linked to a treasury/bank account. Registration saves data to the server database and links it to an active leaf account in the chart of accounts; data is not stored locally in the browser.")}</p>${can("Add") ? `<button class="btn primary" id="go">${tr("تسجيل الحساب","Register account")}</button>` : `<p>${tr("اطلب من المسؤول تسجيل الحساب.","Ask an administrator to register the account.")}</p>`}</div></div>`;
    main.querySelector("#go")?.addEventListener("click", safe(async () => {
      const gl = await api(base + "/gl-accounts"); const byLabel = Object.fromEntries(gl.map(g => [g.label, g.account_id]));
      const isUsdCash = SC === "CashUsd";
      const dlg = formDialog({ title: tr("تسجيل حساب الخزينة/البنك","Register treasury/bank account"),
        values: { name_ar: isUsdCash ? "خزينة الدولار" : "", account_type: info.default_type, currency_code: info.default_currency },
        fields: [{ name: "name_ar", label: tr("الاسم","Name"), required: true, full: true },
          ...(isUsdCash ? [] : [
            { name: "account_type", label: tr("النوع","Type"), type: "select", options: [["Bank", tr("بنك","Bank")], ["Cash", tr("خزينة","Cash")]] },
            { name: "currency_code", label: tr("العملة","Currency"), required: true },
            { name: "bank_account_number", label: tr("رقم الحساب البنكي","Bank account number") }
          ]),
          { name: "gl", label: tr("حساب الأستاذ (نقدية بالصندوق والبنوك)","Ledger account (cash on hand and at banks)"), type: "select", searchable: true,
            options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => { const id = Number(v.gl) || byLabel[v.gl]; if (!id) throw new Error(tr("اختار حساب الأستاذ من القايمة","Select a ledger account from the list"));
          await api(base + "/account", { method: "POST", json: { name_ar: v.name_ar, account_type: isUsdCash ? "Cash" : v.account_type, currency_code: isUsdCash ? "USD" : v.currency_code.toUpperCase(), bank_account_number: isUsdCash ? null : (v.bank_account_number || null), gl_account_id: id } });
          toast(tr("تم التسجيل","Registered")); main.innerHTML = ""; await render(main, { api, auth, route }); } });
    }));
  }
}
