import { esc } from "./ui.js";
export const entityLabel = e => ({Contracts:"عقد",ContractItems:"بند فني",ContractDeductionRules:"قاعدة خصم",ContractAccountingConfig:"إعدادات حسابات",ContractChangeOrders:"أمر تغييري",ContractAddendums:"ملحق",ProgressBillings:"مستخلص قديم",ContractSettlements:"مستخلص مالي",TechnicalSettlementEstimates:"مستخلص فني",JournalEntries:"قيد يومية"}[e] || e || "");
export const actionLabel = a => ({Create:"إنشاء",Update:"تعديل",Delete:"حذف",Post:"ترحيل",Approve:"اعتماد",Print:"طباعة",Save:"حفظ",UpdateDeductions:"تعديل خصومات",AutoLinkRules:"ربط قواعد الخصم بالشجرة",Cancel:"إلغاء قيد",Submit:"إرسال",CreateFromRequest:"إنشاء من طلب"}[a] || a || "نشاط");
export const timeText = v => String(v || "").replace("T", " ").slice(0, 19);
/** يعرض سجل النشاط المرتبط بعقد / مستخلص / قيد في نافذة. params مثل {contract_id:5} أو {settlement_id:9} */
export async function showActivity(api, params, title) {
  const q = new URLSearchParams({ limit: "300", ...params });
  const data = await api("/api/audit-logs?" + q.toString());
  const dlg = document.createElement("dialog");
  dlg.style.cssText = "width:min(1100px,96vw);max-height:90vh;overflow:auto";
  const rows = data.items.map(x => `<tr><td>${esc(timeText(x.created_at))}</td><td>${esc(x.user_name)}</td><td>${esc(actionLabel(x.action))}</td><td>${esc(entityLabel(x.entity))}${x.entity_id ? " #" + esc(x.entity_id) : ""}</td><td>${x.settlement ? esc(x.settlement.no) : "—"}</td><td>${x.journal_entry ? esc(x.journal_entry.no) : "—"}</td></tr>`).join("");
  dlg.innerHTML = `<form method="dialog"><h3>سجل النشاط — ${esc(title)}</h3><p class="muted">كل العمليات المرتبطة بالعقد وبنوده وقواعد خصمه ومستخلصاته الفنية والمالية وقيود اليومية الناتجة عنها (${data.total}).</p><div class="tbl-wrap"><table><thead><tr><th>الوقت</th><th>المستخدم</th><th>العملية</th><th>الكيان</th><th>المستخلص</th><th>القيد</th></tr></thead><tbody>${rows || '<tr><td colspan="6" class="empty">لا توجد أنشطة مسجلة</td></tr>'}</tbody></table></div><div class="actions"><button class="btn" value="x">إغلاق</button></div></form>`;
  document.body.appendChild(dlg);
  dlg.addEventListener("close", () => dlg.remove());
  dlg.showModal();
}
