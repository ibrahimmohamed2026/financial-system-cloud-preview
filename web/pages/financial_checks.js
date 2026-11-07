import { esc, money, toast, safe, formDialog } from "../ui.js";
import { downloadFile } from "../api.js";
import { translate as tr } from "../i18n.js";

const STATUS = ["مسودة", "معتمد", "صادر", "تم التسليم", "تحت التحصيل", "تم التحصيل", "منصرف", "موقوف", "مرتد", "ملغي", "مُحصّل", "مُرتجع"];
const STATUS_CLASS = {"مسودة":"draft", "معتمد":"pending", "صادر":"pending", "تم التسليم":"pending", "تحت التحصيل":"pending", "تم التحصيل":"success", "مُحصّل":"success", "منصرف":"success", "مرتد":"danger", "مُرتجع":"danger", "ملغي":"danger", "موقوف":"danger"};
const statusLabel = s => ({ "مسودة":tr("مسودة","Draft"), "معتمد":tr("معتمد","Approved"), "صادر":tr("صادر","Issued"), "تم التسليم":tr("تم التسليم","Delivered"), "تحت التحصيل":tr("تحت التحصيل","Under collection"), "تم التحصيل":tr("تم التحصيل","Collected"), "مُحصّل":tr("مُحصّل","Collected (legacy)"), "منصرف":tr("منصرف","Paid"), "موقوف":tr("موقوف","On hold"), "مرتد":tr("مرتد","Returned"), "مُرتجع":tr("مُرتجع","Returned (legacy)"), "ملغي":tr("ملغي","Cancelled") }[s] || s || "—");
const NEXT_STATUS = {
  INCOMING: {
    "مسودة": ["تحت التحصيل", "ملغي"],
    "تحت التحصيل": ["تم التحصيل", "مرتد"]
  },
  OUTGOING: {
    "مسودة": ["معتمد", "ملغي"],
    "معتمد": ["صادر", "ملغي"],
    "صادر": ["تم التسليم", "موقوف", "ملغي"],
    "تم التسليم": ["منصرف", "موقوف", "مرتد"],
    "موقوف": ["صادر", "ملغي"]
  }
};
const nextStatuses = cheque => NEXT_STATUS[cheque.check_type]?.[cheque.status] || [];
const EGP = v => `${money(v)} <small class="ch-egp">EGP</small>`;

