import { toast, errText } from "./ui.js";

const CONFIG = {
  "/accounts": { resource: "accounts", importable: true },
  "/journal": { resource: "journal_entries", importable: true },
  "/inventory": { resource: "inventory_items", importable: true },
  "/purchases": { resource: "purchase_orders", importable: true },
  "/contracts": { resource: "contracts", importable: true },
  "/settlements": { resource: "contract_settlements", importable: false },
  "/admin/users": { resource: "users", importable: false },
};

export function mountDataExchange(main, api, route) {
  const cfg = CONFIG[route]; if (!cfg || main.querySelector("#dataExchangeBar")) return;
  const bar = document.createElement("div");
  bar.id = "dataExchangeBar"; bar.className = "toolbar";
  bar.style.cssText = "justify-content:flex-end;gap:8px;margin-bottom:12px;flex-wrap:wrap";
  bar.innerHTML = `<span class="muted">استيراد / تصدير</span>
    <button class="btn sm" type="button" data-export="csv">تصدير CSV</button>
    <button class="btn sm" type="button" data-export="xlsx">تصدير Excel</button>
    <button class="btn sm" type="button" id="importBtn" ${cfg.importable ? "" : 'title="هذا النوع يحتاج نموذج الشاشة المخصص للحفاظ على سلامة البيانات"'}>استيراد ملف</button>
    <input id="importFile" type="file" accept=".csv,.xlsx" hidden />`;
  main.prepend(bar);
  bar.querySelectorAll("[data-export]").forEach(btn => btn.onclick = async () => {
    btn.disabled = true;
    try {
      const r = await api(`/api/export/${cfg.resource}?format=${btn.dataset.export}`, { raw: true });
      const blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement("a");
      a.href = url; a.download = `${cfg.resource}.${btn.dataset.export}`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 30000);
      toast("تم تجهيز ملف التصدير");
    } catch (e) { toast(errText(e)); } finally { btn.disabled = false; }
  });
  const input = bar.querySelector("#importFile"), importBtn = bar.querySelector("#importBtn");
  importBtn.onclick = () => {
    if (!cfg.importable) { toast("استيراد هذا النوع من المستندات غير متاح من ملف عام؛ استخدم نموذج الشاشة المخصص للحفاظ على القيود والتفاصيل."); return; }
    input.click();
  };
  input.onchange = async () => {
    const file = input.files?.[0]; if (!file) return;
    if (file.size > 8 * 1024 * 1024) { toast("الحد الأقصى لحجم الملف 8MB"); input.value = ""; return; }
    const form = new FormData(); form.append("file", file); importBtn.disabled = true;
    try {
      const result = await api(`/api/import/${cfg.resource}`, { method: "POST", form });
      toast(result.message || `تم استيراد ${result.imported} صف`);
      location.reload();
    } catch (e) { toast(errText(e)); } finally { importBtn.disabled = false; input.value = ""; }
  };
}
