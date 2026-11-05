from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import backup_service
from .config import settings
from .client_ip import get_client_ip, request_ip
from .database import engine, SessionLocal
from .db_setup import ensure_schema
from .bootstrap import seed_screens, sync_permissions
from .routers import (accounts, admin, auth, audit_logs, backup, checks, dashboard, journal, projects, reconciliation, reports, contracts, contract_erp, contract_requests, contract_attachments, technical_settlements, inventory, counterparties,
                      treasury, trial_balance, data_exchange, pg_backup, financial_checks, financial_control)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # تهيئة آمنة وقابلة للتكرار: تنشئ الجداول الناقصة، وتحدّث تعريفات الشاشات
    # والصلاحيات دون حذف بيانات موجودة. لا ننفّذ سكربتات T-SQL على PostgreSQL.
    ensure_schema(engine)
    with SessionLocal() as db:
        seed_screens(db)
        sync_permissions(db)
    # الجدولة اليومية من داخل النظام (صفحة النسخ الاحتياطي) هي المسار التلقائي الوحيد.
    # pg_dump يظل متاحًا كنسخ يدوي، ولا يبدأ تلقائيًا لتجنب تعارض الأقفال والنسخ المتزامنة.
    backup_service.start_scheduler()
    try:
        yield
    finally:
        backup_service.stop_scheduler()


app = FastAPI(title="Financial System API", version="0.1.0", lifespan=lifespan,
              docs_url="/docs" if settings.api_docs_enabled else None,
              redoc_url="/redoc" if settings.api_docs_enabled else None,
              openapi_url="/openapi.json" if settings.api_docs_enabled else None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_and_client_ip(request, call_next):
    token = request_ip.set(get_client_ip(request))
    try:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # HTML must never be restored from a stale local copy after a deployment.
        # Static assets may stay in the browser cache, but must be revalidated on
        # every navigation so a replaced file is not silently served from cache.
        if request.method in ("GET", "HEAD"):
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("text/html"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            elif request.url.path.startswith("/static/"):
                response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response
    finally:
        request_ip.reset(token)

app.include_router(auth.router)
app.include_router(data_exchange.router)
app.include_router(data_exchange.exchange_alias_router)
app.include_router(audit_logs.router)
app.include_router(admin.router)
app.include_router(admin.public_router)
app.include_router(backup.router)
app.include_router(pg_backup.router)
app.include_router(dashboard.router)
app.include_router(accounts.router)
app.include_router(financial_checks.router)
for _r in (projects, journal, trial_balance, reports, contracts, contract_erp, contract_requests, contract_attachments, technical_settlements, treasury, reconciliation, checks):
    app.include_router(_r.router)
app.include_router(inventory.inventory)
app.include_router(inventory.purchases)
app.include_router(counterparties.router)
app.include_router(reports.api_router)
app.include_router(financial_control.router)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}


# ----- الواجهة (ملفات ثابتة من مجلد web) -----
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    # اللوجو والأيقونة: تتقدّم من web/ أو من web/static/ (أيهما موجود) عشان ما يتكسرش لو اتنقلوا.
    def _brand(name: str):
        for folder in (WEB_DIR, WEB_DIR / "static"):
            if (folder / name).is_file():
                return FileResponse(folder / name, headers={"Cache-Control": "no-cache"})
        raise HTTPException(404, "Not Found")

    @app.get("/static/company-logos.png", include_in_schema=False)
    def company_logos():
        return _brand("company-logos.png")

    @app.get("/static/favicon.ico", include_in_schema=False)
    def favicon():
        return _brand("favicon.ico")

    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/audit-logs", include_in_schema=False)
    @app.get("/reports", include_in_schema=False)
    @app.get("/contract-requests", include_in_schema=False)
    @app.get("/contracts", include_in_schema=False)
    @app.get("/settlements", include_in_schema=False)
    @app.get("/inventory", include_in_schema=False)
    @app.get("/purchases", include_in_schema=False)
    @app.get("/counterparties", include_in_schema=False)
    def spa_screen():
        return FileResponse(WEB_DIR / "index.html")
