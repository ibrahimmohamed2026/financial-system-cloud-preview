import { esc, money, today, toast, safe, formDialog } from "../ui.js";
const SCREEN = "BankReconciliation";
export async function render(main, { api, auth }) {
  const can = a => auth.can(SCREEN, a);
  const banks = await api("/reconciliations/accounts");
  main.innerHTML = `<div class="toolbar"><div class="w"><label>البنك</label><select id="b"><option value="">الكل</option>${banks.map(b => `<option value="${b.treasury_account_id}">${esc(b.name_ar)} (${esc(b.currency_code)})</option>`).join("")}</select></div>
    ${can("Add") ? '<button class="btn primary" id="add">+ مذكرة تسوية</button>' : ""}</div>
    <div class="tbl-wrap"><table><thead><tr><th>البنك</th><th>التاريخ</th><th>رصيد الدفاتر</th><th>رصيد كشف البنك</th><th>الفرق</th><th>ملاحظات</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s);
  const load = async () => {
    const rs = await api("/reconciliations" + ($("#b").value ? "?treasury_account_id=" + $("#b").value : ""));
    $("#rows").innerHTML = rs.map(r => `<tr><td>${esc(r.account_name)}</td><td>${r.reconciliation_date}</td><td class="num">${money(r.book_balance)}</td><td class="num">${money(r.statement_balance)}</td>
      <td class="num" style="color:${+r.difference ? "var(--danger)" : "var(--ok)"}">${money(r.difference) === "-" ? "0.00" : money(r.difference)}</td><td>${esc(r.notes)}</td>
      <td><button class="btn sm" data-o="${r.reconciliation_id}">فتح</button> ${can("Delete") ? `<button class="btn sm danger" data-d="${r.reconciliation_id}">حذف</button>` : ""}</td></tr>`).join("") || `<tr><td colspan="7" class="muted">لا توجد مذكرات</td></tr>`;
  };
  $("#b").onchange = safe(load);
  if (can("Add")) $("#add").onclick = () => formDialog({ title: "مذكرة تسوية جديدة", values: { reconciliation_date: today() },
    fields: [{ name: "treasury_account_id", label: "البنك", type: "select", required: true, options: banks.map(b => [b.treasury_account_id, b.name_ar]) },
      { name: "reconciliation_date", label: "التاريخ", type: "date", required: true }, { name: "statement_balance", label: "رصيد كشف البنك", type: "number", step: "0.01", required: true },
      { name: "notes", label: "ملاحظات" }],
    onSubmit: async v => { const r = await api("/reconciliations", { method: "POST", json: { treasury_account_id: +v.treasury_account_id, reconciliation_date: v.reconciliation_date, statement_balance: v.statement_balance, notes: v.notes || null } });
      toast("تم الإنشاء — رصيد الدفاتر اتحسب من حركات البنك"); await load(); open(r.reconciliation_id); } });
  $("#rows").onclick = safe(async ev => {
    const o = ev.target.closest("[data-o]"), d = ev.target.closest("[data-d]");
    if (o) await open(+o.dataset.o);
    if (d && confirm("حذف المذكرة وبنودها؟")) { await api("/reconciliations/" + d.dataset.d, { method: "DELETE" }); await load(); }
  });
  async function open(id) {
    const r = await api("/reconciliations/" + id);
    const dlg = document.createElement("dialog"); dlg.style.width = "min(960px,97vw)";
    dlg.innerHTML = `<form method="dialog"><h3>${esc(r.account_name)} — ${r.reconciliation_date}</h3>
      <p>رصيد الدفاتر: <b>${money(r.book_balance)}</b> — رصيد الكشف: <b>${money(r.statement_balance)}</b> — الفرق: <b>${money(r.difference) === "-" ? "0.00" : money(r.difference)}</b> — صافي البنود غير المطابقة: <b>${money(r.unmatched_net) === "-" ? "0.00" : money(r.unmatched_net)}</b></p>
      <div class="tbl-wrap"><table><thead><tr><th>مطابق</th><th>التاريخ</th><th>وارد</th><th>منصرف</th><th>البيان</th><th>رقم الشيك</th><th>الحالة</th><th>المستلم</th><th></th></tr></thead><tbody>
      ${r.lines.map(l => `<tr><td><input type="checkbox" style="width:auto" data-m="${l.line_id}" ${l.is_matched ? "checked" : ""} ${can("Edit") ? "" : "disabled"}></td><td>${l.transaction_date || ""}</td><td class="num">${money(l.inflow)}</td><td class="num">${money(l.outflow)}</td><td>${esc(l.description)}</td><td>${esc(l.check_no)}</td><td>${esc(l.status)}</td><td>${esc(l.recipient)}</td>
      <td>${can("Edit") ? `<button type="button" class="btn sm danger" data-x="${l.line_id}">×</button>` : ""}</td></tr>`).join("") || `<tr><td colspan="9" class="muted">لا توجد بنود</td></tr>`}</tbody></table></div>
      <div class="actions">${can("Edit") ? '<button class="btn" type="button" id="al">+ بند من كشف البنك</button>' : ""}<button class="btn" value="x">إغلاق</button></div></form>`;
    document.body.appendChild(dlg); dlg.addEventListener("close", () => { dlg.remove(); load().catch(() => {}); });
    dlg.onchange = safe(async ev => { const m = ev.target.dataset?.m; if (m) await api(`/reconciliations/${id}/lines/${m}`, { method: "PATCH", json: { is_matched: ev.target.checked } }); });
    dlg.onclick = safe(async ev => {
      const x = ev.target.dataset?.x;
      if (x) { await api(`/reconciliations/${id}/lines/${x}`, { method: "DELETE" }); dlg.close(); return open(id); }
      if (ev.target.id === "al") formDialog({ title: "بند جديد", values: { transaction_date: today() },
        fields: [{ name: "transaction_date", label: "التاريخ", type: "date" }, { name: "check_no", label: "رقم الشيك" }, { name: "inflow", label: "وارد", type: "number", step: "0.01", min: 0 }, { name: "outflow", label: "منصرف", type: "number", step: "0.01", min: 0 },
          { name: "description", label: "البيان", full: true }, { name: "status", label: "الحالة" }, { name: "recipient", label: "المستلم" }],
        onSubmit: async v => { await api(`/reconciliations/${id}/lines`, { method: "POST", json: { transaction_date: v.transaction_date || null, inflow: v.inflow || "0", outflow: v.outflow || "0", description: v.description || null, check_no: v.check_no || null, status: v.status || null, recipient: v.recipient || null } }); dlg.close(); await open(id); } });
    });
    dlg.showModal();
  }
  await load();
}
