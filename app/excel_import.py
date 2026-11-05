"""قراءة والتحقق من ملف Excel لاستيراد شجرة الحسابات — منطق نقي (من غير داتا بيز أو FastAPI)."""
import io
import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

MAX_ROWS = 5000
MAX_AMOUNT = Decimal("9999999999999999.99")  # DECIMAL(18,2)

FIELDS = ["account_code", "account_name_ar", "parent_code", "classification",
          "normal_balance", "opening_debit", "opening_credit"]

TEMPLATE_HEADERS = ["كود الحساب", "اسم الحساب", "كود الحساب الأب", "التصنيف",
                    "طبيعة الرصيد", "رصيد افتتاحي مدين", "رصيد افتتاحي دائن"]

_AR_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ـ": ""})
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")


def norm(value) -> str:
    """تطبيع للمقارنة: حروف صغيرة، توحيد الألف/الياء/التاء المربوطة، حذف المسافات والرموز."""
    s = str(value).strip().lower().translate(_AR_MAP)
    return re.sub(r"[\s_\-\.]+", "", s)


_ALIASES_RAW = {
    "account_code": ["account_code", "code", "كود الحساب", "الكود", "رقم الحساب", "كود", "رمز الحساب"],
    "account_name_ar": ["account_name_ar", "account_name", "name", "اسم الحساب", "الاسم", "اسم الحساب بالعربي"],
    "parent_code": ["parent_code", "parent", "كود الحساب الأب", "كود الأب", "الحساب الأب", "الأب"],
    "classification": ["classification", "التصنيف", "تصنيف الحساب", "تبويب القوائم المالية"],
    "normal_balance": ["normal_balance", "طبيعة الرصيد", "الطبيعة", "طبيعة الحساب"],
    "opening_debit": ["opening_debit", "رصيد افتتاحي مدين", "افتتاحي مدين", "مدين افتتاحي", "مدين", "openning dr", "opening dr"],
    "opening_credit": ["opening_credit", "رصيد افتتاحي دائن", "افتتاحي دائن", "دائن افتتاحي", "دائن", "openning cr", "opening cr"],
}
ALIASES = {norm(a): f for f, lst in _ALIASES_RAW.items() for a in lst}

_DR = {norm(x) for x in ("DR", "debit", "مدين", "م", "D")}
_CR = {norm(x) for x in ("CR", "credit", "دائن", "د", "C")}

def infer_normal_balance(classification_name: str) -> str | None:
    """استنتاج الطبيعة من اسم تبويب القوائم؛ لا نخمن عند عدم وضوح التصنيف."""
    value = norm(classification_name)
    credit_terms = (
        "خصوم", "التزامات", "حقوق الملكيه", "راس المال", "رأس المال",
        "ايرادات", "إيرادات", "دخل", "مبيعات", "دائنون", "موردون",
        "ارصده دائنه", "ارصدة دائنة",
    )
    debit_terms = (
        "اصول", "أصول", "مصروفات", "مصروف", "تكلفه", "تكلفة",
        "مشتريات", "مدينون", "عملاء", "مخزون", "نقديه", "نقدية",
    )
    if any(norm(term) in value for term in credit_terms):
        return "CR"
    if any(norm(term) in value for term in debit_terms):
        return "DR"
    return None



class ImportFileError(ValueError):
    """ملف مش سليم (مش xlsx / مفيش عناوين / كبير أوي)."""


@dataclass
class ExistingAccount:
    account_id: int
    is_active: bool
    has_lines: bool


@dataclass
class ParsedAccount:
    row: int
    code: str
    name: str
    parent_code: str | None
    classification_id: int
    normal_balance: str
    opening_debit: Decimal
    opening_credit: Decimal


@dataclass
class RowError:
    row: int
    field: str | None
    message: str


@dataclass
class ImportPlan:
    total_rows: int = 0
    skipped_existing: int = 0
    items: list[ParsedAccount] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


# ----------------------------- قراءة الملف -----------------------------
def read_rows(data: bytes) -> list[tuple[int, dict]]:
    """بيرجّع [(رقم الصف في الإكسيل، {field: القيمة الخام})] من أول شيت."""
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # zip تالف / مش xlsx
        raise ImportFileError("الملف مش Excel (.xlsx) سليم") from exc
    try:
        # Prefer the workbook's account-balance sheet when the original finance workbook is supplied.
        ws = wb["Trial balance"] if "Trial balance" in wb.sheetnames else wb.worksheets[0]
        header: dict[int, str] | None = None
        rows: list[tuple[int, dict]] = []
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if header is None:
                if idx > 15:
                    break
                found: dict[int, str] = {}
                for col, cell in enumerate(row):
                    f = ALIASES.get(norm(cell)) if cell is not None else None
                    if f and f not in found.values():
                        found[col] = f
                if {"account_code", "account_name_ar"} <= set(found.values()):
                    header = found
                continue
            values = {f: (row[col] if col < len(row) else None) for col, f in header.items()}
            if all(v is None or (isinstance(v, str) and not v.strip()) for v in values.values()):
                continue
            if len(rows) >= MAX_ROWS:
                raise ImportFileError(f"الملف فيه أكتر من {MAX_ROWS} صف — قسّمه على أكتر من ملف")
            rows.append((idx, values))
        if header is None:
            raise ImportFileError("مش لاقي صف العناوين: لازم يبقى فيه عمودي «كود الحساب» و«اسم الحساب»")
        return rows
    finally:
        wb.close()


