import os
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Role, UserRole
from app.security import hash_password, validate_password


def main():
    username = os.getenv("ADMIN_RESET_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_RESET_PASSWORD", "")

    if not password:
        print("ERROR: ADMIN_RESET_PASSWORD is not set.")
        sys.exit(1)

    try:
        validate_password(password)
    except Exception as exc:
        print(f"Invalid password: {exc}")
        sys.exit(1)

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(User.username == username)
        )

        if user:
            user.password_hash = hash_password(password)
            user.is_active = True
            user.failed_login_count = 0
            user.locked_until = None
            user.token_version = (user.token_version or 0) + 1
            print(f"Password reset for user: {username}")
        else:
            user = User(
                username=username,
                password_hash=hash_password(password),
                full_name="System Administrator",
                is_active=True,
                failed_login_count=0,
                token_version=0,
            )
            db.add(user)
            db.flush()
            print(f"Created user: {username}")

        role = db.scalar(
            select(Role).where(Role.name == "Admin")
        )

        if not role:
            role = Role(name="Admin")
            db.add(role)
            db.flush()

        existing_link = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )

        if not existing_link:
            db.add(UserRole(user_id=user.id, role_id=role.id))

        db.commit()
        print("SUCCESS: Admin account is ready.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
