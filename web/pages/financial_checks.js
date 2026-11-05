import { esc, money, toast, safe, formDialog } from "../ui.js";
import { downloadFile } from "../api.js";

const STATUS = ["مسودة", "تحت التحصيل", "مُحصّل", "منصرف", "مُرتجع"];
const STATUS_CLASS = {"مسودة":"draft", "تحت التحصيل":"pending", "مُحصّل":"success", "منصرف":"success", "مُرتجع":"danger"};
const EGP = v => `${money(v)} <small class="ch-egp">EGP</small>`;

export async function render(main, { api, auth }) {
  const can = a => auth.can("FinancialChecks", a) || ["ChecksCib", "ChecksCairoEgp", "ChecksCairoUsd"].some(sc => auth.can(sc, a));
  const [opt, rows0] = await Promise.all([api("/checks-register/options"), api("/checks-register")]);
  let rows = rows0 || [], projectFilter = "all";
  const projects = opt.projects || [];
  const projectLabel = id => projects.find(p => String(p.id) === String(id))?.name || "بدون مشروع";
  main.innerHTML = `
  <section class="cheques-page">
    <div class="ch-hero"><div><div class="ch-eyebrow">TREASURY / CHEQUES CONTROL</div><h2>إدارة الشيكات المالية</h2><p>متابعة دفاتر الشيكات، الاستحقاقات، التحصيلات وربطها بالحسابات البنكية والمشروعات.</p></div><div class="ch-hero-chip"><span class="ch-pulse"></span> سجل الشيكات <b>LIVE</b></div></div>
    <div class="ch-bindings">
      <article class="ch-bind-card"><div class="ch-bind-icon">⌁</div><div><small>ربط حسابات البنوك</small><h3>${Number(opt.bank_binding?.active_bank_accounts || opt.banks?.length || 0)} حساب بنكي نشط</h3><p>حسابات الخزينة المتاحة لتسجيل الشيكات</p></div><span class="ch-status-pill good">متاح</span></article>
      <article class="ch-bind-card cib"><div class="ch-bind-icon">CIB</div><div><small>إعداد دفتر شيكات CIB</small><h3>${Number(opt.bank_binding?.cib_accounts || 0)} حساب مطابق</h3><p>${Number(opt.bank_binding?.cib_accounts || 0) ? "تم العثور على حساب بنكي باسم CIB / البنك التجاري" : "لم يتم اكتشاف حساب CIB بالاسم؛ راجع تعريف حساب البنك في الخزينة"}</p></div><span class="ch-status-pill ${Number(opt.bank_binding?.cib_accounts || 0) ? "good" : "warn"}">${Number(opt.bank_binding?.cib_accounts || 0) ? "مرتبط" : "يحتاج إعداد"}</span></article>
      <article class="ch-bind-card"><div class="ch-bind-icon">↗</div><div><small>ربط الشيكات بالمشروعات</small><h3>${projects.length.toLocaleString("ar-EG")} مشروع نشط</h3><p>اختر المشروع الفعلي عند تسجيل الشيك أو اربط به شيكًا غير مرحّل</p></div><span class="ch-status-pill info">مفعّل</span></article>
    </div>
    <div class="ch-kpis" id="ch-kpis"></div>
    <div class="ch-panel">
      <div class="ch-panel-head"><div><h3>سجل الشيكات</h3><p>بحث سريع وتصنيف حسب المشروع والحالة والنوع.</p></div><div class="ch-actions">${can("Print")?'<button class="ch-btn" id="ch-export">تصدير CSV</button><button class="ch-btn" id="ch-export-xlsx">تصدير Excel</button>':''}${can("Add")?'<button class="ch-btn" id="ch-import">استيراد CSV</button><input hidden type="file" id="ch-file" accept=".csv"><button class="ch-btn primary" id="ch-add">＋ تسجيل شيك</button>':''}</div></div>
      <div class="ch-tabs" id="ch-tabs"><button type="button" data-project="all" class="active">كل المشروعات</button><button type="button" data-project="none">بدون مشروع</button>${projects.map(p=>`<button type="button" data-project="${p.id}">${esc(p.name)}</button>`).join("")}</div>
      <div class="ch-filters"><label><span>بحث برقم الشيك</span><input id="ch-search" placeholder="اكتب رقم الشيك…" autocomplete="off"></label><label><span>حالة الشيك</span><select id="ch-status"><option value="">كل الحالات</option>${STATUS.map(s=>`<option value="${s}">${s}</option>`).join("")}</select></label><label><span>نوع الشيك</span><select id="ch-type"><option value="">كل الأنواع</option><option value="INCOMING">وارد من عميل</option><option value="OUTGOING">صادر لمورد</option></select></label><button class="ch-btn" id="ch-filter">تطبيق الفلاتر</button><button class="ch-btn ghost" id="ch-reset">إعادة ضبط</button></div>
      <div class="ch-table-wrap"><table class="ch-table"><thead><tr><th>رقم الشيك</th><th>المشروع</th><th>النوع</th><th>المبلغ</th><th>تاريخ الاستحقاق</th><th>البنك المسحوب عليه</th><th>حساب الطرف</th><th>الحساب البنكي المرتبط</th><th>الحالة</th><th>قيد اليومية</th><th>إجراء</th></tr></thead><tbody id="ch-rows"></tbody></table></div>
      <div class="ch-foot"><span id="ch-count">—</span><span>جميع المبالغ معروضة بالجنيه المصري EGP</span></div>
    </div>
  </section>`;
  const $ = s => main.querySelector(s);
  const accountName = id => opt.accounts?.find(a=>a.id===id)?.name || `حساب #${id ?? "—"}`;
  const bankName = id => opt.banks?.find(b=>b.id===id)?.name || `بنك #${id ?? "—"}`;
  const updateKpis = list => {
    const total = list.reduce((s,c)=>s+Number(c.amount||0),0);
    const incoming = list.filter(c=>c.check_type==="INCOMING").reduce((s,c)=>s+Number(c.amount||0),0);
    const outgoing = list.filter(c=>c.check_type==="OUTGOING").reduce((s,c)=>s+Number(c.amount||0),0);
    const pending = list.filter(c=>["مسودة","تحت التحصيل"].includes(c.status)).length;
    $("#ch-kpis").innerHTML = `<article><span>إجمالي قيمة الشيكات</span><strong>${money(total)} <small>EGP</small></strong><i>مجموع النتائج الحالية</i></article><article><span>شيكات واردة</span><strong>${money(incoming)} <small>EGP</small></strong><i>تحصيلات العملاء</i></article><article><span>شيكات صادرة</span><strong>${money(outgoing)} <small>EGP</small></strong><i>مدفوعات الموردين</i></article><article><span>تحتاج متابعة</span><strong>${pending.toLocaleString("en-US")}</strong><i>مسودة أو تحت التحصيل</i></article>`;
  };
  const draw = () => {
    const filtered = rows.filter(c => projectFilter==="all" || (projectFilter==="none" ? !c.project_id : String(c.project_id)===projectFilter));
    updateKpis(filtered);
    $("#ch-rows").innerHTML = filtered.map(c=>`<tr><td><b class="ch-number">${esc(c.check_number)}</b><small class="ch-desc">${esc(c.description||"بدون بيان")}</small></td><td><span class="ch-brand general">${esc(projectLabel(c.project_id))}</span></td><td><span class="ch-kind ${c.check_type==='INCOMING'?'in':'out'}">${c.check_type==="INCOMING"?"وارد":"صادر"}</span></td><td class="ch-amount">${EGP(c.amount)}</td><td>${esc(c.due_date||"—")}</td><td>${esc(c.drawee_bank||"—")}</td><td>${esc(accountName(c.party_account_id))}</td><td>${esc(bankName(c.treasury_account_id))}</td><td><span class="ch-state ${STATUS_CLASS[c.status]||''}">${esc(c.status||"—")}</span></td><td>${c.journal_entry_id?`<span class="ch-journal">#${c.journal_entry_id}</span>`:"—"}</td><td>${can("Edit")&&!c.journal_entry_id?`<button type="button" class="ch-btn ghost" data-link-project="${c.check_id}">${c.project_id?"تعديل المشروع":"ربط مشروع"}</button> `:""}${can("Edit")?`<select class="ch-state-select" aria-label="تغيير حالة الشيك" data-state="${c.check_id}"><option value="">تغيير الحالة</option>${STATUS.map(s=>`<option value="${s}">${s}</option>`).join("")}</select>`:"—"}</td></tr>`).join("") || '<tr><td colspan="11" class="ch-empty">لا توجد شيكات مطابقة للفلاتر الحالية.</td></tr>';
    $("#ch-count").textContent = `عدد الشيكات: ${filtered.length.toLocaleString("en-US")}`;
    $("#ch-tabs").querySelectorAll("button").forEach(b=>b.classList.toggle("active",b.dataset.project===projectFilter));
  };
  const reload = async () => {
    const p=new URLSearchParams(); if($("#ch-status").value)p.set("status",$("#ch-status").value); if($("#ch-type").value)p.set("check_type",$("#ch-type").value); if($("#ch-search").value.trim())p.set("qtext",$("#ch-search").value.trim());
    rows=await api("/checks-register"+(p.size?`?${p}`:"")); draw();
  };
  draw();
  $("#ch-tabs").addEventListener("click",e=>{const b=e.target.closest("[data-project]");if(!b)return;projectFilter=b.dataset.project;draw();});
  $("#ch-filter").onclick=safe(reload);
  $("#ch-search").addEventListener("keydown",e=>{if(e.key==="Enter")safe(reload)();});
  $("#ch-reset").onclick=()=>{$("#ch-search").value="";$("#ch-status").value="";$("#ch-type").value="";projectFilter="all";reload();};
  $("#ch-export")?.addEventListener("click",safe(()=>downloadFile("/checks-register/export.csv","financial_checks.csv")));
  $("#ch-export-xlsx")?.addEventListener("click",safe(()=>downloadFile("/api/export/checks?format=xlsx","financial_checks.xlsx")));
  $("#ch-import")?.addEventListener("click",()=>$("#ch-file").click());
  $("#ch-file")?.addEventListener("change",safe(async()=>{const f=$("#ch-file").files[0];if(!f)return;const fd=new FormData();fd.append("file",f);const r=await api("/checks-register/import.csv",{method:"POST",form:fd});toast(`تم استيراد ${r.imported} شيك`);await reload();}));
  $("#ch-add")?.addEventListener("click",()=>formDialog({title:"تسجيل شيك جديد",fields:[{name:"check_number",label:"رقم الشيك",required:true},{name:"project_id",label:"المشروع المرتبط (اختياري)",type:"select",optional:true,options:[["","بدون مشروع"],...projects.map(p=>[p.id,p.name])]},{name:"check_type",label:"نوع الشيك",type:"select",required:true,options:[["INCOMING","وارد من عميل"],["OUTGOING","صادر لمورد"]]},{name:"amount",label:"المبلغ (EGP)",type:"number",step:"0.01",min:"0.01",required:true},{name:"due_date",label:"تاريخ الاستحقاق",type:"date",required:true},{name:"party_account_id",label:"حساب العميل / المورد",type:"select",required:true,full:true,options:opt.accounts.map(a=>[a.id,`${a.code} — ${a.name}`])},{name:"treasury_account_id",label:"الحساب البنكي المرتبط",type:"select",required:true,full:true,options:opt.banks.map(a=>[a.id,a.name])},{name:"drawee_bank",label:"البنك المسحوب عليه"},{name:"description",label:"البيان",full:true}],onSubmit:async v=>{await api("/checks-register",{method:"POST",json:{...v,amount:+v.amount,party_account_id:+v.party_account_id,treasury_account_id:+v.treasury_account_id,project_id:v.project_id?+v.project_id:null}});toast("تم حفظ الشيك كمسودة");await reload();}}));
  $("#ch-rows").addEventListener("click",safe(async e=>{const b=e.target.closest("[data-link-project]");if(!b)return;const c=rows.find(x=>x.check_id===+b.dataset.linkProject);if(!c)return;formDialog({title:`ربط الشيك ${c.check_number} بمشروع`,fields:[{name:"project_id",label:"المشروع",type:"select",optional:true,options:[["","بدون مشروع"],...projects.map(p=>[p.id,p.name])]}],values:{project_id:c.project_id||""},onSubmit:async v=>{await api(`/checks-register/${c.check_id}/project`,{method:"POST",json:{project_id:v.project_id?+v.project_id:null}});toast("تم تحديث المشروع المرتبط بالشيك");await reload();}});}));
  $("#ch-rows").addEventListener("change",safe(async e=>{const el=e.target.closest("[data-state]");if(!el||!el.value)return;const c=rows.find(x=>x.check_id===+el.dataset.state);if(!c)return;if(["مُحصّل","منصرف"].includes(el.value)&&!confirm("سيُنشأ قيد يومية مرحّل وحركة بنك. هل تريد المتابعة؟")){el.value="";return;}await api(`/checks-register/${c.check_id}/status`,{method:"POST",json:{status:el.value}});toast("تم تحديث حالة الشيك");await reload();}));
}