# ----------------------------- تحويل القيم -----------------------------
def to_text(v) -> str:
    return "" if v is None else str(v).strip()


def to_code(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():  # Excel بيخزّن 1101 كـ 1101.0
        return str(int(v))
    return str(v).strip()


def to_decimal(v) -> Decimal:
    if v is None or (isinstance(v, str) and not v.strip()):
        return Decimal("0.00")
    if isinstance(v, bool):
        raise ValueError("قيمة غير رقمية")
    try:
        if isinstance(v, (int, float, Decimal)):
            d = Decimal(str(v))
        else:
            d = Decimal(str(v).strip().translate(_AR_DIGITS).replace(",", "").replace(" ", ""))
    except Exception as exc:
        raise ValueError("قيمة غير رقمية") from exc
    if not d.is_finite():
        raise ValueError("قيمة غير رقمية")
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d < 0:
        raise ValueError("الرصيد مينفعش يبقى سالب")
    if d > MAX_AMOUNT:
        raise ValueError("الرقم كبير أوي")
    return d


# ----------------------------- التحقق -----------------------------
def parse_rows(
    rows: list[tuple[int, dict]],
    classifications: dict[str, int],
    existing: dict[str, ExistingAccount],
    skip_existing: bool = False,
    update_existing: bool = False,
) -> ImportPlan:
    """classifications: norm(اسم التصنيف) → id.  existing: code.casefold() → ExistingAccount."""
    plan = ImportPlan(total_rows=len(rows))
    err = plan.errors
    seen: dict[str, int] = {}  # code.casefold() → أول صف
    file_codes = [to_code(raw.get("account_code")) for _, raw in rows]
    all_codes = set(existing) | {code.casefold() for code in file_codes if code}
    
    def infer_parent(code: str) -> str | None:
        key = code.casefold()
        candidates = [candidate for candidate in all_codes
                      if candidate != key and len(candidate) < len(key) and key.startswith(candidate)]
        return max(candidates, key=len) if candidates else None

    for rownum, raw in rows:
        before = len(err)
        code = to_code(raw.get("account_code"))
        name = to_text(raw.get("account_name_ar"))
        key = code.casefold()

        if not code:
            err.append(RowError(rownum, "account_code", "كود الحساب فاضي"))
        elif len(code) > 30:
            err.append(RowError(rownum, "account_code", "كود الحساب أطول من 30 حرف"))
        if not name:
            err.append(RowError(rownum, "account_name_ar", "اسم الحساب فاضي"))
        elif len(name) > 300:
            err.append(RowError(rownum, "account_name_ar", "اسم الحساب أطول من 300 حرف"))

        if code:
            if key in seen:
                err.append(RowError(rownum, "account_code", f"الكود مكرر (ظهر قبل كده في صف {seen[key]})"))
            else:
                seen[key] = rownum
                if key in existing:
                    # الاستيراد مخصص للإضافة فقط: الحساب الموجود لا يُعدّل ولا يُستبدل.
                    plan.skipped_existing += 1
                    continue

        parent_code = to_code(raw.get("parent_code")) or infer_parent(code)
        if parent_code and parent_code.casefold() == key:
            err.append(RowError(rownum, "parent_code", "الحساب مينفعش يبقى أب لنفسه"))

        cls_name = to_text(raw.get("classification"))
        cls_id = None
        if not cls_name:
            err.append(RowError(rownum, "classification", "التصنيف فاضي"))
        else:
            cls_id = classifications.get(norm(cls_name))
            if cls_id is None:
                err.append(RowError(rownum, "classification", f"التصنيف «{cls_name}» مش موجود في النظام"))

        nb_raw = to_text(raw.get("normal_balance"))
        nb = ("DR" if norm(nb_raw) in _DR else "CR" if norm(nb_raw) in _CR
              else infer_normal_balance(cls_name))
        if nb is None:
            err.append(RowError(rownum, "normal_balance",
                                f"مش قادر أحدد طبيعة الحساب من التصنيف «{cls_name}»؛ راجع اسم التصنيف أو حدّد الطبيعة في الملف."))

        # سياسة هذا الاستيراد: كل الحسابات تبدأ بصفر، ونتجاهل أعمدة الأرصدة والحركات تمامًا.
        opening_debit = Decimal("0.00")
        opening_credit = Decimal("0.00")

        if len(err) == before and code:
            plan.items.append(ParsedAccount(
                row=rownum, code=code, name=name, parent_code=parent_code, classification_id=cls_id,
                normal_balance=nb, opening_debit=opening_debit, opening_credit=opening_credit))

    _check_parents(plan, seen, existing)
    plan.errors.sort(key=lambda e: e.row)
    return plan


def _check_parents(plan: ImportPlan, seen: dict[str, int], existing: dict[str, ExistingAccount]) -> None:
    new_codes = {i.code.casefold() for i in plan.items}
    pmap: dict[str, str] = {}
    bad_rows: set[int] = set()

    for item in plan.items:
        if not item.parent_code:
            continue
        pkey = item.parent_code.casefold()
        if pkey == item.code.casefold():
            continue  # اتبلّغ عنه فوق
        if pkey in new_codes:
            pmap[item.code.casefold()] = pkey
        elif pkey in existing:
            info = existing[pkey]
            if not info.is_active:
                plan.errors.append(RowError(item.row, "parent_code", f"الحساب الأب «{item.parent_code}» غير نشط"))
                bad_rows.add(item.row)
            elif info.has_lines:
                plan.errors.append(RowError(
                    item.row, "parent_code", f"الحساب الأب «{item.parent_code}» عليه حركات — مينفعش يبقى حساب رئيسي"))
                bad_rows.add(item.row)
        elif pkey in seen:
            continue  # صف الأب نفسه فيه خطأ واتبلّغ عنه
        else:
            plan.errors.append(RowError(
                item.row, "parent_code", f"كود الأب «{item.parent_code}» مش موجود لا في الملف ولا في النظام"))
            bad_rows.add(item.row)

    def in_cycle(code: str) -> bool:
        visited: set[str] = set()
        cur = code
        while cur in pmap:
            if cur in visited:
                return True
            visited.add(cur)
            cur = pmap[cur]
        return False

    for item in plan.items:
        if item.code.casefold() in pmap and in_cycle(item.code.casefold()):
            plan.errors.append(RowError(item.row, "parent_code", "الحساب داخل حلقة في تسلسل الحسابات الأب"))
            bad_rows.add(item.row)


# ----------------------------- القالب -----------------------------
def build_template(classification_names: list[str]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "الحسابات"
    ws.sheet_view.rightToLeft = True
    ws.append(["رمز الحساب", "اسم الحساب", "تبويب القوائم المالية"])
    first_cls = classification_names[0] if classification_names else "أصول متداولة"
    ws.append(["1", "الأصول", first_cls])

    head_fill = PatternFill("solid", fgColor="1F3A68")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for col, width in zip("ABC", (22, 45, 38)):
        ws.column_dimensions[col].width = width
    for row in range(2, 1002):
        ws.cell(row=row, column=1).number_format = "@"
    ws.freeze_panes = "A2"

    cls_ws = wb.create_sheet("التصنيفات")
    cls_ws.sheet_view.rightToLeft = True
    cls_ws.append(["التصنيفات المتاحة (انسخ الاسم زي ما هو)"])
    cls_ws["A1"].font = Font(bold=True)
    for name in classification_names:
        cls_ws.append([name])
    cls_ws.column_dimensions["A"].width = 45
    if classification_names:
        dv2 = DataValidation(type="list", formula1=f"='التصنيفات'!$A$2:$A${len(classification_names) + 1}")
        dv2.add("D2:D1001")
        ws.add_data_validation(dv2)

    info = wb.create_sheet("تعليمات")
    info.sheet_view.rightToLeft = True
    for line in (
        "الأعمدة المطلوبة فقط: رمز الحساب، اسم الحساب، تبويب القوائم المالية.",
        "النظام يحدد الحساب الأب تلقائيًا من أطول كود حساب أقصر يبدأ به كود الحساب.",
        "طبيعة الحساب تُستنتج من اسم تبويب القوائم المالية؛ أي تصنيف غير واضح يظهر كخطأ للمراجعة.",
        "كل الحسابات الجديدة تُضاف بأرصدة افتتاحية صفرية.",
        "الحسابات الموجودة بنفس الكود يتم تخطيها دون تعديل أي بيانات.",
        "أعمدة الأرصدة والحركات والإجماليات في ملفك الأصلي يتم تجاهلها.",
        "الاستيراد كله أو لا شيء: لو في خطأ في أي صف مفيش حاجة بتتحفظ.",
    ):
        info.append([line])
    info.column_dimensions["A"].width = 90

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
