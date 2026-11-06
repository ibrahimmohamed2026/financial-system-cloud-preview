"""تهيئة أولية: الأقسام/الشاشات الأساسية + الصلاحيات + مستخدم Admin.

التشغيل:  python -m app.bootstrap --username admin
(آمن للتكرار — بيضيف الناقص بس.)
"""
import argparse
import getpass

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .models import Permission, Role, RolePermission, Screen, Section, User, UserRole, JobProfile, JobProfilePermission

ACTIONS = ["View", "Add", "Edit", "Delete", "Post", "Approve", "EngineeringApprove", "FinancialApprove", "ManagerApprove", "Print"]

# الشاشات الـ17 = شيتات ملف "ميزانيه فارغه.xlsx" بنفس ترتيبها (رقم الشيت في التعليق).
SECTIONS = {
    "ACCOUNTING": ("Accounting", "الحسابات", 1),
    "TREASURY": ("Treasury & Banks", "الخزائن والبنوك", 2),
    "CHECKS": ("Checks", "الشيكات", 3),
    "REPORTS": ("Financial Statements", "القوائم المالية", 4),
}
_S = [  # (section, code, title_en, title_ar, route)
    ("ACCOUNTING", "JournalBook", "General Journal", "دفتر اليومية", "/journal"),                       # 1
    ("ACCOUNTING", "CostCenters", "Cost Centers", "مراكز التكلفة والمشروعات", "/projects"),               # 2
    ("ACCOUNTING", "ChartOfAccounts", "Chart of Accounts", "شجرة الحسابات", "/accounts"),                # 3 Trial balance
    ("ACCOUNTING", "TrialBalance", "Trial Balance", "ميزان المراجعة", "/trial-balance"),                  # 4
    ("REPORTS", "BalanceSheet", "Balance Sheet", "قائمة المركز المالي", "/reports/balance-sheet"),        # 5
    ("REPORTS", "IncomeStatement", "Income Statement", "قائمة الدخل", "/reports/income-statement"),      # 6
    ("TREASURY", "CashAnalysis", "Cash Analysis", "تحليل النقدية", "/treasury/analysis"),                # 7
    ("TREASURY", "BankCibEgp", "CIB Bank - EGP", "البنك التجاري جنيه مصري", "/treasury/cib-egp"),        # 8
    ("CHECKS", "ChecksCib", "CIB Checks", "أرقام شيكات بنك CIB", "/checks/cib"),                          # 9
    ("TREASURY", "BankReconciliation", "Bank Reconciliation", "مذكرة تسوية البنك", "/treasury/reconciliation"),  # 10
    ("TREASURY", "CashUsd", "Cash - USD", "خزينة دولار", "/treasury/cash-usd"),                           # 11
    ("TREASURY", "CashEgp", "Cash - EGP", "صندوق خزينة الجنيه المصري", "/treasury/cash-egp"),
    ("TREASURY", "BankCairoEgp", "Banque du Caire - EGP", "بنك القاهرة جنيه مصري", "/treasury/cairo-egp"),  # 12
    ("TREASURY", "BankHdbUsd", "Real Estate Bank - USD", "البنك العقاري المصري دولار", "/treasury/hdb-usd"),  # 13
    ("TREASURY", "BankHdbEgp", "Real Estate Bank - EGP", "البنك العقاري جنيه مصري", "/treasury/hdb-egp"),  # 14
    ("TREASURY", "BankCibUsd", "CIB Bank - USD", "البنك التجاري دولار", "/treasury/cib-usd"),             # 15
    ("CHECKS", "ChecksCairoEgp", "Banque du Caire Checks - EGP", "أرقام شيكات بنك القاهرة جنيه", "/checks/cairo-egp"),  # 16
    ("CHECKS", "ChecksCairoUsd", "Banque du Caire Checks - USD", "أرقام شيكات بنك القاهرة دولار", "/checks/cairo-usd"),  # 17
    ("CHECKS", "FinancialChecks", "Financial Checks Register", "إدارة الشيكات المالية", "/checks/register"),
    ("REPORTS", "AuditLogs", "Audit Logs", "سجل المراجعة والنشاطات", "/audit-logs"),  # 18
    ("REPORTS", "AnalyticsReports", "Reports & Analytics", "التقارير والرسوم البيانية", "/reports"),  # 19
    ("ACCOUNTING", "Contracts", "Contracts & Technical Office", "العقود والمكتب الفني", "/contracts"),
    ("ACCOUNTING", "ContractRequests", "Contract Requests", "طلبات التعاقد", "/contract-requests"),
    ("ACCOUNTING", "ContractSettlements", "Contract Settlements", "مستخلصات العملاء ومقاولي الباطن", "/settlements"),
    ("ACCOUNTING", "SettlementManagerApproval", "Settlement Manager Approval", "اعتماد المستخلصات — المدير", "/settlements/manager-approval"),
    ("ACCOUNTING", "InventoryManagement", "Inventory Management", "إدارة المخزون", "/inventory"),
    ("ACCOUNTING", "PurchaseCycle", "Purchase Cycle", "دورة المشتريات", "/purchases"),
    ("ACCOUNTING", "Counterparties", "Counterparties", "المقاولون والموردون والعملاء", "/counterparties"),
]
SCREENS = [
    {"section": dict(zip(("code", "name_en", "name_ar", "sort_order"), (sec, *SECTIONS[sec]))),
     "code": code, "title_en": en, "title_ar": ar, "route": route, "sort_order": i}
    for i, (sec, code, en, ar, route) in enumerate(_S, start=1)
]
assert len(SCREENS) == 28


