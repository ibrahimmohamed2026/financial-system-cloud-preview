"""تفقيط المبالغ بالعربية (جنيه مصري وقرش) — مثال: «خمسون جنيهًا وخمسة وعشرون قرشًا فقط لا غير»."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MAX_AMOUNT = Decimal("999999999999.99")

_ONES = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
_TEENS = {10: "عشرة", 11: "أحد عشر", 12: "اثنا عشر", 13: "ثلاثة عشر", 14: "أربعة عشر",
          15: "خمسة عشر", 16: "ستة عشر", 17: "سبعة عشر", 18: "ثمانية عشر", 19: "تسعة عشر"}
_TENS = {2: "عشرون", 3: "ثلاثون", 4: "أربعون", 5: "خمسون", 6: "ستون", 7: "سبعون", 8: "ثمانون", 9: "تسعون"}
_HUNDREDS = {1: "مائة", 2: "مائتان", 3: "ثلاثمائة", 4: "أربعمائة", 5: "خمسمائة",
             6: "ستمائة", 7: "سبعمائة", 8: "ثمانمائة", 9: "تسعمائة"}
# (القيمة، مفرد، مثنى، جمع 3-10، تمييز منصوب 11-99)
_SCALES = [(10**9, "مليار", "ملياران", "مليارات", "مليارًا"),
           (10**6, "مليون", "مليونان", "ملايين", "مليونًا"),
           (10**3, "ألف", "ألفان", "آلاف", "ألفًا")]


def _below_100(n: int) -> str:
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n]
    t, o = divmod(n, 10)
    return (_ONES[o] + " و" if o else "") + _TENS[t]


def _below_1000(n: int) -> str:
    h, r = divmod(n, 100)
    parts = []
    if h:
        parts.append(_HUNDREDS[h])
    if r:
        parts.append(_below_100(r))
    return " و".join(parts)


def _spell(n: int) -> str:
    """رقم صحيح موجب بالحروف (بدون المعدود)."""
    if n == 0:
        return "صفر"
    parts = []
    for value, one, two, plural, acc in _SCALES:
        g, n = divmod(n, value)
        if not g:
            continue
        if g == 1:
            parts.append(one)
        elif g == 2:
            parts.append(two)
        else:
            r = g % 100
            if 3 <= r <= 10:
                parts.append(f"{_below_1000(g)} {plural}")
            elif 11 <= r <= 99:
                parts.append(f"{_below_1000(g)} {acc}")
            else:
                w = _below_1000(g)
                if w.endswith("مائتان"):  # مائتا ألف
                    w = w[:-1]
                parts.append(f"{w} {one}")
    if n:
        parts.append(_below_1000(n))
    return " و".join(parts)


def _counted(n: int, one: str, two: str, plural: str, acc: str) -> str:
    """العدد مع المعدود وفق قواعد العربية: جنيه واحد / جنيهان / ثلاثة جنيهات / أحد عشر جنيهًا / مائة جنيه."""
    r = n % 100
    if r == 1:
        return f"{_spell(n - 1)} و{one} واحد" if n > 1 else f"{one} واحد"
    if r == 2:
        return f"{_spell(n - 2)} و{two}" if n > 2 else two
    if 3 <= r <= 10:
        return f"{_spell(n)} {plural}"
    if 11 <= r <= 99:
        return f"{_spell(n)} {acc}"
    # مضاعفات المئة/الألف/المليون: المعدود يلي آخر كلمة مباشرة، فتتغير صيغتها (مائتا جنيه، ألفا جنيه، أحد عشر ألف جنيه)
    s = _spell(n)
    if s.endswith(("مائتان", "ألفان", "مليونان", "ملياران")):
        s = s[:-1]
    elif s.endswith(("ألفًا", "مليونًا", "مليارًا")):
        s = s[:-2]
    return f"{s} {one}"


# العملات المدعومة: (وحدة: مفرد، مثنى، جمع، تمييز) ، (كسر: مفرد، مثنى، جمع، تمييز)
CURRENCIES = {
    "EGP": (("جنيه", "جنيهان", "جنيهات", "جنيهًا"), ("قرش", "قرشان", "قروش", "قرشًا")),
    "USD": (("دولار", "دولاران", "دولارات", "دولارًا"), ("سنت", "سنتان", "سنتات", "سنتًا")),
}


def amount_in_words(amount, currency: str = "EGP") -> str:
    """يحوّل مبلغًا (Decimal/رقم/نص) إلى تفقيط عربي (الافتراضي جنيه وقرش). يرفع ValueError لمبلغ أو عملة غير مدعومة."""
    units = CURRENCIES.get((currency or "EGP").upper())
    if units is None:
        raise ValueError("العملة غير مدعومة في التفقيط")
    major, minor = units
    try:
        d = Decimal(str(amount).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("المبلغ غير صالح")
    if not d.is_finite() or d < 0:
        raise ValueError("المبلغ لازم يكون رقم موجب")
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d > MAX_AMOUNT:
        raise ValueError("المبلغ أكبر من الحد المدعوم")
    pounds, piasters = int(d), int((d - int(d)) * 100)
    parts = []
    if pounds or not piasters:
        parts.append(_counted(pounds, *major) if pounds else f"صفر {major[0]}")
    if piasters:
        parts.append(_counted(piasters, *minor))
    return " و".join(parts) + " فقط لا غير"
