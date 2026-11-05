"""أدوات مشتركة للـRouters."""
from decimal import Decimal

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from .database import get_db
from .deps import get_current_user, has_permission
from .models import User


def require_dynamic(action: str, allowed: set[str]):
    """صلاحية على شاشة جاية من الـURL (متغيّر screen_code) — لشاشات البنوك والشيكات المتشابهة."""
    def dependency(screen_code: str = Path(...), user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> User:
        if screen_code not in allowed:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "الشاشة غير موجودة")
        if not has_permission(db, user.user_id, screen_code, action):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"ليس لديك صلاحية ({screen_code}:{action})")
        return user
    return dependency


def require_any(screens: set[str], action: str):
    def dependency(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if not any(has_permission(db, user.user_id, s, action) for s in screens):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "ليس لديك صلاحية")
        return user
    return dependency


def money(x) -> str:
    return str(Decimal(x or 0).quantize(Decimal("0.01")))


def ZERO() -> Decimal:
    return Decimal("0")
