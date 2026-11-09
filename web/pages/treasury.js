import { esc, money, toast, safe, formDialog, today, errText } from "../ui.js";
import { translate as tr } from "../i18n.js";
const CODE = { "cib-egp": "BankCibEgp", "cib-usd": "BankCibUsd", "cash-egp": "CashEgp", "cash-usd": "CashUsd" };
const USD_TX_LABELS = { funding: tr("تمويل","Funding"), customer_collection: tr("تحصيل عميل","Customer collection"), customer_advance: tr("دفعة مقدمة من عميل","Customer advance"), direct_income: tr("إيراد مباشر","Direct income"), supplier_payment: tr("سداد مورد/مقاول","Supplier/contractor payment"), supplier_advance: tr("دفعة مقدمة لمورد","Supplier advance"), expense_payment: tr("مصروفات","Expenses"), asset_purchase: tr("شراء أصل/مخزون","Asset/inventory purchase"), cash_transfer: tr("تحويل نقدي","Cash transfer") };

export async function render(main, { api, auth, route }) {
  const SC = CODE[route.split("/").pop()], can = a => auth.can(SC, a), base = "/treasury/" + SC;
  const info = await api(base + "/account");
  if (!info.account) return setup(info);
  const acc = info.account;
  const treasuryOptions = await api(base + "/available-accounts");
  let selectedTreasuryId = String(acc.treasury_account_id);
  const projs = await api("/projects/lookup").catch(() => []);
  main.innerHTML = `<h3 style="margin-top:0">${esc(localStorage.getItem("fs_lang")==="en"?(acc.name_en||acc.name_ar):acc.name_ar)} <small class="muted">${esc(acc.currency_code)} — ${esc(acc.gl_account)}</small> ${auth.can(SC,"Edit") || auth.can(SC,"Add") ? `<button class="btn sm" id="edit-gl-link">${tr("تصحيح ربط شجرة الحسابات","Fix chart of accounts link")}</button>` : ""}</h3>
    <div class="toolbar"><div class="w" style="width:150px"><label>${tr("من","From")}</label><input type="date" id="df"></div><div class="w" style="width:150px"><label>${tr("إلى","To")}</label><input type="date" id="dt"></div>
    <div class="grow"><label>${tr("بحث","Search")}</label><input id="q"></div>${can("Add") ? `<button class="btn primary" id="add">+ ${tr("حركة","Transaction")}</button>` : ""}</div>
    <div id="sum" class="muted" style="margin-bottom:8px"></div>
    <div class="tbl-wrap"><table><thead><tr><th>${tr("التاريخ","Date")}</th><th>${tr("من حساب","From account")}</th><th>${tr("إلى حساب","To account")}</th><th>${tr("وارد","Inflow")}</th><th>${tr("منصرف","Outflow")}</th><th>${tr("الرصيد","Balance")}</th><th>${tr("البيان","Description")}</th>${`<th>${tr("نوع الحركة","Transaction type")}</th><th>${tr("البطاقة المرجعية","Party reference")}</th>`}${acc.currency_code === "USD" ? `<th>${tr("سعر الصرف","Exchange rate")}</th>` : ""}<th>${tr("رقم الإذن","Voucher No.")}</th><th>${tr("الحالة","Status")}</th><th>${tr("المستلم","Recipient")}</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`;
  const $ = s => main.querySelector(s); let items = [];
  $("#edit-gl-link")?.addEventListener("click", safe(() => setup(info, true)));
  const load = async () => {
    const p = new URLSearchParams({ limit: 500 }); for (const [k, id] of [["date_from", "#df"], ["date_to", "#dt"], ["q", "#q"]]) if ($(id).value.trim()) p.set(k, $(id).value.trim());
    p.set("treasury_account_id", selectedTreasuryId);
    const r = await api(base + "/transactions?" + p); items = r.items;
    $("#sum").innerHTML = `${tr("رصيد أول الفترة:","Opening balance:")} <b>${money(r.opening_balance) === "-" ? "0.00" : money(r.opening_balance)}</b> — ${tr("وارد:","Inflow:")} <b>${money(r.total_inflow)}</b> — ${tr("منصرف:","Outflow:")} <b>${money(r.total_outflow)}</b> — ${tr("الرصيد الحالي:","Current balance:")} <b>${money(r.closing_balance) === "-" ? "0.00" : money(r.closing_balance)}</b>${r.total > 500 ? ` — (${tr("معروض أول 500 حركة","First 500 transactions shown")})` : ""}`;
    $("#rows").innerHTML = items.map(t => `<tr><td>${t.transaction_date}</td><td>${esc(t.from_account_label || (+t.inflow > 0 ? (t.counterpart_account_label || "—") : (t.treasury_account_name || acc.name_ar)))}</td><td>${esc(t.to_account_label || (+t.inflow > 0 ? (t.treasury_account_name || acc.name_ar) : (t.counterpart_account_label || "—")))}</td><td class="num">${money(t.inflow)}</td><td class="num">${money(t.outflow)}</td><td class="num">${money(t.balance) === "-" ? "0.00" : money(t.balance)}</td>
      <td>${esc(t.description)}</td>${`<td>${esc(USD_TX_LABELS[t.transaction_type] || "—")}</td><td>${esc(t.counterparty_label || "—")}</td>`}${acc.currency_code === "USD" ? `<td class="num">${t.exchange_rate ? Number(t.exchange_rate).toFixed(6) : "—"}</td>` : ""}<td>${esc(t.voucher_no)}</td><td>${esc(t.status)}</td><td>${esc(t.recipient_name)}</td>
      <td>${t.locked ? `<span class="tag">${tr("مرتبط بقيد","Linked to journal entry")}</span>` : acc.currency_code === "EGP" ? `<span class="tag muted">${tr("حركة قديمة غير مرتبطة — للمراجعة","Legacy movement — reconciliation required")}</span>` : `${can("Edit") ? `<button class="btn sm" data-e="${t.transaction_id}">${tr("تعديل","Edit")}</button> ` : ""}${can("Delete") ? `<button class="btn sm danger" data-d="${t.transaction_id}">${tr("حذف","Delete")}</button>` : ""}`}</td></tr>`).join("")
      || `<tr><td colspan="${acc.currency_code === "USD" ? 14 : 13}" class="muted">${tr("لا توجد حركات","No transactions")}</td></tr>`;
  };
  const form = async t => {
    const initialDirection = t ? (+t.inflow > 0 ? "inflow" : "outflow") : "inflow";
    const initialType = t?.transaction_type || "";
    const initialParties = await api(base + "/counterparties").catch(() => []);
    const initialCounterparts = initialType
      ? await api(base + "/counterpart-accounts?direction=" + initialDirection + "&transaction_type=" + encodeURIComponent(initialType) + "&treasury_account_id=" + encodeURIComponent(t?.treasury_account_id || selectedTreasuryId)).catch(() => []) : [];
    return formDialog({
    title: t ? tr("تعديل حركة","Edit transaction") : tr("حركة جديدة","New transaction"), values: t ? { ...t, amount: +t.inflow > 0 ? (+t.inflow || "") : (+t.outflow || ""), direction: +t.inflow > 0 ? "inflow" : "outflow", project_id: t.project_id ?? "", transaction_type: t.transaction_type || "", counterparty_id: t.counterparty_id ? String(t.counterparty_id) : "", treasury_account_id: String(t.treasury_account_id || selectedTreasuryId) } : { transaction_date: today(), transaction_type: "", amount: "", direction: "inflow", treasury_account_id: selectedTreasuryId },
    fields: [{ name: "transaction_date", label: tr("التاريخ","Date"), type: "date", required: true },
      { name: "treasury_account_id", label: tr("حساب البنك / الخزينة","Bank / cash account"), type: "select", options: treasuryOptions.map(a => [String(a.treasury_account_id), a.label]), required: true, full: true },
      { name: "transaction_type", label: tr("نوع الحركة","Transaction type"), type: "select", options: [
          ["funding", tr("تمويل من المساهمين أو الأطراف ذات العلاقة","Shareholder/related-party funding")],
          ["customer_collection", tr("تحصيل مستحقات من عميل","Customer receivable collection")],
          ["customer_advance", tr("تحصيل دفعة مقدمة من عميل","Customer advance receipt")],
          ["direct_income", tr("تحصيل إيراد مباشر","Direct income receipt")],
          ["supplier_payment", tr("سداد مورد أو مقاول","Supplier/contractor payment")],
          ["supplier_advance", tr("دفعة مقدمة لمورد أو مقاول","Supplier/contractor advance")],
          ["expense_payment", tr("سداد مصروفات","Expense payment")],
          ["asset_purchase", tr("شراء أصل أو مخزون أو أعمال تحت التنفيذ","Asset, inventory or work-in-progress purchase")],
          ["cash_transfer", tr("تحويل بين حسابات نقدية","Transfer between cash/bank accounts")]
        ], required: true, full: true },
      ...(acc.currency_code === "USD" ? [{ name: "exchange_rate", label: tr("سعر الدولار مقابل الجنيه","USD exchange rate to EGP"), type: "number", step: "0.000001", min: "0.000001", required: true }] : []),
      { name: "direction", label: tr("اتجاه الحركة","Movement direction"), type: "select", options: [["inflow", tr("وارد","Inflow")], ["outflow", tr("منصرف","Outflow")]], required: true },
      { name: "counterparty_id", label: tr("بطاقة الطرف (مرجع اختياري)","Party card (optional reference)"), type: "select", searchable: true, options: initialParties.map(p => [String(p.counterparty_id), p.label]), optional: true, full: true },
      { name: "counterpart_account_id", label: tr("الحساب المقابل من شجرة الحسابات","Counterpart account from chart of accounts"), type: "select", searchable: true, options: initialCounterparts.map(a => [String(a.account_id), a.label]), required: true, full: true },
      { name: "amount", label: tr("قيمة الحركة","Transaction amount"), type: "number", step: "0.01", min: "0.01", required: true }, { name: "voucher_no", label: tr("رقم الإذن","Voucher No.") },
      { name: "description", label: tr("البيان","Description"), full: true }, { name: "status", label: tr("الحالة (مثال: تمويل)","Status (e.g. Funding)") }, { name: "recipient_name", label: tr("المستلم","Recipient") },
      { name: "project_id", label: tr("مركز التكلفة (اختياري عند ارتباط الحركة بمشروع)","Cost center (optional; select when the movement relates to a project)"), type: "select", optional: true, options: projs.map(p => [p.project_id, p.name_ar]), full: true }],
    onSubmit: async v => {
      const saved = await api(t ? `${base}/transactions/${t.transaction_id}` : base + "/transactions", { method: t ? "PUT" : "POST", json: {
        transaction_date: v.transaction_date, inflow: v.direction === "inflow" ? (v.amount || "0") : "0", outflow: v.direction === "outflow" ? (v.amount || "0") : "0", description: v.description || null, voucher_no: v.voucher_no || null,
        status: v.status || null, recipient_name: v.recipient_name || null, project_id: v.project_id ? +v.project_id : null,
        exchange_rate: acc.currency_code === "USD" ? v.exchange_rate : null,
        counterpart_account_id: v.counterpart_account_id ? Number(v.counterpart_account_id) : null,
        counterparty_id: v.counterparty_id ? Number(v.counterparty_id) : null,
        treasury_account_id: Number(v.treasury_account_id), transaction_type: v.transaction_type } });
      selectedTreasuryId = String(v.treasury_account_id);
      toast(`${tr("تم الحفظ وإنشاء القيد كمسودة","Saved; draft journal created")}: ${saved.journal_entry_no || "—"}`); await load();
    },
    onOpen: (dlg, formEl) => {
      const counterpartSelect = formEl.elements.namedItem("counterpart_account_id");
      const movementDirectionSelect = formEl.elements.namedItem("direction");
      const partySelect = formEl.elements.namedItem("counterparty_id");
      const accountSelect = formEl.elements.namedItem("treasury_account_id");
      const typeSelect = formEl.elements.namedItem("transaction_type");
      let counterpartIsTreasury = initialCounterparts.some(a =>
        String(a.account_id) === String(t?.counterpart_account_id) && a.is_treasury_account);
      const amount = formEl.elements.namedItem("amount");
      const setFieldLabel = (field, label) => {
        const labelElement = field?.parentElement?.querySelector("label");
        if (labelElement) labelElement.textContent = label;
      };
      const updateFieldLabels = () => {
        const type = typeSelect.value, direction = movementDirectionSelect.value;
        setFieldLabel(accountSelect, tr("حساب البنك / الخزينة","Bank / cash account"));
        const counterpartLabel = counterpartIsTreasury
          ? (direction === "inflow" ? tr("حساب المصدر","Source account") : tr("حساب المستلم","Receiving account"))
          : type === "funding"
            ? tr("حساب الممول (من شجرة الحسابات)","Funding account (from chart of accounts)")
            : tr("الحساب المقابل من شجرة الحسابات","Counterpart account from chart of accounts");
        setFieldLabel(counterpartSelect, counterpartLabel);
      };
      const currentDirection = () => movementDirectionSelect.value;
      const refreshParties = async () => {
        const selected = partySelect.value;
        partySelect.required = false;
        partySelect.disabled = true;
        try {
          const options = await api(base + "/counterparties");
          partySelect.innerHTML = '<option value="">—</option>' + options.map(p =>
            `<option value="${String(p.counterparty_id)}">${esc(p.label)} — ${esc(p.account_label)}</option>`).join("");
          if (options.some(p => String(p.counterparty_id) === selected)) partySelect.value = selected;
        } finally { partySelect.disabled = false; }
      };
      const refreshCounterparts = async direction => {
        const selected = counterpartSelect.value, transactionType = typeSelect.value;
        counterpartSelect.disabled = true;
        try {
          if (!transactionType || !direction) {
            counterpartSelect.innerHTML = '<option value="">—</option>';
            return;
          }
          const accountSelect = formEl.elements.namedItem("treasury_account_id");
          const options = await api(base + "/counterpart-accounts?direction=" + direction + "&transaction_type=" + encodeURIComponent(transactionType) + "&treasury_account_id=" + encodeURIComponent(accountSelect.value));
          counterpartSelect.innerHTML = '<option value="">—</option>' + options.map(a =>
            `<option value="${String(a.account_id)}">${esc(a.label)}</option>`).join("");
          if (options.some(a => String(a.account_id) === selected)) counterpartSelect.value = selected;
          const selectedOption = options.find(a => String(a.account_id) === String(counterpartSelect.value));
          counterpartIsTreasury = Boolean(selectedOption?.is_treasury_account);
          updateFieldLabels();
          updateHint();
        } catch (e) {
          counterpartSelect.innerHTML = '<option value="">—</option>';
          throw e;
        } finally { counterpartSelect.disabled = false; }
      };
      const updateHint = () => {
        const d = currentDirection(), type = typeSelect.value;
        const cashLabel = accountSelect.options[accountSelect.selectedIndex]?.text || "حساب البنك / الخزينة";
        const counterpartLabel = counterpartSelect.options[counterpartSelect.selectedIndex]?.text || "الحساب المقابل";
        const isTransfer = counterpartIsTreasury;
        const routeLabel = isTransfer
          ? (d === "inflow"
            ? "من حساب المصدر " + counterpartLabel + " إلى حساب المستلم " + cashLabel
            : "من حساب المصدر " + cashLabel + " إلى حساب المستلم " + counterpartLabel)
          : d === "inflow"
            ? "من حساب " + counterpartLabel + " إلى حساب " + cashLabel
            : "من حساب " + cashLabel + " إلى حساب " + counterpartLabel;
        const accountingHint = d === "inflow"
          ? "الوارد: البنك/الخزينة مدين والحساب المقابل دائن."
          : "المنصرف: الحساب المقابل مدين والبنك/الخزينة دائن.";
        sideHint.textContent = !type || !d ? "اختَر نوع الحركة واتجاهها المستقل."
          : routeLabel + " — قيمة الحركة: " + (amount.value || "—") + " — " + accountingHint;
      };
      typeSelect.addEventListener("change", () => { updateFieldLabels(); refreshCounterparts(currentDirection()).catch(e => toast(errText(e))); updateHint(); });
      movementDirectionSelect.addEventListener("change", () => { updateFieldLabels(); refreshCounterparts(currentDirection()).catch(e => toast(errText(e))); updateHint(); });
      counterpartSelect.addEventListener("change", updateHint);
      accountSelect.addEventListener("change", () => refreshCounterparts(currentDirection()).catch(e => toast(errText(e))));
      partySelect.addEventListener("change", updateHint);
      updateFieldLabels();
      refreshParties().then(() => refreshCounterparts(currentDirection())).catch(e => toast(errText(e)));
      amount.addEventListener("input", updateHint);
      const sideHint = document.createElement("small");
      sideHint.className = "muted";
      sideHint.textContent = "نوع الحركة وصف فقط؛ اختر اتجاه الوارد أو المنصرف بشكل مستقل.";
      counterpartSelect.parentElement.appendChild(sideHint);
      updateHint();
    } });
  };
  for (const id of ["#df", "#dt"]) $(id).onchange = safe(load);
  let tm; $("#q").oninput = () => { clearTimeout(tm); tm = setTimeout(safe(load), 300); };
  if (can("Add")) $("#add").onclick = safe(() => form(null));
  $("#rows").onclick = safe(async ev => {
    const e = ev.target.closest("[data-e]"), d = ev.target.closest("[data-d]");
    if (e) await form(items.find(x => x.transaction_id == e.dataset.e));
    if (d && confirm(tr("حذف الحركة؟","Delete this transaction?"))) { await api(`${base}/transactions/${d.dataset.d}`, { method: "DELETE" }); toast(tr("تم الحذف","Deleted")); await load(); }
  });
  await load();

  function setup(info, editExisting = false) {
    if (editExisting) {
      api(base + "/gl-accounts").then(gl => formDialog({
        title: `${tr("تصحيح ربط شجرة الحسابات","Fix chart of accounts link")} — ${esc(info.account.name_en||info.account.name_ar)}`,
        values: { gl: String(info.account.gl_account_id) },
        fields: [{ name: "gl", label: tr("حساب الأستاذ (نقدية بالصندوق والبنوك)","Ledger account (cash on hand and at banks)"), type: "select", searchable: true,
          options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => {
          await api(base + "/account", { method: "PUT", json: { gl_account_id: Number(v.gl) } });
          toast(tr("تم تصحيح ربط حساب البنك بشجرة الحسابات","Bank account link updated"));
          main.innerHTML = ""; await render(main, { api, auth, route });
        }
      })).catch(e => toast(errText(e)));
      return;
    }
    main.innerHTML = `<div class="sec"><h3>${tr("تجهيز الحساب","Account setup")}</h3><div style="padding:16px"><p class="muted">${tr("الشاشة دي لسه مش مربوطة بحساب خزينة/بنك. عند التسجيل تُحفظ البيانات في قاعدة بيانات النظام على الخادم، وتُربط بحساب فرعي نشط من شجرة الحسابات؛ لا تُحفظ كبيانات محلية في المتصفح.","This screen is not yet linked to a treasury/bank account. Registration saves data to the server database and links it to an active leaf account in the chart of accounts; data is not stored locally in the browser.")}</p>${can("Add") ? `<button class="btn primary" id="go">${tr("تسجيل الحساب","Register account")}</button>` : `<p>${tr("اطلب من المسؤول تسجيل الحساب.","Ask an administrator to register the account.")}</p>`}</div></div>`;
    main.querySelector("#go")?.addEventListener("click", safe(async () => {
      const gl = await api(base + "/gl-accounts"); const byLabel = Object.fromEntries(gl.map(g => [g.label, g.account_id]));
      const isUsdCash = SC === "CashUsd";
      const fixedName = { "BankCibEgp": "البنك التجاري الدولي CIB - جنيه مصري", "BankCibUsd": "البنك التجاري الدولي CIB - دولار أمريكي", "CashEgp": "خزينة الجنيه المصري", "CashUsd": "خزينة الدولار" }[SC];
      const dlg = formDialog({ title: tr("تسجيل حساب الخزينة/البنك","Register treasury/bank account"),
        values: { name_ar: fixedName, account_type: info.default_type, currency_code: info.default_currency },
        fields: [{ name: "name_ar", label: tr("الحساب الثابت","Fixed account"), readonly: true, required: true, full: true },
          ...(isUsdCash ? [] : [
            { name: "account_type", label: tr("النوع","Type"), type: "select", options: [["Bank", tr("بنك","Bank")], ["Cash", tr("خزينة","Cash")]] },
            { name: "currency_code", label: tr("العملة","Currency"), required: true },
            { name: "bank_account_number", label: tr("رقم الحساب البنكي","Bank account number") }
          ]),
          { name: "gl", label: tr("حساب الأستاذ (نقدية بالصندوق والبنوك)","Ledger account (cash on hand and at banks)"), type: "select", searchable: true,
            options: gl.map(g => [String(g.account_id), g.label]), required: true, full: true }],
        onSubmit: async v => { const id = Number(v.gl) || byLabel[v.gl]; if (!id) throw new Error(tr("اختار حساب الأستاذ من القايمة","Select a ledger account from the list"));
          await api(base + "/account", { method: "POST", json: { name_ar: v.name_ar, account_type: isUsdCash ? "Cash" : v.account_type, currency_code: isUsdCash ? "USD" : v.currency_code.toUpperCase(), bank_account_number: isUsdCash ? null : (v.bank_account_number || null), gl_account_id: id } });
          toast(tr("تم التسجيل","Registered")); main.innerHTML = ""; await render(main, { api, auth, route }); } });
    }));
  }
}
