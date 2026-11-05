from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..common import money
from ..database import get_db
from ..deps import get_current_user
from ..models import (JournalEntry, JournalEntryDetail, Screen, Section, TreasuryAccount, TreasuryTransaction, User,
                      effective_permissions)
from ..schemas import DashboardOut, ScreenCard, SectionCard

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

TREASURY_SCREENS = {"CashAnalysis", "BankCibEgp", "CashUsd", "CashEgp", "BankCairoEgp", "BankHdbUsd", "BankHdbEgp", "BankCibUsd"}
MAIN_CURRENCY = "EGP"
D0 = Decimal("0")


def _allowed_screens(db: Session, user: User) -> set[str]:
    e = effective_permissions.c
    return set(db.scalars(
        select(e.ScreenCode).where(e.UserId == user.user_id, e.ActionCode == "View", e.IsAllowed == 1).distinct()))


def _months_back(today: date, n: int) -> list[tuple[int, int]]:
    """آخر n شهر (سنة، شهر) من الأقدم للأحدث، آخرهم الشهر الحالي."""
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out[::-1]


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """أرقام الشاشة الرئيسية (كروت + رسم الخزينة + آخر القيود). كل جزء بيظهر بس لو المستخدم عنده صلاحية View على شاشته
    (الجزء اللي ملوش صلاحية بيرجع null)."""
    allowed = _allowed_screens(db, user)
    out: dict = {"currency": MAIN_CURRENCY,
                 "kpis": {"total_debit": None, "total_credit": None, "treasury_balance": None, "draft_entries": None},
                 "other_balances": [], "cash_series": None, "latest_entries": None}

    if "JournalBook" in allowed:
        jed, je = JournalEntryDetail, JournalEntry
        td, tc = db.execute(
            select(func.coalesce(func.sum(jed.debit_amount), 0), func.coalesce(func.sum(jed.credit_amount), 0))
            .join(je, je.journal_entry_id == jed.journal_entry_id).where(je.status == "Posted")).one()
        out["kpis"]["total_debit"], out["kpis"]["total_credit"] = money(td), money(tc)
        out["kpis"]["draft_entries"] = db.scalar(
            select(func.count()).select_from(je).where(je.status == "Draft")) or 0
        rows = db.scalars(select(je).order_by(je.entry_date.desc(), je.journal_entry_id.desc()).limit(20)).all()
        out["latest_entries"] = [{"journal_entry_id": r.journal_entry_id, "entry_no": r.entry_no,
                                  "entry_date": r.entry_date, "description": r.description, "status": r.status}
                                 for r in rows]

    if allowed & TREASURY_SCREENS:
        ta, tt = TreasuryAccount, TreasuryTransaction
        net = func.coalesce(func.sum(tt.inflow - tt.outflow), 0)
        for cur, bal in db.execute(
                select(ta.currency_code, net).select_from(tt).join(ta, ta.treasury_account_id == tt.treasury_account_id)
                .where(ta.is_active == True).group_by(ta.currency_code)).all():  # noqa: E712
            if cur == MAIN_CURRENCY:
                out["kpis"]["treasury_balance"] = money(bal)
            else:
                out["other_balances"].append({"currency": cur, "balance": money(bal)})
        if out["kpis"]["treasury_balance"] is None:
            out["kpis"]["treasury_balance"] = money(D0)

        months = _months_back(date.today(), 12)
        first = date(months[0][0], months[0][1], 1)
        base = Decimal(db.scalar(
            select(net).select_from(tt).join(ta, ta.treasury_account_id == tt.treasury_account_id)
            .where(ta.currency_code == MAIN_CURRENCY, ta.is_active == True,  # noqa: E712
                   tt.transaction_date < first)) or 0)
        per_day = db.execute(
            select(tt.transaction_date, net).select_from(tt).join(ta, ta.treasury_account_id == tt.treasury_account_id)
            .where(ta.currency_code == MAIN_CURRENCY, ta.is_active == True,  # noqa: E712
                   tt.transaction_date >= first).group_by(tt.transaction_date)).all()
        by_month: dict[tuple[int, int], Decimal] = {}
        for d, v in per_day:
            by_month[(d.year, d.month)] = by_month.get((d.year, d.month), D0) + Decimal(v or 0)
        series, running = [], base
        for y, m in months:
            running += by_month.get((y, m), D0)
            series.append({"year": y, "month": m, "balance": money(running)})
        out["cash_series"] = series
    return out


def _letter(section: Section) -> str:
    for text in (section.name_en, section.name_ar or ""):
        for ch in text:
            if ch.isalpha():
                return ch.upper()
    return "#"


@router.get("", response_model=DashboardOut)
def dashboard(q: str | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """كروت الأقسام والشاشات اللي المستخدم عنده عليها صلاحية View — بنفس شكل الداشبورد.
    q: بحث (إنجليزي/عربي) في اسم الشاشة أو القسم أو كود الشاشة."""
    e = effective_permissions.c
    allowed = set(db.scalars(
        select(e.ScreenCode).where(e.UserId == user.user_id, e.ActionCode == "View", e.IsAllowed == 1).distinct()
    ))

    rows = db.execute(
        select(Section, Screen)
        .join(Screen, Screen.section_id == Section.section_id)
        .where(Section.is_active == True, Screen.is_active == True)
        .order_by(Section.sort_order, Section.section_id, Screen.sort_order, Screen.screen_id)
    ).all()

    sections: dict[int, tuple[Section, list[Screen]]] = {}
    for section, screen in rows:
        if screen.screen_code in allowed:
            sections.setdefault(section.section_id, (section, []))[1].append(screen)

    total_sections = len(sections)
    total_screens = sum(len(s) for _, s in sections.values())

    needle = (q or "").strip().lower()
    cards: list[SectionCard] = []
    for section, screens in sections.values():
        shown = screens
        if needle:
            section_hit = needle in section.name_en.lower() or needle in (section.name_ar or "").lower()
            if not section_hit:
                shown = [s for s in screens if needle in s.title_en.lower()
                         or needle in (s.title_ar or "").lower() or needle in s.screen_code.lower()]
            if not shown:
                continue
        cards.append(SectionCard(
            section_id=section.section_id, code=section.code, name_en=section.name_en,
            name_ar=section.name_ar, letter=_letter(section), screens_count=len(shown),
            screens=[ScreenCard(screen_id=s.screen_id, code=s.screen_code, title_en=s.title_en,
                                title_ar=s.title_ar, route=s.route) for s in shown],
        ))
    return DashboardOut(sections_count=total_sections, screens_count=total_screens, sections=cards)
