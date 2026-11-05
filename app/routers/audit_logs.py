from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_permission
from ..models import (AuditLog, Contract, ContractAccountingConfig, ContractAddendum, ContractChangeOrder,
                      ContractDeductionRule, ContractItem, ContractSettlement, JournalEntry, ProgressBilling,
                      TechnicalSettlementEstimate, User)

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])

# كيانات تتبع عقدًا مباشرة: اسم الكيان -> (الموديل، حقل المفتاح)
CONTRACT_CHILDREN = {
    "ContractItems": (ContractItem, "item_id"), "ContractDeductionRules": (ContractDeductionRule, "rule_id"),
    "ContractAccountingConfig": (ContractAccountingConfig, "config_id"), "ContractChangeOrders": (ContractChangeOrder, "change_order_id"),
    "ContractAddendums": (ContractAddendum, "addendum_id"), "ProgressBillings": (ProgressBilling, "billing_id"),
}


def _int(v):
    try: return int(v)
    except (TypeError, ValueError): return None


def _settlement_chain(db, settlement_ids=None, journal_entry_ids=None):
    """المستخلص + المستخلص الفني المولِّد له + قيد الترحيل → مجموعات (كيان -> أرقام)."""
    out = {"ContractSettlements": set(), "TechnicalSettlementEstimates": set(), "JournalEntries": set()}
    q = select(ContractSettlement)
    conds = []
    if settlement_ids: conds.append(ContractSettlement.settlement_id.in_(settlement_ids))
    if journal_entry_ids: conds.append(ContractSettlement.journal_entry_id.in_(journal_entry_ids))
    if not conds: return out
    for s in db.scalars(q.where(or_(*conds))).all():
        out["ContractSettlements"].add(str(s.settlement_id))
        if s.journal_entry_id: out["JournalEntries"].add(str(s.journal_entry_id))
        for e in db.scalars(select(TechnicalSettlementEstimate.estimate_id).where(TechnicalSettlementEstimate.financial_settlement_id == s.settlement_id)).all():
            out["TechnicalSettlementEstimates"].add(str(e))
    for j in journal_entry_ids or []: out["JournalEntries"].add(str(j))
    return out


def related_entities(db: Session, contract_id=None, settlement_id=None, journal_entry_id=None) -> dict[str, set]:
    """كل (كيان، رقم) له علاقة بالعقد أو المستخلص أو القيد المطلوب — لفلترة سجل النشاط علاقيًا."""
    rel: dict[str, set] = {}
    def add(entity, ids):
        rel.setdefault(entity, set()).update(str(i) for i in ids)
    if contract_id:
        add("Contracts", [contract_id])
        for name, (model, pk) in CONTRACT_CHILDREN.items():
            add(name, db.scalars(select(getattr(model, pk)).where(model.contract_id == contract_id)).all())
        sids = db.scalars(select(ContractSettlement.settlement_id).where(ContractSettlement.contract_id == contract_id)).all()
        for e in db.scalars(select(TechnicalSettlementEstimate.estimate_id).where(TechnicalSettlementEstimate.contract_id == contract_id)).all():
            add("TechnicalSettlementEstimates", [e])
        for k, v in _settlement_chain(db, settlement_ids=list(sids)).items(): add(k, v)
    if settlement_id or journal_entry_id:
        for k, v in _settlement_chain(db, [settlement_id] if settlement_id else None, [journal_entry_id] if journal_entry_id else None).items(): add(k, v)
    return rel


def resolve_links(db: Session, logs: list[AuditLog]) -> list[dict]:
    """لكل سجل: العقد / المستخلص / القيد المرتبط به (بدون الحاجة لأعمدة جديدة في الجدول)."""
    cache: dict = {}
    def get(model, key):
        k = (model.__name__, key)
        if k not in cache: cache[k] = db.get(model, key) if key is not None else None
        return cache[k]
    def by_journal(jid):
        k = ("byjournal", jid)
        if k not in cache: cache[k] = db.scalar(select(ContractSettlement).where(ContractSettlement.journal_entry_id == jid))
        return cache[k]
    def by_estimate_fin(sid):
        k = ("byest", sid)
        if k not in cache: cache[k] = db.scalar(select(TechnicalSettlementEstimate).where(TechnicalSettlementEstimate.financial_settlement_id == sid))
        return cache[k]
    out = []
    for log in logs:
        ent, eid = log.entity_name, _int(log.entity_id)
        cid = sid = jid = est = None
        if ent == "Contracts": cid = eid
        elif ent in CONTRACT_CHILDREN:
            model, _ = CONTRACT_CHILDREN[ent]; row = get(model, eid); cid = row.contract_id if row else None
        elif ent == "ContractSettlements": sid = eid
        elif ent == "TechnicalSettlementEstimates":
            row = get(TechnicalSettlementEstimate, eid)
            if row: cid, sid, est = row.contract_id, row.financial_settlement_id, row.estimate_no
        elif ent == "JournalEntries": jid = eid
        if sid is None and jid is not None:
            s = by_journal(jid); sid = s.settlement_id if s else None
        s = get(ContractSettlement, sid) if sid else None
        if s:
            cid = cid or s.contract_id; jid = jid or s.journal_entry_id
            if est is None:
                e = by_estimate_fin(s.settlement_id); est = e.estimate_no if e else None
        c = get(Contract, cid) if cid else None
        j = get(JournalEntry, jid) if jid else None
        out.append({
            "contract": {"id": cid, "no": c.contract_no, "title": c.title} if c else None,
            "settlement": {"id": s.settlement_id, "no": s.settlement_no, "side": s.settlement_side, "status": s.status} if s else None,
            "technical_estimate_no": est,
            "journal_entry": {"id": j.journal_entry_id, "no": j.entry_no, "status": j.status} if j else None,
        })
    return out