def seed_screens(db: Session) -> None:
    for item in SCREENS:
        sec = item["section"]
        section = db.scalar(select(Section).where(Section.code == sec["code"]))
        if section is None:
            section = Section(**sec)
            db.add(section)
            db.flush()
        existing_screen = db.scalar(select(Screen).where(Screen.screen_code == item["code"]))
        if existing_screen is None:
            db.add(Screen(section_id=section.section_id, screen_code=item["code"], title_en=item["title_en"],
                          title_ar=item["title_ar"], route=item["route"], sort_order=item["sort_order"]))
        elif item["code"] in ("ContractRequests", "ContractSettlements", "PurchaseCycle", "FinancialChecks", "AnalyticsReports", "Counterparties"):
            # Keep legacy database screen routes synchronized with the implemented frontend routes.
            existing_screen.route = item["route"]
            existing_screen.title_ar = item["title_ar"]
            existing_screen.title_en = item["title_en"]
            existing_screen.is_active = True
    # الشاشات المؤقتة اللي register_excel_screens.py كان بيسجلها (EXCEL_SHEET_xx) بتتعطّل عشان ماتتكررش
    for old in db.scalars(select(Screen).where(Screen.screen_code.like("EXCEL\\_SHEET\\_%", escape="\\"))):
        old.is_active = False
    db.commit()


