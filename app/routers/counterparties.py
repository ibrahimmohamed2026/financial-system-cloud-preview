from typing import Literal
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_permission, write_audit
from ..models import (Counterparty, CounterpartyAlias, Contract, ContractRequest, ContractSettlement,
                      TechnicalSettlementEstimate, TreasuryTransaction, PurchaseOrder, Account,
                      AccountClassification, ContractAccountingConfig, FinancialCheck, JournalEntry,
                      JournalEntryDetail, User)
from ..counterparties import normalize_name, resolve_counterparty

router = APIRouter(prefix="/api/counterparties", tags=["Counterparties"])
PartyType = Literal["Customer", "Contractor", "Supplier", "Mixed", "Other"]

class PartyIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    legal_name: str = Field(min_length=1, max_length=250)
    name_en: str | None = Field(default=None, max_length=250)
    party_type: PartyType = "Other"
    tax_no: str | None = Field(default=None, max_length=50)
    commercial_registration: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    linked_account_id: int | None = None
    is_active: bool = True

class AliasIn(BaseModel):
    alias_name: str = Field(min_length=1, max_length=200)

def _out(db: Session, x: Counterparty):
    aliases = db.scalars(select(CounterpartyAlias.alias_name).where(
        CounterpartyAlias.counterparty_id == x.party_id).order_by(CounterpartyAlias.alias_name)).all()
    counts = {}
    for model in (ContractRequest, Contract, ContractSettlement, TechnicalSettlementEstimate,
                  TreasuryTransaction, PurchaseOrder):
        party_col = getattr(model, "counterparty_id", getattr(model, "supplier_id", None))
        counts[model.__tablename__] = db.scalar(select(func.count()).select_from(model).where(
            party_col == x.party_id)) or 0
    linked_account = db.get(Account, x.linked_account_id) if x.linked_account_id else None
    return {"counterparty_id": x.party_id, "code": x.code, "legal_name": x.legal_name, "name_ar": x.legal_name, "name_en": x.name_en,
            "party_type": x.party_type, "tax_no": x.tax_no, "commercial_registration": x.commercial_registration,
            "phone": x.phone, "email": x.email, "address": x.address,
            "linked_account_id": x.linked_account_id, "is_active": x.is_active,
            "linked_account_code": linked_account.account_code if linked_account else None,
            "linked_account_name": linked_account.account_name_ar if linked_account else None,
            "linked_account_name_en": linked_account.account_name_en if linked_account else None,
            "aliases": aliases, "linked_records": counts}

def _validate_linked_account(db: Session, account_id: int | None, party_type: str) -> None:
    if account_id is None:
        return
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(422, "حساب الأستاذ غير موجود")
    if not account.is_active:
        raise HTTPException(422, "لا يمكن ربط الطرف بحساب غير نشط")
    if db.scalar(select(Account.account_id).where(Account.parent_account_id == account_id).limit(1)):
        raise HTTPException(422, "اختر حسابًا فرعيًا من الشجرة، ولا تربط الطرف بحساب رئيسي")
    if party_type in ("Customer", "Supplier", "Contractor"):
        classification = db.get(AccountClassification, account.classification_id)
        class_name = (classification.name_ar if classification else "").casefold()
        expected = ("عملاء",) if party_type == "Customer" else ("مورد", "دائن")
        if not any(word in class_name for word in expected):
            label = "العملاء" if party_type == "Customer" else "الموردين/الدائنين"
            raise HTTPException(422, f"اختر حسابًا من تصنيف {label} لربط هذا الطرف")

@router.get("")
def list_parties(q: str | None = None, party_type: PartyType | None = None,
                 _: User = Depends(require_permission("Counterparties", "View")), db: Session = Depends(get_db)):
    stmt = select(Counterparty)
    if q and q.strip():
        key = f"%{q.strip()}%"
        alias_ids = select(CounterpartyAlias.counterparty_id).where(CounterpartyAlias.alias_name.ilike(key))
        stmt = stmt.where(Counterparty.legal_name.ilike(key) | Counterparty.name_en.ilike(key) | Counterparty.code.ilike(key) |
                          Counterparty.party_id.in_(alias_ids))
    if party_type:
        stmt = stmt.where(Counterparty.party_type == party_type)
    rows = db.scalars(stmt.order_by(Counterparty.legal_name, Counterparty.party_id).limit(1000)).all()
    return {"items": [_out(db, x) for x in rows]}