@router.get("")
def list_audit_logs(
    date_from: date | None = None, date_to: date | None = None,
    user_id: int | None = Query(None, ge=1), action: str | None = None,
    contract_id: int | None = Query(None, ge=1), settlement_id: int | None = Query(None, ge=1),
    journal_entry_id: int | None = Query(None, ge=1), entity: str | None = None, entity_id: str | None = None,
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_permission("AuditLogs", "View")),
    db: Session = Depends(get_db),
):
    conds = []
    if date_from: conds.append(AuditLog.timestamp >= datetime.combine(date_from, time.min))
    if date_to: conds.append(AuditLog.timestamp < datetime.combine(date_to + timedelta(days=1), time.min))
    if user_id: conds.append(AuditLog.user_id == user_id)
    if action: conds.append(AuditLog.action_type.ilike(f"%{action.strip()}%"))
    if entity: conds.append(AuditLog.entity_name == entity.strip())
    if entity_id: conds.append(AuditLog.entity_id == entity_id.strip())
    if contract_id or settlement_id or journal_entry_id:
        rel = related_entities(db, contract_id, settlement_id, journal_entry_id)
        conds.append(or_(*[and_(AuditLog.entity_name == e, AuditLog.entity_id.in_(sorted(ids))) for e, ids in rel.items() if ids]) if any(rel.values()) else AuditLog.audit_id == -1)
    total = db.scalar(select(func.count()).select_from(AuditLog).where(*conds)) or 0
    stmt = select(AuditLog, User.full_name, User.username).outerjoin(User, User.user_id == AuditLog.user_id).where(*conds)
    rows = db.execute(stmt.order_by(AuditLog.timestamp.desc(), AuditLog.audit_id.desc()).offset(skip).limit(limit)).all()
    links = resolve_links(db, [r[0] for r in rows])
    return {"total": total, "items": [{
        "id": log.audit_id, "user_id": log.user_id, "user_name": name or username or "مستخدم غير معروف",
        "action": log.action_type, "entity": log.entity_name, "entity_id": log.entity_id,
        "description": log.new_value or log.old_value or "", "ip_address": log.ip_address,
        "created_at": log.timestamp, **lk,
    } for (log, name, username), lk in zip(rows, links)]}


def _safe_audit_value(value):
    """Decode stored snapshots while masking credentials and secrets."""
    import json
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return value
    sensitive = ("password", "passwd", "token", "secret", "authorization",
                 "api_key", "apikey", "connection_string", "connectionstring")
    def clean(item):
        if isinstance(item, dict):
            return {key: ("[محجوب]" if any(part in str(key).lower() for part in sensitive) else clean(val))
                    for key, val in item.items()}
        if isinstance(item, list):
            return [clean(v) for v in item]
        return item
    return clean(parsed)


@router.get("/detail/{audit_id}")
def audit_log_detail(
    audit_id: int,
    _: User = Depends(require_permission("AuditLogs", "View")),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    log = db.get(AuditLog, audit_id)
    if log is None:
        raise HTTPException(status_code=404, detail="سجل النشاط غير موجود")
    return {
        "id": log.audit_id,
        "old_value": _safe_audit_value(log.old_value),
        "new_value": _safe_audit_value(log.new_value),
        "description": log.new_value or log.old_value or "",
    }

@router.get("/users")
def audit_users(_: User = Depends(require_permission("AuditLogs", "View")), db: Session = Depends(get_db)):
    rows = db.execute(select(User.user_id, User.full_name, User.username).order_by(User.full_name)).all()
    return [{"user_id": uid, "name": name or username} for uid, name, username in rows]

@router.get("/contracts")
def audit_contracts(_: User = Depends(require_permission("AuditLogs", "View")), db: Session = Depends(get_db)):
    rows = db.execute(select(Contract.contract_id, Contract.contract_no, Contract.title).order_by(Contract.contract_no)).all()
    return [{"contract_id": i, "label": f"{no} — {t}"} for i, no, t in rows]
