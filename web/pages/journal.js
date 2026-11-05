import { esc, money, today, toast, safe, errText, formDialog } from "../ui.js";
const SCREEN = "JournalBook", PAGE = 50;
const ST = { Draft: "مسودة", Posted: "مرحّل", Reversed: "ملغي" };

export async function render(main, { api, auth }) {
  const can = a => auth.can(SCREEN, a);
  const [accs, projs, settlements, company] = await Promise.all([api("/journal/lookup/accounts"), api("/projects/lookup").catch(() => []), api("/journal/lookup/settlements").catch(() => []), api("/company-profile").catch(() => null)]);
  const accByLabel = Object.fromEntries(accs.map(a => [a.label, a.account_id]));
  const st = { q: "", status: "", df: "", dt: "", skip: 0 };
  main.innerHTML = `<div class="toolbar">
    <div class="grow"><label>بحث (رقم القيد / البيان)</label><input id="q"></div>
    <div class="w" style="width:130px"><label>الحالة</label><select id="s"><option value="">الكل</option>${Object.entries(ST).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select></div>
    <div class="w" style="width:150px"><label>من</label><input type="date" id="df"></div><div class="w" style="width:150px"><label>إلى</label><input type="date" id="dt"></div>
    ${can("Add") ? '<button class="btn primary" id="add">+ قيد جديد</button>' : ""}${can("Approve") ? '<button class="btn" id="fy">السنوات المالية</button>' : ""}</div>
    <div class="tbl-wrap"><table><thead><tr><th>رقم القيد</th><th>التاريخ</th><th>البيان</th><th>مدين</th><th>دائن</th><th>الحالة</th></tr></thead><tbody id="rows"></tbody></table></div>
    <div class="pager"><button class="btn sm" id="prev">السابق</button><span id="info"></span><button class="btn sm" id="next">التالي</button></div>`;
  const $ = s => main.querySelector(s); let items = [], total = 0;
  const load = async () => {
    const p = new URLSearchParams({ skip: st.skip, limit: PAGE });
    if (st.q) p.set("q", st.q); if (st.status) p.set("status", st.status); if (st.df) p.set("date_from", st.df); if (st.dt) p.set("date_to", st.dt);
    const r = await api("/journal?" + p); items = r.items; total = r.total;
    $("#rows").innerHTML = items.map(e => `<tr style="cursor:pointer" data-id="${e.journal_entry_id}" class="${e.status === "Reversed" ? "off" : ""}"><td>${esc(e.entry_no)}</td><td>${e.entry_date}</td><td>${(e.line_descriptions || []).map((l, i) => `<div class="journal-desc-line"${i ? ' style="border-top:1px solid var(--line);margin-top:5px;padding-top:5px"' : ""}>${esc(l.description || "—")}</div>`).join("") || esc(e.description || "—")}</td>
      <td class="num">${money(e.total_debit)}</td><td class="num">${money(e.total_credit)}</td><td><span class="tag ${{ Posted: "ok", Reversed: "bad", Draft: "warn" }[e.status] || ""}">${ST[e.status]}</span></td></tr>`).join("")
      || `<tr><td colspan="6" class="muted">لا توجد قيود</td></tr>`;
    const to = Math.min(st.skip + PAGE, total);
    $("#info").textContent = total ? `${st.skip + 1}–${to} من ${total}` : "0"; $("#prev").disabled = !st.skip; $("#next").disabled = to >= total;
  };
  const reload = safe(load);
  let t; $("#q").oninput = e => { clearTimeout(t); t = setTimeout(() => { st.q = e.target.value.trim(); st.skip = 0; reload(); }, 300); };
  $("#s").onchange = e => { st.status = e.target.value; st.skip = 0; reload(); };
  $("#df").onchange = e => { st.df = e.target.value; st.skip = 0; reload(); };
  $("#dt").onchange = e => { st.dt = e.target.value; st.skip = 0; reload(); };
  $("#prev").onclick = () => { st.skip = Math.max(0, st.skip - PAGE); reload(); };
  $("#next").onclick = () => { st.skip += PAGE; reload(); };
  $("#rows").onclick = safe(async ev => { const tr = ev.target.closest("tr[data-id]"); if (tr) await view(+tr.dataset.id); });

  // ---------- عرض وطباعة قيد ----------
  function printEntry(e) {
    const w = window.open("", "_blank");
    if (!w) return toast("اسمح بالنوافذ المنبثقة لطباعة القيد");
    const logoUrl = `${window.location.origin}/static/company-logos.png?v=20261104-journal-print-logo-1`;
    const companyLogo = company?.logo_data || logoUrl;
    const companyInfo = [company?.name_en, company?.address_ar, company?.phone && `هاتف: ${company.phone}`, company?.email && `بريد: ${company.email}`, company?.website, company?.tax_number && `رقم ضريبي: ${company.tax_number}`, company?.commercial_register && `سجل تجاري: ${company.commercial_register}`].filter(Boolean).map(esc).join(" | ");
    const rows = e.lines.map(l => `<tr><td>${l.line_no}</td><td>${esc(l.account_code)} — ${esc(l.account_name)}</td><td>${esc(l.project_name || "—")}</td><td>${esc(l.description || "—")}</td><td class="num">${money(l.debit_amount)}</td><td class="num">${money(l.credit_amount)}</td></tr>`).join("");
    w.document.open();
    w.document.write(`<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><title>قيد ${esc(e.entry_no)}</title><style>
      @page{size:A4 portrait;margin:12mm}*{box-sizing:border-box}body{font:14px/1.7 Tahoma,Arial,sans-serif;color:#111;margin:0}.print-header{display:flex;align-items:center;gap:18px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #bbb}.print-header img{display:block;width:190px;max-height:65px;object-fit:contain}.print-header h1{font-size:22px;margin:0;text-align:right}.meta{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:18px}.meta div{border:1px solid #bbb;padding:8px 10px}.meta b{margin-inline-start:6px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #555;padding:7px 8px;text-align:right;vertical-align:top}th{background:#eee}.num{text-align:left;white-space:nowrap;font-variant-numeric:tabular-nums}.total td{font-weight:bold;background:#f1f1f1}.signs{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:55px;text-align:center}.signs div{border-top:1px solid #555;padding-top:8px}@media print{tr{break-inside:avoid}}
      </style></head><body><header class="print-header"><img src="${esc(companyLogo)}" alt="شعار الشركة"><div><h1>${esc(company?.name_ar||'الشركة')}</h1><small>${companyInfo}</small></div><h1>قيد يومية</h1></header><div class="meta"><div>رقم القيد: <b>${esc(e.entry_no)}</b></div><div>التاريخ: <b>${esc(e.entry_date)}</b></div><div>الحالة: <b>${esc(ST[e.status] || e.status)}</b></div></div>
      <table><thead><tr><th>#</th><th>الحساب</th><th>مركز التكلفة</th><th>بيان السطر</th><th>مدين</th><th>دائن</th></tr></thead><tbody>${rows}<tr class="total"><td colspan="4">الإجمالي</td><td class="num">${money(e.total_debit)}</td><td class="num">${money(e.total_credit)}</td></tr></tbody></table><div class="signs"><div>إعداد</div><div>مراجعة</div><div>اعتماد</div></div><script>window.onload=()=>window.print()<\/script></body></html>`);
    w.document.close();
  }

  // ---------- عرض قيد ----------
  async function view(id) {
    const e = await api("/journal/" + id);
    const dlg = document.createElement("dialog"); dlg.style.width = "min(900px,96vw)";
    dlg.innerHTML = `<form method="dialog"><h3>${esc(e.entry_no)} — ${e.entry_date} <span class="tag">${ST[e.status]}</span></h3><p>${esc(e.description)}</p>
      <div class="tbl-wrap"><table><thead><tr><th>#</th><th>الحساب</th><th>مركز التكلفة</th><th>مدين</th><th>دائن</th><th>البيان</th></tr></thead><tbody>
      ${e.lines.map(l => `<tr><td>${l.line_no}</td><td>${esc(l.account_code)} — ${esc(l.account_name)}</td><td>${esc(l.project_name)}</td><td class="num">${money(l.debit_amount)}</td><td class="num">${money(l.credit_amount)}</td><td>${esc(l.description)}</td></tr>`).join("")}
      <tr class="total"><td colspan="3">الإجمالي</td><td class="num">${money(e.total_debit)}</td><td class="num">${money(e.total_credit)}</td><td></td></tr></tbody></table></div>
      <div class="actions">${e.status === "Draft" && can("Post") ? '<button class="btn primary" type="button" data-a="post">ترحيل</button>' : ""}
      ${e.status === "Draft" && can("Edit") ? '<button class="btn" type="button" data-a="edit">تعديل</button>' : ""}
      ${can("Print") ? '<button class="btn" type="button" data-a="print">طباعة</button>' : ""}
      ${(e.status === "Draft" || e.status === "Reversed") && can("Delete") ? '<button class="btn danger" type="button" data-a="del">' + (e.status === "Reversed" ? "حذف القيد الملغي" : "حذف المسودة") + '</button>' : ""}
      ${e.status === "Posted" && can("Approve") ? '<button class="btn danger" type="button" data-a="cancel">إلغاء القيد</button>' : ""}
      <button class="btn" value="x">إغلاق</button></div></form>`;
    document.body.appendChild(dlg); dlg.addEventListener("close", () => dlg.remove());
    dlg.onclick = safe(async ev => {
      const a = ev.target.dataset?.a; if (!a) return;
      if (a === "print") return printEntry(e);
      if (a === "edit") { dlg.close(); return editor(e); }
      const msg = { post: "ترحيل القيد؟ بعد الترحيل مينفعش يتعدّل.", del: e.status === "Reversed" ? "حذف القيد الملغي نهائيًا؟ سيظل تسجيل عملية الحذف موجودًا في سجل المراجعة." : "حذف المسودة؟", cancel: "إلغاء القيد؟ هيخرج من ميزان المراجعة." }[a];
      if (!confirm(msg)) return;
      if (a === "del") await api("/journal/" + id, { method: "DELETE" }); else await api(`/journal/${id}/${a}`, { method: "POST" });
      dlg.close(); toast("تم"); await load();
    });
    dlg.showModal();
  }

  // ---------- محرر القيد ----------
  function editor(e) {
    const dlg = document.createElement("dialog"); dlg.style.width = "min(980px,97vw)";
    const lines = e ? e.lines.map(l => ({ account_id: l.account_id, label: `${l.account_code} — ${l.account_name}`, project_id: l.project_id || "", d: Number(l.debit_amount) || "", c: Number(l.credit_amount) || "", desc: l.description || e.description || "" }))
      : [{ account_id: null, label: "", project_id: "", d: "", c: "", desc: "" }, { account_id: null, label: "", project_id: "", d: "", c: "", desc: "" }];
    dlg.innerHTML = `<form method="dialog"><h3>${e ? "تعديل " + esc(e.entry_no) : "قيد جديد"}</h3>
      <div class="grid2"><div class="f"><label>التاريخ</label><input type="date" id="dt" value="${e ? e.entry_date : today()}" required></div>
      <div class="f"><label>المستخلص المرتبط (اختياري — لمنع تكرار القيد)</label><select id="settlement"><option value="">قيد عام — بدون مستخلص</option>${settlements.map(s => `<option value="${s.settlement_id}" ${s.settlement_id === e?.source_settlement_id ? "selected" : ""}>${esc(s.settlement_no)} — ${esc(s.contract_no || s.contract_title || "عقد غير معروف")} — ${s.settlement_side === "Customer" ? "عميل" : "مقاول باطن"} — ${esc(s.status)}${s.journal_entry_id ? " — مرحّل" : ""}</option>`).join("")}</select><small class="muted">عند اختيار مستخلص سبق ترحيله، سيرفض النظام حفظ القيد أو ترحيله.</small></div></div>
      <div class="tbl-wrap" style="margin-top:10px;width:100%"><table class="journal-lines"><thead><tr><th>الحساب</th><th>مركز التكلفة</th><th>مدين</th><th>دائن</th><th>بيان السطر</th><th></th></tr></thead><tbody id="ln"></tbody>
      <tfoot><tr class="total"><td colspan="2">الإجمالي <span id="bal"></span></td><td class="num" id="td"></td><td class="num" id="tc"></td><td colspan="2"></td></tr></tfoot></table></div>
      <button class="btn sm" type="button" id="addl" style="margin-top:8px">+ سطر</button>
      <div class="err" id="er"></div><div class="actions"><button class="btn primary" value="ok">حفظ كمسودة</button><button class="btn" value="x" formnovalidate>إلغاء</button></div></form>`;
    document.body.appendChild(dlg); dlg.addEventListener("close", () => dlg.remove());
    const q = s => dlg.querySelector(s);
    const chooseAccount = (i, id) => {
      const a = accs.find(x => x.account_id === id); if (!a) return;
      lines[i].account_id = a.account_id; lines[i].label = a.label;
      const input = q(`#ln input[data-i="${i}"][data-k="label"]`);
      if (input) { input.value = a.label; input.setAttribute("aria-expanded", "false"); }
      const results = q(`#account-options-${i}`); if (results) { results.hidden = true; results.innerHTML = ""; }
    };
    const searchAccounts = (i, term, showAll = false) => {
      const box = q(`#account-options-${i}`), needle = term.trim().toLocaleLowerCase();
      if (!box) return;
      if (!needle && !showAll) { box.hidden = true; box.innerHTML = ""; q(`#ln input[data-i="${i}"][data-k="label"]`)?.setAttribute("aria-expanded", "false"); return; }
      const matches = needle ? accs.filter(a => a.label.toLocaleLowerCase().includes(needle)) : accs;
      const hint = needle ? "" : '<div class="journal-account-hint">الحسابات المتاحة — اكتب الاسم أو الكود لتصفية القائمة</div>';
      box.innerHTML = hint + (matches.length ? matches.map(a => `<button type="button" class="journal-account-option" role="option" data-account-id="${a.account_id}" data-line="${i}">${esc(a.label)}</button>`).join("")
        : '<div class="journal-account-empty">لا يوجد حساب مطابق للاسم أو الكود</div>');
      box.hidden = false;
      const input = q(`#ln input[data-i="${i}"][data-k="label"]`), rect = input.getBoundingClientRect();
      input?.setAttribute("aria-expanded", "true");
      const width = Math.min(Math.max(rect.width, 420), window.innerWidth - 24);
      box.style.width = `${width}px`; box.style.left = `${Math.max(12, Math.min(rect.left, window.innerWidth - width - 12))}px`;
      const maxHeight = Math.min(window.innerHeight * .42, 360), desiredHeight = Math.min(maxHeight, Math.max(54, matches.length * 48 + 12));
      const below = rect.bottom + desiredHeight <= window.innerHeight - 12;
      box.style.maxHeight = `${Math.max(54, Math.min(maxHeight, below ? window.innerHeight - rect.bottom - 16 : rect.top - 16))}px`;
      box.style.top = `${below ? rect.bottom + 4 : Math.max(12, rect.top - desiredHeight - 4)}px`;
    };
    const draw = () => {
      q("#ln").innerHTML = lines.map((l, i) => `<tr><td><div class="journal-account-picker" id="account-picker-${i}"><input data-i="${i}" data-k="label" value="${esc(l.label)}" placeholder="اكتب اسم الحساب أو الكود" title="اكتب اسم الحساب أو الكود ثم اختر الحساب" autocomplete="off" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="account-options-${i}"><div class="journal-account-options" id="account-options-${i}" role="listbox" hidden></div></div></td>
        <td><select data-i="${i}" data-k="project_id"><option value="">—</option>${projs.map(p => `<option value="${p.project_id}" ${p.project_id == l.project_id ? "selected" : ""}>${esc(p.name_ar)}</option>`).join("")}</select></td>
        <td><input type="number" step="0.01" min="0" data-i="${i}" data-k="d" value="${l.d}" style="width:120px"></td><td><input type="number" step="0.01" min="0" data-i="${i}" data-k="c" value="${l.c}" style="width:120px"></td>
        <td><textarea rows="1" data-i="${i}" data-k="desc" placeholder="اكتب بيان هذا السطر — يمكن كتابة بيان طويل" required aria-label="بيان السطر ${i + 1}">${esc(l.desc)}</textarea></td><td>${lines.length > 2 ? `<button type="button" class="btn sm danger" data-x="${i}">×</button>` : ""}</td></tr>`).join("");
      q("#ln").querySelectorAll('textarea[data-k="desc"]').forEach(el => { el.style.height = "auto"; el.style.height = `${el.scrollHeight}px`; });
      sum();
    };
    const sum = () => {
      const d = lines.reduce((a, l) => a + (+l.d || 0), 0), c = lines.reduce((a, l) => a + (+l.c || 0), 0);
      q("#td").textContent = d.toFixed(2); q("#tc").textContent = c.toFixed(2);
      q("#bal").innerHTML = Math.abs(d - c) < 0.005 && d > 0 ? '<span class="tag ok">متوازن</span>' : `<span class="tag bad">فرق ${(d - c).toFixed(2)}</span>`;
    };
    q("#ln").oninput = ev => { const t = ev.target, i = t.dataset.i; if (i === undefined) return; lines[i][t.dataset.k] = t.value;
      if (t.dataset.k === "label") { lines[i].account_id = null; t.setAttribute("aria-expanded", "true"); searchAccounts(+i, t.value); }
      if (t.dataset.k === "d" && +t.value > 0) { lines[i].c = ""; t.closest("tr").querySelector('[data-k="c"]').value = ""; }
      if (t.dataset.k === "c" && +t.value > 0) { lines[i].d = ""; t.closest("tr").querySelector('[data-k="d"]').value = ""; }
      if (t.dataset.k === "desc") { t.style.height = "auto"; t.style.height = `${t.scrollHeight}px`; }
      sum(); };
    q("#ln").onmousedown = ev => { const option = ev.target.closest(".journal-account-option"); if (!option) return; ev.preventDefault(); chooseAccount(+option.dataset.line, +option.dataset.accountId); };
    q("#ln").onfocusin = ev => { const input = ev.target.closest('input[data-k="label"]'); if (input) searchAccounts(+input.dataset.i, "", true); };
    q("#ln").onfocusout = ev => { const input = ev.target.closest('input[data-k="label"]'); if (!input) return; setTimeout(() => { if (!q(`#account-picker-${input.dataset.i}`)?.contains(document.activeElement)) { const box = q(`#account-options-${input.dataset.i}`); if (box) box.hidden = true; input.setAttribute("aria-expanded", "false"); } }, 0); };
    q("#ln").onkeydown = ev => {
      const input = ev.target.closest('input[data-k="label"]'), option = ev.target.closest(".journal-account-option");
      if (input && ev.key === "ArrowDown") { const first = q(`#account-options-${input.dataset.i} .journal-account-option`); if (first) { ev.preventDefault(); first.focus(); } }
      else if (input && ev.key === "Enter") { const opts = [...q(`#account-options-${input.dataset.i}`).querySelectorAll(".journal-account-option")], exact = accs.find(a => a.label.toLocaleLowerCase() === input.value.trim().toLocaleLowerCase()); ev.preventDefault(); if (exact) chooseAccount(+input.dataset.i, exact.account_id); else if (opts.length === 1) chooseAccount(+input.dataset.i, +opts[0].dataset.accountId); else opts[0]?.focus(); }
      else if (option && (ev.key === "ArrowDown" || ev.key === "ArrowUp")) { ev.preventDefault(); const opts = [...option.parentElement.querySelectorAll(".journal-account-option")], n = opts.indexOf(option) + (ev.key === "ArrowDown" ? 1 : -1); (opts[n] || (ev.key === "ArrowUp" ? q(`input[data-i="${option.dataset.line}"][data-k="label"]`) : opts[0]))?.focus(); }
      else if (option && ev.key === "Enter") { ev.preventDefault(); chooseAccount(+option.dataset.line, +option.dataset.accountId); q(`input[data-i="${option.dataset.line}"][data-k="label"]`)?.focus(); }
      else if (ev.key === "Escape" && (input || option)) { ev.preventDefault(); const i = input?.dataset.i || option?.dataset.line; const box = q(`#account-options-${i}`); if (box) box.hidden = true; q(`input[data-i="${i}"][data-k="label"]`)?.focus(); }
    };
    q("#ln").onclick = ev => { const input = ev.target.closest('input[data-k="label"]'); if (input) { searchAccounts(+input.dataset.i, "", true); return; } const x = ev.target.dataset?.x; if (x !== undefined) { lines.splice(+x, 1); draw(); } };
    q("#addl").onclick = () => { lines.push({ account_id: null, label: "", project_id: "", d: "", c: "", desc: "" }); draw(); };
    q("form").onsubmit = async ev => {
      if (ev.submitter?.value !== "ok") return;
      ev.preventDefault();
      try {
        const body = { entry_date: q("#dt").value, source_settlement_id: q("#settlement").value ? +q("#settlement").value : null, lines: lines.filter(l => l.label || l.d || l.c || l.desc).map(l => {
          const id = l.account_id || accByLabel[l.label]; if (!id) throw new Error(`اختار الحساب من نتائج البحث بالاسم أو الكود: «${l.label || "فارغ"}»`);
          return { account_id: id, project_id: l.project_id ? +l.project_id : null, debit_amount: String(+l.d || 0), credit_amount: String(+l.c || 0), description: l.desc.trim() || null };
        }) };
        await api(e ? "/journal/" + e.journal_entry_id : "/journal", { method: e ? "PUT" : "POST", json: body });
        dlg.close(); toast("تم الحفظ كمسودة"); await load();
      } catch (er) { q("#er").textContent = errText(er); }
    };
    draw(); dlg.showModal();
  }
  if (can("Add")) $("#add").onclick = () => editor(null);
  if (can("Approve")) $("#fy").onclick = safe(async () => {
    const fys = await api("/journal/fiscal-years");
    const dlg = formDialog({ title: "السنوات المالية", submitText: "إضافة سنة", values: { start_date: `${new Date().getFullYear()}-01-01`, end_date: `${new Date().getFullYear()}-12-31` },
      fields: [{ name: "start_date", label: "بداية السنة", type: "date", required: true }, { name: "end_date", label: "نهاية السنة", type: "date", required: true }, { name: "company_name", label: "اسم الشركة (لأول سنة فقط)", full: true }],
      onSubmit: async v => { await api("/journal/fiscal-years", { method: "POST", json: { start_date: v.start_date, end_date: v.end_date, company_name: v.company_name || "الشركة" } }); toast("تمت الإضافة"); } });
    dlg.querySelector("h3").insertAdjacentHTML("afterend", `<p class="muted">الموجود: ${fys.map(f => `${f.start_date} → ${f.end_date}`).join(" | ") || "لا توجد سنوات"}</p>`);
  });
  await load();
}
