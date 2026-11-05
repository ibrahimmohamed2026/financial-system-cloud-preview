import { esc, formDialog, toast, safe, errText } from "../ui.js";
import { translate as tr } from "../i18n.js";
const SCREEN = "CostCenters";
export async function render(main, { api, auth }) {
  const can = a => auth.can(SCREEN, a);
  main.innerHTML = `<div class="toolbar"><div class="grow"><label>${tr("بحث","Search")}</label><input id="q"></div>${can("Add") ? '<button class="btn primary" id="add">+ ${tr("مركز تكلفة / مشروع","Cost Center / Project")}</button>' : ""}</div>
    <div class="tbl-wrap"><table><thead><tr><th>#</th><th>${tr("الاسم","Name")}</th><th>${tr("الاسم بالإنجليزي","English name")}</th><th>${tr("مكتب رئيسي","Head office")}</th><th>${tr("الحالة","Status")}</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s); let items = [];
  const load = async () => {
    items = await api("/projects" + ($("#q").value.trim() ? "?q=" + encodeURIComponent($("#q").value.trim()) : ""));
    $("#rows").innerHTML = items.map(p => `<tr class="${p.is_active ? "" : "off"}"><td>${p.project_id}</td><td>${esc(p.name_ar)}</td><td>${esc(p.name_en)}</td>
      <td>${p.is_head_office ? tr("نعم","Yes") : ""}</td><td><span class="tag ${p.is_active ? "ok" : "no"}">${p.is_active ? tr("نشط","Active") : tr("موقوف","Inactive")}</span></td>
      <td>${can("Edit") ? `<button class="btn sm" data-e="${p.project_id}">${tr("تعديل","Edit")}</button> ` : ""}${can("Delete") ? `<button class="btn sm danger" data-d="${p.project_id}">${tr("حذف","Delete")}</button>` : ""}</td></tr>`).join("")
      || `<tr><td colspan="6" class="muted">${tr("لا توجد بيانات","No data")}</td></tr>`;
  };
  const form = p => formDialog({
    title: p ? tr("تعديل","Edit") : tr("مركز تكلفة جديد","New cost center"), values: p ? { ...p, is_active: String(p.is_active), is_head_office: String(p.is_head_office) } : { is_active: "true", is_head_office: "false" },
    fields: [{ name: "name_ar", label: tr("الاسم","Name"), required: true }, { name: "name_en", label: tr("الاسم بالإنجليزي","English name") },
      { name: "is_head_office", label: tr("مكتب رئيسي","Head office"), type: "select", options: [["false", tr("لا","No")], ["true", tr("نعم","Yes")]] },
      { name: "is_active", label: tr("الحالة","Status"), type: "select", options: [["true", tr("نشط","Active")], ["false", tr("موقوف","Inactive")]] }],
    onSubmit: async v => { await api(p ? "/projects/" + p.project_id : "/projects", { method: p ? "PUT" : "POST",
      json: { name_ar: v.name_ar, name_en: v.name_en || null, is_head_office: v.is_head_office === "true", is_active: v.is_active === "true" } }); toast(tr("تم الحفظ","Saved")); await load(); } });
  let t; $("#q").oninput = () => { clearTimeout(t); t = setTimeout(safe(load), 300); };
  if (can("Add")) $("#add").onclick = () => form(null);
  $("#rows").onclick = safe(async ev => {
    const e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]");
    if (e) form(items.find(x => x.project_id == e.dataset.e));
    if (d) { const p = items.find(x => x.project_id == d.dataset.d); if (!confirm(`${tr("حذف","Delete")} ${p.name_ar}?`)) return;
      await api("/projects/" + p.project_id, { method: "DELETE" }); toast(tr("تم الحذف","Deleted")); await load(); }
  });
  await load();
}
