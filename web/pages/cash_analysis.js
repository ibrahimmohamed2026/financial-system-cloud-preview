import { esc, money } from "../ui.js";
import { translate as tr } from "../i18n.js";
export async function render(main, { api }) {
  const r = await api("/treasury/analysis");
  main.innerHTML = `<div class="tbl-wrap"><table><thead><tr><th>${tr("الحساب","Account")}</th><th>${tr("النوع","Type")}</th><th>${tr("العملة","Currency")}</th><th style="text-align:left">${tr("الرصيد","Balance")}</th></tr></thead><tbody>
    ${r.items.map(i => `<tr><td>${esc(localStorage.getItem("fs_lang")==="en"?(i.name_en||i.name_ar):i.name_ar)}</td><td>${i.account_type === "Bank" ? "بنك" : "خزينة"}</td><td>${esc(i.currency_code)}</td><td class="num">${money(i.balance) === "-" ? "0.00" : money(i.balance)}</td></tr>`).join("") || `<tr><td colspan="4" class="muted">لا توجد حسابات — سجّلها من شاشات البنوك والخزائن</td></tr>`}
    ${r.totals.map(t => `<tr class="total"><td colspan="3">إجمالي ${esc(t.currency_code)}</td><td class="num">${money(t.balance) === "-" ? "0.00" : money(t.balance)}</td></tr>`).join("")}</tbody></table></div>`;
}