def sync_permissions(db: Session) -> None:
    """ينشئ صلاحيات الشاشات، دون منح دور Admin القديم تجاوزًا عامًا للصلاحيات."""
    codes = db.scalars(select(Screen.screen_code)).all()
    existing = {(p.screen_code, p.action_code) for p in db.scalars(select(Permission))}
    for code in codes:
        for action in ACTIONS:
            if (code, action) not in existing:
                db.add(Permission(screen_code=code, action_code=action))
    db.flush()

    # Track pending grants too: a grant may be requested by more than one
    # migration below before the transaction is committed.
    role_permission_pairs = {
        (rp.role_id, rp.permission_id) for rp in db.scalars(select(RolePermission))
    }

    def grant(role_id: int, permission_id: int) -> None:
        pair = (role_id, permission_id)
        if pair not in role_permission_pairs:
            # Two app workers can seed permissions concurrently at startup. Use
            # an atomic conflict-safe insert for the supported production/test DBs.
            dialect = db.get_bind().dialect.name
            if dialect == "postgresql":
                stmt = pg_insert(RolePermission).values(role_id=role_id, permission_id=permission_id)
                db.execute(stmt.on_conflict_do_nothing(
                    index_elements=[RolePermission.role_id, RolePermission.permission_id]))
            elif dialect == "sqlite":
                stmt = sqlite_insert(RolePermission).values(role_id=role_id, permission_id=permission_id)
                db.execute(stmt.on_conflict_do_nothing(
                    index_elements=[RolePermission.role_id, RolePermission.permission_id]))
            else:
                db.add(RolePermission(role_id=role_id, permission_id=permission_id))
            role_permission_pairs.add(pair)

    # Keep access to the new financial-checks module for roles already allowed
    # to use any legacy check-book screen.
    fin_view = next((p.permission_id for p in db.scalars(select(Permission))
                     if p.screen_code == "FinancialChecks" and p.action_code == "View"), None)
    legacy_codes = {"ChecksCib", "ChecksCairoEgp", "ChecksCairoUsd"}
    if fin_view is not None:
        roles_with_checks = set(db.scalars(
            select(RolePermission.role_id).join(Permission, Permission.permission_id == RolePermission.permission_id)
            .where(Permission.screen_code.in_(legacy_codes), Permission.action_code == "View")
        ))
        have_fin_view = set(db.scalars(select(RolePermission.role_id).where(RolePermission.permission_id == fin_view)))
        for rid in roles_with_checks - have_fin_view:
            grant(rid, fin_view)

    # Preserve legacy contract approvers while migrating them to the explicit two-stage workflow.
    permission_ids = {(p.screen_code, p.action_code): p.permission_id for p in db.scalars(select(Permission))}
    old_approve = permission_ids.get(("Contracts", "Approve"))
    stage_ids = [permission_ids.get(("Contracts", action)) for action in ("EngineeringApprove", "FinancialApprove")]
    if old_approve and all(stage_ids):
        legacy_roles = set(db.scalars(select(RolePermission.role_id).where(RolePermission.permission_id == old_approve)))
        for role_id in legacy_roles:
            for permission_id in stage_ids:
                grant(role_id, permission_id)

    # Give existing settlement viewers access to the dedicated manager approval screen.
    manager_view = permission_ids.get(("SettlementManagerApproval", "View"))
    settlement_view = permission_ids.get(("ContractSettlements", "View"))
    if manager_view and settlement_view:
        settlement_view_roles = set(db.scalars(select(RolePermission.role_id).where(
            RolePermission.permission_id == settlement_view)))
        manager_action = permission_ids.get(("ContractSettlements", "ManagerApprove"))
        manager_roles = set(db.scalars(select(RolePermission.role_id).where(
            RolePermission.permission_id == manager_action))) if manager_action else set()
        manager_view_roles = set(db.scalars(select(RolePermission.role_id).where(
            RolePermission.permission_id == manager_view)))
        for role_id in (settlement_view_roles | manager_roles) - manager_view_roles:
            grant(role_id, manager_view)

    # Preserve existing settlement approvers while introducing finance then manager approval.
    settlement_approve = permission_ids.get(("ContractSettlements", "Approve"))
    settlement_stage_ids = [permission_ids.get(("ContractSettlements", action)) for action in ("EngineeringApprove", "FinancialApprove", "ManagerApprove")]
    if settlement_approve and all(settlement_stage_ids):
        legacy_settlement_roles = set(db.scalars(select(RolePermission.role_id).where(RolePermission.permission_id == settlement_approve)))
        for role_id in legacy_settlement_roles:
            for permission_id in settlement_stage_ids:
                grant(role_id, permission_id)

    # Keep the legacy role record for compatibility, but it has no global grants.
    admin = db.scalar(select(Role).where(Role.role_name == "Admin"))
    if admin is None:
        admin = Role(role_name="Admin")
        db.add(admin)
        db.flush()
    db.execute(delete(RolePermission).where(RolePermission.role_id == admin.role_id))
    db.commit()


