"""Audited administrator-only cascade deletion for contract settlement records."""
from sqlalchemy import select, func
from fastapi import HTTPException

from .deps import write_audit
from .models import (Role, UserRole, Check, FinancialCheck, TreasuryTransaction, JournalEntry, JournalEntryDetail,
    ContractSettlement, ContractSettlementItem, ContractAttachment,
    TechnicalSettlementEstimate, TechnicalSettlementEstimateItem)


def require_admin(db, user_id: int) -> None:
    is_admin = db.scalar(select(Role.role_id).join(UserRole, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user_id, func.lower(Role.role_name).like("%admin%")).limit(1))
    if not is_admin:
        raise HTTPException(403, "الحذف العام متاح لمسؤول النظام فقط")


def delete_settlement_tree(db, settlement: ContractSettlement, user_id: int) -> None:
    sid = settlement.settlement_id
    # ContractSettlements owns a restrictive FK to JournalEntries. Clear and
    # flush that reference before removing the posted entry in PostgreSQL.
    settlement_entry_id = settlement.journal_entry_id
    original_settlement_entry_id = settlement_entry_id
    if settlement_entry_id:
        settlement.journal_entry_id = None
        db.flush()
    linked_tech = db.scalars(select(TechnicalSettlementEstimate).where(
        TechnicalSettlementEstimate.financial_settlement_id == sid)).all()
    # Keep issued check records and their status history, but detach them from
    # a settlement that an administrator explicitly removes.
    for check in db.scalars(select(Check).where(Check.settlement_id == sid)).all():
        write_audit(db, user_id, "DetachFromDeletedSettlement", "Checks", check.check_id,
                    {"settlement_id": sid, "check_no": check.check_no, "status": check.status},
                    {"settlement_id": None, "check_no": check.check_no, "status": check.status})
        check.settlement_id = None
    transactions = db.scalars(select(TreasuryTransaction).where(TreasuryTransaction.settlement_id == sid)).all()
    entry_ids = {x.journal_entry_id for x in transactions if x.journal_entry_id}
    if settlement_entry_id:
        entry_ids.add(settlement_entry_id)
    # Include linked manual entries too; this link was added for duplicate-post
    # prevention and must be cleaned before deleting its settlement FK target.
    entry_ids.update(db.scalars(select(JournalEntry.journal_entry_id).where(
        JournalEntry.source_settlement_id == sid)).all())
    if entry_ids:
        for tx in db.scalars(select(TreasuryTransaction).where(TreasuryTransaction.journal_entry_id.in_(entry_ids))).all():
            if tx not in transactions:
                transactions.append(tx)
    for tx in transactions:
        write_audit(db, user_id, "DeleteCascade", "TreasuryTransactions", tx.transaction_id,
                    {"voucher_no": tx.voucher_no, "settlement_id": tx.settlement_id,
                     "inflow": str(tx.inflow), "outflow": str(tx.outflow)}, None)
        if tx.journal_entry_id:
            entry_ids.add(tx.journal_entry_id)
        db.delete(tx)
    if entry_ids:
        for check in db.scalars(select(FinancialCheck).where(FinancialCheck.journal_entry_id.in_(entry_ids))).all():
            write_audit(db, user_id, "DetachFromDeletedJournal", "FinancialChecks", check.check_id,
                        {"journal_entry_id": check.journal_entry_id, "check_number": check.check_number},
                        {"journal_entry_id": None, "check_number": check.check_number})
            check.journal_entry_id = None
    for entry_id in entry_ids:
        for line in db.scalars(select(JournalEntryDetail).where(JournalEntryDetail.journal_entry_id == entry_id)).all():
            db.delete(line)
        entry = db.get(JournalEntry, entry_id)
        if entry:
            write_audit(db, user_id, "DeleteCascade", "JournalEntries", entry_id,
                        {"entry_no": entry.entry_no, "status": entry.status}, None)
            db.delete(entry)
    for tech in linked_tech:
        for line in db.scalars(select(TechnicalSettlementEstimateItem).where(
                TechnicalSettlementEstimateItem.estimate_id == tech.estimate_id)).all():
            db.delete(line)
        write_audit(db, user_id, "DeleteCascade", "TechnicalSettlementEstimates", tech.estimate_id,
                    {"estimate_no": tech.estimate_no, "status": tech.status}, None)
        db.delete(tech)
    # PostgreSQL enforces TechnicalSettlementEstimates.FinancialSettlementId.
    # Flush estimate deletions before deleting the referenced ContractSettlement;
    # otherwise the unit-of-work may issue the settlement DELETE first because
    # these tables have no ORM relationship to establish dependency ordering.
    db.flush()
    for attachment in db.scalars(select(ContractAttachment).where(ContractAttachment.settlement_id == sid)).all():
        db.delete(attachment)
    for line in db.scalars(select(ContractSettlementItem).where(ContractSettlementItem.settlement_id == sid)).all():
        db.delete(line)
    write_audit(db, user_id, "DeleteCascade", "ContractSettlements", sid,
                {"settlement_no": settlement.settlement_no, "status": settlement.status,
                 "journal_entry_id": original_settlement_entry_id}, None)
    db.delete(settlement)
