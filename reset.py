"""إعادة ضبط كلمة مرور مستخدم وفك القفل عنه (SQLite أو أي قاعدة بيانات مربوطة في .env).

ملاحظة: النسخة القديمة كانت بتستخدم pyodbc + werkzeug مباشرة على SQL Server، وبهاش
مختلف عن اللي بيتحقق بيه تسجيل الدخول في البرنامج (bcrypt). النسخة دي بتستخدم نفس
دوال البرنامج (SQLAlchemy + security.hash_password) فتشتغل صح مع أي قاعدة بيانات.

التشغيل:  python reset.py
"""
import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

username = input("اسم المستخدم المطلوب إعادة ضبطه [admin]: ").strip() or "admin"
new_password = getpass.getpass("كلمة المرور الجديدة: ")

with SessionLocal() as db:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        print(f"مفيش مستخدم بالاسم ({username}).")
    else:
        user.password_hash = hash_password(new_password)
        user.failed_login_count = 0
        user.locked_until = None
        user.is_active = True
        db.commit()
        print(f"تم إعادة ضبط كلمة المرور وفك قفل حساب ({username}) بنجاح وجاهز لتسجيل الدخول!")
