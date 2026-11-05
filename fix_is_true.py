"""Replace  X.is_(True) / X.is_(False) / X.is_(is_active)  with  X == True / == False / == is_active  in app/**/*.py
(is_(None) / is_not(None) are left alone: they are correct, they become IS NULL).

SQL Server has no 'IS 1' syntax; '== True' is rendered as '= 1' there (and as
'= true' / 'IS true' where the database has real booleans), so it works everywhere.

Usage:  python fix_is_true.py "<path to the financial_system folder>"
Run it once on your source project, and once on the installed copy if you like.
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
pattern = re.compile(r"\.is_\((True|False|is_active)\)")
changed = 0
for f in sorted((root / "app").rglob("*.py")):
    text = f.read_text(encoding="utf-8")
    new, n = pattern.subn(lambda m: f" == {m.group(1)}", text)
    if n:
        f.write_text(new, encoding="utf-8")
        print(f"{f.relative_to(root)}: {n} replaced")
        changed += n
print("total replaced:", changed)
