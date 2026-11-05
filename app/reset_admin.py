"""One-off admin recovery utility. Run only from a trusted environment."""
import os
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Role, UserRole
from app.bootstrap import sync_permissions
from app.security import hash_password, validate_password


def main():
    username = os.getenv("ADMIN_RESET_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_RESET_PASSWORD", "")

    if not username:
        print("ERROR: ADMIN_RESET_USERNAME is empty.")
        sys.exit(1)
    if not password:
        print("ERROR: ADMIN_RESET_PASSWORD is not set.")
        sys.exit(1)

    try:
        validate_password(password)
    except ValueError as exc:
        print(f"Invalid password: {exc}")
        sys.exit(1)

    with SessionLocal() as db:
        try:
            # Ensure the Admin role and its permissions exist before linking the user.
            sync_permissions(db)

            user = db.scalar(select(User).where(User.username == username))
            if user is None:
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
                result = "created"
            else:
                user.password_hash = hash_password(password)
                user.is_active = True
                user.failed_login_count = 0
                user.locked_until = None
                user.token_version = (user.token_version or 0) + 1
                result = "reset"

            role = db.scalar(select(Role).where(Role.role_name == "Admin"))
            if role is None:
                raise RuntimeError("Admin role was not created by sync_permissions.")

            link = db.get(UserRole, (user.user_id, role.role_id))
            if link is None:
                db.add(UserRole(user_id=user.user_id, role_id=role.role_id))

            db.commit()
            print(f"SUCCESS: Admin account {result}. Username: {username}")
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
