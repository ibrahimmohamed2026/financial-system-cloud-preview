import { esc, money, today, safe } from "../ui.js";
export async function render(main, { api }) {
  const y = new Date().getFullYear();
  main.innerHTML = `<div class="trial-balance-page"><div class="toolbar">
    <div class="w"><label>من تاريخ</label><input type="date" id="df"></div><div class="w"><label>إلى تاريخ</label><input type="date" id="dt" value="${today()}"></div>
    <div class="grow"><label>بحث</label><input id="q"></div>
    <label style="display:flex;gap:6px;align-items:center;margin:0 0 8px"><input type="checkbox" id="hz" style="width:auto"> إخفاء الأصفار</label>
    <label style="display:flex;gap:6px;align-items:center;margin:0 0 8px"><input type="checkbox" id="lf" style="width:auto"> الفرعية فقط</label>
    <button class="btn" id="csv">تصدير CSV</button></div>
    <div id="state" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>الكود</th><th>اسم الحساب</th><th>التصنيف</th><th>افتتاحي مدين</th><th>افتتاحي دائن</th><th>مدين الفترة</th><th>دائن الفترة</th><th>إجمالي مدين</th><th>إجمالي دائن</th><th>رصيد مدين</th><th>رصيد دائن</th></tr></thead><tbody id="rows"></tbody><tfoot id="foot"></tfoot></table></div></div>`;
  const $ = s => main.querySelector(s); let data;
  const K = ["od", "oc", "d", "c", "td", "tc", "bd", "bc"];
  const load = async () => {
    const p = new URLSearchParams(); if ($("#df").value) p.set("date_from", $("#df").value); if ($("#dt").value) p.set("date_to", $("#dt").value);
    if ($("#q").value.trim()) p.set("q", $("#q").value.trim()); if ($("#hz").checked) p.set("hide_zero", true); if ($("#lf").checked) p.set("leaves_only", true);
    data = await api("/trial-balance?" + p);
    $("#rows").innerHTML = data.items.map(r => `<tr class="${r.is_parent ? "parent" : ""}"><td>${esc(r.code)}</td><td style="padding-inline-start:${12 + r.level * 14}px">${esc(r.name)}</td><td>${esc(r.classification)}</td>${K.map(k => `<td class="num">${money(r[k])}</td>`).join("")}</tr>`).join("")
      || `<tr><td colspan="11" class="muted">لا توجد بيانات</td></tr>`;
    const t = data.totals;
    $("#foot").innerHTML = `<tr class="total"><td colspan="3">الإجمالي (الحسابات الفرعية)</td><td class="num">${money(t.od)}</td><td class="num">${money(t.oc)}</td><td class="num">${money(t.d)}</td><td class="num">${money(t.c)}</td><td class="num">${money(t.td)}</td><td class="num">${money(t.tc)}</td><td colspan="2"></td></tr>`;
    $("#state").innerHTML = data.balanced ? `<span class="tag ok">الميزان متوازن</span>` : `<span class="tag bad">الميزان غير متوازن — فرق ${money(Number(t.td) - Number(t.tc))}</span>`;
  };
  let t; for (const id of ["#df", "#dt", "#hz", "#lf"]) $(id).onchange = safe(load);
  $("#q").oninput = () => { clearTimeout(t); t = setTimeout(safe(load), 300); };
  $("#csv").onclick = () => {
    const head = ["الكود", "اسم الحساب", "التصنيف", ...K];
    const lines = [head, ...data.items.map(r => [r.code, r.name, r.classification, ...K.map(k => r[k])])]
      .map(l => l.map(c => `"${String(c).replace(/"/g, '""')}"`).join(","));
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" }));
    a.download = "trial_balance.csv"; a.click();
  };
  await load();
}