def seed_job_profiles(db: Session) -> None:
    """Seed editable least-privilege templates once; never overwrite admin customization."""
    templates = {
        "مسؤول النظام IT": ("IT System Administrator", {"AuditLogs": ["View"], "AnalyticsReports": ["View"]}),
        "المدير العام": ("General Manager", {"Contracts": ["View"], "ContractRequests": ["View"], "ContractSettlements": ["View", "ManagerApprove"], "SettlementManagerApproval": ["View"], "JournalBook": ["View"], "CostCenters": ["View"], "ChartOfAccounts": ["View"], "TrialBalance": ["View"], "BalanceSheet": ["View"], "IncomeStatement": ["View"], "AnalyticsReports": ["View"], "AuditLogs": ["View"]}),
        "مدير المشروعات": ("Projects Manager", {"Contracts": ["View", "Edit"], "ContractRequests": ["View", "Edit"], "ContractSettlements": ["View"], "CostCenters": ["View"], "InventoryManagement": ["View"], "PurchaseCycle": ["View"], "AnalyticsReports": ["View"]}),
        "مدير الموقع": ("Site Manager", {"Contracts": ["View"], "ContractSettlements": ["View"], "InventoryManagement": ["View", "Add", "Edit"], "PurchaseCycle": ["View", "Add"], "CostCenters": ["View"]}),
        "مهندس موقع": ("Site Engineer", {"Contracts": ["View"], "ContractSettlements": ["View", "Add", "Edit"], "CostCenters": ["View"]}),
        "مدير المكتب الفني": ("Technical Office Manager", {"Contracts": ["View", "Add", "Edit"], "ContractRequests": ["View", "Add", "Edit"], "ContractSettlements": ["View"], "CostCenters": ["View"]}),
        "مراجع فني": ("Technical Reviewer", {"Contracts": ["View"], "ContractSettlements": ["View", "EngineeringApprove"], "CostCenters": ["View"]}),
        "مسؤول العقود": ("Contracts Officer", {"Contracts": ["View", "Add", "Edit"], "ContractRequests": ["View", "Add", "Edit"], "Counterparties": ["View", "Add", "Edit"], "CostCenters": ["View"]}),
        "محاسب": ("Accountant", {"ContractSettlements": ["View", "Add", "Edit"], "JournalBook": ["View", "Add", "Edit"], "ChartOfAccounts": ["View"], "Counterparties": ["View"], "TrialBalance": ["View"]}),
        "مراجع مالي": ("Financial Reviewer", {"ContractSettlements": ["View", "FinancialApprove"], "JournalBook": ["View"], "ChartOfAccounts": ["View"], "TrialBalance": ["View"], "AuditLogs": ["View"]}),
        "المدير المالي": ("Finance Manager", {"ContractSettlements": ["View", "ManagerApprove"], "SettlementManagerApproval": ["View"], "JournalBook": ["View"], "ChartOfAccounts": ["View"], "TrialBalance": ["View"], "BalanceSheet": ["View"], "IncomeStatement": ["View"], "AnalyticsReports": ["View"]}),
        "محاسب خزينة": ("Treasury Accountant", {"CashAnalysis": ["View"], "BankCibEgp": ["View", "Add", "Edit", "Post"], "CashEgp": ["View", "Add", "Edit", "Post"], "CashUsd": ["View", "Add", "Edit", "Post"], "BankCairoEgp": ["View", "Add", "Edit", "Post"], "BankHdbEgp": ["View", "Add", "Edit", "Post"], "BankHdbUsd": ["View", "Add", "Edit", "Post"], "BankCibUsd": ["View", "Add", "Edit", "Post"], "ChecksCib": ["View", "Add", "Edit"], "ChecksCairoEgp": ["View", "Add", "Edit"], "ChecksCairoUsd": ["View", "Add", "Edit"], "FinancialChecks": ["View", "Add", "Edit"]}),
        "مسؤول مشتريات": ("Procurement Officer", {"PurchaseCycle": ["View", "Add", "Edit"], "Counterparties": ["View"], "InventoryManagement": ["View"], "CostCenters": ["View"]}),
        "أمين مخزن": ("Storekeeper", {"InventoryManagement": ["View", "Add", "Edit"], "CostCenters": ["View"]}),
        "مراجع داخلي": ("Internal Auditor", {"AuditLogs": ["View"], "AnalyticsReports": ["View"], "Contracts": ["View"], "ContractRequests": ["View"], "ContractSettlements": ["View"], "JournalBook": ["View"], "CostCenters": ["View"], "ChartOfAccounts": ["View"], "TrialBalance": ["View"], "BalanceSheet": ["View"], "IncomeStatement": ["View"], "InventoryManagement": ["View"], "PurchaseCycle": ["View"], "Counterparties": ["View"], "FinancialChecks": ["View"]}),
        "مستخدم مشاهدة فقط": ("Read Only User", {"Contracts": ["View"], "ContractRequests": ["View"], "ContractSettlements": ["View"], "JournalBook": ["View"], "CostCenters": ["View"], "ChartOfAccounts": ["View"], "TrialBalance": ["View"], "BalanceSheet": ["View"], "IncomeStatement": ["View"], "InventoryManagement": ["View"], "PurchaseCycle": ["View"], "Counterparties": ["View"], "AnalyticsReports": ["View"]}),
    }
    available = {(p.screen_code, p.action_code): p.permission_id for p in db.scalars(select(Permission))}
    for name_ar, (name_en, grants) in templates.items():
        if db.scalar(select(JobProfile.job_profile_id).where(JobProfile.name_ar == name_ar)) is not None:
            continue
        profile = JobProfile(name_ar=name_ar, name_en=name_en, is_active=True)
        db.add(profile); db.flush()
        for screen, actions in grants.items():
            for action in actions:
                pid = available.get((screen, action))
                if pid is not None:
                    db.add(JobProfilePermission(job_profile_id=profile.job_profile_id, permission_id=pid))
    # مسؤول النظام IT هو ملف الصلاحيات الإداري الوحيد، ويحتاج إدارة جميع شاشات النظام.
    it_profile = db.scalar(select(JobProfile).where(JobProfile.name_ar == "مسؤول النظام IT"))
    if it_profile is not None:
        existing_ids = set(db.scalars(select(JobProfilePermission.permission_id).where(
            JobProfilePermission.job_profile_id == it_profile.job_profile_id)))
        all_ids = set(db.scalars(select(Permission.permission_id)))
        for permission_id in all_ids - existing_ids:
            db.add(JobProfilePermission(job_profile_id=it_profile.job_profile_id, permission_id=permission_id))

        # ترحيل الحسابات التي كانت تعتمد على Admin القديم إلى الوظيفة المعتمدة.
        legacy_admin = db.scalar(select(Role).where(Role.role_name == "Admin"))
        if legacy_admin is not None:
            legacy_users = db.scalars(select(User).join(
                UserRole, UserRole.user_id == User.user_id).where(
                UserRole.role_id == legacy_admin.role_id)).all()
            for legacy_user in legacy_users:
                if legacy_user.job_profile_id is None:
                    legacy_user.job_profile_id = it_profile.job_profile_id
                db.execute(delete(UserRole).where(
                    UserRole.user_id == legacy_user.user_id, UserRole.role_id == legacy_admin.role_id))
    db.commit()


