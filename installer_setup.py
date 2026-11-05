"""SQLite-native post-install setup for Inno Setup. Existing DB files are preserved."""
import argparse, secrets
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--answers',required=True); args=ap.parse_args(); path=Path(args.answers)
    try: values=dict(line.split('=',1) for line in path.read_text(encoding='utf-8-sig').splitlines() if '=' in line)
    finally:
        try: path.unlink()
        except OSError: pass
    username=values.get('username','admin').strip(); password=values.get('password',''); year=int(values.get('year','2026') or 2026)
    if not username or not password or len(password.encode('utf-8'))>72: raise SystemExit('Invalid username/password; password must be 1–72 UTF-8 bytes.')
    env=ROOT/'.env'
    if not env.exists(): env.write_text('DATABASE_URL=sqlite:///./financial_system.db\nJWT_SECRET='+secrets.token_urlsafe(48)+'\nACCESS_TOKEN_MINUTES=30\nREFRESH_TOKEN_DAYS=7\nMAX_FAILED_LOGINS=5\nLOCKOUT_MINUTES=15\nCORS_ORIGINS=\n',encoding='utf-8')
    import os; os.chdir(ROOT)
    from sqlalchemy import text, select
    from app.database import engine, SessionLocal
    from app.models import Base, User
    from app import bootstrap
    Base.metadata.create_all(engine)
    with engine.begin() as c:
        if not c.execute(text("SELECT name FROM sqlite_master WHERE type='view' AND name='vw_EffectivePermissions'")).first():
            c.execute(text("""CREATE VIEW vw_EffectivePermissions AS SELECT u.UserId,p.PermissionId,p.ScreenCode,p.ActionCode,CASE WHEN up.IsAllowed IS NOT NULL THEN up.IsAllowed WHEN rp.PermissionId IS NOT NULL THEN 1 ELSE 0 END AS IsAllowed FROM Users u CROSS JOIN Permissions p LEFT JOIN UserRoles ur ON ur.UserId=u.UserId LEFT JOIN RolePermissions rp ON rp.RoleId=ur.RoleId AND rp.PermissionId=p.PermissionId LEFT JOIN UserPermissions up ON up.UserId=u.UserId AND up.PermissionId=p.PermissionId"""))
    with SessionLocal() as db:
        bootstrap.seed_screens(db); bootstrap.sync_permissions(db); bootstrap.create_admin(db,username,password)
        user=db.scalar(select(User).where(User.username==username))
        from app.security import hash_password
        user.password_hash=hash_password(password); user.is_active=True; user.failed_login_count=0; user.locked_until=None; db.commit()
        bootstrap.ensure_fiscal_year(db,year)
    print('SQLite setup completed')
if __name__=='__main__': main()
