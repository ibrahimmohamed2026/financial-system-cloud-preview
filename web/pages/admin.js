import { esc, toast, errText } from "../ui.js";
import { auth, userAvatarUrl } from "../api.js";
export async function render(root, {api}) {\n  const tr = (ar, en) => { try { return localStorage.getItem("fs_lang") === "en" ? en : ar; } catch { return ar; } };
  root.innerHTML = `<div class="pagehead"><h2>${tr("إدارة المستخدمين والصلاحيات", "Users & Permissions")}</h2><button class="btn" id="back">${tr("الرئيسية", "Home")}</button></div>
    <div class="tabs"><button class="btn primary" data-tab="users">${tr("المستخدمون", "Users")}</button><button class="btn" data-tab="roles">${tr("الأدوار والصلاحيات", "Roles & Permissions")}</button></div>
    <section id="content" class="panel">${tr("جاري التحميل...", "Loading...")}</section>`;
  root.querySelector('#back').onclick=()=>location.hash='#/';
  let users=[], roles=[], permissions=[], tab='users';
  const content=root.querySelector('#content');
  const load=async()=>{[users,roles,permissions]=await Promise.all([api('/admin/users'),api('/admin/roles'),api('/admin/permissions')]); draw();};
  function draw(){
    root.querySelectorAll('[data-tab]').forEach(b=>{b.className='btn'+(b.dataset.tab===tab?' primary':'')});
    if(tab==='users'){
      content.innerHTML=`<div class="pagehead"><h3>${tr("المستخدمون", "Users")}</h3><button class="btn primary" id="newuser">${tr("إضافة مستخدم", "Add user")}</button></div>
      <div class="tablewrap"><table><thead><tr><th>${tr("الصورة", "Photo")}</th><th>${tr("اسم الدخول", "Username")}</th><th>${tr("الاسم", "Name")}</th><th>${tr("الحالة", "Status")}</th><th>${tr("الأدوار", "Roles")}</th><th>${tr("محاولات فاشلة", "Failed attempts")}</th><th>${tr("إجراءات", "Actions")}</th></tr></thead><tbody>${users.map(u=>`<tr><td><span class="user-avatar" data-avatar-id="${u.user_id}" title="${esc(u.full_name)}">${esc([...(u.full_name||u.username||'؟').trim()][0]||'؟')}</span></td><td>${esc(u.username)}</td><td>${esc(u.full_name)}</td><td>${u.is_active?tr('نشط','Active'):tr('معطّل','Disabled')}</td><td>${esc(u.roles.join('، '))}</td><td>${u.failed_login_count}</td><td><button class="btn sm" data-edit="${u.user_id}">${tr("تعديل", "Edit")}</button></td></tr>`).join('')}</tbody></table></div>
      <div id="userform"></div>`;
      content.querySelectorAll('[data-avatar-id]').forEach(el=>{const u=users.find(x=>x.user_id===+el.dataset.avatarId);if(u?.avatar_updated_at)userAvatarUrl(u.user_id,u.avatar_updated_at).then(url=>{if(el.isConnected&&url)el.innerHTML=`<img src="${url}" alt="">`;}).catch(()=>{});});
      content.querySelector('#newuser').onclick=()=>userForm();
      content.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>userForm(users.find(u=>u.user_id===+b.dataset.edit)));
    } else {
      content.innerHTML=`<div class="pagehead"><h3>${tr("الأدوار", "Roles")}</h3><button class="btn primary" id="newrole">${tr("إضافة دور", "Add role")}</button></div>
      <div class="tablewrap"><table><thead><tr><th>${tr("اسم الدور", "Role name")}</th><th>${tr("عدد الصلاحيات", "Permission count")}</th><th>${tr("إجراءات", "Actions")}</th></tr></thead><tbody>${roles.map(r=>`<tr><td>${esc(r.role_name)}</td><td>${r.permission_ids.length}</td><td><button class="btn sm" data-role="${r.role_id}">${tr("إدارة الصلاحيات", "Manage permissions")}</button></td></tr>`).join('')}</tbody></table></div><div id="roleform"></div>`;
      content.querySelector('#newrole').onclick=()=>roleForm();
      content.querySelectorAll('[data-role]').forEach(b=>b.onclick=()=>roleForm(roles.find(r=>r.role_id===+b.dataset.role)));
    }
  }
  function userForm(u){
    const box=content.querySelector('#userform');
    box.innerHTML=`<form class="panel formgrid"><h3>${u?tr('تعديل مستخدم','Edit user'):tr('مستخدم جديد','New user')}</h3>${u?'':`<label>${tr("اسم الدخول","Username")}<input name="username" required minlength="2"></label>`}<label>${tr("الاسم الكامل","Full name")}<input name="full_name" required value="${esc(u?.full_name||'')}"></label><label>${tr("كلمة المرور","Password")} ${u?'(اتركها فارغة دون تغيير)':'(12 حرفًا على الأقل)'}<input name="password" type="password" ${u?'':'required'} minlength="12"></label><div class="avatar-editor"><span class="user-avatar" id="avatar-preview">${esc([...(u?.full_name||u?.username||'؟').trim()][0]||'؟')}</span><label>${tr("الصورة الشخصية (JPG أو PNG أو WebP، حتى 3 ميجابايت)","Profile photo (JPG, PNG or WebP, up to 3 MB)")}<input name="avatar" type="file" accept="image/jpeg,image/png,image/webp"></label>${u?.avatar_updated_at?'<label><input type="checkbox" name="remove_avatar"> ${tr("حذف الصورة الحالية","Remove current photo")}</label>':''}</div><label><input type="checkbox" name="active" ${u?.is_active===false?'':'checked'}> ${tr("الحساب نشط","Account active")}</label><label>${tr("الأدوار","Roles")}<select name="roles" multiple size="${Math.min(5,Math.max(2,roles.length))}">${roles.map(r=>`<option value="${r.role_id}" ${(u?.role_ids||[]).includes(r.role_id)?'selected':''}>${esc(r.role_name)}</option>`).join('')}</select></label><div><button class="btn primary">${tr("حفظ","Save")}</button> <button class="btn" type="button" id="cancel">${tr("إلغاء","Cancel")}</button></div><div class="err" id="error"></div></form>`;
    const f=box.querySelector('form'); box.querySelector('#cancel').onclick=()=>box.innerHTML='';
    if(u?.avatar_updated_at)userAvatarUrl(u.user_id,u.avatar_updated_at).then(url=>{const el=box.querySelector('#avatar-preview');if(el&&url)el.innerHTML=`<img src="${url}" alt="">`;}).catch(()=>{});
    f.avatar.onchange=()=>{const file=f.avatar.files[0];if(file){const preview=box.querySelector('#avatar-preview');preview.innerHTML=`<img src="${URL.createObjectURL(file)}" alt="">`;}};
    f.onsubmit=async e=>{e.preventDefault();const data={full_name:f.full_name.value,is_active:f.active.checked,role_ids:[...f.roles.selectedOptions].map(o=>+o.value)};if(f.password.value)data.password=f.password.value;try{let id=u?.user_id;if(u)await api('/admin/users/'+id,{method:'PATCH',json:data});else{data.username=f.username.value;data.password=f.password.value;id=(await api('/admin/users',{method:'POST',json:data})).user_id;}const photo=f.avatar.files[0];if(photo){const form=new FormData();form.append('file',photo);await api(`/admin/users/${id}/avatar`,{method:'POST',form});}else if(f.remove_avatar?.checked)await api(`/admin/users/${id}/avatar`,{method:'DELETE'});toast(tr('تم الحفظ','Saved successfully'));await load();if(id===auth.user?.user_id){const me=await api('/auth/me');auth.updateUser({avatar_updated_at:me.avatar_updated_at});location.reload();}}catch(x){f.querySelector('#error').textContent=errText(x)}};
  }
  function roleForm(r){
    const box=content.querySelector('#roleform'); const ids=new Set(r?.permission_ids||[]);
    box.innerHTML=`<form class="panel"><h3>${r?tr('تعديل الدور والصلاحيات','Edit role & permissions'):tr('إنشاء دور','Create role')}</h3><label>${tr("اسم الدور","Role name")}<input name="name" required value="${esc(r?.role_name||'')}"></label><div class="tablewrap" style="max-height:420px;overflow:auto"><table><thead><tr><th>${tr("الشاشة", "Screen")}</th><th>${tr("القسم", "Section")}</th><th>${tr("الإجراء", "Action")}</th><th>${tr("مسموح", "Allowed")}</th></tr></thead><tbody>${permissions.map(p=>`<tr><td>${esc(localStorage.getItem("fs_lang")==="en"?(p.screen_en||p.screen_ar):p.screen_ar)}</td><td>${esc(localStorage.getItem("fs_lang")==="en"?(p.section_en||p.section_ar):p.section_ar)}</td><td>${esc(p.action_code)}</td><td><input type="checkbox" name="p" value="${p.permission_id}" ${ids.has(p.permission_id)?'checked':''}></td></tr>`).join('')}</tbody></table></div><button class="btn primary">${tr("حفظ الدور والصلاحيات","Save role & permissions")}</button> <button type="button" class="btn" id="cancel">${tr("إلغاء","Cancel")}</button><div class="err" id="error"></div></form>`;
    const f=box.querySelector('form');box.querySelector('#cancel').onclick=()=>box.innerHTML='';
    f.onsubmit=async e=>{e.preventDefault();const data={role_name:f.name.value,permission_ids:[...f.querySelectorAll('[name=p]:checked')].map(x=>+x.value)};try{if(r)await api('/admin/roles/'+r.role_id,{method:'PUT',json:data});else await api('/admin/roles',{method:'POST',json:data});toast(tr('تم حفظ الدور','Role saved'));await load();}catch(x){f.querySelector('#error').textContent=errText(x)}};
  }
  root.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;draw()});
  try{await load()}catch(e){content.textContent=errText(e)}
}
