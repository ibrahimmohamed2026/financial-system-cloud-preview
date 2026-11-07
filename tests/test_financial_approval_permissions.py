from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.bootstrap import seed_job_profiles
from app.models import Base, JobProfile, JobProfilePermission, Permission


def test_existing_finance_profiles_receive_new_stage_permissions_without_full_reseed():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        finance_reviewer = JobProfile(name_ar="مراجع مالي", name_en="Financial Reviewer")
        finance_manager = JobProfile(name_ar="المدير المالي", name_en="Finance Manager")
        general_manager = JobProfile(name_ar="المدير العام", name_en="General Manager")
        db.add_all([finance_reviewer, finance_manager, general_manager])
        db.flush()

        finance_approve = Permission(screen_code="ContractSettlements", action_code="FinancialApprove")
        manager_approve = Permission(screen_code="ContractSettlements", action_code="ManagerApprove")
        unrelated_view = Permission(screen_code="Contracts", action_code="View")
        db.add_all([finance_approve, manager_approve, unrelated_view])
        db.flush()

        # Preserve the administrator's existing customization: the reviewer
        # intentionally has no Contracts:View grant in this fixture.
        db.add(JobProfilePermission(
            job_profile_id=finance_manager.job_profile_id,
            permission_id=unrelated_view.permission_id,
        ))
        db.commit()

        seed_job_profiles(db)

        grants = set(db.execute(select(
            JobProfilePermission.job_profile_id,
            JobProfilePermission.permission_id,
        )).all())
        assert (finance_reviewer.job_profile_id, finance_approve.permission_id) in grants
        assert (finance_manager.job_profile_id, manager_approve.permission_id) in grants
        assert (general_manager.job_profile_id, manager_approve.permission_id) in grants
        assert (finance_reviewer.job_profile_id, unrelated_view.permission_id) not in grants

        # Re-running startup seeding must remain idempotent.
        before = len(grants)
        seed_job_profiles(db)
        after = db.scalar(select(func.count()).select_from(JobProfilePermission))
        assert after == before
