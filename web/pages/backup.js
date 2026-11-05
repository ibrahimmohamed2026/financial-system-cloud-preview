import { api, auth } from "../api.js";
import { esc, toast, errText } from "../ui.js";

const KIND = { manual: "يدوية", auto: "تلقائية", pre_restore: "أمان قبل استعادة", backup: "قديمة" };
const mb = n => (n / 1048576).toFixed(n < 104857 ? 2 : 1) + " MB";
const when = iso => (iso || "").replace("T", " ");

export async function render(main) {
  main.innerHTML = `<section class="sec"><h3>النسخ الاحتياطي والصيانة</h3>
    <div style="padding:16px">
      <div id="info" class="muted">جاري التحميل...</div>
      <details id="cfg" style="margin-top:12px"><summary><b>إعدادات النسخ الاحتياطي (المكان والمواعيد)</b></summary>
        <div class="toolbar" style="margin-top:10px">
          <div class="grow"><label for="cfgdir">مجلد حفظ النسخ (مسار كامل)</label><br><input id="cfgdir" dir="ltr" style="width:100%" placeholder="D:/Backups/financial"></div>
          <div><label for="cfgtime">وقت النسخ اليومي</label><br><input id="cfgtime" type="time" dir="ltr"></div>
          <div><label for="cfgkeep">عدد النسخ المحتفظ بها</label><br><input id="cfgkeep" type="number" min="1" max="365" style="width:90px"></div>
          <div><label><input id="cfgon" type="checkbox"> تفعيل النسخ اليومي</label></div>
          <button class="btn primary" id="cfgsave">حفظ الإعدادات</button>
        </div>
        <p class="muted">التغيير يسري فورًا. لازم المجلد يكون متاح وعليه صلاحية كتابة (يُنشأ تلقائيًا لو غير موجود). النسخ القديمة تفضل في المكان القديم. يُفضّل قرص أو جهاز غير اللي عليه قاعدة البيانات.</p>
      </details>
      <div class="toolbar" style="margin-top:14px">
        <button class="btn primary" id="dl">نسخة احتياطية الآن وتنزيلها</button>
        <button class="btn" id="save">حفظ نسخة في مجلد النسخ فقط</button>
      </div>
      <p class="muted">النسخة تشمل قاعدة البيانات كاملة + ملفات النظام. لا تتضمن ملف <code>.env</code> (فيه كلمات مرور وأسرار) فاحتفظ به بشكل منفصل.</p>
      <hr>
      <h4>استعادة نسخة احتياطية</h4>
      <div class="toolbar">
        <div class="grow"><label for="restorefile">اختر ملف النسخة (ZIP)</label><br><input id="restorefile" type="file" accept=".zip,application/zip"></div>
        <button class="btn danger" id="restore">استعادة من الملف</button>
      </div>
      <p class="muted">تحذير: الاستعادة تستبدل كل بيانات النظام الحالية. قبل الاستبدال يتم أخذ نسخة أمان تلقائية، ولو فشلت الاستعادة لا يتغير أي شيء. ملفات النظام داخل النسخة للأرشفة ولا تُستبدل.</p>
      <hr>
      <h4>النسخ المحفوظة على السيرفر</h4>
      <div class="tbl-wrap"><table><thead><tr><th>الملف</th><th>النوع</th><th>التاريخ</th><th>الحجم</th><th></th></tr></thead>
        <tbody id="rows"><tr><td colspan="5" class="muted">...</td></tr></tbody></table></div>
      <div class="err" id="err"></div>
    </div></section>`;
  const $ = s => main.querySelector(s);
  const setBusy = (busy) => main.querySelectorAll("button").forEach(b => (b.disabled = busy));
  const run = async (fn) => {
    $("#err").textContent = ""; setBusy(true);
    try { await fn(); } catch (e) { $("#err").textContent = errText(e); } finally { setBusy(false); }
  };

  async function download(path, fallbackName) {
    const r = await api(path, { raw: true });
    const cd = r.headers.get("Content-Disposition") || "";
    const name = (cd.match(/filename="?([^";]+)"?/) || [])[1] || fallbackName;
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a"); a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }

  function afterRestore(d) {
    toast(d.message || "تمت الاستعادة");
    auth.clear();
    setTimeout(() => { location.hash = "#/login"; location.reload(); }, 1500);
  }

  function confirmRestore(label) {
    return confirm(`تحذير: سيتم استبدال كل بيانات النظام الحالية بمحتوى:\n${label}\n\nسيتم أخذ نسخة أمان تلقائية قبل الاستبدال. هل تريد المتابعة؟`)
      && confirm("تأكيد أخير: بعد الاستعادة ستُغلق جلستك وتحتاج لتسجيل الدخول من جديد. هل أنت متأكد؟");
  }

  function fillCfg(s) {
    $("#cfgdir").value = s.backup_dir; $("#cfgtime").value = s.auto_time;
    $("#cfgkeep").value = s.retention; $("#cfgon").checked = !!s.auto_enabled;
  }

  async function load() {
    const s = await api("/admin/backup/status");
    if (!$("#cfg").open) fillCfg(s);
    $("#info").innerHTML = `قاعدة البيانات: <b>${esc(s.db_backend)}</b> · مجلد النسخ: <code>${esc(s.backup_dir)}</code><br>
      النسخ اليومي التلقائي: ${s.auto_enabled ? `<span class="tag ok">مفعّل</span> الساعة <b>${esc(s.auto_time)}</b> يوميًا (يُحتفظ بآخر ${s.retention} نسخة)` : `<span class="tag no">متوقف</span>`}
      ${s.last_auto ? `· آخر نسخة تلقائية: ${esc(when(s.last_auto.created_at))}` : "· لم تتم أي نسخة تلقائية بعد"}`;
    $("#rows").innerHTML = s.backups.length ? s.backups.map(b => `<tr><td dir="ltr">${esc(b.name)}</td><td>${esc(KIND[b.kind] || b.kind)}</td>
        <td dir="ltr">${esc(when(b.created_at))}</td><td dir="ltr">${mb(b.size)}</td>
        <td><button class="btn sm" data-dl="${esc(b.name)}">تنزيل</button> <button class="btn sm danger" data-rs="${esc(b.name)}">استعادة</button></td></tr>`).join("")
      : `<tr><td colspan="5" class="muted">لا توجد نسخ بعد</td></tr>`;
    main.querySelectorAll("[data-dl]").forEach(b => b.onclick = () => run(() => download("/admin/backup/download/" + encodeURIComponent(b.dataset.dl), b.dataset.dl)));
    main.querySelectorAll("[data-rs]").forEach(b => b.onclick = () => {
      if (!confirmRestore(b.dataset.rs)) return;
      run(async () => {
        const fd = new FormData(); fd.append("confirm", "yes");
        afterRestore(await api("/admin/backup/restore/" + encodeURIComponent(b.dataset.rs), { method: "POST", form: fd }));
      });
    });
  }

  $("#cfgsave").onclick = () => run(async () => {
    const d = await api("/admin/backup/settings", { method: "PUT", json: {
      backup_dir: $("#cfgdir").value, auto_time: $("#cfgtime").value,
      retention: +$("#cfgkeep").value, auto_enabled: $("#cfgon").checked } });
    toast(d.message); await load();
  });
  $("#dl").onclick = () => run(async () => { await download("/admin/backup", "financial_system_backup.zip"); toast("تم إنشاء النسخة وتنزيلها"); await load(); });
  $("#save").onclick = () => run(async () => { const d = await api("/admin/backup/run", { method: "POST" }); toast(d.message); await load(); });
  $("#restore").onclick = () => {
    const f = $("#restorefile").files[0];
    if (!f) { $("#err").textContent = "اختر ملف ZIP أولاً"; return; }
    if (!confirmRestore(f.name)) return;
    run(async () => {
      const fd = new FormData(); fd.append("file", f); fd.append("confirm", "yes");
      afterRestore(await api("/admin/backup/restore", { method: "POST", form: fd }));
    });
  };
  run(load);
}
