// معاينة وطباعة الشيك بمقاس ومواضع قابلة للضبط (بالمليمتر) + إزاحة عامة (زود/نقّص) لكل دفتر شيكات.
import { esc, money, toast, safe } from "./ui.js";

const LABELS = { check_date: "التاريخ", payee_note: "عبارة الصرف", beneficiary: "المستفيد", amount_words: "التفقيط", amount_number: "المبلغ بالأرقام", signatory_1: "اسم التوقيع الأول", signatory_2: "اسم التوقيع الثاني" };
const ALIGN = { Left: "يسار", Center: "منتصف", Right: "يمين" };
const num = (v, d = 0) => (Number.isFinite(+v) && v !== "" ? +v : d);
const AR_DIGITS = "٠١٢٣٤٥٦٧٨٩";
const formatChequeDate = value => {
  const m = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return value || "";
  const months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"];
  return `${m[3]} ${months[Number(m[2]) - 1] || m[2]} ${m[1]}`.replace(/\d/g, d => AR_DIGITS[Number(d)]);
};

/** HTML الشيك بمقاس الورقة بالمللي. frame=true يرسم إطار الشيك وخطوط معايرة (للتجربة على ورقة عادية). */
export function checkHTML(cfg, c, { frame = false, autoprint = false } = {}) {
  const W = num(cfg.page_w, 184.2), H = num(cfg.page_h, 76.2), ox = num(cfg.offset_x), oy = num(cfg.offset_y);
  const val = {
    check_date: formatChequeDate(c.check_date), payee_note: "يصرف للمستفيد الأول", beneficiary: c.beneficiary || "", amount_words: c.amount_words || "",
    amount_number: money(c.amount) === "-" ? "" : money(c.amount),
    signatory_1: cfg.fields.find(f => f.name === "signatory_1")?.text || "أسامه شوقت حافظ خليل",
    signatory_2: cfg.fields.find(f => f.name === "signatory_2")?.text || "محمد احمد محمد مصطفى",
  };
  const fields = cfg.fields.map(f => {
    const x = num(f.x) + ox, y = num(f.y) + oy;
    const tr = f.align === "Right" ? "translateX(-100%)" : f.align === "Center" ? "translateX(-50%)" : "none";
    const maxw = Math.max(10, f.align === "Right" ? x - 2 : f.align === "Center" ? 2 * Math.min(x, W - x) - 2 : W - x - 2);
    const textAlign = f.align === "Right" ? "right" : f.align === "Center" ? "center" : "left";
    const dir = f.name === "amount_number" ? "ltr" : "rtl";
    // Give each absolutely positioned field its available column width.
    // Without an explicit width, browsers shrink-to-fit the Arabic text around
    // the longest word, causing amount-in-words to stack vertically.
    return `<div class="f" style="left:${x}mm;top:${y}mm;width:${maxw}mm;max-width:${maxw}mm;text-align:${textAlign};font-size:${num(f.font_size, 11)}pt;transform:${tr};direction:${dir}">${esc(val[f.name])}</div>`;
  }).join("");
  const guides = frame ? `<div class="fr"></div><div class="gx"></div><div class="gy"></div>` +
    cfg.fields.map(f => `<div class="pt" style="left:${num(f.x) + ox}mm;top:${num(f.y) + oy}mm"></div>`).join("") : "";
  return `<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>شيك ${esc(c.check_no || c.sequence_no || "")}</title>
<style>@page{size:${W}mm ${H}mm;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0;background:#fff}
body{width:${W}mm;height:${H}mm;position:relative;overflow:hidden;font-family:Tahoma,Arial,sans-serif;color:#000}
.f{position:absolute;white-space:normal;line-height:1.3;transform-origin:top left}
.fr{position:absolute;inset:0;border:.3mm solid #c00}.gx,.gy{position:absolute;background:#c00;opacity:.35}
.gx{left:0;right:0;top:${H / 2}mm;height:.15mm}.gy{top:0;bottom:0;left:${W / 2}mm;width:.15mm}
.pt{position:absolute;width:2mm;height:2mm;margin:-1mm 0 0 -1mm;border:.2mm solid #c00;border-radius:50%}</style>
<body>${fields}${guides}${autoprint ? "<script>onload=()=>setTimeout(()=>print(),150)</script>" : ""}</body></html>`;
}

export function printCheck(cfg, c, opts = {}) {
  const w = window.open("", "_blank");
  if (!w) return toast("اسمح بالنوافذ المنبثقة للطباعة");
  w.document.write(checkHTML(cfg, c, { ...opts, autoprint: true }));
  w.document.close();
}

