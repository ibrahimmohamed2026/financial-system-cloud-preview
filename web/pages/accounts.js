import { esc, money, toast, errText } from "../ui.js";

const SCREEN = "ChartOfAccounts", PAGE = 50;

export async function render(main, { api, auth }) {
  const can = a => auth.can(SCREEN, a);
  const cls = await api("/accounts/classifications");
  const clsName = Object.fromEntries(cls.map(c => [c.classification_id, c.name_ar]));
  const st = { q: "", cid: "", active: "", skip: 0 };
  let parents = [];

  main.innerHTML = `
  <div class="accounts-toolbar" dir="rtl">
    <div class="accounts-filters">
      <div class="accounts-filter-search"><label for="q">بحث برقم أو اسم الحساب</label><input id="q" type="search" placeholder="اكتب كود الحساب أو اسمه..."></div>
      <div><label for="cid">التصنيف</label><select id="cid"><option value="">كل التصنيفات</option>${cls.map(c => `<option value="${c.classification_id}">${esc(c.name_ar)}</option>`).join("")}</select></div>
      <div><label for="act">الحالة</label><select id="act"><option value="">كل الحالات</option><option value="true">نشط</option><option value="false">موقوف</option></select></div>
    </div>
    <div class="accounts-toolbar-actions">
      ${can("Add") ? `<button class="btn primary" id="add">+ حساب جديد</button><button class="btn" id="imp">استيراد Excel</button>` : ""}
      ${can("Print") ? `<button class="btn" id="pdf">طباعة PDF</button>` : ""}
    </div>
  </div>
  <div class="tbl-wrap"><table><thead><tr><th>الكود</th><th>اسم الحساب</th><th>التصنيف</th><th>الطبيعة</th><th>مدين افتتاحي</th><th>دائن افتتاحي</th><th>الحالة</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>
  <div class="pager"><button class="btn sm" id="prev">السابق</button><span id="info"></span><button class="btn sm" id="next">التالي</button></div>
  <dialog id="dlg"></dialog>`;
  const $ = s => main.querySelector(s), dlg = $("#dlg");
  let items = [], total = 0;

  async function load() {
    const p = new URLSearchParams({ skip: st.skip, limit: PAGE });
    if (st.q) p.set("q", st.q); if (st.cid) p.set("classification_id", st.cid); if (st.active) p.set("is_active", st.active);
    const r = await api("/accounts?" + p); items = r.items; total = r.total;
    $("#rows").innerHTML = items.map(a => `<tr class="${a.is_active ? "" : "off"}"><td>${esc(a.account_code)}</td><td>${esc(a.account_name_ar)}</td>
      <td>${esc(clsName[a.classification_id])}</td><td>${a.normal_balance === "DR" ? "مدين" : "دائن"}</td>
      <td class="num">${money(a.opening_debit)}</td><td class="num">${money(a.opening_credit)}</td>
      <td><span class="tag ${a.is_active ? "ok" : "no"}">${a.is_active ? "نشط" : "موقوف"}</span></td>
      <td>${can("Edit") ? `<button class="btn sm" data-e="${a.account_id}">تعديل</button> ` : ""}${can("Delete") ? `<button class="btn sm danger" data-d="${a.account_id}">حذف</button>` : ""}</td></tr>`).join("")
      || `<tr><td colspan="8" class="muted">لا توجد حسابات مطابقة</td></tr>`;
    const to = Math.min(st.skip + PAGE, total);
    $("#info").textContent = total ? `${st.skip + 1}–${to} من ${total}` : "0";
    $("#prev").disabled = st.skip === 0; $("#next").disabled = to >= total;
  }
  const safe = fn => async (...a) => { try { await fn(...a); } catch (e) { toast(errText(e)); } };
  const reload = safe(load);

  let t; $("#q").oninput = e => { clearTimeout(t); t = setTimeout(() => { st.q = e.target.value.trim(); st.skip = 0; reload(); }, 300); };
  $("#cid").onchange = e => { st.cid = e.target.value; st.skip = 0; reload(); };
  $("#act").onchange = e => { st.active = e.target.value; st.skip = 0; reload(); };
  $("#prev").onclick = () => { st.skip = Math.max(0, st.skip - PAGE); reload(); };
  $("#next").onclick = () => { st.skip += PAGE; reload(); };

  $("#rows").onclick = safe(async ev => {
    const e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]");
    if (e) return openForm(items.find(x => x.account_id == e.dataset.e));
    if (d) {
      const a = items.find(x => x.account_id == d.dataset.d);
      if (!confirm(`حذف الحساب ${a.account_code} — ${a.account_name_ar}؟`)) return;
      await api("/accounts/" + a.account_id, { method: "DELETE" }); toast("تم الحذف"); await load();
    }
  });

  async function openForm(acc) {
    parents = (await api("/accounts?limit=1000&is_active=true")).items.filter(p => !acc || p.account_id !== acc.account_id);
    const v = acc || { account_code: "", account_name_ar: "", parent_account_id: "", classification_id: cls[0]?.classification_id, normal_balance: "DR", opening_debit: 0, opening_credit: 0, is_active: true };
    dlg.innerHTML = `<form method="dialog"><h3>${acc ? "تعديل حساب" : "حساب جديد"}</h3>
      <div class="grid2">
      <div class="f"><label>الكود</label><input name="account_code" value="${esc(v.account_code)}" required maxlength="30"></div>
      <div class="f"><label>الاسم</label><input name="account_name_ar" value="${esc(v.account_name_ar)}" required maxlength="300"></div>
      <div class="f"><label>الحساب الأب</label><select name="parent_account_id"><option value="">— بدون —</option>${parents.map(p => `<option value="${p.account_id}" ${p.account_id == v.parent_account_id ? "selected" : ""}>${esc(p.account_code)} — ${esc(p.account_name_ar)}</option>`).join("")}</select></div>
      <div class="f"><label>التصنيف</label><select name="classification_id">${cls.map(c => `<option value="${c.classification_id}" ${c.classification_id == v.classification_id ? "selected" : ""}>${esc(c.name_ar)}</option>`).join("")}</select></div>
      <div class="f"><label>طبيعة الرصيد</label><select name="normal_balance"><option value="DR" ${v.normal_balance === "DR" ? "selected" : ""}>مدين</option><option value="CR" ${v.normal_balance === "CR" ? "selected" : ""}>دائن</option></select></div>
      <div class="f"><label>الحالة</label><select name="is_active"><option value="true" ${v.is_active ? "selected" : ""}>نشط</option><option value="false" ${v.is_active ? "" : "selected"}>موقوف</option></select></div>
      <div class="f"><label>رصيد افتتاحي مدين</label><input name="opening_debit" type="number" step="0.01" min="0" value="${v.opening_debit}"></div>
      <div class="f"><label>رصيد افتتاحي دائن</label><input name="opening_credit" type="number" step="0.01" min="0" value="${v.opening_credit}"></div></div>
      <div class="err" id="fe"></div>
      <div class="actions"><button class="btn primary" value="ok">حفظ</button><button class="btn" value="x" formnovalidate>إلغاء</button></div></form>`;
    const f = dlg.querySelector("form");
    f.onsubmit = async ev => {
      if (ev.submitter?.value !== "ok") return;
      ev.preventDefault();
      const fd = new FormData(f);
      const body = {
        account_code: fd.get("account_code").trim(), account_name_ar: fd.get("account_name_ar").trim(),
        parent_account_id: fd.get("parent_account_id") ? +fd.get("parent_account_id") : null,
        classification_id: +fd.get("classification_id"), normal_balance: fd.get("normal_balance"),
        opening_debit: String(fd.get("opening_debit") || 0), opening_credit: String(fd.get("opening_credit") || 0),
        is_active: fd.get("is_active") === "true",
      };
      try {
        await api(acc ? "/accounts/" + acc.account_id : "/accounts", { method: acc ? "PUT" : "POST", json: body });
        dlg.close(); toast("تم الحفظ"); await load();
      } catch (e) { dlg.querySelector("#fe").textContent = errText(e); }
    };
    dlg.showModal();
  }
  if (can("Add")) $("#add").onclick = safe(() => openForm(null));

  async function download(path, name, open) {
    const r = await api(path, { raw: true }); const url = URL.createObjectURL(await r.blob());
    if (open) window.open(url, "_blank"); else { const a = document.createElement("a"); a.href = url; a.download = name; a.click(); }
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
  if (can("Print")) $("#pdf").onclick = safe(() => {
    const p = new URLSearchParams(); if (st.q) p.set("q", st.q); if (st.cid) p.set("classification_id", st.cid); if (st.active) p.set("is_active", st.active);
    return download("/accounts/export/pdf?" + p, "chart_of_accounts.pdf", true);
  });

  if (can("Add")) $("#imp").onclick = () => {
    dlg.innerHTML = `<form method="dialog"><h3>استيراد شجرة حسابات من Excel</h3>
      <p class="muted">الفحص أولًا بدون حفظ، ولو سليم تقدر تحفظ. الحفظ كله أو لا شيء.</p>
      <div class="f"><input type="file" id="file" accept=".xlsx"></div>
      <div class="f"><label>سياسة الاستيراد</label><p class="muted">إضافة الحسابات الجديدة فقط حسب كود الحساب؛ أي حساب موجود سيتم تخطيه دون تعديل بياناته.</p></div>
      <div class="rep" id="rep" hidden></div>
      <div class="actions"><button class="btn" value="x" id="chk" type="button">فحص</button><button class="btn primary" id="save" type="button" disabled>حفظ</button>
      <button class="btn" type="button" id="tpl">تحميل القالب</button><button class="btn" value="x" formnovalidate>إغلاق</button></div></form>`;
    const q = s => dlg.querySelector(s);
    const run = async dry => {
      const f = q("#file").files[0]; if (!f) return toast("اختر ملف .xlsx");
      const fd = new FormData(); fd.append("file", f); fd.append("dry_run", dry); fd.append("skip_existing", "true"); fd.append("update_existing", "false");
      let r; try { r = await api("/accounts/import", { method: "POST", form: fd }); } catch (e) { r = e.detail?.errors ? e.detail : null; if (!r) return toast(errText(e)); }
      const rep = q("#rep"); rep.hidden = false;
      rep.innerHTML = `<b>${r.total_rows}</b> صف — حسابات جديدة صالحة: <b>${r.valid_rows}</b> — حسابات موجودة تم تخطيها: <b>${r.skipped_existing}</b>${r.created ? ` — تمت الإضافة: <b>${r.created}</b>` : ""}` +
        (r.errors.length ? `<ul>${r.errors.map(e => `<li>صف ${e.row}: ${esc(e.message)}</li>`).join("")}</ul>` : "") +
        (dry && !r.errors.length ? `<p class="muted">معاينة فقط؛ لم يتم حفظ أي تغيير. سيتم إضافة الحسابات الجديدة فقط، والأرصدة الافتتاحية صفر، والحسابات الموجودة لن يتم تعديلها.</p>` : "");
      q("#save").disabled = !(dry && !r.errors.length && r.valid_rows);
      if (!dry && !r.errors.length) { toast("تم الاستيراد"); await load(); }
    };
    q("#chk").onclick = safe(() => run(true)); q("#save").onclick = safe(() => run(false));
    q("#tpl").onclick = safe(() => download("/accounts/import/template", "accounts_import_template.xlsx"));
    q("#file").onchange = () => (q("#save").disabled = true);
    dlg.showModal();
  };
  await load();
}
