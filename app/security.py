from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


def validate_password(password: str) -> str:
    common = {"password1234", "password12345", "qwerty123456", "123456789012", "admin1234567", "welcome12345"}
    if len(password) < 12 or len(password.encode("utf-8")) > 72 or password.casefold() in common:
        raise ValueError("كلمة المرور يجب أن تكون 12 حرفًا على الأقل، غير شائعة، وبحد أقصى 72 بايت")
    return password


def hash_password(password: str) -> bytes:
    validate_password(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), bytes(hashed))
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, kind: str, expires: timedelta, token_version: int = 0) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "type": kind, "ver": token_version, "iat": now, "exp": now + expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, kind: str, token_version: int | None = None) -> int | None:
    """بيرجّع UserId لو التوكن سليم ونوعه مطابق (access/refresh)، وإلا None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != kind:
        return None
    if token_version is not None and payload.get("ver", 0) != token_version:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        return None
