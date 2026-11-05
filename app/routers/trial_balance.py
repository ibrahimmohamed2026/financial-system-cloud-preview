from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..common import money
from ..database import get_db
from ..deps import require_permission
from ..models import User
from ..services_tb import compute_tb

SCREEN = "TrialBalance"
router = APIRouter(prefix="/trial-balance", tags=["TrialBalance"])


@router.get("")
def trial_balance(date_from: date | None = None, date_to: date | None = None, q: str | None = None,
                  classification_id: int | None = None, hide_zero: bool = False, leaves_only: bool = False,
                  _: User = Depends(require_permission(SCREEN, "View")), db: Session = Depends(get_db)):
    rows = compute_tb(db, date_from, date_to)
    tot = {k: Decimal("0") for k in ("od", "oc", "d", "c")}
    for r in rows:  # الإجماليات من أرقام كل حساب نفسه (من غير تجميع الآباء) عشان ما يتكررش العد
        for k in tot:
            tot[k] += r["own"][k]
    needle = (q or "").strip().lower()
    items = []
    for r in rows:
        if needle and needle not in r["code"].lower() and needle not in r["name"].lower():
            continue
        if classification_id is not None and r["classification_id"] != classification_id:
            continue
        if leaves_only and r["is_parent"]:
            continue
        if hide_zero and not any((r["od"], r["oc"], r["d"], r["c"])):
            continue
        items.append({"account_id": r["account_id"], "code": r["code"], "name": r["name"], "level": r["level"],
                      "is_parent": r["is_parent"], "classification": r["classification"],
                      **{k: money(r[k]) for k in ("od", "oc", "d", "c", "td", "tc", "bd", "bc")}})
    td, tc = tot["od"] + tot["d"], tot["oc"] + tot["c"]
    return {"items": items,
            "totals": {"od": money(tot["od"]), "oc": money(tot["oc"]), "d": money(tot["d"]), "c": money(tot["c"]),
                       "td": money(td), "tc": money(tc)},
            "balanced": td == tc}
