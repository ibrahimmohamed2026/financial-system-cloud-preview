"""حساب ميزان المراجعة من القيود المرحّلة (بدون الاعتماد على الـView) — بيدعم فترة من/إلى."""
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, case, false, func, select, true
from sqlalchemy.orm import Session

from .models import Account, AccountClassification, JournalEntry, JournalEntryDetail

D0 = Decimal("0")


def compute_tb(db: Session, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    jed, je = JournalEntryDetail, JournalEntry
    pre = (je.entry_date < date_from) if date_from else false()
    per = true()
    if date_from:
        per = and_(per, je.entry_date >= date_from)
    if date_to:
        per = and_(per, je.entry_date <= date_to)
    s = lambda cond, col: func.coalesce(func.sum(case((cond, col), else_=0)), 0)  # noqa: E731
    sub = (select(jed.account_id.label("aid"), s(pre, jed.debit_amount).label("pd"),
                  s(pre, jed.credit_amount).label("pc"), s(per, jed.debit_amount).label("d"),
                  s(per, jed.credit_amount).label("c"))
           .join(je, je.journal_entry_id == jed.journal_entry_id).where(je.status == "Posted")
           .group_by(jed.account_id).subquery())
    rows = db.execute(
        select(Account, AccountClassification.name_ar, AccountClassification.statement_type,
               sub.c.pd, sub.c.pc, sub.c.d, sub.c.c)
        .join(AccountClassification, AccountClassification.classification_id == Account.classification_id)
        .outerjoin(sub, sub.c.aid == Account.account_id).order_by(Account.account_code)).all()

    own: dict[int, dict] = {}
    for a, cls, st, pd, pc, d, c in rows:
        own[a.account_id] = {
            "account_id": a.account_id, "code": a.account_code, "name": a.account_name_ar,
            "parent_id": a.parent_account_id, "classification_id": a.classification_id,
            "classification": cls, "statement_type": st, "normal_balance": a.normal_balance,
            "is_active": a.is_active,
            "od": Decimal(a.opening_debit or 0) + Decimal(pd or 0), "oc": Decimal(a.opening_credit or 0) + Decimal(pc or 0),
            "d": Decimal(d or 0), "c": Decimal(c or 0),
        }
    children: dict[int, list[int]] = {}
    for r in own.values():
        if r["parent_id"] in own:
            children.setdefault(r["parent_id"], []).append(r["account_id"])

    memo: dict[int, tuple] = {}

    def roll(aid: int, depth: int = 0) -> tuple:
        if aid in memo:
            return memo[aid]
        r = own[aid]
        tot = [r["od"], r["oc"], r["d"], r["c"]]
        if depth < 60:
            for ch in children.get(aid, []):
                for i, v in enumerate(roll(ch, depth + 1)):
                    tot[i] += v
        memo[aid] = tuple(tot)
        return memo[aid]

    def level(aid: int) -> int:
        n, cur = 0, own[aid]
        while cur["parent_id"] in own and n < 60:
            cur, n = own[cur["parent_id"]], n + 1
        return n

    out = []
    for aid, r in own.items():
        od, oc, d, c = roll(aid)
        td, tc = od + d, oc + c
        out.append({**r, "level": level(aid), "is_parent": aid in children,
                    "od": od, "oc": oc, "d": d, "c": c, "td": td, "tc": tc,
                    "bd": max(td - tc, D0), "bc": max(tc - td, D0),
                    "own": {"od": r["od"], "oc": r["oc"], "d": r["d"], "c": r["c"]}})
    out.sort(key=lambda x: x["code"])
    return out