@router.get("/chart-accounts")
def list_linkable_accounts(_: User = Depends(require_permission("Counterparties", "View")),
                           db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account).where(Account.is_active.is_(True)).order_by(Account.account_code)).all()
    parent_ids = set(db.scalars(select(Account.parent_account_id).where(Account.parent_account_id.is_not(None))))
    classes = {x.classification_id: (x.name_ar, x.name_en) for x in db.scalars(select(AccountClassification))}
    return [{"account_id": x.account_id, "account_code": x.account_code,
             "account_name_ar": x.account_name_ar, "account_name_en": x.account_name_en, "classification": classes.get(x.classification_id, ("", None))[0], "classification_en": classes.get(x.classification_id, ("", None))[1]}
            for x in accounts if x.account_id not in parent_ids]

def _customer_close_check(db: Session, x: Counterparty) -> dict:
    blockers = []
    balance = None
    account = db.get(Account, x.linked_account_id) if x.linked_account_id else None
    if not account:
        blockers.append("اربط العميل بحساب فرعي في شجرة الحسابات أولًا")
    else:
        if not account.is_active:
            blockers.append("حساب الأستاذ المرتبط موقوف؛ فعّله قبل فحص وإقفال الحساب")
        debit, credit = db.execute(
            select(func.coalesce(func.sum(JournalEntryDetail.debit_amount), 0),
                   func.coalesce(func.sum(JournalEntryDetail.credit_amount), 0))
            .join(JournalEntry, JournalEntry.journal_entry_id == JournalEntryDetail.journal_entry_id)
            .where(JournalEntryDetail.account_id == account.account_id, JournalEntry.status == "Posted")
        ).one()
        balance = (Decimal(account.opening_debit or 0) - Decimal(account.opening_credit or 0)
                   + Decimal(debit or 0) - Decimal(credit or 0))
        other_parties = db.scalar(select(func.count()).select_from(Counterparty).where(
            Counterparty.linked_account_id == account.account_id, Counterparty.party_id != x.party_id)) or 0
        if other_parties:
            blockers.append("حساب الأستاذ مربوط بأكثر من طرف؛ لا يمكن التحقق من رصيد العميل منفردًا")
        if abs(balance) >= Decimal("0.01"):
            blockers.append(f"رصيد حساب الأستاذ غير مصفّر: {balance:.2f}")
        pending_checks = db.scalars(select(FinancialCheck).where(
            FinancialCheck.party_account_id == account.account_id,
            FinancialCheck.status.notin_(("مُحصّل", "منصرف"))
        ).order_by(FinancialCheck.due_date, FinancialCheck.check_number)).all()
        if pending_checks:
            blockers.append(f"يوجد {len(pending_checks)} شيك غير مسوّى: " + "، ".join(c.check_number for c in pending_checks[:5]))

    contracts = db.scalars(select(Contract).where(Contract.counterparty_id == x.party_id)).all()
    contract_ids = [c.contract_id for c in contracts]
    requests = db.scalars(select(ContractRequest).where(
        ContractRequest.counterparty_id == x.party_id, ContractRequest.status != "Rejected")).all()
    open_requests = [r for r in requests if not db.scalar(select(Contract.contract_id).where(Contract.request_id == r.request_id))]
    if open_requests:
        blockers.append(f"يوجد {len(open_requests)} طلب تعاقد لم يتحول إلى عقد أو لم يُغلق: " + "، ".join(r.request_no for r in open_requests[:5]))
    customer_settlements = (db.scalars(select(ContractSettlement).where(
        ContractSettlement.contract_id.in_(contract_ids), ContractSettlement.settlement_side == "Customer")).all()
        if contract_ids else [])
    if contract_ids and account:
        configs = db.scalars(select(ContractAccountingConfig).where(
            ContractAccountingConfig.contract_id.in_(contract_ids),
            ContractAccountingConfig.settlement_side == "Customer")).all()
        config_by_contract = {c.contract_id: c for c in configs}
        settled_contract_ids = {s.contract_id for s in customer_settlements}
        mismatched = [c.contract_no for c in contracts if c.contract_id in settled_contract_ids and
                      (c.contract_id not in config_by_contract or config_by_contract[c.contract_id].control_account_id != account.account_id)]
        if mismatched:
            blockers.append("حساب العميل في إعدادات المستخلص لا يطابق حساب الأستاذ المرتبط به في العقود: " + "، ".join(mismatched[:5]))
    unposted = [s for s in customer_settlements if s.status != "Posted" or not s.journal_entry_id]
    if unposted:
        blockers.append(f"يوجد {len(unposted)} مستخلص عميل غير مرحّل أو بلا قيد محاسبي")
    if contract_ids:
        pending_estimates = db.scalars(select(TechnicalSettlementEstimate).where(
            TechnicalSettlementEstimate.contract_id.in_(contract_ids),
            TechnicalSettlementEstimate.settlement_side == "Customer",
            TechnicalSettlementEstimate.status.in_(("UnderReview", "TechnicallyApproved")),
            TechnicalSettlementEstimate.financial_settlement_id.is_(None))).all()
        if pending_estimates:
            blockers.append(f"يوجد {len(pending_estimates)} مستخلص فني للعميل لم يكتمل اعتماده المالي")
    aliases = db.scalars(select(CounterpartyAlias.alias_name).where(CounterpartyAlias.counterparty_id == x.party_id)).all()
    unposted_cash = db.scalars(select(TreasuryTransaction).where(
        or_(TreasuryTransaction.counterparty_id == x.party_id,
            TreasuryTransaction.recipient_name.in_([x.legal_name, *aliases])),
        TreasuryTransaction.journal_entry_id.is_(None))).all()
    if unposted_cash:
        blockers.append(f"يوجد {len(unposted_cash)} حركة خزينة مرتبطة بالعميل لم تُرحّل إلى قيد محاسبي")
    if x.party_type not in ("Customer", "Mixed"):
        blockers.append("إجراء الإقفال متاح للعملاء فقط")
    return {"counterparty_id": x.party_id, "party_name": x.legal_name, "is_active": x.is_active,
            "account": ({"account_id": account.account_id, "code": account.account_code,
                         "name": account.account_name_ar, "balance": f"{balance:.2f}"} if account else None),
            "settlement_count": len(customer_settlements), "blockers": blockers,
            "can_close": x.is_active and not blockers}

