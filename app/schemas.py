from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ----------------------------- Auth -----------------------------
class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class LanguagePreferenceIn(BaseModel):
    language: Literal["ar", "en"]


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: str
    full_name: str
    preferred_language: str = "ar"
    avatar_updated_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class PermissionOut(BaseModel):
    screen: str
    action: str


class MeOut(UserOut):
    permissions: list[PermissionOut]


# ----------------------------- Dashboard -----------------------------
class ScreenCard(BaseModel):
    screen_id: int
    code: str
    title_en: str
    title_ar: str | None
    route: str


class SectionCard(BaseModel):
    section_id: int
    code: str
    name_en: str
    name_ar: str | None
    letter: str
    screens_count: int
    screens: list[ScreenCard]


class DashboardOut(BaseModel):
    sections_count: int  # عدد الأقسام المتاحة للمستخدم (قبل البحث)
    screens_count: int   # عدد الشاشات المتاحة للمستخدم (قبل البحث)
    sections: list[SectionCard]


# ----------------------------- Chart of accounts -----------------------------
Money = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)


class ClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    classification_id: int
    name_ar: str
    statement_type: str


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    account_code: str = Field(min_length=1, max_length=30)
    account_name_ar: str = Field(min_length=1, max_length=300)
    parent_account_id: int | None = None
    classification_id: int
    normal_balance: Literal["DR", "CR"]
    opening_debit: Decimal = Money
    opening_credit: Decimal = Money
    is_active: bool = True

    @model_validator(mode="after")
    def _one_sided_opening(self):
        if self.opening_debit > 0 and self.opening_credit > 0:
            raise ValueError("الرصيد الافتتاحي إما مدين أو دائن، مش الاتنين")
        return self


class AccountUpdate(BaseModel):
    """كل الحقول اختيارية — اللي يتبعت بس هو اللي يتغيّر. parent_account_id=null يعني نقل للجذر."""
    model_config = ConfigDict(str_strip_whitespace=True)
    account_code: str | None = Field(default=None, min_length=1, max_length=30)
    account_name_ar: str | None = Field(default=None, min_length=1, max_length=300)
    parent_account_id: int | None = None
    classification_id: int | None = None
    normal_balance: Literal["DR", "CR"] | None = None
    opening_debit: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    opening_credit: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    is_active: bool | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    account_id: int
    account_code: str
    account_name_ar: str
    parent_account_id: int | None
    classification_id: int
    normal_balance: str
    opening_debit: Decimal
    opening_credit: Decimal
    is_active: bool
    created_at: datetime


class AccountDetail(AccountOut):
    children_count: int
    journal_lines_count: int
    can_delete: bool
    blockers: list[str]


class AccountList(BaseModel):
    total: int
    items: list[AccountOut]


class AccountNode(AccountOut):
    children: list["AccountNode"] = []


# ----------------------------- Excel import -----------------------------
class ImportRowError(BaseModel):
    row: int
    field: str | None = None
    message: str


class ImportPreviewRow(BaseModel):
    row: int
    account_code: str
    account_name_ar: str
    parent_code: str | None = None


class ImportReport(BaseModel):
    dry_run: bool
    total_rows: int
    valid_rows: int
    skipped_existing: int
    created: int
    errors: list[ImportRowError]
    preview: list[ImportPreviewRow]
