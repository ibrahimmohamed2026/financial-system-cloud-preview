"""طباعة PDF عربي (RTL) لشجرة الحسابات — reportlab + arabic-reshaper + python-bidi."""
import os
import re
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

_AR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")


class PdfSetupError(RuntimeError):
    """نقص في إعداد الطباعة (خط عربي أو مكتبات التشكيل)."""


def _font_candidates() -> list[tuple[str, str]]:
    win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    return [
        (os.path.join(win, "tahoma.ttf"), os.path.join(win, "tahomabd.ttf")),
        (os.path.join(win, "arial.ttf"), os.path.join(win, "arialbd.ttf")),
        (os.path.join(win, "segoeui.ttf"), os.path.join(win, "segoeuib.ttf")),
        ("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
         "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
    ]


@lru_cache(maxsize=8)
def _fonts(font_path: str | None, bold_path: str | None) -> tuple[str, str]:
    if font_path:
        if not os.path.isfile(font_path):
            raise PdfSetupError(f"ملف الخط مش موجود: {font_path}")
        reg, bold = font_path, (bold_path if bold_path and os.path.isfile(bold_path) else font_path)
    else:
        for r, b in _font_candidates():
            if os.path.isfile(r):
                reg, bold = r, (b if os.path.isfile(b) else r)
                break
        else:
            raise PdfSetupError("مفيش خط عربي متاح — حدد مسار ملف .ttf في PDF_FONT_PATH داخل .env")
    pdfmetrics.registerFont(TTFont("AppFont", reg))
    pdfmetrics.registerFont(TTFont("AppFont-Bold", bold))
    return "AppFont", "AppFont-Bold"


def _shape(text: str) -> str:
    if not text or not _AR_RE.search(text):
        return text
    try:
        import arabic_reshaper
        try:
            from bidi import get_display
        except ImportError:  # الإصدارات القديمة من python-bidi
            from bidi.algorithm import get_display
    except ImportError as exc:
        raise PdfSetupError("لازم تسطّب arabic-reshaper و python-bidi (pip install -r requirements.txt)") from exc
    return get_display(arabic_reshaper.reshape(text))


def _fit(text: str, font: str, size: float, max_width: float) -> str:
    """بيقص النص (قبل التشكيل) لحد ما يناسب عرض العمود، وبيضيف …"""
    shaped = _shape(text)
    if pdfmetrics.stringWidth(shaped, font, size) <= max_width:
        return shaped
    cut = text
    while len(cut) > 1:
        cut = cut[:-1]
        shaped = _shape(cut.rstrip() + "…")
        if pdfmetrics.stringWidth(shaped, font, size) <= max_width:
            return shaped
    return _shape("…")


def _money(value: Decimal | None) -> str:
    return "-" if not value else f"{value:,.2f}"


def build_accounts_pdf(
    rows: list[dict],
    *,
    title: str = "شجرة الحسابات",
    filters_text: str = "",
    printed_by: str = "",
    font_path: str | None = None,
    bold_font_path: str | None = None,
) -> bytes:
    """rows: dict(code, name, level, is_parent, classification, normal_balance, debit, credit, is_active)."""
    reg, bold = _fonts(font_path, bold_font_path)
    page = landscape(A4)
    margin = 1.2 * cm
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # الأعمدة من الشمال لليمين (RTL: العمود الأول المنطقي «الكود» هو الأيمن)
    logical_headers = ["الكود", "اسم الحساب", "التصنيف", "الطبيعة", "مدين افتتاحي", "دائن افتتاحي", "الحالة"]
    widths = [2.0, 3.2, 3.2, 2.2, 5.0, 8.5, 3.2]  # بالسنتي، بترتيب العرض من الشمال
    widths = [w * cm for w in widths]
    NAME_COL = 5
    size = 8.5

    header = [_shape(h) for h in reversed(logical_headers)]
    data = [header]
    styles = [
        ("FONTNAME", (0, 0), (-1, -1), reg),
        ("FONTSIZE", (0, 0), (-1, -1), size),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A68")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (2, -1), "RIGHT"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (6, -1), "RIGHT"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#D5D9E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]

    total_debit = total_credit = Decimal("0")
    for i, r in enumerate(rows, start=1):
        level = min(int(r.get("level", 0)), 6)
        pad = 6 + level * 12
        font = bold if r.get("is_parent") else reg
        cells = [
            _shape("نشط" if r["is_active"] else "موقوف"),
            _fit(_money(r["credit"]), font, size, widths[1] - 12),
            _fit(_money(r["debit"]), font, size, widths[2] - 12),
            _shape("مدين" if r["normal_balance"] == "DR" else "دائن"),
            _fit(r["classification"] or "", font, size, widths[4] - 12),
            _fit(r["name"], font, size, widths[NAME_COL] - pad - 6),
            _fit(str(r["code"]), font, size, widths[6] - 12),
        ]
        data.append(cells)
        styles.append(("RIGHTPADDING", (NAME_COL, i), (NAME_COL, i), pad))
        if r.get("is_parent"):
            styles.append(("FONTNAME", (0, i), (-1, i), bold))
            styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#EEF2F8")))
        if not r["is_active"]:
            styles.append(("TEXTCOLOR", (0, i), (-1, i), colors.HexColor("#8A8F98")))
        total_debit += r["debit"] or 0
        total_credit += r["credit"] or 0

    if not rows:
        data.append(["", "", "", "", "", _shape("لا توجد حسابات مطابقة"), ""])
        styles.append(("ALIGN", (NAME_COL, 1), (NAME_COL, 1), "RIGHT"))
    else:
        n = len(data)
        data.append(["", _money(total_credit), _money(total_debit), "", "", _shape("الإجمالي"), ""])
        styles += [
            ("FONTNAME", (0, n), (-1, n), bold),
            ("LINEABOVE", (0, n), (-1, n), 1, colors.HexColor("#1F3A68")),
            ("BACKGROUND", (0, n), (-1, n), colors.HexColor("#F4F6FA")),
            ("ALIGN", (1, n), (2, n), "RIGHT"),
            ("ALIGN", (NAME_COL, n), (NAME_COL, n), "RIGHT"),
        ]

    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle(styles))

    def decorate(canvas, doc):
        w, h = page
        canvas.saveState()
        canvas.setFont(bold, 15)
        canvas.drawRightString(w - margin, h - 1.3 * cm, _shape(title))
        canvas.setFont(reg, 9)
        if filters_text:
            canvas.drawRightString(w - margin, h - 1.9 * cm, _shape(filters_text))
        canvas.drawString(margin, h - 1.3 * cm, now)
        canvas.setStrokeColor(colors.HexColor("#1F3A68"))
        canvas.setLineWidth(0.8)
        canvas.line(margin, h - 2.2 * cm, w - margin, h - 2.2 * cm)
        canvas.setFont(reg, 8.5)
        canvas.drawCentredString(w / 2, 0.8 * cm, _shape(f"صفحة {doc.page}"))
        if printed_by:
            canvas.drawRightString(w - margin, 0.8 * cm, _shape(f"طُبع بواسطة: {printed_by}"))
        canvas.restoreState()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=page, leftMargin=margin, rightMargin=margin, topMargin=2.6 * cm, bottomMargin=1.6 * cm,
        title=title, author=printed_by or "Financial System",
    )
    doc.build([table], onFirstPage=decorate, onLaterPages=decorate)
    return buf.getvalue()