export async function render(main, { api, auth }) {
  const can = a => auth.can("FinancialChecks", a) || ["ChecksCib", "ChecksCairoEgp", "ChecksCairoUsd"].some(sc => auth.can(sc, a));
  const [opt, rows0] = await Promise.all([api("/checks-register/options"), api("/checks-register")]);
  let rows = rows0 || [], projectFilter = "all";
  const projects = opt.projects || [];
  const projectLabel = id => projects.find(p => String(p.id) === String(id))?.name || tr("بدون مشروع","No project");
  main.innerHTML = `
  <section class="cheques-page">
    <div class="ch-hero"><div><div class="ch-eyebrow">TREASURY / CHEQUES CONTROL</div><h2>${tr("إدارة الشيكات المالية","Financial Cheque Management")}</h2><p>${tr("متابعة دفاتر الشيكات، الاستحقاقات، التحصيلات وربطها بالحسابات البنكية والمشروعات.","Track cheque books, due dates, collections and links to bank accounts and projects.")}</p></div><div class="ch-hero-chip"><span class="ch-pulse"></span> ${tr("سجل الشيكات","Cheque register")} <b>LIVE</b></div></div>
    <div class="ch-bindings">
      <article class="ch-bind-card"><div class="ch-bind-icon">⌁</div><div><small>${tr("ربط حسابات البنوك","Bank account links")}</small><h3>${Number(opt.bank_binding?.active_bank_accounts || opt.banks?.length || 0)} ${tr("حساب بنكي نشط","active bank accounts")}</h3><p>${tr("حسابات الخزينة المتاحة لتسجيل الشيكات","Treasury accounts available for cheque registration")}</p></div><span class="ch-status-pill good">${tr("متاح","Available")}</span></article>
      <article class="ch-bind-card cib"><div class="ch-bind-icon">CIB</div><div><small>${tr("إعداد دفتر شيكات CIB","CIB cheque book setup")}</small><h3>${Number(opt.bank_binding?.cib_accounts || 0)} ${tr("حساب مطابق","matching accounts")}</h3><p>${Number(opt.bank_binding?.cib_accounts || 0) ? tr("تم العثور على حساب بنكي باسم CIB / البنك التجاري","A CIB bank account was found") : tr("لم يتم اكتشاف حساب CIB بالاسم؛ راجع تعريف حساب البنك في الخزينة","No CIB account found by name; check the treasury bank account setup")}</p></div><span class="ch-status-pill ${Number(opt.bank_binding?.cib_accounts || 0) ? "good" : "warn"}">${Number(opt.bank_binding?.cib_accounts || 0) ? tr("مرتبط","Linked") : tr("يحتاج إعداد","Setup required")}</span></article>
      <article class="ch-bind-card"><div class="ch-bind-icon">↗</div><div><small>${tr("ربط الشيكات بالمشروعات","Cheque-to-project links")}</small><h3>${projects.length.toLocaleString("ar-EG")} ${tr("مشروع نشط","active projects")}</h3><p>${tr("اختر المشروع الفعلي عند تسجيل الشيك أو اربط به شيكًا غير مرحّل","Select the actual project when registering a cheque or link an unposted cheque later")}</p></div><span class="ch-status-pill info">${tr("مفعّل","Enabled")}</span></article>
    </div>
    <div class="ch-kpis" id="ch-kpis"></div>
    <div class="ch-panel">
      <div class="ch-panel-head"><div><h3>${tr("سجل الشيكات","Cheque Register")}</h3><p>${tr("بحث سريع وتصنيف حسب المشروع والحالة والنوع.","Search and filter by project, status and type.")}</p></div><div class="ch-actions">${can("Print")?`<button class="ch-btn" id="ch-export">${tr("تصدير CSV","Export CSV")}</button><button class="ch-btn" id="ch-export-xlsx">${tr("تصدير Excel","Export Excel")}</button>`:''}${can("Add")?`<button class="ch-btn" id="ch-import">${tr("استيراد CSV","Import CSV")}</button><input hidden type="file" id="ch-file" accept=".csv"><button class="ch-btn primary" id="ch-add">＋ ${tr("تسجيل شيك","Register cheque")}</button>`:''}</div></div>
      <div class="ch-tabs" id="ch-tabs"><button type="button" data-project="all" class="active">${tr("كل المشروعات","All projects")}</button><button type="button" data-project="none">${tr("بدون مشروع","No project")}</button>${projects.map(p=>`<button type="button" data-project="${p.id}">${esc(p.name)}</button>`).join("")}</div>
      <div class="ch-filters"><label><span>${tr("بحث برقم الشيك","Search cheque number")}</span><input id="ch-search" placeholder="${tr("اكتب رقم الشيك…","Enter cheque number…")}" autocomplete="off"></label><label><span>${tr("حالة الشيك","Cheque status")}</span><select id="ch-status"><option value="">${tr("كل الحالات","All statuses")}</option>${nextStatuses(c).map(s=>`<option value="${s}">${statusLabel(s)}</option>`).join("")}</select></label><label><span>${tr("نوع الشيك","Cheque type")}</span><select id="ch-type"><option value="">${tr("كل الأنواع","All types")}</option><option value="INCOMING">${tr("وارد من عميل","Incoming from customer")}</option><option value="OUTGOING">${tr("صادر لمورد","Outgoing to supplier")}</option></select></label><button class="ch-btn" id="ch-filter">${tr("تطبيق الفلاتر","Apply filters")}</button><button class="ch-btn ghost" id="ch-reset">${tr("إعادة ضبط","Reset")}</button></div>
      <div class="ch-table-wrap"><table class="ch-table"><thead><tr><th>${tr("رقم الشيك","Cheque No.")}</th><th>${tr("المشروع","Project")}</th><th>${tr("النوع","Type")}</th><th>${tr("المبلغ","Amount")}</th><th>${tr("تاريخ الاستحقاق","Due date")}</th><th>${tr("البنك المسحوب عليه","Drawee bank")}</th><th>${tr("حساب الطرف","Party account")}</th><th>${tr("الحساب البنكي المرتبط","Linked bank account")}</th><th>${tr("الحالة","Status")}</th><th>${tr("قيد اليومية","Journal entry")}</th><th>${tr("إجراء","Action")}</th></tr></thead><tbody id="ch-rows"></tbody></table></div>
      <div class="ch-foot"><span id="ch-count">—</span><span>${tr("جميع المبالغ معروضة بالجنيه المصري EGP","All amounts are displayed in Egyptian pounds (EGP)")}</span></div>
    </div>
  </section>`;
  const $ = s => main.querySelector(s);
  const accountName = id => opt.accounts?.find(a=>a.id===id)?.name || `${tr("حساب","Account")} #${id ?? "—"}`;
  const bankName = id => opt.banks?.find(b=>b.id===id)?.name || `${tr("بنك","Bank")} #${id ?? "—"}`;
  const updateKpis = list => {
    const total = list.reduce((s,c)=>s+Number(c.amount||0),0);
    const incoming = list.filter(c=>c.check_type==="INCOMING").reduce((s,c)=>s+Number(c.amount||0),0);
    const outgoing = list.filter(c=>c.check_type==="OUTGOING").reduce((s,c)=>s+Number(c.amount||0),0);
    const pending = list.filter(c=>["مسودة","تحت التحصيل"].includes(c.status)).length;
    $("#ch-kpis").innerHTML = `<article><span>${tr("إجمالي قيمة الشيكات","Total cheque value")}</span><strong>${money(total)} <small>EGP</small></strong><i>${tr("مجموع النتائج الحالية","Current result total")}</i></article><article><span>${tr("شيكات واردة","Incoming cheques")}</span><strong>${money(incoming)} <small>EGP</small></strong><i>${tr("تحصيلات العملاء","Customer collections")}</i></article><article><span>${tr("شيكات صادرة","Outgoing cheques")}</span><strong>${money(outgoing)} <small>EGP</small></strong><i>${tr("مدفوعات الموردين","Supplier payments")}</i></article><article><span>${tr("تحتاج متابعة","Needs follow-up")}</span><strong>${pending.toLocaleString("en-US")}</strong><i>${tr("مسودة أو تحت التحصيل","Draft or under collection")}</i></article>`;
  };
  const draw = () => {
    const filtered = rows.filter(c => projectFilter==="all" || (projectFilter==="none" ? !c.project_id : String(c.project_id)===projectFilter));
    updateKpis(filtered);
    $("#ch-rows").innerHTML = filtered.map(c=>`<tr><td><b class="ch-number">${esc(c.check_number)}</b><small class="ch-desc">${esc(c.description||"بدون بيان")}</small></td><td><span class="ch-brand general">${esc(projectLabel(c.project_id))}</span></td><td><span class="ch-kind ${c.check_type==='INCOMING'?'in':'out'}">${c.check_type==="INCOMING"?tr("وارد","Incoming"):tr("صادر","Outgoing")}</span></td><td class="ch-amount">${EGP(c.amount)}</td><td>${esc(c.due_date||"—")}</td><td>${esc(c.drawee_bank||"—")}</td><td>${esc(accountName(c.party_account_id))}</td><td>${esc(bankName(c.treasury_account_id))}</td><td><span class="ch-state ${STATUS_CLASS[c.status]||''}">${esc(statusLabel(c.status))}</span></td><td>${c.journal_entry_id?`<span class="ch-journal">#${c.journal_entry_id}</span>`:"—"}</td><td>${can("Edit")&&!c.journal_entry_id?`<button type="button" class="ch-btn ghost" data-link-project="${c.check_id}">${c.project_id?"تعديل المشروع":"ربط مشروع"}</button> `:""}${can("Edit")&&c.check_type==="OUTGOING"&&!c.journal_entry_id?`<button type="button" class="ch-btn ghost" data-allocate="${c.check_id}">${tr("تخصيص مستخلص","Allocate settlement")}</button> `:""}${can("Edit")&&!c.journal_entry_id?`<select class="ch-state-select" aria-label="${tr("تغيير حالة الشيك","Change cheque status")}" data-state="${c.check_id}"><option value="">${tr("تغيير الحالة","Change status")}</option>${STATUS.map(s=>`<option value="${s}">${statusLabel(s)}</option>`).join("")}</select>`:"—"}</td></tr>`).join("") || `<tr><td colspan="11" class="ch-empty">${tr("لا توجد شيكات مطابقة للفلاتر الحالية.","No cheques match the current filters.")}</td></tr>`;
    $("#ch-count").textContent = `${tr("عدد الشيكات: ","Cheques: ")}${filtered.length.toLocaleString("en-US")}`;
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
  $("#ch-file")?.addEventListener("change",safe(async()=>{const f=$("#ch-file").files[0];if(!f)return;const fd=new FormData();fd.append("file",f);const r=await api("/checks-register/import.csv",{method:"POST",form:fd});toast(`${tr("تم استيراد","Imported")} ${r.imported} ${tr("شيك","cheques")}`);await reload();}));
  $("#ch-add")?.addEventListener("click",()=>formDialog({title:tr("تسجيل شيك جديد","Register new cheque"),fields:[{name:"check_number",label:tr("رقم الشيك","Cheque number"),required:true},{name:"project_id",label:tr("المشروع المرتبط (اختياري)","Linked project (optional)"),type:"select",optional:true,options:[["",tr("بدون مشروع","No project")],...projects.map(p=>[p.id,p.name])]},{name:"check_type",label:tr("نوع الشيك","Cheque type"),type:"select",required:true,options:[["INCOMING",tr("وارد من عميل","Incoming from customer")],["OUTGOING",tr("صادر لمورد","Outgoing to supplier")]]},{name:"amount",label:tr("المبلغ (EGP)","Amount (EGP)"),type:"number",step:"0.01",min:"0.01",required:true},{name:"due_date",label:tr("تاريخ الاستحقاق","Due date"),type:"date",required:true},{name:"party_account_id",label:tr("حساب العميل / المورد","Customer / supplier account"),type:"select",required:true,full:true,options:opt.accounts.map(a=>[a.id,`${a.code} — ${a.name}`])},{name:"treasury_account_id",label:tr("الحساب البنكي المرتبط","Linked bank account"),type:"select",required:true,full:true,options:opt.banks.map(a=>[a.id,a.name])},{name:"drawee_bank",label:tr("البنك المسحوب عليه","Drawee bank")},{name:"description",label:tr("البيان","Description"),full:true}],onSubmit:async v=>{await api("/checks-register",{method:"POST",json:{...v,amount:+v.amount,party_account_id:+v.party_account_id,treasury_account_id:+v.treasury_account_id,project_id:v.project_id?+v.project_id:null}});toast(tr("تم حفظ الشيك كمسودة","Cheque saved as draft"));await reload();}}));
  $("#ch-rows").addEventListener("click",safe(async e=>{const b=e.target.closest("[data-link-project]");if(!b)return;const c=rows.find(x=>x.check_id===+b.dataset.linkProject);if(!c)return;formDialog({title:`${tr("ربط الشيك","Link cheque")} ${c.check_number} ${tr("بمشروع","to project")}`,fields:[{name:"project_id",label:tr("المشروع","Project"),type:"select",optional:true,options:[["",tr("بدون مشروع","No project")],...projects.map(p=>[p.id,p.name])]}],values:{project_id:c.project_id||""},onSubmit:async v=>{await api(`/checks-register/${c.check_id}/project`,{method:"POST",json:{project_id:v.project_id?+v.project_id:null}});toast(tr("تم تحديث المشروع المرتبط بالشيك","Cheque project updated"));await reload();}});}));

  $("#ch-rows").addEventListener("click",safe(async e=>{
    const b=e.target.closest("[data-allocate]");
    if(!b)return;
    const c=rows.find(x=>x.check_id===+b.dataset.allocate);
    if(!c)return;
    const result=await api(`/checks-register/${c.check_id}/allocation-options`);
    const options=result.items||[];
    if(!options.length){toast(tr("لا توجد مستخلصات معتمدة متبقية لهذا المقاول والمشروع.","No approved outstanding settlements match this contractor and project."));return;}
    formDialog({
      title:`${tr("تخصيص مستخلص للشيك","Allocate a settlement to cheque")} ${c.check_number}`,
      fields:[
        {name:"settlement_id",label:tr("المستخلص المعتمد","Approved settlement"),type:"select",required:true,full:true,options:options.map(x=>[x.settlement_id,`${x.settlement_no} — ${x.contract_no} — ${x.counterparty_name} — ${money(x.remaining_amount)} EGP`])},
        {name:"allocated_amount",label:tr("المبلغ المخصص (EGP)","Allocated amount (EGP)"),type:"number",step:"0.01",min:"0.01",required:true,full:true}
      ],
      onSubmit:async v=>{
        const chosen=options.find(x=>String(x.settlement_id)===String(v.settlement_id));
        if(!chosen)throw new Error(tr("المستخلص المختار غير متاح.","Selected settlement is unavailable."));
        if(Number(v.allocated_amount)>Number(chosen.remaining_amount))throw new Error(tr("المبلغ أكبر من المتبقي بالمستخلص.","Amount exceeds the settlement balance."));
        const saved=await api(`/checks-register/${c.check_id}/allocations`,{method:"POST",json:{settlement_id:+v.settlement_id,allocated_amount:v.allocated_amount}});
        toast(tr("تم تخصيص المستخلص بنجاح.","Settlement allocated successfully."));
        const current=saved.items||[];
        if(current.length)console.info("Cheque settlement allocations",current);
      }
    });
  }));
  $("#ch-rows").addEventListener("change",safe(async e=>{const el=e.target.closest("[data-state]");if(!el||!el.value)return;const c=rows.find(x=>x.check_id===+el.dataset.state);if(!c)return;if(["مُحصّل","منصرف"].includes(el.value)&&!confirm(tr("سيُنشأ قيد يومية مرحّل وحركة بنك. هل تريد المتابعة؟","A posted journal entry and bank transaction will be created. Continue?"))){el.value="";return;}await api(`/checks-register/${c.check_id}/status`,{method:"POST",json:{status:el.value}});toast(tr("تم تحديث حالة الشيك","Cheque status updated"));await reload();}));
}
