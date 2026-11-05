from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User, effective_permissions, utcnow
from ..schemas import LoginIn, MeOut, PermissionOut, RefreshIn, TokenOut, UserOut
from ..security import create_token, decode_token, verify_password
from ..client_ip import get_client_ip
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

router = APIRouter(prefix="/auth", tags=["Auth"])

_login_attempts: dict[str, deque[float]] = defaultdict(deque)
_login_attempts_lock = Lock()

_BAD_CREDENTIALS = "اسم المستخدم أو كلمة المرور غير صحيحة"


def _issue(user: User) -> TokenOut:
    return TokenOut(
        access_token=create_token(user.user_id, "access", timedelta(minutes=settings.access_token_minutes), user.token_version),
        refresh_token=create_token(user.user_id, "refresh", timedelta(days=settings.refresh_token_days), user.token_version),
        user=UserOut.model_validate(user),
    )


def _limit_login(request: Request) -> None:
    now = monotonic()
    window = max(1, settings.auth_rate_limit_window_seconds)
    limit = max(1, settings.auth_rate_limit_attempts)
    key = get_client_ip(request)
    with _login_attempts_lock:
        attempts = _login_attempts[key]
        while attempts and now - attempts[0] >= window:
            attempts.popleft()
        if len(attempts) >= limit:
            retry_after = max(1, int(window - (now - attempts[0])))
            raise HTTPException(429, "محاولات دخول كثيرة؛ حاول مرة أخرى بعد قليل",
                                headers={"Retry-After": str(retry_after)})
        attempts.append(now)
        # Bound memory use when clients send requests from many source addresses.
        if len(_login_attempts) > 4096:
            stale = [ip for ip, values in _login_attempts.items() if not values or now - values[-1] >= window]
            for ip in stale:
                _login_attempts.pop(ip, None)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    _limit_login(request)
    user = db.scalar(select(User).where(User.username == body.username))
    # Don't reveal whether the username exists.
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _BAD_CREDENTIALS)

    now = utcnow()
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "المستخدم معطّل")

    if user.locked_until and user.locked_until > now:
        mins = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise HTTPException(status.HTTP_423_LOCKED,
                            f"الحساب مقفول مؤقتًا، حاول بعد {mins} دقيقة")

    if not verify_password(body.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= settings.max_failed_logins:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            # Keep the count at the threshold until a successful login/reset.
        db.commit()
        if user.locked_until and user.locked_until > now:
            raise HTTPException(status.HTTP_423_LOCKED,
                                f"تم قفل الحساب لمدة {settings.lockout_minutes} دقيقة بسبب المحاولات الفاشلة")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _BAD_CREDENTIALS)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    return _issue(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    user_id = decode_token(body.refresh_token, "refresh")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active or decode_token(body.refresh_token, "refresh", user.token_version) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "جلسة غير صالحة — سجّل الدخول من جديد")
    return _issue(user)


@router.post("/logout", status_code=204)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    e = effective_permissions.c
    rows = db.execute(
        select(e.ScreenCode, e.ActionCode).where(e.UserId == user.user_id, e.IsAllowed == 1)
        .distinct().order_by(e.ScreenCode, e.ActionCode)
    ).all()
    return MeOut(**UserOut.model_validate(user).model_dump(),
                 permissions=[PermissionOut(screen=s, action=a) for s, a in rows])
