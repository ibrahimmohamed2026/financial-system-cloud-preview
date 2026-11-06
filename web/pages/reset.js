import { esc, toast, errText } from "../ui.js";

export async function render(main, { api }) {
  const tr = (ar, en) => { try { return localStorage.getItem("fs_lang") === "en" ? en : ar; } catch { return ar; } };
  main.innerHTML = `<section class="sec">
    <h3>${tr("إعادة ضبط بيانات النظام","System Data Reset")}</h3>
    <div class="panel" style="padding:16px">
      <div class="tag no">${tr("إجراء حساس — لا يتم الحذف قبل المعاينة والتأكيد","Sensitive action — nothing is deleted before preview and confirmation")}</div>
      <p>${tr("اختر مستوى إعادة الضبط. ستظهر لك الجداول وعدد السجلات المتأثرة قبل أي تنفيذ.","Choose a reset level. A table-by-table count is shown before anything is executed.")}</p>
      <div class="formgrid" style="margin-top:16px">
        <div>
          <h4>${tr("تصفير البيانات","Reset data")}</h4>
          <p class="muted">${tr("يمسح القيود والحركات والمستندات التشغيلية فقط، مع الاحتفاظ بالأطراف والأصناف والمخازن والخزائن وكل الإعدادات الأساسية.","Deletes transactions and operational documents only; preserves parties, items, warehouses, treasuries and core configuration.")}</p>
          <button class="btn primary reset-preview" data-mode="operational">${tr("معاينة تصفير البيانات","Preview data reset")}</button>
        </div>
        <div>
          <h4>${tr("ضبط مصنع","Factory reset")}</h4>
          <p class="muted">${tr("يمسح البيانات التشغيلية والبيانات الأساسية التشغيلية، ويصفّر الأرصدة الافتتاحية. يحتفظ بالشركة والسنة المالية والمشروعات وكل المستخدمين والصلاحيات والوظائف ودليل الحسابات والخزائن والبنوك وربطها المحاسبي وقوالب الشيكات.","Clears operational data and operational master records, and zeros opening balances. Preserves company, fiscal year, projects, all users, permissions, job profiles, chart of accounts, treasuries, banks, their GL links and cheque templates.")}</p>
          <button class="btn danger reset-preview" data-mode="full">${tr("معاينة ضبط المصنع","Preview factory reset")}</button>
        </div>
      </div>
      <div id="previewbox" style="margin-top:16px"></div>
      <div id="confirmbox" hidden style="margin-top:16px;border-top:1px solid var(--line);padding-top:16px">
        <h4>${tr("التأكيد النهائي","Final confirmation")}</h4>
        <p class="muted">${tr("سيتم إنشاء نسخة احتياطية كاملة تلقائيًا أولاً. إذا فشلت النسخة فلن يتم حذف أي بيانات.","A complete backup is created first. If backup creation fails, no data is deleted.")}</p>
        <div class="formgrid">
          <label>${tr("كلمة مرور المدير","Administrator password")}<input id="resetpassword" type="password" autocomplete="current-password"></label>
          <label>${tr("اكتب RESET للتأكيد","Type RESET to confirm")}<input id="resetphrase" dir="ltr" autocomplete="off"></label>
        </div>
        <button class="btn danger" id="execute">${tr("تنفيذ إعادة الضبط الآن","Execute reset now")}</button>
      </div>
      <div id="reseterr" class="err" style="margin-top:12px"></div>
    </div>
  </section>`;
  const $ = s => main.querySelector(s);
  let previewMode = null;
  const busy = v => main.querySelectorAll("button,input").forEach(x => x.disabled = v);
  main.querySelectorAll(".reset-preview").forEach(button => button.addEventListener("click", async () => {
    const m = button.dataset.mode;
    previewMode = null; $("#previewbox").innerHTML = "";
    busy(true); $("#reseterr").textContent = ""; $("#confirmbox").hidden = true;
      const d = await api("/admin/reset/preview?mode=" + encodeURIComponent(m));
      previewMode = m;
      const labels = {
        JournalEntryDetails:"تفاصيل قيود اليومية", JournalEntries:"قيود اليومية",
        TreasuryTransactions:"حركات الخزائن", BankReconciliations:"التسويات البنكية",
        BankReconciliationLines:"تفاصيل التسويات", Checks:"الشيكات", FinancialChecks:"الشيكات المالية",
        CheckStatusHistory:"سجل حالات الشيكات", ContractRequests:"طلبات العقود", Contracts:"العقود",
        ContractSettlementSchedules:"جدول المستخلصات", ContractAddendums:"ملاحق العقود",
        ContractAddendumLines:"بنود ملاحق العقود", ProgressBillings:"مستخلصات الأعمال",
        ContractItems:"بنود العقود", ContractDeductionRules:"قواعد الخصومات",
        ContractAccountingConfig:"إعدادات محاسبة العقود", ContractSettlements:"المستخلصات",
        ContractSettlementItems:"بنود المستخلصات", ContractChangeOrders:"أوامر التغيير",
        InventoryMovements:"حركات المخزون", SiteIssueRequests:"طلبات صرف الموقع",
        SiteIssueRequestLines:"بنود طلبات الصرف", InventoryStocktakes:"الجرد",
        InventoryStocktakeLines:"بنود الجرد", InventoryReturns:"مرتجعات المخزون",
        InventoryReturnLines:"بنود المرتجعات", PurchaseRequisitions:"طلبات الشراء",
        PurchaseRequisitionLines:"بنود طلبات الشراء", SupplierQuotations:"عروض أسعار الموردين",
        SupplierQuotationLines:"بنود عروض الأسعار", PurchaseOrders:"أوامر الشراء",
        PurchaseOrderLines:"بنود أوامر الشراء", PurchaseGoodsReceipts:"استلام التوريدات",
        PurchaseGoodsReceiptLines:"بنود الاستلام", SupplierInvoices:"فواتير الموردين",
        SupplierInvoiceLines:"بنود فواتير الموردين", ContractAttachments:"مرفقات العقود",
        TechnicalSettlementEstimates:"تقديرات المستخلصات الفنية",
        TechnicalSettlementEstimateItems:"بنود التقديرات الفنية",
        CounterpartyAliases:"الأسماء البديلة للأطراف", Counterparties:"العملاء والموردون والمقاولون",
        Beneficiaries:"المستفيدون", InventoryWarehouses:"المخازن", InventoryItems:"أصناف المخزون",
        TreasuryAccounts:"تعريفات الخزائن والبنوك", ItemCatalog:"دليل الأصناف"
      };
      $("#previewbox").innerHTML = `<h4>${tr("ملخص المعاينة","Preview summary")}</h4>
        <p><b>${tr("عدد السجلات التي ستُحذف:","Rows to delete:")} ${d.total_rows.toLocaleString()}</b></p>
        ${d.tables.length ? `<div class="tbl-wrap"><table><thead><tr><th>${tr("الجدول","Table")}</th><th>${tr("عدد السجلات","Rows")}</th></tr></thead><tbody>${d.tables.map(x=>`<tr><td>${esc(labels[x.table] || x.table)}</td><td>${x.count.toLocaleString()}</td></tr>`).join("")}</tbody></table></div>` : `<p class="muted">${tr("لا توجد سجلات في الجداول المحددة للحذف.","No records found in the selected tables.")}</p>`}
        ${d.accounts_opening_balances_to_zero ? `<p>${tr("حسابات سيتم تصفير أرصدتها الافتتاحية:","Accounts with opening balances to zero:")} <b>${d.accounts_opening_balances_to_zero}</b></p>` : ""}
        <p class="muted">${tr("بيانات ستظل محفوظة:","Data that will be preserved:")} ${d.protected.map(esc).join("، ")}</p>
        <p class="muted">${tr("راجع القائمة جيدًا. لن يتم الحذف بمجرد المعاينة.","Review carefully. Preview alone never deletes data.")}</p>`;
      $("#confirmbox").hidden = false;
    } catch(e) { $("#reseterr").textContent = errText(e); }
    finally { busy(false); }
  }));
  $("#execute").onclick = async () => {
    if (!previewMode) { $("#reseterr").textContent = tr("اختر تصفير البيانات أو ضبط المصنع وأعد المعاينة قبل التنفيذ.","Choose a reset action and preview it before execution."); return; }
    if ($("#resetphrase").value !== "RESET") { $("#reseterr").textContent = tr("اكتب RESET كما هو.","Type RESET exactly."); return; }
    if (!$("#resetpassword").value) { $("#reseterr").textContent = tr("أدخل كلمة مرور المدير.","Enter the administrator password."); return; }
    const promptText = tr("تأكيد أخير: سيتم أخذ نسخة احتياطية ثم حذف البيانات الموضحة في المعاينة. هل تريد الاستمرار؟","Final confirmation: a backup will be created, then the previewed data will be deleted. Continue?");
    if (!confirm(promptText)) return;
    busy(true); $("#reseterr").textContent = "";
    try {
      const d = await api("/admin/reset/execute", {method:"POST", json:{mode:previewMode,confirm_text:$("#resetphrase").value,password:$("#resetpassword").value}});
      toast(d.message);
      $("#previewbox").innerHTML = `<p class="tag ok">${esc(d.message)}</p><p>${tr("النسخة الاحتياطية:","Backup:")} <b dir="ltr">${esc(d.backup)}</b></p><p>${tr("عدد السجلات المحذوفة:","Deleted rows:")} ${Object.values(d.deleted).reduce((a,b)=>a+b,0).toLocaleString()}</p>`;
      $("#confirmbox").hidden = true; previewMode = null;
    } catch(e) { $("#reseterr").textContent = errText(e); }
    finally { busy(false); }
  };
}
