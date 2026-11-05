"""بيعمل ملف .env من .env.example ويولّد JWT_SECRET عشوائي (لو .env مش موجود)."""
import re
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent
env, example = root / ".env", root / ".env.example"
if not env.exists():
    text = example.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^JWT_SECRET=.*$", "JWT_SECRET=" + secrets.token_urlsafe(48), text)
    env.write_text(text, encoding="utf-8")
    print(".env created")
