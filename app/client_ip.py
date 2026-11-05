"""Client IP extraction that trusts forwarded headers only from configured proxies."""
from __future__ import annotations

import ipaddress
from contextvars import ContextVar

from fastapi import Request

from .config import settings

request_ip: ContextVar[str | None] = ContextVar("request_ip", default=None)


def _is_trusted(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    for entry in settings.trusted_proxy_list:
        try:
            if address in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            continue
    return False


def get_client_ip(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    if not _is_trusted(peer):
        return peer

    forwarded = request.headers.get("x-forwarded-for", "")
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    # Walk from the proxy-facing end. Ignore trusted proxies and choose the
    # nearest untrusted hop, so an arbitrary leftmost client value is not used.
    for candidate in reversed(chain):
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if not _is_trusted(candidate):
            return candidate
    return peer
