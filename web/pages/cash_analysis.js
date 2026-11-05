import { esc, money } from "../ui.js";
export async function render(main, { api }) {
  const r = await api("/treasury/analysis");
  main.innerHTML = `<div class="tbl-wrap"><table><thead><tr><th>الحساب</th><th>النوع</th><th>العملة</th><th style="text-align:left">الرصيد</th></tr></thead><tbody>
    ${r.items.map(i => `<tr><td>${esc(i.name_ar)}</td><td>${i.account_type === "Bank" ? "بنك" : "خزينة"}</td><td>${esc(i.currency_code)}</td><td class="num">${money(i.balance) === "-" ? "0.00" : money(i.balance)}</td></tr>`).join("") || `<tr><td colspan="4" class="muted">لا توجد حسابات — سجّلها من شاشات البنوك والخزائن</td></tr>`}
    ${r.totals.map(t => `<tr class="total"><td colspan="3">إجمالي ${esc(t.currency_code)}</td><td class="num">${money(t.balance) === "-" ? "0.00" : money(t.balance)}</td></tr>`).join("")}</tbody></table></div>`;
}
