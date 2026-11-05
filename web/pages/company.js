import { esc, toast, safe } from "../ui.js";

export async function render(main, { api }) {
  const data = await api("/admin/company").catch(() => null);
  main.innerHTML = `<section class="panel" style="max-width:1000px;margin:auto">
    <h3>بيانات الشركة</h3>
    <p class="muted">تظهر هذه البيانات في ترويسة طباعة العقود والقيود والمستخلصات.</p>
    <form id="company-form" class="grid2">
      <div class="f"><label>اسم الشركة بالعربية</label><input name="name_ar" maxlength="200" required></div>
      <div class="f"><label>اسم الشركة بالإنجليزية</label><input name="name_en" maxlength="200"></div>
      <div class="f"><label>الرقم الضريبي</label><input name="tax_number" maxlength="50"></div>
      <div class="f"><label>رقم السجل التجاري</label><input name="commercial_register" maxlength="50"></div>
      <div class="f"><label>رقم الهاتف</label><input name="phone" maxlength="50"></div>
      <div class="f"><label>البريد الإلكتروني</label><input name="email" type="email" maxlength="200"></div>
      <div class="f"><label>الموقع الإلكتروني</label><input name="website" type="url" maxlength="200" placeholder="https://"></div>
      <div class="f"><label>العنوان</label><input name="address_ar" maxlength="500"></div>
      <div class="f" style="grid-column:1/-1"><label>شعار الشركة (PNG / JPG / WebP — بحد أقصى 1 ميجابايت)</label><input id="logo-file" type="file" accept="image/png,image/jpeg,image/webp"><div style="display:flex;align-items:center;gap:12px;margin-top:8px"><img id="logo-preview" alt="معاينة الشعار" style="max-width:200px;max-height:90px;object-fit:contain"><button class="btn sm" type="button" id="logo-clear">إزالة الشعار</button></div></div>
      <div class="err" id="company-error" style="grid-column:1/-1"></div>
      <div class="actions" style="grid-column:1/-1"><button class="btn primary" type="submit">حفظ بيانات الشركة</button></div>
    </form></section>`;
  const form = main.querySelector("#company-form"), preview = main.querySelector("#logo-preview");
  let logoData = data?.logo_data || null;
  for (const [name, value] of Object.entries(data || {})) {
    if (form.elements[name]) form.elements[name].value = value || "";
  }
  if (logoData) preview.src = logoData; else preview.hidden = true;
  main.querySelector("#logo-file").onchange = safe(async ev => {
    const file = ev.target.files?.[0];
    if (!file) return;
    if (file.size > 1024 * 1024) { ev.target.value = ""; throw new Error("حجم الشعار يجب ألا يتجاوز 1 ميجابايت"); }
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) { ev.target.value = ""; throw new Error("اختر شعارًا بصيغة PNG أو JPG أو WebP"); }
    logoData = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error("تعذرت قراءة ملف الشعار")); reader.readAsDataURL(file); });
    preview.src = logoData; preview.hidden = false;
  });
  main.querySelector("#logo-clear").onclick = () => { logoData = null; preview.removeAttribute("src"); preview.hidden = true; main.querySelector("#logo-file").value = ""; };
  form.onsubmit = safe(async ev => {
    ev.preventDefault();
    const body = Object.fromEntries(new FormData(form));
    body.logo_data = logoData;
    const saved = await api("/admin/company", { method: "PUT", json: body });
    logoData = saved.logo_data || null;
    toast("تم حفظ بيانات الشركة");
  });
}
