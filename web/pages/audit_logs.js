import { esc, safe } from "../ui.js";
import { entityLabel, actionLabel as actLbl, timeText } from "../activity.js";

const actionLabel = a => ({Create:"إنشاء",Update:"تعديل",Delete:"حذف",Post:"ترحيل",Approve:"اعتماد",Print:"طباعة",POST_JOURNAL:"ترحيل قيد",CREATE_USER:"إنشاء مستخدم",UPDATE_ACCOUNT:"تعديل حساب"}[a] || a || "نشاط");
const statusClass = a => /create/i.test(a) ? "ok" : /update/i.test(a) ? "warn" : /delete/i.test(a) ? "bad" : /print/i.test(a) ? "print" : /post|approve/i.test(a) ? "ok" : /cancel|reverse/i.test(a) ? "bad" : "no";
export async function render(main, { api }) {
  main.innerHTML = `<div class="toolbar">
    <div class="w"><label>من تاريخ</label><input type="date" id="from"></div>
    <div class="w"><label>إلى تاريخ</label><input type="date" id="to"></div>
    <div class="w"><label>المستخدم</label><select id="user"><option value="">كل المستخدمين</option></select></div>
    <div class="w"><label>العقد</label><select id="contract"><option value="">كل العقود</option></select></div>
    <div class="w"><label>رقم مستخلص (ID)</label><input id="settlement" type="number" min="1" placeholder="مستخلص مالي"></div>
    <div class="w"><label>رقم قيد (ID)</label><input id="jentry" type="number" min="1" placeholder="قيد يومية"></div>
    <div class="w"><label>نوع الحركة</label><input id="action" placeholder="مثال: Update"></div>
    <button class="btn primary" id="apply">بحث</button><button class="btn" id="reset">مسح الفلاتر</button>
  </div><div class="panel" style="margin-bottom:14px"><b id="total">سجل النشاطات</b><span class="muted"> — سجل تدقيق للعمليات المسجلة بالنظام</span></div>
  <div class="tbl-wrap"><table><thead><tr><th>التاريخ والوقت</th><th>المستخدم</th><th>نوع الحركة</th><th>الكيان</th><th>العقد</th><th>المستخلص</th><th>القيد</th><th>عنوان IP</th></tr></thead><tbody id="rows"><tr><td colspan="8">جارٍ التحميل...</td></tr></tbody></table></div><div class="pager" id="pager"></div>`;
  const $ = id => main.querySelector('#'+id); let skip=0, total=0; const limit=100;
  try { const cs=await api('/api/audit-logs/contracts'); $('contract').insertAdjacentHTML('beforeend',cs.map(c=>`<option value="${c.contract_id}">${esc(c.label)}</option>`).join('')); } catch {}
  try { const users=await api('/api/audit-logs/users'); $('user').insertAdjacentHTML('beforeend',users.map(u=>`<option value="${u.user_id}">${esc(u.name)}</option>`).join('')); } catch {}
  const load = async () => {
    const q=new URLSearchParams({skip:String(skip),limit:String(limit)}); if($('from').value)q.set('date_from',$('from').value);if($('to').value)q.set('date_to',$('to').value);if($('user').value)q.set('user_id',$('user').value);if($('action').value.trim())q.set('action',$('action').value.trim());if($('contract').value)q.set('contract_id',$('contract').value);if($('settlement').value)q.set('settlement_id',$('settlement').value);if($('jentry').value)q.set('journal_entry_id',$('jentry').value);
    const data=await api('/api/audit-logs?'+q.toString()); total=data.total;
    $('rows').innerHTML=data.items.map(x=>`<tr><td>${esc(timeText(x.created_at))}</td><td>${esc(x.user_name)}</td><td><span class="tag ${statusClass(x.action)}">${esc(actLbl(x.action))}</span><small class="muted"> ${esc(x.action)}</small></td><td>${esc(entityLabel(x.entity))} ${x.entity_id?'#'+esc(x.entity_id):''}</td><td>${x.contract?`<a href=\"#\" data-c=\"${x.contract.id}\">${esc(x.contract.no)}</a>`:'—'}</td><td>${x.settlement?`<a href=\"#\" data-s=\"${x.settlement.id}\">${esc(x.settlement.no)}</a>${x.technical_estimate_no?`<div class=\"muted\">فني: ${esc(x.technical_estimate_no)}</div>`:''}`:(x.technical_estimate_no?`فني: ${esc(x.technical_estimate_no)}`:'—')}</td><td>${x.journal_entry?`<a href=\"#\" data-j=\"${x.journal_entry.id}\">${esc(x.journal_entry.no)}</a>`:'—'}</td><td>${esc(x.ip_address||'—')}</td></tr>`).join('') || '<tr><td colspan="8" class="empty">لا توجد سجلات مطابقة</td></tr>';
    $('total').textContent=`إجمالي السجلات: ${total}`;main.querySelectorAll('[data-c]').forEach(a=>a.onclick=e=>{e.preventDefault();$('contract').value=a.dataset.c;$('settlement').value='';$('jentry').value='';skip=0;safe(load)();});main.querySelectorAll('[data-s]').forEach(a=>a.onclick=e=>{e.preventDefault();$('settlement').value=a.dataset.s;$('contract').value='';$('jentry').value='';skip=0;safe(load)();});main.querySelectorAll('[data-j]').forEach(a=>a.onclick=e=>{e.preventDefault();$('jentry').value=a.dataset.j;$('contract').value='';$('settlement').value='';skip=0;safe(load)();}); $('pager').innerHTML=`<button class="btn" id="prev" ${skip===0?'disabled':''}>السابق</button><span>${total?skip+1:0}–${Math.min(skip+limit,total)} من ${total}</span><button class="btn" id="next" ${skip+limit>=total?'disabled':''}>التالي</button>`;
    $('prev').onclick=()=>{skip=Math.max(0,skip-limit);safe(load)()};$('next').onclick=()=>{skip+=limit;safe(load)()};
  };
  $('apply').onclick=()=>{skip=0;safe(load)()};$('reset').onclick=()=>{$('from').value='';$('to').value='';$('user').value='';$('action').value='';$('contract').value='';$('settlement').value='';$('jentry').value='';skip=0;safe(load)()};
  await load();
}