export async function openPrintDialog({ api, base, check, canEdit }) {
  const cfg = await api(base + "/print-template");
  let signatoryOptions = [];
  try { signatoryOptions = (await api(base + "/signatories"))?.items || []; } catch { /* Custom names can still be entered. */ }
  // The template is scoped to the treasury account (checkbook), so make that
  // scope explicit before the user changes or saves calibration values.
  const bookLabel = [check.bank || "البنك", check.bank_account_no ? `حساب ${check.bank_account_no}` : "",
    check.check_book_no ? `دفتر ${check.check_book_no}` : ""].filter(Boolean).join(" — ");
  const dlg = document.createElement("dialog"); dlg.style.width = "min(980px,96vw)";
  const step = 0.5;
  const numIn = (id, v, min, max) => `<input type="number" data-k="${id}" value="${v}" step="0.1" min="${min}" max="${max}" style="width:88px">`;
  dlg.innerHTML = `<form method="dialog" style="padding:18px">
    <h3 style="margin:0 0 4px">معاينة وطباعة الشيك — ${esc(check.beneficiary)} <small class="muted">${esc(check.check_no || "")}</small></h3>
    <p style="margin:0 0 4px;font-size:13px"><b>قالب الطباعة لهذا الدفتر:</b> ${esc(bookLabel)}</p>
    <p class="muted" style="margin:0 0 12px;font-size:13px">المقاسات بالمليمتر من الحافة العلوية اليسرى للشيك، وتُحفظ لهذا الحساب البنكي فقط. عايرها بتجربة الإطار على ورقة عادية فوق الشيك. عند الطباعة اختر الحجم الفعلي / 100%، وأوقف الرؤوس والتذييلات، واجعل الهوامش بلا هوامش.</p>
    <div style="display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start">
      <div style="flex:1 1 560px;min-width:0;overflow:auto;border:1px dashed var(--line);border-radius:8px;padding:10px;background:var(--bg)"><iframe id="pv" style="border:1px solid #888;background:#fff;display:block;margin:auto" title="معاينة"></iframe></div>
      <div style="flex:0 0 330px;max-width:100%">
        <div class="grid2" style="margin-bottom:10px">
          <div class="f"><label>عرض الشيك (مم)</label>${numIn("page_w", cfg.page_w, 50, 400)}</div>
          <div class="f"><label>طول الشيك (مم)</label>${numIn("page_h", cfg.page_h, 30, 400)}</div>
        </div>
        <label>إزاحة عامة (تحريك كل النصوص معًا)</label>
        <div style="display:grid;grid-template-columns:auto 1fr auto;gap:6px;align-items:center;margin-bottom:6px"><span>يمين/يسار</span><span></span>
          <span><button type="button" class="btn sm" data-n="offset_x:-${step}">◀ يسار</button> <input type="number" data-k="offset_x" value="${cfg.offset_x}" step="0.1" style="width:76px"> <button type="button" class="btn sm" data-n="offset_x:${step}">يمين ▶</button></span>
          <span>فوق/تحت</span><span></span>
          <span><button type="button" class="btn sm" data-n="offset_y:-${step}">▲ فوق</button> <input type="number" data-k="offset_y" value="${cfg.offset_y}" step="0.1" style="width:76px"> <button type="button" class="btn sm" data-n="offset_y:${step}">تحت ▼</button></span></div>
        <label>الموقّعون على الشيك (اكتب للبحث أو اختر اسمًا)</label>
        <datalist id="check-signatory-options">${signatoryOptions.map(name => `<option value="${esc(name)}"></option>`).join("")}</datalist>
        <div class="grid2" style="margin:6px 0 10px">
          ${["signatory_1", "signatory_2"].map((name, ix) => {
            const field = cfg.fields.find(f => f.name === name);
            field.text ||= ix === 0 ? "أسامه شوقت حافظ خليل" : "محمد احمد محمد مصطفى";
            return `<div><label for="${name}">${LABELS[name]}</label><input id="${name}" data-text="${name}" list="check-signatory-options" value="${esc(field.text)}" maxlength="200" autocomplete="off"></div>`;
          }).join("")}
        </div>
        <div class="tbl-wrap" style="margin:10px 0"><table style="font-size:13px"><thead><tr><th>الحقل</th><th>X</th><th>Y</th><th>خط</th><th>محاذاة</th></tr></thead><tbody>
          ${cfg.fields.map((f, i) => `<tr><td>${LABELS[f.name]}</td><td><input type="number" data-f="${i}.x" value="${f.x}" step="0.5" style="width:70px;padding:4px"></td><td><input type="number" data-f="${i}.y" value="${f.y}" step="0.5" style="width:70px;padding:4px"></td>
          <td><input type="number" data-f="${i}.font_size" value="${f.font_size}" step="0.5" min="6" max="48" style="width:60px;padding:4px"></td>
          <td><select data-f="${i}.align" style="padding:4px">${Object.entries(ALIGN).map(([k, l]) => `<option value="${k}" ${k === f.align ? "selected" : ""}>${l}</option>`).join("")}</select></td></tr>`).join("")}</tbody></table></div>
        <label style="display:flex;gap:6px;align-items:center"><input type="checkbox" id="fr" style="width:auto"> إظهار إطار ونقاط المعايرة في المعاينة</label>
        <div class="err" data-err></div>
      </div></div>
    <div class="actions"><button type="button" class="btn primary" id="pr">طباعة الشيك</button><button type="button" class="btn" id="tp">طباعة اختبار المعايرة</button>${canEdit ? '<button type="button" class="btn" id="sv">حفظ الإعدادات</button><button type="button" class="btn" id="rs">الرجوع للقيم المبدئية</button>' : ""}<button class="btn" value="x" formnovalidate>إغلاق</button></div></form>`;
  document.body.appendChild(dlg);
  const $ = s => dlg.querySelector(s), pv = $("#pv");
  const read = () => {
    dlg.querySelectorAll("[data-k]").forEach(i => (cfg[i.dataset.k] = num(i.value, cfg[i.dataset.k])));
    dlg.querySelectorAll("[data-f]").forEach(i => { const [n, k] = i.dataset.f.split("."); cfg.fields[n][k] = k === "align" ? i.value : num(i.value, cfg.fields[n][k]); });
    dlg.querySelectorAll("[data-text]").forEach(i => { const f = cfg.fields.find(x => x.name === i.dataset.text); if (f) f.text = i.value; });
  };
  const draw = () => { read(); pv.style.width = cfg.page_w + "mm"; pv.style.height = cfg.page_h + "mm"; pv.srcdoc = checkHTML(cfg, check, { frame: $("#fr").checked }); };
  dlg.addEventListener("input", draw); dlg.addEventListener("change", draw);
  dlg.addEventListener("click", ev => {
    const b = ev.target.closest("[data-n]"); if (!b) return;
    const [k, d] = b.dataset.n.split(":"), inp = $(`[data-k="${k}"]`);
    inp.value = Math.max(-30, Math.min(30, Math.round((num(inp.value) + +d) * 100) / 100)); draw();
  });
  // Actual cheque output follows the supplied workbook layout; calibration
  // guides are available only through the explicitly named test action.
  $("#pr").onclick = () => { read(); printCheck(cfg, check); };
  $("#tp").onclick = () => { read(); printCheck(cfg, check, { frame: true }); };
  if (canEdit) {
    $("#sv").onclick = safe(async () => {
      read();
      await api(base + "/print-template", { method: "PUT", json: { page_w: cfg.page_w, page_h: cfg.page_h, offset_x: cfg.offset_x, offset_y: cfg.offset_y, fields: cfg.fields } });
      toast(`تم حفظ إعدادات الطباعة: ${bookLabel}`);
    });
    $("#rs").onclick = () => { if (!confirm("الرجوع للقيم المبدئية؟ (مش هتتحفظ إلا لما تضغط حفظ)")) return;
      Object.assign(cfg, { page_w: 184.2, page_h: 76.2, offset_x: 0, offset_y: 0 });
      const d = [[170, 10, 11, "Right"], [125, 21, 12, "Right"], [170, 30, 12, "Right"], [170, 42, 12, "Right"], [180, 51, 13, "Right"], [170, 68, 9, "Right"], [115, 68, 9, "Center"]];
      cfg.fields.forEach((f, i) => Object.assign(f, { x: d[i][0], y: d[i][1], font_size: d[i][2], align: d[i][3] }));
      cfg.fields.find(f => f.name === "signatory_1").text = "أسامه شوقت حافظ خليل";
      cfg.fields.find(f => f.name === "signatory_2").text = "محمد احمد محمد مصطفى";
      dlg.querySelectorAll("[data-k]").forEach(i => (i.value = cfg[i.dataset.k]));
      dlg.querySelectorAll("[data-f]").forEach(i => { const [n, k] = i.dataset.f.split("."); i.value = cfg.fields[n][k]; });
      dlg.querySelectorAll("[data-text]").forEach(i => { i.value = cfg.fields.find(f => f.name === i.dataset.text)?.text || ""; }); draw(); };
  }
  dlg.addEventListener("close", () => dlg.remove());
  dlg.showModal(); draw();
}