def ensure_fiscal_year(db: Session, year: int, company_name: str = "الشركة") -> None:
    from datetime import date

    from sqlalchemy import func

    from .models import Company, FiscalYear
    if db.scalar(select(func.count()).select_from(FiscalYear)):
        return
    company = db.scalar(select(Company)) or Company(name_ar=company_name)
    db.add(company)
    db.flush()
    db.add(FiscalYear(company_id=company.company_id, start_date=date(year, 1, 1), end_date=date(year, 12, 31)))
    db.commit()


def create_admin(db: Session, username: str, password: str, full_name: str = "System Admin") -> User:
    from .security import hash_password, validate_password

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, password_hash=hash_password(password), full_name=full_name)
        db.add(user)
        db.flush()
    it_profile = db.scalar(select(JobProfile).where(JobProfile.name_ar == "مسؤول النظام IT"))
    if it_profile is None:
        raise RuntimeError("وظيفة مسؤول النظام IT غير مهيأة؛ شغّل seed_job_profiles أولاً")
    user.job_profile_id = it_profile.job_profile_id
    admin = db.scalar(select(Role).where(Role.role_name == "Admin"))
    if admin is not None:
        db.execute(delete(UserRole).where(UserRole.user_id == user.user_id, UserRole.role_id == admin.role_id))
    db.commit()
    return user


if __name__ == "__main__":
    from .database import SessionLocal

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--full-name", default="System Admin")
    parser.add_argument("--company", default="الشركة")
    parser.add_argument("--year", type=int, default=None, help="ينشئ سنة مالية 1/1–31/12 لو مفيش أي سنة")
    args = parser.parse_args()
    while True:
        pwd = getpass.getpass("Password (12 characters minimum): ")
        try:
            validate_password(pwd)
            break
        except ValueError as exc:
            print(exc)
    with SessionLocal() as session:
        seed_screens(session)
        sync_permissions(session)
        create_admin(session, args.username, pwd, args.full_name)
        if args.year:
            ensure_fiscal_year(session, args.year, args.company)
    print("done")
