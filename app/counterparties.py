"""Shared identity helpers for customers, suppliers and subcontractors."""
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Counterparty, CounterpartyAlias


def normalize_name(value: str | None) -> str:
    return " ".join((value or "").strip().split()).casefold()


def resolve_counterparty(db: Session, name: str | None, party_type: str = "Other",
                         party_id: int | None = None, *, create: bool = True,
                         allow_inactive: bool = False) -> Counterparty | None:
    if party_id is not None:
        party = db.get(Counterparty, party_id)
        if party and not party.is_active and not allow_inactive:
            raise HTTPException(409, f"الطرف {party.legal_name} موقوف؛ أعد تنشيطه قبل إنشاء معاملات جديدة")
        return party
    display = " ".join((name or "").strip().split())
    if not display:
        return None
    key = normalize_name(display)
    alias = db.scalar(select(CounterpartyAlias).where(func.lower(func.trim(CounterpartyAlias.alias_name)) == key))
    party = db.get(Counterparty, alias.counterparty_id) if alias and alias.counterparty_id else None
    if party is None:
        party = db.scalar(select(Counterparty).where(
            func.lower(func.trim(Counterparty.legal_name)) == key))
    if party is None and alias:
        party = db.scalar(select(Counterparty).where(
            func.lower(func.trim(Counterparty.legal_name)) == normalize_name(alias.canonical_name)))
    if party is None and create:
        legal = " ".join((alias.canonical_name if alias else display).strip().split())
        roles = [party_type] if party_type not in ("Other", "Mixed") else []
        # Do not use a shared placeholder code: concurrent party creation can
        # otherwise collide on the unique Code index before the final ID code is assigned.
        party = Counterparty(code=f"TMP-{uuid4().hex}", name=legal, legal_name=legal, roles=roles,
                             party_type=party_type, is_active=True)
        db.add(party)
        db.flush()
        party.code = f"CP-{party.counterparty_id:06d}"
    if party and not party.is_active and not allow_inactive:
        raise HTTPException(409, f"الطرف {party.legal_name} موقوف؛ أعد تنشيطه قبل إنشاء معاملات جديدة")
    if party:
        current = party.party_type or "Other"
        if party_type not in ("Other", "Mixed") and current not in ("Other", party_type, "Mixed"):
            party.party_type = "Mixed"
        elif current == "Other" and party_type not in ("Other", "Mixed"):
            party.party_type = party_type
        party.roles = list(dict.fromkeys([*(party.roles or []), *roles_for(party_type)]))
        if not party.name:
            party.name = party.legal_name
    if party and alias and alias.counterparty_id is None:
        alias.counterparty_id = party.counterparty_id
    return party


def roles_for(party_type: str) -> list[str]:
    return [party_type] if party_type not in ("Other", "Mixed") else []
