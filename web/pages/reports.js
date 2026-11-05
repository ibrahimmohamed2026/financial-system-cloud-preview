import { esc, money, today, safe } from "../ui.js";
const block = (title, items, total) => `<div class="tbl-wrap" style="margin-bottom:14px"><table><thead><tr><th>${title}</th><th style="text-align:left">المبلغ</th></tr></thead><tbody>
  ${items.map(i => `<tr><td>${esc(i.name)}</td><td class="num">${money(i.amount)}</td></tr>`).join("") || `<tr><td colspan="2" class="muted">لا توجد بيانات</td></tr>`}
  <tr class="total"><td>الإجمالي</td><td class="num">${money(total)}</td></tr></tbody></table></div>`;
export async function render(main, { api, route }) {
  const bs = route.endsWith("balance-sheet");
  main.innerHTML = `<div class="toolbar">${bs ? `<div class="w"><label>حتى تاريخ</label><input type="date" id="a" value="${today()}"></div>`
    : `<div class="w"><label>من</label><input type="date" id="a" value="${new Date().getFullYear()}-01-01"></div><div class="w"><label>إلى</label><input type="date" id="b" value="${today()}"></div>`}
    <button class="btn" onclick="print()">طباعة</button></div><div id="out"></div>`;
  const out = main.querySelector("#out");
  const load = async () => {
    const a = main.querySelector("#a").value, b = main.querySelector("#b")?.value;
    if (bs) {
      const r = await api("/reports/balance-sheet?as_of=" + a);
      out.innerHTML = `<h3>قائمة المركز المالي في ${esc(r.as_of)}</h3>${block("الأصول", r.assets, r.total_assets)}${block("الخصوم وحقوق الملكية", r.liabilities_equity, r.total_liabilities_equity)}
        <p>${r.balanced ? '<span class="tag ok">القائمة متوازنة</span>' : `<span class="tag bad">فرق ${money(r.difference)}</span>`}</p>`;
    } else {
      const r = await api(`/reports/income-statement?date_from=${a}&date_to=${b}`);
      out.innerHTML = `<h3>قائمة الدخل من ${esc(r.date_from)} إلى ${esc(r.date_to)}</h3>${block("الإيرادات", r.revenue, r.total_revenue)}${block("المصروفات", r.expenses, r.total_expenses)}
        <h3>صافي ${Number(r.net_income) >= 0 ? "الربح" : "الخسارة"}: ${money(Math.abs(r.net_income)) === "-" ? "0.00" : money(Math.abs(r.net_income))}</h3>`;
    }
  };
  main.querySelectorAll("input[type=date]").forEach(i => (i.onchange = safe(load)));
  await load();
}
