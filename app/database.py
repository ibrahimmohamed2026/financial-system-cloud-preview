from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

_url = settings.effective_database_url
if _url.startswith("sqlite"):
    _kwargs = {"connect_args": {"check_same_thread": False}}
else:  # PostgreSQL
    _kwargs = {"pool_size": 5, "max_overflow": 10, "pool_recycle": 1800}
engine = create_engine(_url, pool_pre_ping=True, **_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
