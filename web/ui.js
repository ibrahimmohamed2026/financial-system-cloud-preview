export const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const formatNumber = v => { const n = Number(v); return Number.isFinite(n) ? n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "0.00"; };
export const money = v => formatNumber(v);
let t;
export function toast(msg) {
  const el = document.getElementById("toast"); el.textContent = msg; el.hidden = false;
  clearTimeout(t); t = setTimeout(() => (el.hidden = true), 3500);
}
export function errText(e) {
  const d = e.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map(x => x.msg).join("، ");
  if (d?.reasons) return d.message + ": " + d.reasons.join("، ");
  return d?.message || e.message || "حدث خطأ";
}

export const today = () => new Date().toISOString().slice(0, 10);
export const fmtDate = d => d || "";

/** نافذة نموذج عامة. fields: [{name,label,type:text|number|date|select|textarea,options:[[v,l]],required,step,full}] */
export function formDialog({ title, fields, values = {}, submitText = "حفظ", onSubmit, onOpen }) {
  const dlg = document.createElement("dialog");
  const inp = f => {
    const v = values[f.name] ?? "";
    const req = f.required ? "required" : "";
    if (f.type === "select") {
      const options = (f.optional ? [['', '— بدون —']] : []).concat(f.options || []);
      const select = `<select name="${f.name}" ${req} ${f.searchable ? 'data-searchable-select="true"' : ''}>${options.map(([val, l]) => `<option value="${esc(val)}" ${String(val) === String(v) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
      return f.searchable ? `<input type="search" data-select-search="${f.name}" placeholder="ابحث بالكود أو اسم الحساب..." autocomplete="off" aria-label="البحث في ${esc(f.label)}" style="width:100%;margin-bottom:6px"><div class="muted" style="font-size:12px;margin-bottom:4px">اكتب كود الحساب أو جزءًا من اسمه، ثم اختر النتيجة.</div>${select}` : select;
    }
    if (f.readonly) return `<input name="${f.name}" value="${esc(v)}" readonly tabindex="-1" style="background:var(--bg)">`;
    if (f.type === "textarea") return `<textarea name="${f.name}" rows="${f.rows || 5}" ${req} style="width:100%;min-height:${f.minHeight || 120}px;resize:vertical;box-sizing:border-box;">${esc(v)}</textarea>`;
    return `<input name="${f.name}" type="${f.type || "text"}" value="${esc(v)}" ${f.step ? `step="${f.step}"` : ""} ${f.min !== undefined ? `min="${f.min}"` : ""} ${req}>`;
  };
  dlg.innerHTML = `<form method="dialog"><h3>${esc(title)}</h3><div class="grid2">${fields.map(f => `<div class="f" ${f.full ? 'style="grid-column:1/-1"' : ""}><label>${esc(f.label)}</label>${inp(f)}</div>`).join("")}</div>
    <div class="err" data-err></div><div class="actions"><button class="btn primary" value="ok">${esc(submitText)}</button><button class="btn" value="x" formnovalidate>إلغاء</button></div></form>`;
  document.body.appendChild(dlg);
  const form = dlg.querySelector("form");
  // Searchable selects filter options in place, preserving the selected internal ID.
  form.querySelectorAll("input[data-select-search]").forEach(search => {
    const select = form.elements.namedItem(search.dataset.selectSearch);
    if (!(select instanceof HTMLSelectElement)) return;
    search.addEventListener("input", () => {
      const q = search.value.trim().toLocaleLowerCase();
      for (const option of select.options) {
        const haystack = `${option.textContent || ""} ${option.value}`.toLocaleLowerCase();
        option.hidden = Boolean(q) && !haystack.includes(q);
      }
      // Never silently assign a different account just because the search text changed.
      const current = select.selectedOptions[0];
      if (current?.hidden) select.selectedIndex = -1;
    });
    search.addEventListener("keydown", ev => {
      if (ev.key === "ArrowDown") { ev.preventDefault(); select.focus(); }
    });
  });
  form.onsubmit = async ev => {
    if (ev.submitter?.value !== "ok") return;
    ev.preventDefault();
    const out = {}; for (const [k, v] of new FormData(form)) { const el = form.elements.namedItem(k); out[k] = typeof v === "string" ? (el instanceof HTMLTextAreaElement ? v : v.trim()) : v; }
    try { await onSubmit(out); dlg.close(); } catch (e) { form.querySelector("[data-err]").textContent = errText(e); }
  };
  dlg.addEventListener("close", () => dlg.remove());
  dlg.showModal();
  dlg.querySelectorAll("textarea").forEach(area => {
    const resize = () => { area.style.height = "auto"; area.style.height = `${Math.max(area.scrollHeight, Number.parseInt(area.style.minHeight, 10) || 120)}px`; };
    area.addEventListener("input", resize);
    resize();
  });
  onOpen?.(dlg, form);
  return dlg;
}

export const opt = (arr, v, l) => arr.map(x => [x[v], typeof l === "function" ? l(x) : x[l]]);
export const statusTag = s => `<span class="tag">${esc(s)}</span>`;
export const wrap = (main, html) => { main.innerHTML = html; return s => main.querySelector(s); };
export const safe = fn => async (...a) => { try { await fn(...a); } catch (e) { toast(errText(e)); } };
