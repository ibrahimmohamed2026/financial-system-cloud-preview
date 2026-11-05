"""Interactive wrapper to initialize SQLite without fragile BAT variable expansion."""
import sys
from datetime import date

def main():
    username = input("Admin username [admin]: ").strip() or "admin"
    year_text = input(f"First fiscal year [{date.today().year}]: ").strip() or str(date.today().year)
    try:
        year = int(year_text)
        if year < 1900 or year > 2200:
            raise ValueError
    except ValueError:
        print("ERROR: Enter a valid year, e.g. 2026.")
        return 2
    sys.argv = ["init_sqlite_db.py", "--username", username, "--year", str(year)]
    import init_sqlite_db
    init_sqlite_db.main()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
