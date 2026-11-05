"""إنشاء مستخدم جديد مباشرة في قاعدة البيانات (SQLite أو أي قاعدة بيانات مربوطة في .env).

ملاحظة: النسخة القديمة كانت بتستخدم pyodbc + werkzeug مباشرة على SQL Server، وكانت
بتعمل هاش بطريقة (werkzeug) مختلفة عن اللي بيتحقق بيه تسجيل الدخول في البرنامج (bcrypt)،
فكان المستخدم الجديد يتعمل لكن مايقدرش يسجّل دخول. النسخة دي بتستخدم نفس دوال البرنامج
(SQLAlchemy + security.hash_password) فتشتغل صح مع أي قاعدة بيانات (SQLite/SQL Server).

التشغيل:  python create.py
"""
import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

new_username = input("اسم المستخدم الجديد: ").strip()
full_name = input("الاسم بالكامل: ").strip() or new_username
new_password = getpass.getpass("كلمة المرور: ")

with SessionLocal() as db:
    existing = db.scalar(select(User).where(User.username == new_username))
    if existing is not None:
        print(f"المستخدم ({new_username}) موجود بالفعل.")
    else:
        db.add(User(username=new_username, password_hash=hash_password(new_password),
                     full_name=full_name, is_active=True))
        db.commit()
        print(f"تم إنشاء المستخدم ({new_username}) بنجاح!")
        print("ملحوظة: المستخدم الجديد مالوش أي دور/صلاحيات لسه — ضيفله دور من شاشة إدارة المستخدمين"
              " أو من جدول UserRoles.")
