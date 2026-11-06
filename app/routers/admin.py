from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, write_audit
from ..models import User, UserAvatar, Company, Role, UserRole, RolePermission, Permission, Screen, Section, UserPermission, JobProfile, JobProfilePermission, Project
from ..security import hash_password, validate_password

router = APIRouter(prefix="/admin", tags=["Users & Roles"])
public_router = APIRouter(tags=["Company profile"])


class CompanyProfileUpdate(BaseModel):
    name_ar: str = Field(min_length=1, max_length=200)
    name_en: str | None = Field(default=None, max_length=200)
    tax_number: str | None = Field(default=None, max_length=50)
    commercial_register: str | None = Field(default=None, max_length=50)
    address_ar: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=200)
    logo_data: str | None = None

    @field_validator("name_ar")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("اسم الشركة بالعربية مطلوب")
        return value

    @field_validator("logo_data")
    @classmethod
    def validate_logo(cls, value: str | None) -> str | None:
        if not value:
            return None
        allowed = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
        if not value.startswith(allowed) or len(value) > 1_500_000:
            raise ValueError("الشعار يجب أن يكون PNG أو JPG أو WebP وألا يتجاوز حجمه 1 ميجابايت")
        return value


def company_profile_out(company: Company) -> dict:
    return {"company_id": company.company_id, "name_ar": company.name_ar, "name_en": company.name_en,
            "tax_number": company.tax_number, "commercial_register": company.commercial_register,
            "address_ar": company.address_ar, "phone": company.phone, "email": company.email,
            "website": company.website, "logo_data": company.logo_data}

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=12, max_length=72)
    is_active: bool = True
    role_ids: list[int] = []
    job_profile_id: int | None = None
    project_id: int | None = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_password(value)

class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=72)
    role_ids: list[int] | None = None
    job_profile_id: int | None = None
    project_id: int | None = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_password(value)

class RoleCreate(BaseModel):
    role_name: str = Field(min_length=2, max_length=100)
    permission_ids: list[int] = []

class RoleUpdate(BaseModel):
    role_name: str | None = Field(default=None, min_length=2, max_length=100)
    permission_ids: list[int] | None = None


def admin_user(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    is_admin = db.scalar(select(UserRole.user_id).join(Role, Role.role_id == UserRole.role_id)
                         .where(UserRole.user_id == user.user_id, Role.role_name == "Admin"))
    if not is_admin:
        raise HTTPException(403, "هذه الشاشة متاحة لمدير النظام فقط")
    return user

@router.get("/status")
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"is_admin": bool(db.scalar(select(UserRole.user_id).join(Role, Role.role_id == UserRole.role_id)
            .where(UserRole.user_id == user.user_id, Role.role_name == "Admin")))}


