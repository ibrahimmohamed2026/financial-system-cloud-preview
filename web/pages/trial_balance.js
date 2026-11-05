import { esc, money, today, safe } from "../ui.js";

export async function render(main, { api }) {
  const tr = (ar, en) => {
    try { return localStorage.getItem("fs_lang") === "en" ? en : ar; }
    catch { return ar; }
  };
  const y = new Date().getFullYear();
  main.innerHTML = `<div class="trial-balance-page"><div class="toolbar">
    <div class="w"><label>${tr("من تاريخ", "From date")}</label><input type="date" id="df"></div><div class="w"><label>${tr("إلى تاريخ", "To date")}</label><input type="date" id="dt" value="${today()}"></div>
    <div class="grow"><label>${tr("بحث", "Search")}</label><input id="q" placeholder="${tr("ابحث بالكود أو اسم الحساب", "Search code or account name")}"></div>
    <label style="display:flex;gap:6px;align-items:center;margin:0 0 8px"><input type="checkbox" id="hz" style="width:auto">${tr("إخفاء الأصفار", "Hide zero balances")}</label>
    <label style="display:flex;gap:6px;align-items:center;margin:0 0 8px"><input type="checkbox" id="lf" style="width:auto">${tr("الحسابات الفرعية فقط", "Leaf accounts only")}</label>
    <button class="btn" id="csv">${tr("تصدير CSV", "Export CSV")}</button></div>
    <div id="state" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>${tr("الكود", "Code")}</th><th>${tr("اسم الحساب", "Account name")}</th><th>${tr("التصنيف", "Classification")}</th><th>${tr("افتتاحي مدين", "Opening debit")}</th><th>${tr("افتتاحي دائن", "Opening credit")}</th><th>${tr("مدين الفترة", "Period debit")}</th><th>${tr("دائن الفترة", "Period credit")}</th><th>${tr("إجمالي مدين", "Total debit")}</th><th>${tr("إجمالي دائن", "Total credit")}</th><th>${tr("رصيد مدين", "Debit balance")}</th><th>${tr("رصيد دائن", "Credit balance")}</th></tr></thead><tbody id="rows"></tbody><tfoot id="foot"></tfoot></table></div></div>`;
  const $ = s => main.querySelector(s);
  let data;
  const K = ["od", "oc", "d", "c", "td", "tc", "bd", "bc"];
  const load = async () => {
    data = await api("/trial-balance?" + (() => {
      const p = new URLSearchParams();
      if ($("#df").value) p.set("date_from", $("#df").value);
      if ($("#dt").value) p.set("date_to", $("#dt").value);
      if ($("#q").value.trim()) p.set("q", $("#q").value.trim());
      if ($("#hz").checked) p.set("hide_zero", true);
      if ($("#lf").checked) p.set("leaves_only", true);
      return p;
    })());
    $("#rows").innerHTML = data.items.map(r => `<tr class="${r.is_parent ? "parent" : ""}"><td>${esc(r.code)}</td><td style="padding-inline-start:${12 + r.level * 14}px">${esc(r.name)}</td><td>${esc(r.classification)}</td>${K.map(k => `<td class="num">${money(r[k])}</td>`).join("")}</tr>`).join("")
      || `<tr><td colspan="11" class="muted">${tr("لا توجد بيانات", "No data")}</td></tr>`;
    const t = data.totals;
    $("#foot").innerHTML = `<tr class="total"><td colspan="3">${tr("الإجمالي (الحسابات الفرعية)", "Total (leaf accounts)")}</td><td class="num">${money(t.od)}</td><td class="num">${money(t.oc)}</td><td class="num">${money(t.d)}</td><td class="num">${money(t.c)}</td><td class="num">${money(t.td)}</td><td class="num">${money(t.tc)}</td><td colspan="2"></td></tr>`;
    $("#state").innerHTML = data.balanced
      ? `<span class="tag ok">${tr("الميزان متوازن", "Trial balance is balanced")}</span>`
      : `<span class="tag bad">${tr("الميزان غير متوازن — فرق", "Trial balance is unbalanced — difference")} ${money(Number(t.td) - Number(t.tc))}</span>`;
  };
  let timer;
  for (const id of ["#df", "#dt", "#hz", "#lf"]) $(id).onchange = safe(load);
  $("#q").oninput = () => { clearTimeout(timer); timer = setTimeout(safe(load), 300); };
  $("#csv").onclick = () => {
    const head = ["code", "account_name", "classification", ...K].map((k, i) =>
      [tr("الكود", "Code"), tr("اسم الحساب", "Account name"), tr("التصنيف", "Classification"), ...K][i]);
    const lines = [head, ...data.items.map(r => [r.code, r.name, r.classification, ...K.map(k => r[k])])]
      .map(line => line.map(c => `"${String(c).replace(/"/g, '""')}"`).join(","));
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" }));
    a.download = "trial_balance.csv"; a.click();
    URL.revokeObjectURL(a.href);
  };
  await load();
}
