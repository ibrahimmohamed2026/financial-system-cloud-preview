from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.bootstrap import seed_screens, seed_job_profiles, sync_permissions
from app.models import Base, JobProfile, JobProfilePermission, Permission


def _seed_permission_catalog():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_screens(db)
        sync_permissions(db)
        seed_job_profiles(db)
        return engine


def test_user_permission_management_has_exact_three_actions_and_it_default_grants():
    engine = _seed_permission_catalog()
    with Session(engine) as db:
        rows = db.scalars(select(Permission).where(
            Permission.screen_code == "UserPermissionManagement"
        )).all()
        assert {row.action_code for row in rows} == {
            "View", "Edit", "ManageJobProfilePermissions"
        }

        it_profile = db.scalar(select(JobProfile).where(
            JobProfile.name_ar == "مسؤول النظام IT"
        ))
        assert it_profile is not None and it_profile.is_active
        granted = set(db.scalars(select(JobProfilePermission.permission_id).where(
            JobProfilePermission.job_profile_id == it_profile.job_profile_id
        )))
        assert {row.permission_id for row in rows} <= granted

        other_profile = db.scalar(select(JobProfile).where(
            JobProfile.name_ar == "المدير المالي"
        ))
        assert other_profile is not None
        other_grants = set(db.scalars(select(JobProfilePermission.permission_id).where(
            JobProfilePermission.job_profile_id == other_profile.job_profile_id
        )))
        assert not ({row.permission_id for row in rows} & other_grants)


def test_user_permission_management_seed_is_idempotent():
    engine = _seed_permission_catalog()
    with Session(engine) as db:
        seed_screens(db)
        sync_permissions(db)
        seed_job_profiles(db)
        rows = db.scalars(select(Permission).where(
            Permission.screen_code == "UserPermissionManagement"
        )).all()
        assert len(rows) == 3
        assert len({row.action_code for row in rows}) == 3