@router.get("/company")
def get_company_settings(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    company = db.scalar(select(Company).order_by(Company.company_id))
    return company_profile_out(company) if company else None


@router.put("/company")
def save_company_settings(body: CompanyProfileUpdate, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    company = db.scalar(select(Company).order_by(Company.company_id).with_for_update())
    old = company_profile_out(company) if company else None
    if old:
        old["has_logo"] = bool(old.pop("logo_data", None))
    if company is None:
        company = Company(name_ar=body.name_ar)
        db.add(company)
    for key, value in body.model_dump().items():
        setattr(company, key, value.strip() if isinstance(value, str) and key != "logo_data" else value)
    db.flush()
    new = company_profile_out(company)
    new["has_logo"] = bool(new.pop("logo_data", None))
    write_audit(db, user.user_id, "Update", "Companies", company.company_id, old, new)
    db.commit()
    db.refresh(company)
    return company_profile_out(company)


@public_router.get("/company-profile", include_in_schema=False)
def public_company_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Company identity fields used in printed financial documents for signed-in users."""
    company = db.scalar(select(Company).where(Company.is_active == True).order_by(Company.company_id))
    return company_profile_out(company) if company else None

@router.get("/job-profiles")
def list_job_profiles(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(JobProfile).order_by(JobProfile.name_ar)).all()
    return [{"job_profile_id": p.job_profile_id, "name_ar": p.name_ar, "name_en": p.name_en,
             "description": p.description, "is_active": p.is_active,
             "permission_ids": db.scalars(select(JobProfilePermission.permission_id).where(
                 JobProfilePermission.job_profile_id == p.job_profile_id)).all()} for p in rows]


@router.post("/job-profiles", status_code=201)
def create_job_profile(body: dict, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    name_ar = str(body.get("name_ar") or "").strip()
    name_en = str(body.get("name_en") or name_ar).strip()
    ids = body.get("permission_ids") or []
    if not name_ar or not name_en or len(name_ar) > 150 or len(name_en) > 150:
        raise HTTPException(422, "اسم الوظيفة بالعربية والإنجليزية مطلوب")
    if not isinstance(ids, list) or any(type(x) is not int for x in ids):
        raise HTTPException(422, "قائمة الصلاحيات غير صحيحة")
    if db.scalar(select(JobProfile).where(JobProfile.name_ar == name_ar)):
        raise HTTPException(409, "الوظيفة موجودة بالفعل")
    valid = set(db.scalars(select(Permission.permission_id).where(Permission.permission_id.in_(ids))).all()) if ids else set()
    if valid != set(ids):
        raise HTTPException(422, "توجد صلاحية غير صحيحة")
    p = JobProfile(name_ar=name_ar, name_en=name_en, description=(body.get("description") or "").strip() or None,
                   is_active=bool(body.get("is_active", True)))
    db.add(p); db.flush()
    for pid in sorted(valid):
        db.add(JobProfilePermission(job_profile_id=p.job_profile_id, permission_id=pid))
    write_audit(db, actor.user_id, "Create", "JobProfiles", p.job_profile_id,
                new={"name_ar": name_ar, "permission_ids": sorted(valid)})
    db.commit()
    return {"job_profile_id": p.job_profile_id}


@router.put("/job-profiles/{profile_id}")
def update_job_profile(profile_id: int, body: dict, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    p = db.get(JobProfile, profile_id)
    if p is None:
        raise HTTPException(404, "الوظيفة غير موجودة")
    name_ar = str(body.get("name_ar", p.name_ar) or "").strip()
    name_en = str(body.get("name_en", p.name_en) or "").strip()
    if not name_ar or not name_en or len(name_ar) > 150 or len(name_en) > 150:
        raise HTTPException(422, "اسم الوظيفة غير صحيح")
    if db.scalar(select(JobProfile).where(JobProfile.name_ar == name_ar, JobProfile.job_profile_id != profile_id)):
        raise HTTPException(409, "اسم الوظيفة مستخدم بالفعل")
    old = {"name_ar": p.name_ar, "name_en": p.name_en, "is_active": p.is_active,
           "permission_ids": sorted(db.scalars(select(JobProfilePermission.permission_id).where(
               JobProfilePermission.job_profile_id == profile_id)).all())}
    p.name_ar, p.name_en = name_ar, name_en
    if "description" in body:
        p.description = (body.get("description") or "").strip() or None
    if "is_active" in body:
        p.is_active = bool(body["is_active"])
    if "permission_ids" in body:
        ids = body["permission_ids"]
        if not isinstance(ids, list) or any(type(x) is not int for x in ids):
            raise HTTPException(422, "قائمة الصلاحيات غير صحيحة")
        valid = set(db.scalars(select(Permission.permission_id).where(Permission.permission_id.in_(ids))).all()) if ids else set()
        if valid != set(ids):
            raise HTTPException(422, "توجد صلاحية غير صحيحة")
        db.execute(delete(JobProfilePermission).where(JobProfilePermission.job_profile_id == profile_id))
        for pid in sorted(valid):
            db.add(JobProfilePermission(job_profile_id=profile_id, permission_id=pid))
    new_permissions = sorted(db.scalars(select(JobProfilePermission.permission_id).where(
        JobProfilePermission.job_profile_id == profile_id)).all())
    write_audit(db, actor.user_id, "Update", "JobProfiles", profile_id, old,
                {"name_ar": p.name_ar, "name_en": p.name_en, "is_active": p.is_active,
                 "permission_ids": new_permissions})
    db.commit()
    return {"ok": True}


@router.get("/projects")
def list_assignable_projects(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [{"project_id": p.project_id, "name_ar": p.name_ar, "is_active": p.is_active}
            for p in db.scalars(select(Project).order_by(Project.name_ar)).all()]


@router.get("/users")
def list_users(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.user_id)).all()
    out=[]
    for u in users:
        roles=db.scalars(select(Role.role_name).join(UserRole, UserRole.role_id==Role.role_id).where(UserRole.user_id==u.user_id)).all()
        out.append({"user_id":u.user_id,"username":u.username,"full_name":u.full_name,"is_active":u.is_active,
                    "avatar_updated_at":u.avatar_updated_at,
                    "failed_login_count":u.failed_login_count,"locked_until":u.locked_until,"roles":roles,
                    "role_ids":db.scalars(select(UserRole.role_id).where(UserRole.user_id==u.user_id)).all(),
                    "job_profile_id":u.job_profile_id,"project_id":u.project_id})
    return out

@router.post("/users", status_code=201)
def create_user(body: UserCreate, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username.strip())):
        raise HTTPException(409, "اسم المستخدم مستخدم بالفعل")
    roles=db.scalars(select(Role).where(Role.role_id.in_(body.role_ids))).all() if body.role_ids else []
    if len(roles) != len(set(body.role_ids)):
        raise HTTPException(422, "يوجد دور غير صحيح")
    if body.job_profile_id is not None:
        profile = db.get(JobProfile, body.job_profile_id)
        if profile is None or not profile.is_active:
            raise HTTPException(422, "الوظيفة غير موجودة أو غير نشطة")
        if roles:
            raise HTTPException(422, "لا يمكن الجمع بين الوظيفة وأدوار مستقلة")
    if body.project_id is not None and db.get(Project, body.project_id) is None:
        raise HTTPException(422, "المشروع أو الموقع غير موجود")
    if body.job_profile_id is not None and body.project_id is None:
        raise HTTPException(422, "يجب تحديد المشروع أو الموقع للموظف")
    u=User(username=body.username.strip(),full_name=body.full_name.strip(),password_hash=hash_password(body.password),
           is_active=body.is_active,job_profile_id=body.job_profile_id,project_id=body.project_id)
    db.add(u); db.flush()
    for r in roles: db.add(UserRole(user_id=u.user_id,role_id=r.role_id))
    write_audit(db, actor.user_id, "Create", "Users", u.user_id, new={"username":u.username,"roles":body.role_ids})
    db.commit(); return {"user_id":u.user_id,"username":u.username}

@router.patch("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"المستخدم غير موجود")
    if u.user_id == actor.user_id and body.is_active is False: raise HTTPException(400,"لا يمكنك تعطيل حسابك الحالي")
    if body.full_name is not None: u.full_name=body.full_name.strip()
    if body.is_active is not None:
        if u.is_active and not body.is_active: u.token_version += 1
        u.is_active=body.is_active
    if body.password: u.password_hash=hash_password(body.password); u.failed_login_count=0; u.locked_until=None
    if body.password: u.token_version += 1
    if body.job_profile_id is not None:
        profile = db.get(JobProfile, body.job_profile_id)
        if profile is None or not profile.is_active:
            raise HTTPException(422, "الوظيفة غير موجودة أو غير نشطة")
        if body.project_id is None and u.project_id is None:
            raise HTTPException(422, "يجب تحديد المشروع أو الموقع للموظف")
        if body.role_ids:
            raise HTTPException(422, "لا يمكن الجمع بين الوظيفة وأدوار مستقلة")
        u.job_profile_id = body.job_profile_id
        admin_role_ids = select(Role.role_id).where(Role.role_name == "Admin")
        db.execute(delete(UserRole).where(UserRole.user_id == u.user_id, UserRole.role_id.not_in(admin_role_ids)))
    if body.project_id is not None:
        if db.get(Project, body.project_id) is None:
            raise HTTPException(422, "المشروع أو الموقع غير موجود")
        u.project_id = body.project_id
    if body.role_ids is not None:
        if u.job_profile_id is not None and body.role_ids:
            raise HTTPException(422, "لا يمكن الجمع بين الوظيفة وأدوار مستقلة")
        roles=db.scalars(select(Role).where(Role.role_id.in_(body.role_ids))).all() if body.role_ids else []
        if len(roles)!=len(set(body.role_ids)): raise HTTPException(422,"يوجد دور غير صحيح")
        if u.user_id==actor.user_id and not any(r.role_name=="Admin" for r in roles): raise HTTPException(400,"لا يمكنك إزالة دور Admin من حسابك الحالي")
        db.execute(delete(UserRole).where(UserRole.user_id==u.user_id))
        for r in roles: db.add(UserRole(user_id=u.user_id,role_id=r.role_id))
    write_audit(db,actor.user_id,"Update","Users",u.user_id,new={"is_active":u.is_active})
    db.commit(); return {"ok":True}


def _image_type(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP": return "image/webp"
    return None


@router.get("/users/{user_id}/avatar")
def get_user_avatar(user_id: int, actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"المستخدم غير موجود")
    is_admin=db.scalar(select(UserRole.user_id).join(Role,Role.role_id==UserRole.role_id)
                       .where(UserRole.user_id==actor.user_id,Role.role_name=="Admin"))
    if actor.user_id != user_id and not is_admin: raise HTTPException(403,"لا يمكنك عرض صورة هذا المستخدم")
    avatar=db.get(UserAvatar,user_id)
    if not avatar: raise HTTPException(404,"لا توجد صورة لهذا المستخدم")
    return Response(content=avatar.image_data,media_type=avatar.media_type,
                    headers={"Cache-Control":"private, max-age=300"})


@router.post("/users/{user_id}/avatar")
async def save_user_avatar(user_id: int, file: UploadFile = File(...), actor: User = Depends(admin_user),
                           db: Session = Depends(get_db)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"المستخدم غير موجود")
    data=await file.read(3*1024*1024+1)
    if len(data)>3*1024*1024: raise HTTPException(413,"حجم الصورة يجب ألا يتجاوز 3 ميجابايت")
    media_type=_image_type(data)
    if not media_type: raise HTTPException(415,"الصيغ المدعومة: JPG وPNG وWebP")
    avatar=db.get(UserAvatar,user_id)
    if avatar is None:
        avatar=UserAvatar(user_id=user_id,image_data=data,media_type=media_type); db.add(avatar)
    else:
        avatar.image_data=data; avatar.media_type=media_type
    target.avatar_updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
    write_audit(db,actor.user_id,"Update","UserAvatar",user_id,new={"filename":file.filename,"media_type":media_type})
    db.commit()
    return {"ok":True,"avatar_updated_at":target.avatar_updated_at}


@router.delete("/users/{user_id}/avatar",status_code=204)
def delete_user_avatar(user_id: int, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    target=db.get(User,user_id)
    if not target: raise HTTPException(404,"المستخدم غير موجود")
    avatar=db.get(UserAvatar,user_id)
    if avatar: db.delete(avatar)
    target.avatar_updated_at=None
    write_audit(db,actor.user_id,"Delete","UserAvatar",user_id)
    db.commit()
    return Response(status_code=204)

@router.get("/roles")
def list_roles(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    roles=db.scalars(select(Role).order_by(Role.role_id)).all(); out=[]
    for r in roles:
        ids=db.scalars(select(RolePermission.permission_id).where(RolePermission.role_id==r.role_id)).all()
        out.append({"role_id":r.role_id,"role_name":r.role_name,"permission_ids":ids})
    return out

@router.get("/permissions")
def list_permissions(_: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows=db.execute(select(Permission,Screen,Section).join(Screen,Screen.screen_code==Permission.screen_code, isouter=True)
                    .join(Section,Section.section_id==Screen.section_id,isouter=True)
                    .order_by(Section.sort_order,Screen.sort_order,Permission.screen_code,Permission.action_code)).all()
    return [{"permission_id":p.permission_id,"screen_code":p.screen_code,"action_code":p.action_code,
             "screen_ar":s.title_ar if s else p.screen_code,"section_ar":sec.name_ar if sec else "أخرى"} for p,s,sec in rows]

@router.post("/roles", status_code=201)
def create_role(body: RoleCreate, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    name=body.role_name.strip()
    if name.casefold() == "admin": raise HTTPException(400, "اسم Admin محجوز لدور مدير النظام")
    if db.scalar(select(Role).where(Role.role_name==name)): raise HTTPException(409,"اسم الدور موجود بالفعل")
    ids=set(db.scalars(select(Permission.permission_id).where(Permission.permission_id.in_(body.permission_ids))).all()) if body.permission_ids else set()
    if ids != set(body.permission_ids): raise HTTPException(422,"قائمة الصلاحيات غير صحيحة")
    r=Role(role_name=name); db.add(r); db.flush()
    for pid in ids: db.add(RolePermission(role_id=r.role_id,permission_id=pid))
    write_audit(db,actor.user_id,"Create","Roles",r.role_id,new={"role_name":name,"permission_ids":sorted(ids)})
    db.commit(); return {"role_id":r.role_id}

@router.put("/roles/{role_id}")
def update_role(role_id: int, body: RoleUpdate, actor: User = Depends(admin_user), db: Session = Depends(get_db)):
    r=db.get(Role,role_id)
    if not r: raise HTTPException(404,"الدور غير موجود")
    if body.role_name is not None:
        name=body.role_name.strip()
        if name.casefold() == "admin" and r.role_name != "Admin": raise HTTPException(400, "اسم Admin محجوز لدور مدير النظام")
        other=db.scalar(select(Role).where(Role.role_name==name,Role.role_id!=role_id))
        if other: raise HTTPException(409,"اسم الدور موجود بالفعل")
        if r.role_name=="Admin" and name!="Admin": raise HTTPException(400,"لا يمكن تغيير اسم دور Admin")
        r.role_name=name
    if body.permission_ids is not None:
        ids=set(db.scalars(select(Permission.permission_id).where(Permission.permission_id.in_(body.permission_ids))).all()) if body.permission_ids else set()
        if ids != set(body.permission_ids): raise HTTPException(422,"قائمة الصلاحيات غير صحيحة")
        db.execute(delete(RolePermission).where(RolePermission.role_id==role_id))
        for pid in ids: db.add(RolePermission(role_id=role_id,permission_id=pid))
    write_audit(db,actor.user_id,"Update","Roles",r.role_id,new={"role_name":r.role_name})
    db.commit(); return {"ok":True}
