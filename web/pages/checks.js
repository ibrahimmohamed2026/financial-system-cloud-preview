import { esc, money, today, toast, safe, formDialog } from "../ui.js";
import { downloadFile } from "../api.js";
import { openPrintDialog } from "../check_print.js";
import { translate as tr } from "../i18n.js";
const CODE = { "cib": "ChecksCib", "cairo-egp": "ChecksCairoEgp", "cairo-usd": "ChecksCairoUsd" };
const statusLabel = s => ({ "جديد":tr("جديد","New"), "مطبوعة":tr("مطبوعة","Printed"), "صادرة":tr("صادرة","Issued"), "ملغي":tr("ملغي","Cancelled"), "مرتد":tr("مرتد","Returned"), "مسلّم":tr("مسلّم","Delivered") }[s] || s || "—");
export async function render(main, { api, auth, route }) {
  const SC = CODE[route.split("/").pop()], can = a => auth.can(SC, a), base = "/checks/" + SC;
  const info = await api(base + "/account");
  if (!info.account) {
    main.innerHTML = `<div class="sec"><h3>${tr("إعداد دفتر الشيكات","Cheque book setup")}</h3><div style="padding:16px"><p class="muted">${tr("دفتر الشيكات ده غير مربوط بحساب بنك حتى الآن. اختَر «ربط بحساب بنك» لربطه بحساب البنك الصحيح قبل تسجيل الشيكات.","This cheque book is not linked to a bank account yet. Choose “Link bank account” before registering cheques.")}</p>${can("Add") ? `<button class="btn primary" id="go">${tr('ربط بحساب بنك','Link bank account')}</button>` : ""}</div></div>`;
    main.querySelector("#go")?.addEventListener("click", () => formDialog({ title: tr("ربط بحساب بنك","Link bank account"), fields: [{ name: "id", label: tr("حساب البنك المتاح لهذا الدفتر","Bank account available for this book"), type: "select", required: true, full: true, options: info.available_banks.map(b => [b.treasury_account_id, `${b.name_ar} (${b.currency_code})`]) }],
      onSubmit: async v => { await api(base + "/account", { method: "POST", json: { treasury_account_id: +v.id } }); toast(tr("تم الربط","Linked")); await render(main, { api, auth, route }); } }));
    if (!info.available_banks.length) main.querySelector("p").insertAdjacentHTML("afterend", `<p class="muted">${tr('مفيش حسابات بنوك متاحة — سجّل الحساب الأول من شاشات البنوك.','No bank accounts are available. Register a bank account first.')}</p>`);
    return;
  }
  const [bens, projs, settlements] = await Promise.all([api("/checks/beneficiaries"), api("/checks/projects"), can("Add") ? api("/checks/payable-settlements") : Promise.resolve({ items: [] })]);
  const payableSettlements = settlements.items || [];
  main.innerHTML = `<h3 style="margin-top:0">${esc(info.account.name_ar)} <small class="muted">${esc(info.account.currency_code)}</small></h3>
    <div class="toolbar">
      <div class="w"><label>${tr("رقم الحساب (تطابق كامل)","Account number (exact match)")}</label><input id="acc" inputmode="numeric" autocomplete="off" placeholder="${tr("مثال: 110205","e.g. 110205")}"></div>
      <div class="w"><label>${tr("رقم الشيك","Cheque number")}</label><input id="no" inputmode="numeric" autocomplete="off"></div>
      <div class="w"><label>${tr("المستفيد","Beneficiary")}</label><input id="ben" autocomplete="off"></div>
      <div class="w"><label>${tr("بحث عام (بيان / أمر شراء)","General search (description / purchase order)")}</label><input id="q" autocomplete="off"></div>
      <div class="w" style="width:150px"><label>${tr("الحالة","Status")}</label><select id="s"><option value="">${tr("الكل","All")}</option></select></div>
      <div class="w" id="bankw" hidden><label>${tr("البنك","Bank")}</label><select id="bank"><option value="">${tr("كل البنوك","All banks")}</option></select></div>
      <label style="display:flex;gap:6px;align-items:center;margin:0 4px 8px"><input type="checkbox" id="all" style="width:auto"> ${tr("كل الدفاتر","All books")}</label>
      <button class="btn" id="clr">${tr("مسح الفلاتر","Clear filters")}</button>
      ${can("Print") ? `<button class="btn" id="xl">${tr('تصدير Excel','Export Excel')}</button>` : ""}
      ${can("Add") ? `<button class="btn primary" id="add">+ ${tr('شيك','Cheque')}</button><button class="btn" id="nb">+ ${tr('مستفيد','Beneficiary')}</button>` : ""}</div>
    <div id="sum" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>${tr("الدفتر","Book")}</th><th>#</th><th>${tr("رقم الشيك","Cheque No.")}</th><th>${tr("التاريخ","Date")}</th><th class="bk" hidden>${tr("البنك","Bank")}</th><th>${tr("رقم حساب البنك","Bank account No.")}</th><th>${tr("المستفيد","Beneficiary")}</th><th>${tr("من حساب → إلى حساب","From account → To account")}</th><th>${tr("المبلغ","Amount")}</th><th>${tr("التفقيط","Amount in words")}</th><th>${tr("أمر الشراء","Purchase order")}</th><th>${tr("المشروع","Project")}</th><th>${tr("المستخلص المالي","Financial statement")}</th><th>${tr("البيان","Description")}</th><th>${tr("الحالة","Status")}</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s); let items = [], ready = false, screenOf = {}, curOf = {};
  const params = () => {
    const p = new URLSearchParams({ limit: 500 });
    if (!$("#all").checked) p.set("screen", SC);
    for (const [k, id] of [["account_no", "#acc"], ["check_no", "#no"], ["beneficiary", "#ben"], ["q", "#q"], ["status", "#s"], ["bank_id", "#bank"]]) {
      const v = $(id).value.trim(); if (v && (k !== "bank_id" || $("#all").checked)) p.set(k, v);
    }
    return p;
  };
  const sumTxt = r => r.summary.map(s => `${esc(s.status)}${r.banks.length > 1 ? " " + esc(s.currency_code) : ""}: <b>${s.count}</b> (${money(s.amount) === "-" ? "0.00" : money(s.amount)})`).join(" — ");
  const load = async () => {
    const all = $("#all").checked, r = await api("/checks/search?" + params());
    items = r.items; screenOf = {}; curOf = {};
    r.banks.forEach(b => { screenOf[b.treasury_account_id] = b.screen_code; curOf[b.treasury_account_id] = b.currency_code; });
    if (!ready) { $("#s").innerHTML += r.statuses.map(s => `<option>${esc(s)}</option>`).join(""); ready = true; }
    const sel = $("#bank").value; $("#bank").innerHTML = '<option value="">${tr("كل البنوك","All banks")}</option>' + r.banks.map(b => `<option value="${b.treasury_account_id}">${esc(b.name_ar)}${b.bank_account_number ? " — " + esc(b.bank_account_number) : ""}</option>`).join(""); $("#bank").value = sel;
    $("#bankw").hidden = !all; main.querySelectorAll(".bk").forEach(e => (e.hidden = !all));
    $("#sum").innerHTML = `<b>${r.total}</b> ${tr("شيك","cheques")}${r.total > items.length ? ` (${tr("معروض","showing")} ${items.length})` : ""} — ` + sumTxt(r);
    const cols = all ? 16 : 15, cn = (c, a) => auth.can(screenOf[c.treasury_account_id], a);
    $("#rows").innerHTML = items.map(c => `<tr class="${["ملغي", "مرتد"].includes(c.status) ? "off" : ""}"><td>${esc(c.check_book_no)}</td><td>${c.sequence_no}</td><td>${esc(c.check_no)}</td><td>${c.check_date || ""}</td>${all ? `<td>${esc(c.bank)}</td>` : ""}<td>${esc(c.bank_account_no)}</td><td>${esc(c.beneficiary)}</td><td><small>${esc(c.from_account_label || c.bank || "—")} → ${esc(c.to_account_label || c.beneficiary || "—")}<br>${tr("المسار عند الصرف","Flow on clearing")}</small></td>
      <td class="num">${money(c.amount)}</td><td style="white-space:normal;min-width:200px">${esc(c.amount_words)}</td><td>${esc(c.purchase_order_no)}</td><td>${esc(c.project)}</td><td>${esc(c.settlement_no || "—")}</td><td>${esc(c.description)}</td><td><span class="tag">${esc(statusLabel(c.status))}</span></td>
      <td>${cn(c, "Print") ? `<button class="btn sm" data-p="${c.check_id}">${tr("معاينة / طباعة","Preview / Print")}</button> ` : ""}${cn(c, "Edit") ? c.next_statuses.map(s => `<button class="btn sm" data-s="${c.check_id}|${esc(s)}">${esc(s)}</button>`).join(" ") + ` <button class="btn sm" data-e="${c.check_id}">${tr("تعديل","Edit")}</button>` : ""}${cn(c, "Delete") && c.status === "جديد" ? ` <button class="btn sm danger" data-d="${c.check_id}">${tr("حذف","Delete")}</button>` : ""}</td></tr>`).join("")
      || `<tr><td colspan="${cols}" class="muted">${tr("لا توجد شيكات مطابقة","No matching cheques")}</td></tr>`;
  };
  const baseOf = c => "/checks/" + screenOf[c.treasury_account_id];
  const form = c => formDialog({ title: c ? tr("تعديل شيك","Edit cheque") : tr("شيك جديد","New cheque"), values: c ? { ...c, amount: c.amount ?? "", project_id: c.project_id ?? "" } : { check_date: today() },
    fields: [{ name: "check_book_no", label: tr("رقم الدفتر","Book number"), required: true }, { name: "sequence_no", label: tr("التسلسل","Sequence"), type: "number", required: true, min: 1 },
      { name: "check_no", label: tr("رقم الشيك","Cheque number") }, { name: "check_date", label: tr("تاريخ الشيك","Cheque date"), type: "date" },
      { name: "beneficiary_id", label: tr("المستفيد","Beneficiary"), type: "select", required: true, full: true, options: bens.map(b => [b.beneficiary_id, `${b.name_ar} — ${b.linked_account_label || "حساب غير مربوط"}`]) },
      { name: "flow_description", label: tr("مسار الأموال عند الصرف","Money route on clearing"), readonly: true, full: true },
      { name: "settlement_id", label: tr("ربط بمستخلص مالي مرحّل (اختياري)","Link to posted financial statement (optional)"), type: "select", optional: true, full: true,
        options: payableSettlements.map(s => [s.settlement_id, `${s.settlement_no} — ${s.contract_no} — ${s.counterparty_name} — ${tr("متبقي","Remaining")} ${money(s.remaining_amount)}`]) },
      { name: "amount", label: tr("المبلغ","Amount"), type: "number", step: "0.01", min: 0 }, { name: "purchase_order_no", label: tr("رقم أمر الشراء","Purchase order number") },
      { name: "amount_words", label: tr("التفقيط (تلقائي)","Amount in words (automatic)"), readonly: true, full: true },
      { name: "project_id", label: tr("المشروع","Project"), type: "select", optional: true, options: projs.map(p => [p.project_id, p.name_ar]), full: true }, { name: "description", label: tr("البيان","Description"), full: true }],
    onOpen: (dlg, f) => {
      const amt = f.elements.amount, out = f.elements.amount_words, cur = c ? curOf[c.treasury_account_id] : info.account.currency_code; let t, seq = 0;
      const beneficiarySelect = f.elements.beneficiary_id, flow = f.elements.flow_description;
      const updateFlow = () => {
        const beneficiary = bens.find(b => String(b.beneficiary_id) === String(beneficiarySelect.value));
        flow.value = tr("من حساب البنك","From bank account") + ": " + info.account.name_ar + " → " +
          tr("إلى حساب المستفيد","To beneficiary account") + ": " +
          (beneficiary?.linked_account_label || tr("حساب المستفيد غير مربوط بعد","Beneficiary ledger account not linked yet"));
      };
      beneficiarySelect.addEventListener("change", updateFlow);
      updateFlow();
      const upd = () => { clearTimeout(t); t = setTimeout(async () => {
        const v = amt.value.trim(), my = ++seq; if (v === "") { out.value = ""; return; }
        try { const r = await api("/checks/amount-words?" + new URLSearchParams({ amount: v, currency: cur })); if (my === seq) out.value = r.amount_words; }
        catch (e) { if (my === seq) out.value = ""; }
      }, 150); };
      amt.addEventListener("input", upd); if (c?.amount_words) out.value = c.amount_words;
    },
    onSubmit: async v => { await api(c ? `${baseOf(c)}/items/${c.check_id}` : base + "/items", { method: c ? "PUT" : "POST", json: {
      check_book_no: v.check_book_no, sequence_no: +v.sequence_no, check_no: v.check_no || null, check_date: v.check_date || null, beneficiary_id: +v.beneficiary_id,
      amount: v.amount || null, purchase_order_no: v.purchase_order_no || null, project_id: v.project_id ? +v.project_id : null,
      settlement_id: v.settlement_id ? +v.settlement_id : null, description: v.description || null } }); toast(tr("تم الحفظ","Saved")); await load(); } });
  // معاينة وطباعة الشيك بمقاس ومواضع قابلة للضبط لكل دفتر (check_print.js)
  const preview = c => openPrintDialog({ api, base: baseOf(c), check: c, canEdit: auth.can(screenOf[c.treasury_account_id], "Edit") });
  let t; const go = () => { clearTimeout(t); t = setTimeout(safe(load), 300); };
  ["#acc", "#no", "#ben", "#q"].forEach(id => ($(id).oninput = go)); ["#s", "#bank", "#all"].forEach(id => ($(id).onchange = safe(load)));
  $("#clr").onclick = safe(async () => { ["#acc", "#no", "#ben", "#q", "#s", "#bank"].forEach(id => ($(id).value = "")); $("#all").checked = false; await load(); });
  if (can("Print")) $("#xl").onclick = safe(() => { const p = params(); p.delete("limit"); return downloadFile("/checks/search/xlsx?" + p, "checks.xlsx"); });
  if (can("Add")) {
    $("#add").onclick = () => { if (!bens.length) return toast(tr("أضف مستفيد الأول","Add a beneficiary first")); form(null); };
    $("#nb").onclick = () => formDialog({ title: tr("مستفيد جديد","New beneficiary"), fields: [{ name: "name_ar", label: tr("الاسم","Name"), required: true, full: true }, { name: "code", label: tr("الكود (اختياري)","Code (optional)") }, { name: "bank_account_number", label: tr("رقم الحساب","Account number") }],
      onSubmit: async v => { const b = await api("/checks/beneficiaries", { method: "POST", json: { name_ar: v.name_ar, code: v.code || null, bank_account_number: v.bank_account_number || null } }); bens.push(b); toast(tr("تمت الإضافة","Added")); } });
  }
  $("#rows").onclick = safe(async ev => {
    const s = ev.target.closest("[data-s]"), e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]"), p = ev.target.closest("[data-p]");
    const get = id => items.find(x => x.check_id == id);
    if (p) preview(get(p.dataset.p));
    if (s) { const [id, st] = s.dataset.s.split("|"); if (confirm(`${tr("تغيير الحالة إلى","Change status to")} «${statusLabel(st)}»?`)) { await api(`${baseOf(get(id))}/items/${id}/status`, { method: "POST", json: { status: st } }); await load(); } }
    if (e) form(get(e.dataset.e));
    if (d && confirm(tr("حذف الشيك؟","Delete this cheque?"))) { await api(`${baseOf(get(d.dataset.d))}/items/${d.dataset.d}`, { method: "DELETE" }); await load(); }
  });
  await load();
}
