import { esc, money, today, toast, safe, formDialog } from "../ui.js";
import { translate as tr } from "../i18n.js";
const SCREEN = "BankReconciliation";
export async function render(main, { api, auth }) {
  const can = a => auth.can(SCREEN, a);
  const banks = await api("/reconciliations/accounts");
  main.innerHTML = `<div class="toolbar"><div class="w"><label>${tr("البنك","Bank")}</label><select id="b"><option value="">${tr("الكل","All")}</option>${banks.map(b => `<option value="${b.treasury_account_id}">${esc(b.name_ar)} (${esc(b.currency_code)})</option>`).join("")}</select></div>
    ${can("Add") ? `<button class="btn primary" id="add">+ ${tr('مذكرة تسوية','Reconciliation')}</button>` : ""}</div>
    <div class="tbl-wrap"><table><thead><tr><th>${tr("البنك","Bank")}</th><th>${tr("التاريخ","Date")}</th><th>${tr("رصيد الدفاتر","Book balance")}</th><th>${tr("رصيد كشف البنك","Bank statement balance")}</th><th>${tr("الفرق","Difference")}</th><th>${tr("ملاحظات","Notes")}</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s);
  const load = async () => {
    const rs = await api("/reconciliations" + ($("#b").value ? "?treasury_account_id=" + $("#b").value : ""));
    $("#rows").innerHTML = rs.map(r => `<tr><td>${esc(r.account_name)}</td><td>${r.reconciliation_date}</td><td class="num">${money(r.book_balance)}</td><td class="num">${money(r.statement_balance)}</td>
      <td class="num" style="color:${+r.difference ? "var(--danger)" : "var(--ok)"}">${money(r.difference) === "-" ? "0.00" : money(r.difference)}</td><td>${esc(r.notes)}</td>
      <td><button class="btn sm" data-o="${r.reconciliation_id}">${tr("فتح","Open")}</button> ${can("Delete") ? `<button class="btn sm danger" data-d="${r.reconciliation_id}">${tr("حذف","Delete")}</button>` : ""}</td></tr>`).join("") || `<tr><td colspan="7" class="muted">${tr("لا توجد مذكرات","No reconciliations")}</</td></tr>`;
  };
  $("#b").onchange = safe(load);
  if (can("Add")) $("#add").onclick = () => formDialog({ title: tr("مذكرة تسوية جديدة","New reconciliation"), values: { reconciliation_date: today() },
    fields: [{ name: "treasury_account_id", label: tr("البنك","Bank"), type: "select", required: true, options: banks.map(b => [b.treasury_account_id, b.name_ar]) },
      { name: "reconciliation_date", label: tr("التاريخ","Date"), type: "date", required: true }, { name: "statement_balance", label: tr("رصيد كشف البنك","Bank statement balance"), type: "number", step: "0.01", required: true },
      { name: "notes", label: tr("ملاحظات","Notes") }],
    onSubmit: async v => { const r = await api("/reconciliations", { method: "POST", json: { treasury_account_id: +v.treasury_account_id, reconciliation_date: v.reconciliation_date, statement_balance: v.statement_balance, notes: v.notes || null } });
      toast(tr("تم الإنشاء — رصيد الدفاتر اتحسب من حركات البنك","Created — book balance calculated from bank transactions")); await load(); open(r.reconciliation_id); } });
  $("#rows").onclick = safe(async ev => {
    const o = ev.target.closest("[data-o]"), d = ev.target.closest("[data-d]");
    if (o) await open(+o.dataset.o);
    if (d && confirm(tr("حذف المذكرة وبنودها؟","Delete this reconciliation and its lines?"))) { await api("/reconciliations/" + d.dataset.d, { method: "DELETE" }); await load(); }
  });
  async function open(id) {
    const r = await api("/reconciliations/" + id);
    const dlg = document.createElement("dialog"); dlg.style.width = "min(960px,97vw)";
    dlg.innerHTML = `<form method="dialog"><h3>${esc(r.account_name)} — ${r.reconciliation_date}</h3>
      <p>${tr("رصيد الدفاتر:","Book balance:")} <b>${money(r.book_balance)}</b> — ${tr("رصيد الكشف:","Statement balance:")} <b>${money(r.statement_balance)}</b> — ${tr("الفرق:","Difference:")} <b>${money(r.difference) === "-" ? "0.00" : money(r.difference)}</b> — ${tr("صافي البنود غير المطابقة:","Unmatched net:")} <b>${money(r.unmatched_net) === "-" ? "0.00" : money(r.unmatched_net)}</b></p>
      <div class="tbl-wrap"><table><thead><tr><th>${tr("مطابق","Matched")}</th><th>${tr("التاريخ","Date")}</th><th>${tr("وارد","Inflow")}</th><th>${tr("منصرف","Outflow")}</th><th>${tr("البيان","Description")}</th><th>${tr("رقم الشيك","Cheque No.")}</th><th>${tr("الحالة","Status")}</th><th>${tr("المستلم","Recipient")}</th><th></th></tr></thead><tbody>
      ${r.lines.map(l => `<tr><td><input type="checkbox" style="width:auto" data-m="${l.line_id}" ${l.is_matched ? "checked" : ""} ${can("Edit") ? "" : "disabled"}></td><td>${l.transaction_date || ""}</td><td class="num">${money(l.inflow)}</td><td class="num">${money(l.outflow)}</td><td>${esc(l.description)}</td><td>${esc(l.check_no)}</td><td>${esc(l.status)}</td><td>${esc(l.recipient)}</td>
      <td>${can("Edit") ? `<button type="button" class="btn sm danger" data-x="${l.line_id}">×</button>` : ""}</td></tr>`).join("") || `<tr><td colspan="9" class="muted">${tr("لا توجد بنود","No lines")}</</td></tr>`}</tbody></table></div>
      <div class="actions">${can("Edit") ? '<button class="btn" type="button" id="al">+ ${tr("بند من كشف البنك","Bank statement line")}</button>' : ""}<button class="btn" value="x">${tr("إغلاق","Close")}</button></div></form>`;
    document.body.appendChild(dlg); dlg.addEventListener("close", () => { dlg.remove(); load().catch(() => {}); });
    dlg.onchange = safe(async ev => { const m = ev.target.dataset?.m; if (m) await api(`/reconciliations/${id}/lines/${m}`, { method: "PATCH", json: { is_matched: ev.target.checked } }); });
    dlg.onclick = safe(async ev => {
      const x = ev.target.dataset?.x;
      if (x) { await api(`/reconciliations/${id}/lines/${x}`, { method: "DELETE" }); dlg.close(); return open(id); }
      if (ev.target.id === "al") formDialog({ title: tr("بند جديد","New line"), values: { transaction_date: today() },
        fields: [{ name: "transaction_date", label: tr("التاريخ","Date"), type: "date" }, { name: "check_no", label: tr("رقم الشيك","Cheque No.") }, { name: "inflow", label: tr("وارد","Inflow"), type: "number", step: "0.01", min: 0 }, { name: "outflow", label: tr("منصرف","Outflow"), type: "number", step: "0.01", min: 0 },
          { name: "description", label: tr("البيان","Description"), full: true }, { name: "status", label: tr("الحالة","Status") }, { name: "recipient", label: tr("المستلم","Recipient") }],
        onSubmit: async v => { await api(`/reconciliations/${id}/lines`, { method: "POST", json: { transaction_date: v.transaction_date || null, inflow: v.inflow || "0", outflow: v.outflow || "0", description: v.description || null, check_no: v.check_no || null, status: v.status || null, recipient: v.recipient || null } }); dlg.close(); await open(id); } });
    });
    dlg.showModal();
  }
  await load();
}
