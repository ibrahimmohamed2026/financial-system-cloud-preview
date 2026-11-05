"""Financial control dashboard and filtered management reports.

All figures are read-only and derived from posted accounting entries,
contract settlements and linked treasury transactions.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..common import money
from ..database import get_db
from ..deps import require_permission
from ..models import (
    Account, Check, Contract, ContractAddendum, ContractChangeOrder,
    ContractSettlement, FinancialCheck, JournalEntry, JournalEntryDetail,
    TechnicalSettlementEstimate, TreasuryTransaction, User,
)

router = APIRouter(prefix="/api/financial-control", tags=["Financial Control"])
D0 = Decimal("0")
CLOSED_CHECKS = {"مُحصّل", "منصرف", "ملغي"}
CANCELLED = {"Cancelled", "Canceled", "ملغي"}


def _dates(date_from: date | None, date_to: date | None):
    today = date.today()
    start = date_from or date(today.year, 1, 1)
    end = date_to or today
    if start > end:
        raise HTTPException(422, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
    return start, end


def _dec(value):
    return Decimal(str(value or 0))


def _money(value):
    return str(money(_dec(value)))


def _settlement_paid(db: Session, settlement: ContractSettlement) -> Decimal:
    stmt = select(func.coalesce(func.sum(
        TreasuryTransaction.outflow if settlement.settlement_side == "Subcontractor"
        else TreasuryTransaction.inflow
    ), 0)).where(
        TreasuryTransaction.settlement_id == settlement.settlement_id,
        TreasuryTransaction.status.notin_(tuple(CANCELLED)),
    )
    if settlement.settlement_side == "Subcontractor":
        stmt = stmt.where(TreasuryTransaction.status == "تم الصرف")
    return _dec(db.scalar(stmt))


def _contract_value(db: Session, contract: Contract) -> Decimal:
    addenda = db.scalar(select(func.coalesce(func.sum(ContractAddendum.value_change), 0)).where(
        ContractAddendum.contract_id == contract.contract_id)) or 0
    changes = db.scalar(select(func.coalesce(func.sum(ContractChangeOrder.value_change), 0)).where(
        ContractChangeOrder.contract_id == contract.contract_id,
        ContractChangeOrder.status == "Approved")) or 0
    return _dec(contract.original_value) + _dec(addenda) + _dec(changes)


def _overview(db: Session, start: date, end: date):
    contracts = db.scalars(select(Contract).order_by(Contract.contract_no)).all()
    contract_total = sum((_contract_value(db, c) for c in contracts), D0)
    settlements = db.scalars(select(ContractSettlement).where(
        ContractSettlement.settlement_date >= start,
        ContractSettlement.settlement_date <= end,
        ContractSettlement.status != "Cancelled",
    ).order_by(ContractSettlement.settlement_date.desc(), ContractSettlement.settlement_id.desc())).all()

    total_net = sum((_dec(s.net_amount) for s in settlements), D0)
    paid_total = D0
    aging = {"0-30": D0, "31-60": D0, "61-90": D0, "90+": D0}
    aging_rows = []
    for s in settlements:
        paid = min(_dec(s.net_amount), _settlement_paid(db, s))
        paid_total += paid
        if s.status not in ("Approved", "Posted"):
            continue
        balance = max(D0, _dec(s.net_amount) - paid)
        if balance <= 0:
            continue
        age = max(0, (date.today() - s.settlement_date).days)
        bucket = "0-30" if age <= 30 else "31-60" if age <= 60 else "61-90" if age <= 90 else "90+"
        aging[bucket] += balance
        contract = db.get(Contract, s.contract_id)
        aging_rows.append({
            "settlement_id": s.settlement_id, "settlement_no": s.settlement_no,
            "contract_no": contract.contract_no if contract else "",
            "counterparty": s.counterparty_name, "side": s.settlement_side,
            "settlement_date": str(s.settlement_date), "age_days": age,
            "bucket": bucket, "status": s.status,
            "net_amount": _money(s.net_amount), "paid_amount": _money(paid),
            "outstanding_amount": _money(balance),
            "overdue": age > 30,
        })

    posted_ids = select(JournalEntry.journal_entry_id).where(
        JournalEntry.status == "Posted",
        JournalEntry.entry_date >= start, JournalEntry.entry_date <= end,
    )
    posted_count = db.scalar(select(func.count()).select_from(JournalEntry).where(
        JournalEntry.journal_entry_id.in_(posted_ids))) or 0
    posted_debit = db.scalar(select(func.coalesce(func.sum(JournalEntryDetail.debit_amount), 0))
        .join(JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
        .where(JournalEntry.status == "Posted", JournalEntry.entry_date >= start,
               JournalEntry.entry_date <= end)) or 0

    technical = db.scalars(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.estimate_date >= start,
        TechnicalSettlementEstimate.estimate_date <= end,
    ).order_by(TechnicalSettlementEstimate.estimate_date.desc(),
               TechnicalSettlementEstimate.estimate_id.desc()).limit(500)).all()
    technical_by_fin = {t.financial_settlement_id: t for t in technical if t.financial_settlement_id}
    lifecycle = []
    for t in technical:
        fin = db.get(ContractSettlement, t.financial_settlement_id) if t.financial_settlement_id else None
        contract = db.get(Contract, t.contract_id)
        paid = _settlement_paid(db, fin) if fin else D0
        lifecycle.append({
            "technical_no": t.estimate_no, "financial_no": fin.settlement_no if fin else "",
            "contract_no": contract.contract_no if contract else "",
            "counterparty": t.counterparty_name, "side": t.settlement_side,
            "created": str(t.created_at.date() if t.created_at else t.estimate_date),
            "technical_status": t.status, "financial_status": fin.status if fin else "لم يُنشأ مالياً",
            "journal_status": "مرحّل" if fin and fin.journal_entry_id else "غير مرحّل",
            "paid_amount": _money(paid), "net_amount": _money(fin.net_amount) if fin else "0.00",
        })
    # Financial settlements created without a technical estimate are also part of the workflow.
    for s in settlements:
        if s.settlement_id in technical_by_fin:
            continue
        contract = db.get(Contract, s.contract_id)
        lifecycle.append({
            "technical_no": "", "financial_no": s.settlement_no,
            "contract_no": contract.contract_no if contract else "",
            "counterparty": s.counterparty_name, "side": s.settlement_side,
            "created": str(s.created_at.date() if s.created_at else s.settlement_date),
            "technical_status": "غير مرتبط بمستخلص فني", "financial_status": s.status,
            "journal_status": "مرحّل" if s.journal_entry_id else "غير مرحّل",
            "paid_amount": _money(_settlement_paid(db, s)), "net_amount": _money(s.net_amount),
        })

    notifications = []
    pending_tech = db.scalars(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.status == "UnderReview").order_by(
        TechnicalSettlementEstimate.estimate_date)).all()
    for t in pending_tech:
        notifications.append({"type": "مستخلص فني منتظر", "reference": t.estimate_no,
            "party": t.counterparty_name, "date": str(t.estimate_date),
            "message": "ينتظر المراجعة والاعتماد الهندسي", "severity": "warning"})
    pending_fin = db.scalars(select(ContractSettlement).where(
        ContractSettlement.status.in_(("PendingApproval", "Approved"))).order_by(
        ContractSettlement.settlement_date)).all()
    for s in pending_fin:
        notifications.append({"type": "مستخلص مالي منتظر", "reference": s.settlement_no,
            "party": s.counterparty_name, "date": str(s.settlement_date),
            "message": "بانتظار الاعتماد المالي" if s.status == "PendingApproval" else "معتمد وينتظر الترحيل",
            "severity": "warning"})
    due_checks = db.scalars(select(FinancialCheck).where(
        FinancialCheck.due_date <= date.today() + timedelta(days=30),
        FinancialCheck.status.notin_(tuple(CLOSED_CHECKS))).order_by(
        FinancialCheck.due_date)).all()
    for c in due_checks:
        notifications.append({"type": "شيك مستحق", "reference": c.check_number,
            "party": str(c.party_account_id), "date": str(c.due_date),
            "message": f"{c.status} — {'وارد' if c.check_type == 'INCOMING' else 'صادر'} — {_money(c.amount)}",
            "severity": "danger" if c.due_date < date.today() else "warning"})
    notifications.sort(key=lambda n: (n["date"], n["type"]))

    accounts = db.scalars(select(Account).where(Account.is_active.is_(True)).order_by(Account.account_code)).all()
    return {
        "date_from": str(start), "date_to": str(end),
        "kpis": {
            "contracts_count": len(contracts), "contracts_value": _money(contract_total),
            "settlements_count": len(settlements), "settlements_net": _money(total_net),
            "paid_amount": _money(paid_total), "posted_entries_count": int(posted_count),
            "posted_entries_debit": _money(posted_debit),
            "outstanding_amount": _money(sum((_dec(r["outstanding_amount"]) for r in aging_rows), D0)),
            "overdue_amount": _money(sum((_dec(r["outstanding_amount"]) for r in aging_rows if r["overdue"]), D0)),
        },
        "aging": {"buckets": [{"label": k, "amount": _money(v)} for k, v in aging.items()],
                  "items": aging_rows[:500],
                  "basis": "عمر المستحق محسوب من تاريخ المستخلص؛ يعتبر متأخراً بعد 30 يوماً لعدم وجود تاريخ استحقاق مستقل."},
        "lifecycle": lifecycle[:500],
        "notifications": notifications[:500],
        "accounts": [{"account_id": a.account_id, "code": a.account_code,
                      "name": a.account_name_ar} for a in accounts],
    }


@router.get("/overview")
def overview(date_from: date | None = None, date_to: date | None = None,
             _: User = Depends(require_permission("AnalyticsReports", "View")),
             db: Session = Depends(get_db)):
    start, end = _dates(date_from, date_to)
    return _overview(db, start, end)


@router.get("/account-statement")
def account_statement(account_id: int, date_from: date | None = None, date_to: date | None = None,
                      _: User = Depends(require_permission("AnalyticsReports", "View")),
                      db: Session = Depends(get_db)):
    start, end = _dates(date_from, date_to)
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(404, "الحساب غير موجود")
    base = select(JournalEntryDetail, JournalEntry).join(
        JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id
    ).where(JournalEntryDetail.account_id == account_id, JournalEntry.status == "Posted")
    opening_rows = db.execute(base.where(JournalEntry.entry_date < start)).all()
    opening = sum((_dec(d.debit_amount) - _dec(d.credit_amount) for d, _ in opening_rows), D0)
    rows = db.execute(base.where(JournalEntry.entry_date >= start, JournalEntry.entry_date <= end)
        .order_by(JournalEntry.entry_date, JournalEntry.journal_entry_id, JournalEntryDetail.line_no)
        .limit(5000)).all()
    debit = sum((_dec(d.debit_amount) for d, _ in rows), D0)
    credit = sum((_dec(d.credit_amount) for d, _ in rows), D0)
    running = opening
    items = []
    for d, entry in rows:
        running += _dec(d.debit_amount) - _dec(d.credit_amount)
        items.append({
            "date": str(entry.entry_date), "entry_no": entry.entry_no,
            "description": d.description or entry.description or "",
            "debit": _money(d.debit_amount), "credit": _money(d.credit_amount),
            "balance": _money(running),
        })
    return {
        "account": {"id": account.account_id, "code": account.account_code, "name": account.account_name_ar},
        "date_from": str(start), "date_to": str(end), "opening_balance": _money(opening),
        "total_debit": _money(debit), "total_credit": _money(credit),
        "closing_balance": _money(opening + debit - credit), "items": items,
        "truncated": len(rows) >= 5000,
    }


def _report_rows(data):
    rows = []
    for x in data["aging"]["items"]:
        rows.append(["أعمار المستحقات", x["settlement_no"], x["contract_no"], x["counterparty"],
                     x["side"], x["settlement_date"], x["age_days"], x["net_amount"],
                     x["paid_amount"], x["outstanding_amount"], x["status"]])
    for x in data["lifecycle"]:
        rows.append(["دورة المستخلص", x["financial_no"] or x["technical_no"], x["contract_no"],
                     x["counterparty"], x["side"], x["created"], x["technical_status"],
                     x["financial_status"], x["journal_status"], x["paid_amount"], x["net_amount"]])
    for x in data["notifications"]:
        rows.append(["إشعار", x["type"], x["reference"], x["party"], x["date"], x["message"]])
    return rows


@router.get("/export.xlsx")
def export_xlsx(date_from: date | None = None, date_to: date | None = None,
                _: User = Depends(require_permission("AnalyticsReports", "View")),
                db: Session = Depends(get_db)):
    start, end = _dates(date_from, date_to)
    data = _overview(db, start, end)
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "ملخص الرقابة"
    ws.append(["المؤشر", "القيمة"])
    for key, label in [
        ("contracts_count", "عدد العقود"), ("contracts_value", "إجمالي قيمة العقود"),
        ("settlements_count", "عدد المستخلصات"), ("settlements_net", "صافي المستخلصات"),
        ("paid_amount", "المدفوع"), ("outstanding_amount", "المتبقي"),
        ("overdue_amount", "المتأخر"), ("posted_entries_count", "عدد القيود المرحلة"),
        ("posted_entries_debit", "إجمالي القيود المرحلة"),
    ]:
        ws.append([label, data["kpis"][key]])
    for name, headers, rows in [
        ("أعمار المستحقات", ["رقم المستخلص", "العقد", "الطرف", "النوع", "التاريخ", "العمر يوم", "الصافي", "المدفوع", "المتبقي", "الحالة"],
         [[x["settlement_no"],x["contract_no"],x["counterparty"],x["side"],x["settlement_date"],x["age_days"],x["net_amount"],x["paid_amount"],x["outstanding_amount"],x["status"]] for x in data["aging"]["items"]]),
        ("دورة المستخلص", ["فني", "مالي", "العقد", "الطرف", "النوع", "تاريخ الإنشاء", "الحالة الفنية", "الحالة المالية", "القيد", "المدفوع", "الصافي"],
         [[x["technical_no"],x["financial_no"],x["contract_no"],x["counterparty"],x["side"],x["created"],x["technical_status"],x["financial_status"],x["journal_status"],x["paid_amount"],x["net_amount"]] for x in data["lifecycle"]]),
        ("الإشعارات", ["النوع", "المرجع", "الطرف", "التاريخ", "التفاصيل"],
         [[x["type"],x["reference"],x["party"],x["date"],x["message"]] for x in data["notifications"]]),
    ]:
        sh = wb.create_sheet(name)
        sh.append(headers)
        for row in rows: sh.append(row)
    for sh in wb.worksheets:
        sh.freeze_panes = "A2"
        sh.auto_filter.ref = sh.dimensions
        for cell in sh[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="24557A")
            cell.alignment = Alignment(horizontal="center")
        for col in sh.columns:
            width = min(42, max(12, max(len(str(c.value or "")) for c in col) + 2))
            sh.column_dimensions[get_column_letter(col[0].column)].width = width
            for cell in col: cell.alignment = Alignment(horizontal="right", vertical="center")
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="financial-control-{start}-{end}.xlsx"'})


@router.get("/export.pdf")
def export_pdf(date_from: date | None = None, date_to: date | None = None,
               _: User = Depends(require_permission("AnalyticsReports", "View")),
               db: Session = Depends(get_db)):
    start, end = _dates(date_from, date_to)
    data = _overview(db, start, end)
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    import os
    font_path = next((p for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    ) if os.path.exists(p)), None)
    if not font_path:
        raise HTTPException(500, "خط PDF العربي غير متاح على الخادم")
    pdfmetrics.registerFont(TTFont("Arabic", font_path))
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        shape = lambda v: get_display(arabic_reshaper.reshape(str(v)))
    except Exception:
        shape = str
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=22, leftMargin=22, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ArabicTitle", parent=styles["Title"], fontName="Arabic", alignment=TA_RIGHT, fontSize=15)
    body = ParagraphStyle("ArabicBody", parent=styles["BodyText"], fontName="Arabic", alignment=TA_RIGHT, fontSize=7, leading=10)
    story = [Paragraph(shape("لوحة الرقابة المالية"), title),
             Paragraph(shape(f"الفترة: {start} إلى {end}"), body), Spacer(1, 10)]
    summary = [["المؤشر", "القيمة"]] + [[k, v] for k, v in [
        ("عدد العقود", data["kpis"]["contracts_count"]), ("قيمة العقود", data["kpis"]["contracts_value"]),
        ("عدد المستخلصات", data["kpis"]["settlements_count"]), ("صافي المستخلصات", data["kpis"]["settlements_net"]),
        ("المدفوع", data["kpis"]["paid_amount"]), ("المتبقي", data["kpis"]["outstanding_amount"]),
        ("المتأخر", data["kpis"]["overdue_amount"]), ("القيود المرحلة", data["kpis"]["posted_entries_count"]),
    ]]
    def add_table(title_text, headers, rows):
        story.append(Paragraph(shape(title_text), body))
        table_data = [[Paragraph(shape(str(c)), body) for c in row] for row in [headers] + rows]
        t = Table(table_data, repeatRows=1, hAlign="RIGHT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#24557A")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), .35, colors.grey),
            ("FONTNAME", (0,0), (-1,-1), "Arabic"),
            ("ALIGN", (0,0), (-1,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t); story.append(Spacer(1, 8))
    add_table("المؤشرات", ["المؤشر", "القيمة"], [[shape(str(a)), shape(str(b))] for a,b in summary[1:]])
    add_table("أعمار المستحقات", ["المستخلص","العقد","الطرف","العمر","الصافي","المدفوع","المتبقي"],
        [[x["settlement_no"],x["contract_no"],x["counterparty"],x["age_days"],x["net_amount"],x["paid_amount"],x["outstanding_amount"]] for x in data["aging"]["items"][:100]])
    add_table("دورة المستخلص", ["فني","مالي","العقد","الحالة الفنية","الحالة المالية","القيد"],
        [[x["technical_no"],x["financial_no"],x["contract_no"],x["technical_status"],x["financial_status"],x["journal_status"]] for x in data["lifecycle"][:100]])
    add_table("الإشعارات", ["النوع","المرجع","التاريخ","التفاصيل"],
        [[x["type"],x["reference"],x["date"],x["message"]] for x in data["notifications"][:100]])
    doc.build(story); buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="financial-control-{start}-{end}.pdf"'})