@router.get("/{party_id}/close-readiness")
def close_readiness(party_id: int, _: User = Depends(require_permission("Counterparties", "Edit")), db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x: raise HTTPException(404, "الطرف غير موجود")
    return _customer_close_check(db, x)

@router.post("/{party_id}/close")
def close_customer(party_id: int, user: User = Depends(require_permission("Counterparties", "Edit")), db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x: raise HTTPException(404, "الطرف غير موجود")
    result = _customer_close_check(db, x)
    if not result["can_close"]:
        raise HTTPException(409, "لا يمكن إقفال حساب العميل: " + "؛ ".join(result["blockers"]))
    account = db.get(Account, x.linked_account_id)
    account.is_active = False
    x.is_active = False
    write_audit(db, user.user_id, "CloseAccount", "Counterparties", party_id,
                old={"is_active": True, "account_is_active": True},
                new={"is_active": False, "account_is_active": False, "account_balance": result["account"]["balance"]})
    db.commit(); db.refresh(x)
    return _out(db, x)

@router.post("/{party_id}/reopen")
def reopen_customer(party_id: int, user: User = Depends(require_permission("Counterparties", "Edit")), db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x: raise HTTPException(404, "الطرف غير موجود")
    if x.party_type not in ("Customer", "Mixed"):
        raise HTTPException(409, "إعادة فتح حساب بهذا الإجراء متاحة للعملاء فقط")
    if x.is_active: return _out(db, x)
    account = db.get(Account, x.linked_account_id) if x.linked_account_id else None
    if account: account.is_active = True
    x.is_active = True
    write_audit(db, user.user_id, "ReopenAccount", "Counterparties", party_id,
                old={"is_active": False, "account_is_active": False},
                new={"is_active": True, "account_is_active": True if account else None})
    db.commit(); db.refresh(x)
    return _out(db, x)

@router.post("", status_code=201)
def create_party(body: PartyIn, user: User = Depends(require_permission("Counterparties", "Add")),
                 db: Session = Depends(get_db)):
    if body.party_type in ("Customer", "Mixed") and not body.is_active:
        raise HTTPException(409, "لا يمكن إنشاء عميل موقوف مباشرة؛ أنشئه نشطًا ثم استخدم إجراء إقفال الحساب بعد التسوية")
    key = normalize_name(body.legal_name)
    existing = db.scalar(select(Counterparty).where(func.lower(func.trim(Counterparty.legal_name)) == key))
    if existing:
        raise HTTPException(409, f"الطرف موجود بالفعل بالكود {existing.code}")
    _validate_linked_account(db, body.linked_account_id, body.party_type)
    values = body.model_dump()
    # Use a unique temporary code so concurrent additions cannot collide on the
    # unique Code index before the permanent CP-<id> code is assigned.
    x = Counterparty(code=f"TMP-{uuid4().hex}", name=body.legal_name, roles=[body.party_type], **values)
    db.add(x); db.flush(); x.code = f"CP-{x.party_id:06d}"
    write_audit(db, user.user_id, "Create", "Counterparties", x.party_id, new=body.model_dump())
    db.commit(); db.refresh(x)
    return _out(db, x)

@router.put("/{party_id}")
def update_party(party_id: int, body: PartyIn, user: User = Depends(require_permission("Counterparties", "Edit")),
                 db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x: raise HTTPException(404, "الطرف غير موجود")
    client_record = x.party_type in ("Customer", "Mixed") or body.party_type in ("Customer", "Mixed")
    if client_record and x.is_active != body.is_active:
        raise HTTPException(409, "استخدم إجراء إقفال الحساب أو إعادة تنشيطه حتى يتحدّث حساب الأستاذ المرتبط بأمان")
    if not x.is_active and x.party_type in ("Customer", "Mixed") and body.linked_account_id != x.linked_account_id:
        raise HTTPException(409, "أعد تنشيط العميل قبل تغيير حساب الأستاذ المرتبط")
    duplicate = db.scalar(select(Counterparty.party_id).where(
        Counterparty.party_id != party_id, func.lower(func.trim(Counterparty.legal_name)) == normalize_name(body.legal_name)))
    if duplicate: raise HTTPException(409, "الاسم مستخدم لطرف آخر")
    client_record = x.party_type in ("Customer", "Mixed") or body.party_type in ("Customer", "Mixed")
    if client_record and x.is_active != body.is_active:
        raise HTTPException(409, "استخدم إجراء إقفال الحساب أو إعادة تنشيطه حتى يتحدّث حساب الأستاذ المرتبط بأمان")
    if not x.is_active and x.party_type in ("Customer", "Mixed") and body.linked_account_id != x.linked_account_id:
        raise HTTPException(409, "أعد تنشيط العميل قبل تغيير حساب الأستاذ المرتبط")
    if not (not x.is_active and x.party_type in ("Customer", "Mixed") and body.linked_account_id == x.linked_account_id):
        _validate_linked_account(db, body.linked_account_id, body.party_type)
    old = {k: getattr(x, k) for k in body.model_fields}
    for k, v in body.model_dump().items(): setattr(x, k, v)
    x.name = body.legal_name
    x.roles = list(dict.fromkeys([*(x.roles or []), body.party_type]))
    # Keep historical display fields readable while the stable FK remains the source of truth.
    _replace_legacy_names(db, party_id, old["legal_name"], x.legal_name)
    write_audit(db, user.user_id, "Update", "Counterparties", party_id, old, body.model_dump())
    db.commit(); db.refresh(x)
    return _out(db, x)

def _replace_legacy_names(db: Session, party_id: int, old_name: str, new_name: str):
    for model, field in ((ContractRequest, "counterparty_name"), (Contract, "client_name"),
                         (ContractSettlement, "counterparty_name"), (TechnicalSettlementEstimate, "counterparty_name"),
                         (TreasuryTransaction, "recipient_name"), (PurchaseOrder, "supplier_name")):
        col = getattr(model, field)
        db.query(model).filter(model.counterparty_id == party_id).update({col: new_name}, synchronize_session=False)
        # Migrate old rows before their counterparty FK has been backfilled.
        db.query(model).filter(model.counterparty_id.is_(None), func.lower(func.trim(col)) == normalize_name(old_name)).update(
            {model.counterparty_id: party_id, col: new_name}, synchronize_session=False)

@router.post("/{party_id}/aliases", status_code=201)
def add_alias(party_id: int, body: AliasIn, user: User = Depends(require_permission("Counterparties", "Edit")),
              db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x: raise HTTPException(404, "الطرف غير موجود")
    alias_name = body.alias_name.strip()
    if normalize_name(alias_name) == normalize_name(x.legal_name): raise HTTPException(422, "الاسم البديل يطابق الاسم المعتمد")
    row = db.scalar(select(CounterpartyAlias).where(func.lower(func.trim(CounterpartyAlias.alias_name)) == normalize_name(alias_name)))
    if row and row.counterparty_id not in (None, party_id): raise HTTPException(409, "الاسم البديل مرتبط بطرف آخر")
    if row is None:
        row = CounterpartyAlias(alias_name=alias_name, canonical_name=x.legal_name, counterparty_id=party_id); db.add(row)
    else:
        row.counterparty_id, row.canonical_name = party_id, x.legal_name
    # Adopt records stored with this historical spelling.
    for model, field in ((ContractRequest, "counterparty_name"), (Contract, "client_name"),
                         (ContractSettlement, "counterparty_name"), (TechnicalSettlementEstimate, "counterparty_name"),
                         (TreasuryTransaction, "recipient_name"), (PurchaseOrder, "supplier_name")):
        col = getattr(model, field)
        db.query(model).filter(model.counterparty_id.is_(None), func.lower(func.trim(col)) == normalize_name(alias_name)).update(
            {model.counterparty_id: party_id}, synchronize_session=False)
    db.flush(); write_audit(db, user.user_id, "AddAlias", "Counterparties", party_id,
                            new={"alias_name": alias_name, "counterparty_id": party_id})
    db.commit()
    return _out(db, x)

@router.post("/{source_id}/merge/{target_id}")
def merge_parties(source_id: int, target_id: int,
                  user: User = Depends(require_permission("Counterparties", "Delete")), db: Session = Depends(get_db)):
    if source_id == target_id: raise HTTPException(422, "لا يمكن دمج الطرف مع نفسه")
    source, target = db.get(Counterparty, source_id), db.get(Counterparty, target_id)
    if not source or not target: raise HTTPException(404, "أحد الطرفين غير موجود")
    if source.linked_account_id and target.linked_account_id and source.linked_account_id != target.linked_account_id:
        raise HTTPException(409, "للطرفين حسابا أستاذ مختلفان؛ وحّد الحساب المرتبط قبل الدمج")
    if target.linked_account_id is None:target.linked_account_id=source.linked_account_id
    if target.party_type=="Other":target.party_type=source.party_type
    old_name, target_name = source.legal_name, target.legal_name
    _replace_legacy_names(db, target_id, old_name, target_name)
    for model in (ContractRequest, Contract, ContractSettlement, TechnicalSettlementEstimate, TreasuryTransaction, PurchaseOrder):
        db.query(model).filter(model.counterparty_id == source_id).update({model.counterparty_id: target_id}, synchronize_session=False)
    aliases = db.scalars(select(CounterpartyAlias).where(CounterpartyAlias.counterparty_id == source_id)).all()
    names = {normalize_name(a.alias_name) for a in db.scalars(select(CounterpartyAlias).where(CounterpartyAlias.counterparty_id == target_id))}
    for a in aliases:
        if normalize_name(a.alias_name) not in names:
            a.counterparty_id, a.canonical_name = target_id, target_name
            names.add(normalize_name(a.alias_name))
        else:
            db.delete(a)
    if normalize_name(old_name) != normalize_name(target_name) and normalize_name(old_name) not in names:
        db.add(CounterpartyAlias(alias_name=old_name, canonical_name=target_name, counterparty_id=target_id))
    write_audit(db, user.user_id, "Merge", "Counterparties", target_id,
                {"source_id": source_id, "source_name": old_name}, {"target_id": target_id, "target_name": target_name})
    db.delete(source); db.commit()
    return _out(db, target)

def _party_delete_readiness(db: Session, x: Counterparty) -> dict:
    linked = _out(db, x)["linked_records"]
    blockers = [f"يوجد {count} سجل مرتبط في {table}" for table, count in linked.items() if count]
    # Check both the current linked account and the legacy AccountId field.
    # Do not allow deleting a party while either account is referenced by accounting activity.
    account_ids = {i for i in (x.linked_account_id, x.account_id) if i is not None}
    for account_id in sorted(account_ids):
        account = db.get(Account, account_id)
        if not account:
            continue
        journal_count = db.scalar(select(func.count()).select_from(JournalEntryDetail).where(
            JournalEntryDetail.account_id == account.account_id)) or 0
        check_count = db.scalar(select(func.count()).select_from(FinancialCheck).where(
            FinancialCheck.party_account_id == account.account_id)) or 0
        if journal_count:
            blockers.append(f"حساب الأستاذ {account.account_code} يحتوي على {journal_count} حركة/سطر محاسبي؛ لا يمكن حذف الطرف")
        if check_count:
            blockers.append(f"يوجد {check_count} شيك مرتبط بحساب الأستاذ {account.account_code}")
    return {"counterparty_id": x.party_id, "party_name": x.legal_name,
            "linked_records": linked, "blockers": blockers, "can_delete": not blockers}


@router.get("/{party_id}/delete-readiness")
def delete_readiness(party_id: int, _: User = Depends(require_permission("Counterparties", "Delete")),
                     db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x:
        raise HTTPException(404, "الطرف غير موجود")
    return _party_delete_readiness(db, x)


@router.delete("/{party_id}")
def delete_party(party_id: int, user: User = Depends(require_permission("Counterparties", "Delete")),
                 db: Session = Depends(get_db)):
    x = db.get(Counterparty, party_id)
    if not x:
        raise HTTPException(404, "الطرف غير موجود")
    readiness = _party_delete_readiness(db, x)
    if not readiness["can_delete"]:
        raise HTTPException(409, "لا يمكن حذف الطرف: " + "؛ ".join(readiness["blockers"]))
    old = {"code": x.code, "legal_name": x.legal_name, "party_type": x.party_type,
           "linked_account_id": x.linked_account_id, "is_active": x.is_active}
    aliases = db.scalars(select(CounterpartyAlias).where(
        CounterpartyAlias.counterparty_id == party_id)).all()
    for alias in aliases:
        db.delete(alias)
    write_audit(db, user.user_id, "Delete", "Counterparties", party_id, old=old,
                new={"deleted": True, "linked_records": readiness["linked_records"]})
    db.delete(x)
    db.commit()
    return {"deleted": True, "counterparty_id": party_id, "legal_name": old["legal_name"]}
