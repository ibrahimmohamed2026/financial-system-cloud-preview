import { esc, money, today, safe } from "../ui.js";
import { translate as tr } from "../i18n.js";
const block = (title, items, total) => `<div class="tbl-wrap" style="margin-bottom:14px"><table><thead><tr><th>${title}</th><th style="text-align:left">${tr("المبلغ","Amount")}</th></tr></thead><tbody>
  ${items.map(i => `<tr><td>${esc(i.name)}</td><td class="num">${money(i.amount)}</td></tr>`).join("") || `<tr><td colspan="2" class="muted">${tr("لا توجد بيانات","No data")}</td></tr>`}
  <tr class="total"><td>${tr("الإجمالي","Total")}</td><td class="num">${money(total)}</td></tr></tbody></table></div>`;
export async function render(main, { api, route }) {
  const bs = route.endsWith("balance-sheet");
  main.innerHTML = `<div class="toolbar">${bs ? `<div class="w"><label>${tr("حتى تاريخ","As of")}</label><input type="date" id="a" value="${today()}"></div>`
    : `<div class="w"><label>${tr("من","From")}</label><input type="date" id="a" value="${new Date().getFullYear()}-01-01"></div><div class="w"><label>${tr("إلى","To")}</label><input type="date" id="b" value="${today()}"></div>`}
    <div class="w" id="account-filter"><label>${tr("تصفية حسب عدة حسابات","Filter by multiple accounts")}</label><input id="account-search" placeholder="${tr("ابحث بكود أو اسم الحساب","Search account code or name")}"><select id="accounts" multiple size="4"></select><div style="display:flex;gap:6px;margin-top:4px"><button class="btn sm" type="button" id="select-all">${tr("تحديد الكل","Select all")}</button><button class="btn sm" type="button" id="clear-all">${tr("إلغاء الكل","Clear all")}</button></div></div>
    <button class="btn" onclick="print()">${tr("طباعة","Print")}</button></div><div id="out"></div>`;
  const out = main.querySelector("#out");
  const lookups = await api("/api/reports/financial-lookups").catch(() => ({accounts: []}));
  const accounts = lookups.accounts || [];
  main.querySelector("#accounts").innerHTML = accounts.map(a => `<option value="${a.account_id}">${esc(a.code)} — ${esc(a.name)}</option>`).join("");
  if (!accounts.length) main.querySelector("#account-filter").hidden = true;
  const load = async () => {
    const a = main.querySelector("#a").value, b = main.querySelector("#b")?.value;
    const selected = [...main.querySelector("#accounts").selectedOptions].map(o => o.value);
    if (bs) {
      const p = new URLSearchParams({as_of: a}); selected.forEach(id => p.append("account_ids", id));
      const r = await api("/reports/balance-sheet?" + p);
      out.innerHTML = `<h3>${tr("قائمة المركز المالي في","Balance Sheet as of")} ${esc(r.as_of)}</h3>${block(tr("الأصول","Assets"), r.assets, r.total_assets)}${block(tr("الخصوم وحقوق الملكية","Liabilities & Equity"), r.liabilities_equity, r.total_liabilities_equity)}
        <p>${r.balanced ? '<span class="tag ok">${tr("القائمة متوازنة","Balanced")}</span>' : `<span class="tag bad">${tr("فرق","Difference")} ${money(r.difference)}</span>`}</p>`;
    } else {
      const p = new URLSearchParams({date_from: a, date_to: b}); selected.forEach(id => p.append("account_ids", id));
      const r = await api(`/reports/income-statement?${p}`);
      out.innerHTML = `<h3>${tr("قائمة الدخل من","Income Statement from")} ${esc(r.date_from)} ${tr("إلى","to")} ${esc(r.date_to)}</h3>${block(tr("الإيرادات","Revenue"), r.revenue, r.total_revenue)}${block(tr("المصروفات","Expenses"), r.expenses, r.total_expenses)}
        <h3>${tr("صافي","Net")} ${Number(r.net_income) >= 0 ? tr("الربح","Profit") : tr("الخسارة","Loss")}: ${money(Math.abs(r.net_income)) === "-" ? "0.00" : money(Math.abs(r.net_income))}</h3>`;
    }
  };
  main.querySelectorAll("input[type=date], #accounts").forEach(i => (i.onchange = safe(load)));
  main.querySelector("#account-search").oninput = ev => {
    const term = ev.target.value.trim().toLocaleLowerCase();
    [...main.querySelector("#accounts").options].forEach(o => { o.hidden = !!term && !o.text.toLocaleLowerCase().includes(term); });
  };
  main.querySelector("#select-all").onclick = () => { [...main.querySelector("#accounts").options].forEach(o => { if (!o.hidden) o.selected = true; }); safe(load)(); };
  main.querySelector("#clear-all").onclick = () => { [...main.querySelector("#accounts").options].forEach(o => o.selected = false); safe(load)(); };
  await load();
}
