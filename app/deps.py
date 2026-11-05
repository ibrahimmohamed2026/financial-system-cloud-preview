import json
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditLog, User, effective_permissions
from .security import decode_token
from .client_ip import request_ip

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "غير مصرّح — سجّل الدخول", headers={"WWW-Authenticate": "Bearer"})
    if creds is None:
        raise unauthorized
    user_id = decode_token(creds.credentials, "access")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active or decode_token(creds.credentials, "access", user.token_version) is None:
        raise unauthorized
    return user


def has_permission(db: Session, user_id: int, screen: str, action: str) -> bool:
    # الـView ممكن يرجّع أكتر من صف للمستخدم الواحد لو عنده أكتر من دور،
    # فالصلاحية متاحة لو أي صف فيهم IsAllowed = 1.
    e = effective_permissions.c
    count = db.scalar(
        select(func.count()).select_from(effective_permissions).where(
            e.UserId == user_id, e.ScreenCode == screen, e.ActionCode == action, e.IsAllowed == 1)
    )
    return bool(count)


def require_permission(screen: str, action: str):
    """Dependency: يتحقق من vw_EffectivePermissions قبل تنفيذ الـEndpoint."""
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if not has_permission(db, user.user_id, screen, action):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"ليس لديك صلاحية ({screen}:{action})")
        return user
    return dependency


def write_audit(db: Session, user_id: int | None, action: str, entity: str, entity_id: Any,
                old: dict | None = None, new: dict | None = None, ip_address: str | None = None) -> None:
    if ip_address is None:
        ip_address = request_ip.get()
    dump = lambda d: None if d is None else json.dumps(d, ensure_ascii=False, default=str)  # noqa: E731
    db.add(AuditLog(user_id=user_id, action_type=action, entity_name=entity,
                    entity_id=str(entity_id) if entity_id is not None else None, old_value=dump(old),
                    new_value=dump(new), ip_address=ip_address))


def log_activity(db: Session, user_id: int | None, action: str, description: str,
                 ip_address: str | None = None) -> AuditLog:
    """واجهة مبسطة لتسجيل النشاطات؛ يجب أن تُحفظ ضمن معاملة العملية المستهدفة."""
    if ip_address is None:
        ip_address = request_ip.get()
    return_audit = AuditLog(user_id=user_id, action_type=action[:30], entity_name="Activity",
                            entity_id=None, old_value=None, new_value=description, ip_address=ip_address)
    db.add(return_audit)
    db.flush()
    return return_audit
