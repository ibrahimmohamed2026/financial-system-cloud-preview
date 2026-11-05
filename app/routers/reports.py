from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, select, case, or_

from ..common import money
from ..database import get_db
from ..deps import require_permission
from ..models import (User, Account, AccountClassification, JournalEntry, JournalEntryDetail, TreasuryAccount,
                      TreasuryTransaction, Contract, ContractAddendum, ContractChangeOrder, ContractSettlement,
                      ContractSettlementItem, ContractItem, TechnicalSettlementEstimate,
                      TechnicalSettlementEstimateItem, Counterparty, CounterpartyAlias, ContractRequest, PurchaseOrder,
                      Check, Beneficiary, PurchaseOrderLine, InventoryItem, InventoryMovement, InventoryWarehouse, Project,
                      SupplierInvoice)
from ..services_tb import compute_tb

router = APIRouter(prefix="/reports", tags=["Reports"])
api_router = APIRouter(prefix="/api/reports", tags=["Reports Analytics"])
D0 = Decimal("0")


def json_object(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        import json
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _group(rows: list[dict], net) -> dict[int, dict]:
    g: dict[int, dict] = {}
    for r in rows:
        x = g.setdefault(r["classification_id"], {"classification_id": r["classification_id"],
                                                  "name": r["classification"], "dr": 0, "cr": 0, "net": D0})
        x["dr" if r["normal_balance"] == "DR" else "cr"] += 1
        x["net"] += net(r)  # صافي (مدين - دائن)
    return g


@router.get("/balance-sheet")
def balance_sheet(as_of: date | None = None, _: User = Depends(require_permission("BalanceSheet", "View")),
                  db: Session = Depends(get_db)):
    as_of = as_of or date.today()
    rows = [r for r in compute_tb(db, None, as_of) if not r["is_parent"]]
    bs = _group([r for r in rows if r["statement_type"] == "BalanceSheet"], lambda r: r["td"] - r["tc"])
    result = sum((r["tc"] - r["td"] for r in rows if r["statement_type"] == "IncomeStatement"), D0)
    assets, liabs = [], []
    for g in bs.values():
        side = "DR" if g["dr"] >= g["cr"] else "CR"
        amount = g["net"] if side == "DR" else -g["net"]
        if amount == 0:
            continue
        (assets if side == "DR" else liabs).append({"name": g["name"], "amount": money(amount)})
    liabs.append({"name": "صافي ربح (خسارة) الفترة", "amount": money(result)})
    ta = sum((Decimal(x["amount"]) for x in assets), D0)
    tl = sum((Decimal(x["amount"]) for x in liabs), D0)
    return {"as_of": as_of, "assets": assets, "liabilities_equity": liabs, "total_assets": money(ta),
            "total_liabilities_equity": money(tl), "difference": money(ta - tl), "balanced": ta == tl}


@router.get("/income-statement")
def income_statement(date_from: date | None = None, date_to: date | None = None,
                     _: User = Depends(require_permission("IncomeStatement", "View")),
                     db: Session = Depends(get_db)):
    today = date.today()
    date_from, date_to = date_from or date(today.year, 1, 1), date_to or today
    rows = [r for r in compute_tb(db, date_from, date_to) if not r["is_parent"] and r["statement_type"] == "IncomeStatement"]
    g = _group(rows, lambda r: r["d"] - r["c"])
    revenue, expenses = [], []
    for x in g.values():
        side = "CR" if x["cr"] > x["dr"] else "DR"
        amount = -x["net"] if side == "CR" else x["net"]
        if amount == 0:
            continue
        (revenue if side == "CR" else expenses).append({"name": x["name"], "amount": money(amount)})
    tr = sum((Decimal(i["amount"]) for i in revenue), D0)
    te = sum((Decimal(i["amount"]) for i in expenses), D0)
    return {"date_from": date_from, "date_to": date_to, "revenue": revenue, "expenses": expenses,
            "total_revenue": money(tr), "total_expenses": money(te), "net_income": money(tr - te)}


@api_router.get("/data", tags=["Reports Analytics"])
@router.get("/data", tags=["Reports Analytics"])
def reports_analytics(date_from: date | None = None, date_to: date | None = None,
                      _: User = Depends(require_permission("AnalyticsReports", "View")),
                      db: Session = Depends(get_db)):
    """بيانات التحليلات من القيود المرحلة وحركات الخزينة الفعلية."""
    today = date.today()
    date_from = date_from or date(today.year, 1, 1)
    date_to = date_to or today
    if date_from > date_to:
        from fastapi import HTTPException
        raise HTTPException(422, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")

    base = (select(AccountClassification.statement_type, AccountClassification.name_ar, Account.normal_balance,
                   func.coalesce(func.sum(JournalEntryDetail.debit_amount), 0),
                   func.coalesce(func.sum(JournalEntryDetail.credit_amount), 0))
            .select_from(JournalEntryDetail)
            .join(JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
            .join(Account, Account.account_id == JournalEntryDetail.account_id)
            .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
            .where(JournalEntry.status == "Posted", JournalEntry.entry_date >= date_from, JournalEntry.entry_date <= date_to)
            .group_by(AccountClassification.statement_type, AccountClassification.name_ar, Account.normal_balance))
    revenue = Decimal("0"); expenses = Decimal("0"); expense_items = []
    for stype, cname, normal_balance, dr, cr in db.execute(base).all():
        dr, cr = Decimal(dr or 0), Decimal(cr or 0)
        if stype != "IncomeStatement":
            continue
        # الحسابات ذات الرصيد الطبيعي الدائن تُعامل كإيراد، والمدين كمصروف.
        if normal_balance == "CR":
            revenue += max(cr - dr, D0)
        else:
            amount = max(dr - cr, D0)
            if amount:
                expenses += amount
                expense_items.append({"category": cname, "amount": money(amount)})

    # آخر 12 شهرًا حتى شهر date_to، مع احترام حد التاريخ المطلوب.
    month_start = date(date_to.year, date_to.month, 1)
    months = []
    y, m = month_start.year, month_start.month
    for _i in range(12):
        months.append((y, m))
        m -= 1
        if m == 0: y, m = y - 1, 12
    months.reverse()
    labels = [f"{y:04d}-{m:02d}" for y, m in months]
    cash_stmt = (select(extract("year", TreasuryTransaction.transaction_date),
                        extract("month", TreasuryTransaction.transaction_date),
                        func.coalesce(func.sum(TreasuryTransaction.inflow), 0),
                        func.coalesce(func.sum(TreasuryTransaction.outflow), 0))
                 .select_from(TreasuryTransaction)
                 .join(TreasuryAccount, TreasuryAccount.treasury_account_id == TreasuryTransaction.treasury_account_id)
                 .where(TreasuryTransaction.transaction_date >= date_from, TreasuryTransaction.transaction_date <= date_to,
                        TreasuryAccount.is_active == True)
                 .group_by(extract("year", TreasuryTransaction.transaction_date), extract("month", TreasuryTransaction.transaction_date)))
    cash_rows = {(int(y), int(m)): (Decimal(i or 0), Decimal(o or 0)) for y, m, i, o in db.execute(cash_stmt).all()}
    cash_flow = [{"month": label, "inflow": money(cash_rows.get((y, m), (D0, D0))[0]),
                  "outflow": money(cash_rows.get((y, m), (D0, D0))[1])} for (y, m), label in zip(months, labels)]

    # أفضل خمسة حسابات حسب إجمالي الحركة المدينة/الدائنة في الفترة؛ الرصيد الختامي شامل الافتتاحي.
    rows = compute_tb(db, None, date_to)
    accounts = []
    for r in rows:
        if r.get("is_parent"):
            continue
        debit = Decimal(r.get("td", 0) or 0); credit = Decimal(r.get("tc", 0) or 0)
        balance = debit - credit
        normal = r.get("normal_balance", "DR")
        side = "مدين" if balance >= 0 else "دائن"
        abnormal = (balance < 0 and normal == "DR") or (balance > 0 and normal == "CR")
        accounts.append({"account_code": r.get("code", ""), "account_name": r.get("name", ""),
                         "closing_balance": money(abs(balance)), "side": side,
                         "status": "حرج" if abnormal else "مستقر", "activity": debit + credit})
    accounts.sort(key=lambda a: a["activity"], reverse=True)
    return {"date_from": date_from, "date_to": date_to,
            "kpis": {"total_revenue": money(revenue), "total_expenses": money(expenses), "net_profit": money(revenue-expenses)},
            "cash_flow_monthly": cash_flow, "expenses_breakdown": sorted(expense_items, key=lambda x: Decimal(x["amount"]), reverse=True),
            "top_accounts": [{k:v for k,v in a.items() if k != "activity"} for a in accounts[:5]]}


def _validate_report_dates(date_from: date | None, date_to: date | None):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")


@api_router.get("/projects")
def report_projects(_: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    return {"items": [{"project_id": p.project_id, "name": p.name_ar} for p in db.scalars(
        select(Project).where(Project.is_active.is_(True)).order_by(Project.name_ar)).all()]}


@api_router.get("/financial-lookups")
def financial_report_lookups(_: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    active_accounts = db.scalars(select(Account).where(Account.is_active.is_(True)).order_by(Account.account_code)).all()
    parents = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    accounts = [{"account_id": a.account_id, "code": a.account_code, "name": a.account_name_ar}
        for a in active_accounts if a.account_id not in parents]
    treasury = db.scalars(select(TreasuryAccount).where(TreasuryAccount.is_active.is_(True)).order_by(TreasuryAccount.name_ar)).all()
    return {"accounts": accounts, "treasury_accounts": [{"treasury_account_id": t.treasury_account_id,
        "name": t.name_ar, "currency": t.currency_code} for t in treasury]}


@api_router.get("/account-ledger")
def account_ledger_report(account_id: int, date_from: date | None = None, date_to: date | None = None,
                          project_id: int | None = None,
                          _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    _validate_report_dates(date_from, date_to)
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "الحساب غير موجود")
    base = (select(JournalEntryDetail, JournalEntry).join(JournalEntry,
        JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
        .where(JournalEntryDetail.account_id == account_id, JournalEntry.status == "Posted"))
    if project_id:
        base = base.where(JournalEntryDetail.project_id == project_id)
    # For a bounded period, calculate the balance immediately before its start.
    # With no start date, the ledger itself begins at the account opening balance.
    opening_q = base.where(JournalEntry.entry_date < date_from) if date_from else None
    opening_rows = db.execute(opening_q).all() if opening_q is not None else []
    opening_debit = sum((Decimal(r.debit_amount or 0) for r, _ in opening_rows), D0)
    opening_credit = sum((Decimal(r.credit_amount or 0) for r, _ in opening_rows), D0)
    account_opening = (Decimal(account.opening_debit or 0) - Decimal(account.opening_credit or 0)) if not project_id else D0
    opening = account_opening + opening_debit - opening_credit
    stmt = base
    if date_from:
        stmt = stmt.where(JournalEntry.entry_date >= date_from)
    if date_to:
        stmt = stmt.where(JournalEntry.entry_date <= date_to)
    rows = db.execute(stmt.order_by(JournalEntry.entry_date, JournalEntry.journal_entry_id,
                                    JournalEntryDetail.line_no, JournalEntryDetail.detail_id)).all()
    running = opening
    items = []
    for detail, entry in rows:
        debit, credit = Decimal(detail.debit_amount or 0), Decimal(detail.credit_amount or 0)
        running += debit - credit
        project = db.get(Project, detail.project_id) if detail.project_id else None
        items.append({"date": str(entry.entry_date), "entry_no": entry.entry_no,
            "description": detail.description or entry.description or "", "project": project.name_ar if project else "",
            "debit": str(debit), "credit": str(credit), "balance": str(running)})
    return {"account": {"account_id": account.account_id, "code": account.account_code,
        "name": account.account_name_ar, "normal_balance": account.normal_balance},
        "opening_balance": str(opening), "total_debit": str(sum((Decimal(r[0].debit_amount or 0) for r in rows), D0)),
        "total_credit": str(sum((Decimal(r[0].credit_amount or 0) for r in rows), D0)),
        "closing_balance": str(running), "items": items}


@api_router.get("/project-financials")
def project_financial_report(date_from: date | None = None, date_to: date | None = None,
                             project_id: int | None = None,
                             _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    _validate_report_dates(date_from, date_to)
    stmt = (select(Project.project_id, Project.name_ar, AccountClassification.statement_type,
        Account.normal_balance, func.coalesce(func.sum(JournalEntryDetail.debit_amount), 0),
        func.coalesce(func.sum(JournalEntryDetail.credit_amount), 0))
        .select_from(JournalEntryDetail).join(JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
        .join(Account, Account.account_id == JournalEntryDetail.account_id)
        .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
        .join(Project, Project.project_id == JournalEntryDetail.project_id)
        .where(JournalEntry.status == "Posted"))
    if date_from: stmt = stmt.where(JournalEntry.entry_date >= date_from)
    if date_to: stmt = stmt.where(JournalEntry.entry_date <= date_to)
    if project_id: stmt = stmt.where(Project.project_id == project_id)
    stmt = stmt.group_by(Project.project_id, Project.name_ar, AccountClassification.statement_type, Account.normal_balance)
    totals: dict[int, dict] = {}
    names: dict[int, str] = {}
    for pid, name, statement_type, normal, debit, credit in db.execute(stmt).all():
        names[pid] = name
        row = totals.setdefault(pid, {"revenue": D0, "expenses": D0})
        debit, credit = Decimal(debit or 0), Decimal(credit or 0)
        if statement_type != "IncomeStatement":
            continue
        if normal == "CR": row["revenue"] += max(credit - debit, D0)
        else: row["expenses"] += max(debit - credit, D0)
    items = [{"project": names[pid], "revenue": str(v["revenue"]), "expenses": str(v["expenses"]),
        "net": str(v["revenue"] - v["expenses"])} for pid, v in sorted(totals.items(), key=lambda x: names[x[0]])]
    return {"items": items, "summary": {"project_count": len(items),
        "revenue": str(sum((Decimal(x["revenue"]) for x in items), D0)),
        "expenses": str(sum((Decimal(x["expenses"]) for x in items), D0)),
        "net": str(sum((Decimal(x["net"]) for x in items), D0))}}


@api_router.get("/cash-flow")
def cash_flow_report(date_from: date | None = None, date_to: date | None = None,
                     treasury_account_id: int | None = None,
                     _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    _validate_report_dates(date_from, date_to)
    stmt = (select(TreasuryTransaction, TreasuryAccount).join(TreasuryAccount,
        TreasuryAccount.treasury_account_id == TreasuryTransaction.treasury_account_id)
        .where(or_(TreasuryTransaction.status.is_(None), TreasuryTransaction.status.notin_(
            ("Cancelled", "ملغي", "ملغى", "مرتد")))))
    if date_from: stmt = stmt.where(TreasuryTransaction.transaction_date >= date_from)
    if date_to: stmt = stmt.where(TreasuryTransaction.transaction_date <= date_to)
    if treasury_account_id: stmt = stmt.where(TreasuryAccount.treasury_account_id == treasury_account_id)
    rows = db.execute(stmt.order_by(TreasuryTransaction.transaction_date, TreasuryTransaction.transaction_id).limit(5000)).all()
    items = [{"date": str(tx.transaction_date), "account": account.name_ar, "voucher_no": tx.voucher_no or "",
        "description": tx.description or "", "recipient": tx.recipient_name or "", "inflow": str(tx.inflow or 0),
        "outflow": str(tx.outflow or 0), "net": str(Decimal(tx.inflow or 0) - Decimal(tx.outflow or 0)),
        "project": db.get(Project, tx.project_id).name_ar if tx.project_id and db.get(Project, tx.project_id) else ""}
        for tx, account in rows]
    return {"items": items, "summary": {"count": len(items),
        "inflow": str(sum((Decimal(x["inflow"]) for x in items), D0)),
        "outflow": str(sum((Decimal(x["outflow"]) for x in items), D0)),
        "net": str(sum((Decimal(x["net"]) for x in items), D0))}}


@api_router.get("/aging")
def receivables_payables_aging(as_of: date | None = None, project_id: int | None = None,
                               _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    """Outstanding posted settlements/invoices grouped by age since document date."""
    as_of = as_of or date.today()
    rows = []
    settlements = db.scalars(select(ContractSettlement).where(
        ContractSettlement.status == "Posted", ContractSettlement.settlement_date <= as_of)
        .order_by(ContractSettlement.settlement_date)).all()
    for settlement in settlements:
        contract = db.get(Contract, settlement.contract_id)
        if not contract or (project_id and contract.project_id != project_id):
            continue
        paid_col = TreasuryTransaction.inflow if settlement.settlement_side == "Customer" else TreasuryTransaction.outflow
        paid = Decimal(db.scalar(select(func.coalesce(func.sum(paid_col), 0)).where(
            TreasuryTransaction.settlement_id == settlement.settlement_id,
            TreasuryTransaction.transaction_date <= as_of,
            or_(TreasuryTransaction.status.is_(None), TreasuryTransaction.status.notin_(("Cancelled", "ملغي", "ملغى", "مرتد"))))) or 0)
        balance = max(Decimal(settlement.net_amount or 0) - paid, D0)
        if balance <= 0: continue
        name = settlement.counterparty_name or contract.client_name or ""
        doc_no, doc_date = settlement.settlement_no, settlement.settlement_date
        kind = "مستحق لنا" if settlement.settlement_side == "Customer" else "مستحق علينا"
        project = db.get(Project, contract.project_id) if contract.project_id else None
        _append_aging_row(rows, as_of, kind, name, doc_no, doc_date, balance, project.name_ar if project else "")

    invoices = db.scalars(select(SupplierInvoice).where(SupplierInvoice.status == "Posted",
        SupplierInvoice.invoice_date <= as_of).order_by(SupplierInvoice.invoice_date)).all()
    for invoice in invoices:
        if project_id and invoice.project_id != project_id: continue
        paid = Decimal(db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(
            TreasuryTransaction.supplier_invoice_id == invoice.invoice_id,
            TreasuryTransaction.transaction_date <= as_of,
            or_(TreasuryTransaction.status.is_(None), TreasuryTransaction.status.notin_(("Cancelled", "ملغي", "ملغى", "مرتد"))))) or 0)
        balance = max(Decimal(invoice.total_amount or 0) - paid, D0)
        if balance <= 0: continue
        party = db.get(Counterparty, invoice.supplier_id)
        _append_aging_row(rows, as_of, "مستحق علينا", party.legal_name or party.name if party else "",
            invoice.invoice_no, invoice.invoice_date, balance,
            db.get(Project, invoice.project_id).name_ar if invoice.project_id and db.get(Project, invoice.project_id) else "")
    rows.sort(key=lambda r: (r["age_days"], r["party"]), reverse=True)
    buckets = {key: sum((Decimal(r["balance"]) for r in rows if r["bucket"] == key), D0)
        for key in ("0-30", "31-60", "61-90", "90+")}
    return {"as_of": as_of, "items": rows, "summary": {"count": len(rows),
        "receivable": str(sum((Decimal(r["balance"]) for r in rows if r["kind"] == "مستحق لنا"), D0)),
        "payable": str(sum((Decimal(r["balance"]) for r in rows if r["kind"] == "مستحق علينا"), D0)),
        "buckets": {key: str(value) for key, value in buckets.items()}}}


def _append_aging_row(rows, as_of, kind, party, number, doc_date, balance, project):
    age = max((as_of - doc_date).days, 0)
    bucket = "0-30" if age <= 30 else "31-60" if age <= 60 else "61-90" if age <= 90 else "90+"
    rows.append({"kind": kind, "party": party, "document_no": number, "document_date": str(doc_date),
        "age_days": age, "bucket": bucket, "balance": str(balance), "project": project})


@api_router.get("/settlements")
def settlements_report(date_from: date | None = None, date_to: date | None = None,
                      settlement_side: str | None = None, project_id: int | None = None, status: str | None = None,
                      _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    """كشف شامل للعقود والمستخلصات والمدفوعات المباشرة المرتبطة بها دون توحيد أسماء الأطراف."""
    _validate_report_dates(date_from, date_to)
    q = select(ContractSettlement, Contract).join(Contract, Contract.contract_id == ContractSettlement.contract_id)
    if date_from: q = q.where(ContractSettlement.settlement_date >= date_from)
    if date_to: q = q.where(ContractSettlement.settlement_date <= date_to)
    if settlement_side in ("Customer", "Subcontractor"): q = q.where(ContractSettlement.settlement_side == settlement_side)
    if project_id: q = q.where(Contract.project_id == project_id)
    if status: q = q.where(ContractSettlement.status == status)
    rows = db.execute(q.order_by(ContractSettlement.settlement_date.desc(), ContractSettlement.settlement_id.desc()).limit(5000)).all()
    ids = [x.settlement_id for x, _ in rows]
    paid_rows = db.execute(select(TreasuryTransaction.settlement_id,
                                 func.coalesce(func.sum(TreasuryTransaction.outflow), 0))
                           .where(TreasuryTransaction.settlement_id.in_(ids), TreasuryTransaction.outflow > 0)
                           .group_by(TreasuryTransaction.settlement_id)).all() if ids else []
    paid_by_id = {sid: Decimal(value or 0) for sid, value in paid_rows}
    items = []
    for x, contract in rows:
        paid = paid_by_id.get(x.settlement_id, D0)
        net = Decimal(x.net_amount or 0)
        items.append({"settlement_id": x.settlement_id, "settlement_no": x.settlement_no,
                      "settlement_date": x.settlement_date, "settlement_side": x.settlement_side,
                      "counterparty_name": x.counterparty_name, "contract_no": contract.contract_no,
                      "contract_title": contract.title, "project_id": contract.project_id,
                      "project": (db.get(Project, contract.project_id).name_ar if contract.project_id and db.get(Project, contract.project_id) else ""),
                      "work_value": money(x.work_value), "deductions": money(sum(
                          (Decimal(str(v.get("amount", 0))) for v in json_object(x.deductions_json).values()
                           if isinstance(v, dict)), D0)),
                      "vat_amount": money(x.vat_amount), "net_amount": money(net),
                      "paid_amount": money(paid), "remaining_amount": money(max(D0, net-paid)), "status": x.status})
    summary = {"count": len(items), "work_value": money(sum((Decimal(i["work_value"]) for i in items), D0)),
               "deductions": money(sum((Decimal(i["deductions"]) for i in items), D0)),
               "net_amount": money(sum((Decimal(i["net_amount"]) for i in items), D0)),
               "paid_amount": money(sum((Decimal(i["paid_amount"]) for i in items), D0)),
               "remaining_amount": money(sum((Decimal(i["remaining_amount"]) for i in items), D0))}
    return {"items": items, "summary": summary, "date_from": date_from, "date_to": date_to}


@api_router.get("/checks")
def checks_report(date_from: date | None = None, date_to: date | None = None, status: str | None = None,
                  project_id: int | None = None,
                  _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    """قائمة شيكات البنك حسب تاريخ الشيك وحالته، مع المستخلص المالي إن كان مرتبطًا."""
    _validate_report_dates(date_from, date_to)
    q = (select(Check, Beneficiary.name_ar, TreasuryAccount.name_ar, ContractSettlement.settlement_no)
         .join(Beneficiary, Beneficiary.beneficiary_id == Check.beneficiary_id)
         .join(TreasuryAccount, TreasuryAccount.treasury_account_id == Check.treasury_account_id)
         .outerjoin(ContractSettlement, ContractSettlement.settlement_id == Check.settlement_id))
    if date_from: q = q.where(Check.check_date >= date_from)
    if date_to: q = q.where(Check.check_date <= date_to)
    if status: q = q.where(Check.status == status)
    if project_id: q = q.where(Check.project_id == project_id)
    rows = db.execute(q.order_by(Check.check_date.desc(), Check.check_id.desc()).limit(5000)).all()
    items = [{"check_no": c.check_no or str(c.sequence_no), "check_date": c.check_date, "bank": bank,
              "beneficiary": beneficiary, "amount": money(c.amount or 0), "status": c.status,
              "settlement_no": settlement_no or "", "project_id": c.project_id,
              "project": (db.get(Project, c.project_id).name_ar if c.project_id and db.get(Project, c.project_id) else ""),
              "description": c.description or ""} for c, beneficiary, bank, settlement_no in rows]
    summary = {"count": len(items), "amount": money(sum((Decimal(i["amount"]) for i in items), D0)),
               "paid_amount": money(sum((Decimal(i["amount"]) for i in items if i["status"] == "تم الصرف"), D0)),
               "unlinked_count": sum(1 for i in items if not i["settlement_no"])}
    return {"items": items, "summary": summary, "date_from": date_from, "date_to": date_to}


@api_router.get("/purchases")
def purchases_report(date_from: date | None = None, date_to: date | None = None, status: str | None = None,
                     project_id: int | None = None,
                     _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    _validate_report_dates(date_from, date_to)
    q = select(PurchaseOrder).where(True)
    if date_from: q = q.where(PurchaseOrder.order_date >= date_from)
    if date_to: q = q.where(PurchaseOrder.order_date <= date_to)
    if status: q = q.where(PurchaseOrder.status == status)
    if project_id: q = q.where(PurchaseOrder.project_id == project_id)
    rows = db.scalars(q.order_by(PurchaseOrder.order_date.desc(), PurchaseOrder.purchase_order_id.desc()).limit(5000)).all()
    items = []
    for po in rows:
        warehouse = db.get(InventoryWarehouse, po.warehouse_id)
        lines = db.scalars(select(PurchaseOrderLine).where(
            PurchaseOrderLine.purchase_order_id == po.purchase_order_id)).all()
        received = sum((Decimal(line.received_quantity or 0) for line in lines), D0)
        ordered = sum((Decimal(line.quantity or 0) for line in lines), D0)
        project = db.get(Project, po.project_id) if po.project_id else None
        items.append({"order_no": po.order_no, "order_date": po.order_date, "supplier": po.supplier_name,
                      "project": project.name_ar if project else "",
                      "warehouse": warehouse.name if warehouse else "", "status": po.status,
                      "total_amount": money(po.total_amount), "ordered_quantity": str(ordered),
                      "received_quantity": str(received)})
    return {"items": items, "summary": {"count": len(items),
            "total_amount": money(sum((Decimal(i["total_amount"]) for i in items), D0))},
            "date_from": date_from, "date_to": date_to}


@api_router.get("/inventory")
def inventory_report(_: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    movement_rows = db.execute(select(InventoryMovement.item_id,
        func.sum(case((InventoryMovement.movement_type == "IN", InventoryMovement.quantity), else_=0)),
        func.sum(case((InventoryMovement.movement_type == "OUT", InventoryMovement.quantity), else_=0)))
        .group_by(InventoryMovement.item_id)).all()
    movement_by_item = {item_id: (Decimal(incoming or 0), Decimal(outgoing or 0))
                        for item_id, incoming, outgoing in movement_rows}
    items = []
    for item in db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all():
        incoming, outgoing = movement_by_item.get(item.item_id, (D0, D0))
        balance = incoming - outgoing
        items.append({"code": item.code, "name": item.name, "category": item.category or "", "unit": item.unit,
                      "balance": str(balance), "minimum": str(item.min_quantity or 0),
                      "low_stock": Decimal(item.min_quantity or 0) > 0 and balance <= Decimal(item.min_quantity or 0)})
    return {"items": items, "summary": {"count": len(items), "low_stock_count": sum(1 for i in items if i["low_stock"])}}


@api_router.get("/contractors")
def contractor_report_names(_: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):
    """Return raw names from business records; report filters never depend on alias consolidation."""
    name_queries = (
        select(ContractSettlement.counterparty_name).where(
            ContractSettlement.counterparty_name.is_not(None), func.trim(ContractSettlement.counterparty_name) != ""),
        select(TechnicalSettlementEstimate.counterparty_name).where(
            TechnicalSettlementEstimate.counterparty_name.is_not(None), func.trim(TechnicalSettlementEstimate.counterparty_name) != ""),
        select(TreasuryTransaction.recipient_name).where(
            TreasuryTransaction.settlement_id.is_(None), TreasuryTransaction.outflow > 0,
            TreasuryTransaction.recipient_name.is_not(None), func.trim(TreasuryTransaction.recipient_name) != ""),
        select(Contract.client_name).where(Contract.client_name.is_not(None), func.trim(Contract.client_name) != ""),
        select(PurchaseOrder.supplier_name).where(PurchaseOrder.supplier_name.is_not(None), func.trim(PurchaseOrder.supplier_name) != ""),
        select(ContractRequest.counterparty_name).where(ContractRequest.counterparty_name.is_not(None), func.trim(ContractRequest.counterparty_name) != ""),
    )
    names = {str(value).strip() for query in name_queries for value in db.scalars(query).all() if str(value).strip()}
    return {"items": [{"name": name} for name in sorted(names, key=str.casefold)]}


class ContractorAliasIn(BaseModel):

    alias_name: str = Field(min_length=1, max_length=200)

    canonical_name: str = Field(min_length=1, max_length=200)





@api_router.post("/contractor-aliases")

def set_contractor_alias(body: ContractorAliasIn,

                         user: User = Depends(require_permission("AnalyticsReports", "Edit")),

                         db: Session = Depends(get_db)):

    alias, canonical = body.alias_name.strip(), body.canonical_name.strip()

    if alias.casefold() == canonical.casefold():

        raise HTTPException(422, "اختر اسمين مختلفين")

    if db.scalar(select(CounterpartyAlias.alias_id).where(func.lower(CounterpartyAlias.alias_name) == canonical.casefold())):

        raise HTTPException(422, "الاسم الموحد نفسه مرتبط باسم آخر؛ اختر الاسم الأساسي الظاهر في القائمة")

    row = db.scalar(select(CounterpartyAlias).where(func.lower(CounterpartyAlias.alias_name) == alias.casefold()))

    party=db.scalar(select(Counterparty).where(func.lower(func.trim(Counterparty.legal_name))==canonical.casefold()))

    if party is None:

        from ..counterparties import resolve_counterparty

        party=resolve_counterparty(db,canonical,"Contractor",allow_inactive=True)

    # If the old name was itself a group's canonical label, move its aliases too.

    db.query(CounterpartyAlias).filter(func.lower(CounterpartyAlias.canonical_name) == alias.casefold()).update(

        {CounterpartyAlias.canonical_name: canonical}, synchronize_session=False)

    if row is None:

        row = CounterpartyAlias(alias_name=alias, canonical_name=canonical,counterparty_id=party.party_id if party else None)

        db.add(row)

    else:

        row.canonical_name = canonical; row.counterparty_id=party.party_id if party else row.counterparty_id

    db.flush()

    if party:

        for model,field in ((ContractSettlement,"counterparty_name"),(TechnicalSettlementEstimate,"counterparty_name"),(TreasuryTransaction,"recipient_name")):

            col=getattr(model,field)

            db.query(model).filter(model.counterparty_id.is_(None),func.lower(func.trim(col))==alias.casefold()).update({model.counterparty_id:party.party_id},synchronize_session=False)

    from ..deps import write_audit

    write_audit(db, user.user_id, "MapAlias", "CounterpartyAliases", row.alias_id,

                None, {"alias_name": alias, "canonical_name": canonical})

    db.commit()

    return {"alias_name": alias, "canonical_name": canonical}





@api_router.get("/contractor")

def contractor_report(counterparty_name: str | None = None, date_from: date | None = None, date_to: date | None = None,

                      _: User = Depends(require_permission("AnalyticsReports", "View")), db: Session = Depends(get_db)):

    # Resolve reports only by the exact name stored on the business records.
    name = (counterparty_name or "").strip()

    if not name:

        raise HTTPException(422, "اختر اسم المقاول")

    if date_from and date_to and date_from > date_to:

        raise HTTPException(422, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")

    # Exact source-name match deliberately keeps reports independent from
    # CounterpartyAlias and counterparty_id consolidation.
    source_name = name
    tech_q = select(TechnicalSettlementEstimate).where(
        func.trim(TechnicalSettlementEstimate.counterparty_name) == source_name)
    fin_q = select(ContractSettlement).where(
        func.trim(ContractSettlement.counterparty_name) == source_name)

    if date_from:

        tech_q = tech_q.where(TechnicalSettlementEstimate.estimate_date >= date_from)

        fin_q = fin_q.where(ContractSettlement.settlement_date >= date_from)

    if date_to:

        tech_q = tech_q.where(TechnicalSettlementEstimate.estimate_date <= date_to)

        fin_q = fin_q.where(ContractSettlement.settlement_date <= date_to)

    techs = db.scalars(tech_q.order_by(TechnicalSettlementEstimate.estimate_date, TechnicalSettlementEstimate.estimate_id)).all()

    financial = db.scalars(fin_q.order_by(ContractSettlement.settlement_date, ContractSettlement.sequence_no)).all()

    tech_by_fin = {t.financial_settlement_id: t for t in techs if t.financial_settlement_id is not None}

    linked_fin_ids = {t.financial_settlement_id for t in db.scalars(select(TechnicalSettlementEstimate).where(

        TechnicalSettlementEstimate.financial_settlement_id.is_not(None))).all()}

    contracts_by_id = {}

    settlements = []

    work_items = []

    approved_work = D0

    for t in techs:

        c = db.get(Contract, t.contract_id)

        if c:

            contracts_by_id[c.contract_id] = c

        linked = db.get(ContractSettlement, t.financial_settlement_id) if t.financial_settlement_id else None

        settlements.append({"kind": "فني", "number": t.estimate_no, "date": t.estimate_date,

            "contract_no": c.contract_no if c else "", "contract_title": c.title if c else "",

            "side": t.settlement_side, "status": t.status, "work_value": str(t.work_value),

            "deductions": "0", "vat": "0", "net": "", "linked_number": linked.settlement_no if linked else ""})

        lines = db.execute(select(TechnicalSettlementEstimateItem, ContractItem).join(

            ContractItem, ContractItem.item_id == TechnicalSettlementEstimateItem.contract_item_id

        ).where(TechnicalSettlementEstimateItem.estimate_id == t.estimate_id)).all()

        for line, item in lines:

            contract_qty = Decimal(str(item.quantity or 0))

            total_qty = Decimal(str(line.previous_quantity or 0)) + Decimal(str(line.current_quantity or 0))

            work_items.append({"date": t.estimate_date, "settlement_no": t.estimate_no, "kind": "فني",

                "contract_no": c.contract_no if c else "", "contract_title": c.title if c else "",

                "side": t.settlement_side, "status": t.status, "item_no": item.item_no,

                "description": item.description, "unit": item.unit,

                "previous_quantity": str(line.previous_quantity), "quantity": str(line.current_quantity),

                "cumulative_quantity": str(total_qty),

                "progress_percent": str((total_qty / contract_qty * 100) if contract_qty else D0),

                "unit_price": str(line.unit_price), "amount": str(line.amount)})

        if t.status == "TechnicallyApproved":

            approved_work += Decimal(str(t.work_value or 0))

    net_total = D0

    paid_total = D0

    outstanding_total = D0

    for x in financial:

        c = db.get(Contract, x.contract_id)

        if c:

            contracts_by_id[c.contract_id] = c

        linked_tech = tech_by_fin.get(x.settlement_id)

        deductions = sum((Decimal(str(v.get("amount", 0))) for v in json_object(x.deductions_json).values() if isinstance(v, dict)), D0)

        paid = Decimal(str(db.scalar(select(func.coalesce(func.sum(TreasuryTransaction.outflow), 0)).where(

            TreasuryTransaction.settlement_id == x.settlement_id)) or 0))

        outstanding = max(D0, Decimal(str(x.net_amount or 0)) - paid)

        settlements.append({"kind": "مالي", "number": x.settlement_no, "date": x.settlement_date,

            "contract_no": c.contract_no if c else "", "contract_title": c.title if c else "",

            "side": x.settlement_side, "status": x.status, "work_value": str(x.work_value),

            "deductions": str(deductions), "vat": str(x.vat_amount), "net": str(x.net_amount),

            "linked_number": linked_tech.estimate_no if linked_tech else "",

            "paid": str(paid), "outstanding": str(outstanding)})

        lines = db.execute(select(ContractSettlementItem, ContractItem).join(

            ContractItem, ContractItem.item_id == ContractSettlementItem.contract_item_id

        ).where(ContractSettlementItem.settlement_id == x.settlement_id)).all()

        for line, item in lines:

            if x.settlement_id in tech_by_fin:

                continue  # The technical estimate already reports these performed quantities.

            work_items.append({"date": x.settlement_date, "settlement_no": x.settlement_no, "kind": "مالي",

                "contract_no": c.contract_no if c else "", "contract_title": c.title if c else "",

                "side": x.settlement_side, "status": x.status, "item_no": item.item_no,

                "description": item.description, "unit": item.unit, "previous_quantity": "",

                "quantity": str(line.quantity), "cumulative_quantity": "", "progress_percent": "",

                "unit_price": str(line.unit_price), "amount": str(line.amount)})

        if x.status in ("Approved", "Posted"):

            net_total += Decimal(str(x.net_amount or 0))

            if x.settlement_side == "Subcontractor":

                paid_total += paid

                outstanding_total += outstanding

            if x.settlement_id not in linked_fin_ids or x.settlement_id not in tech_by_fin:

                approved_work += Decimal(str(x.work_value or 0))

    contract_rows = []

    for c in sorted(contracts_by_id.values(), key=lambda v: (v.contract_no or "")):

        addenda = db.scalar(select(func.coalesce(func.sum(ContractAddendum.value_change), 0)).where(

            ContractAddendum.contract_id == c.contract_id)) or 0

        changes = db.scalar(select(func.coalesce(func.sum(ContractChangeOrder.value_change), 0)).where(

            ContractChangeOrder.contract_id == c.contract_id, ContractChangeOrder.status == "Approved")) or 0

        contract_rows.append({"contract_no": c.contract_no, "title": c.title, "client_name": c.client_name,

            "status": c.status, "contract_value": str(Decimal(str(c.original_value or 0)) + Decimal(str(addenda or 0)) + Decimal(str(changes or 0)))})

    settlements.sort(key=lambda x: (str(x["date"]), x["number"]))

    work_items.sort(key=lambda x: (str(x["date"]), x["contract_no"], x["item_no"]))

    unallocated_q = select(TreasuryTransaction).where(
        TreasuryTransaction.settlement_id.is_(None), TreasuryTransaction.outflow > 0,
        func.trim(TreasuryTransaction.recipient_name) == source_name)

    if date_from:

        unallocated_q = unallocated_q.where(TreasuryTransaction.transaction_date >= date_from)

    if date_to:

        unallocated_q = unallocated_q.where(TreasuryTransaction.transaction_date <= date_to)

    unallocated_rows = db.scalars(unallocated_q.order_by(TreasuryTransaction.transaction_date, TreasuryTransaction.transaction_id)).all()

    unallocated = [{"date": t.transaction_date, "voucher_no": t.voucher_no or "", "description": t.description or "",

                    "amount": str(t.outflow), "project_id": t.project_id, "transaction_id": t.transaction_id}

                   for t in unallocated_rows]

    unallocated_total = sum((Decimal(str(t.outflow or 0)) for t in unallocated_rows), D0)

    return {"counterparty_name": name, "date_from": date_from, "date_to": date_to,

        "contracts": contract_rows, "settlements": settlements, "work_items": work_items,

        "unallocated_payments": unallocated,

        "summary": {"contract_count": len(contract_rows), "technical_count": len(techs),

            "financial_count": len(financial), "approved_work_value": money(approved_work),

            "approved_net_settlements": money(net_total), "paid_amount": money(paid_total),

            "outstanding_amount": money(outstanding_total), "unallocated_payments": money(unallocated_total)}}

