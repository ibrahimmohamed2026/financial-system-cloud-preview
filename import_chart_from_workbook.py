"""Import account classifications and chart from the original workbook.

Safe by default: previews only. Use --apply to write. Existing account codes are never overwritten.
Usage: python import_chart_from_workbook.py "path\\ميزانيه فارغه.xlsx" [--apply]
"""
import argparse
from collections import OrderedDict, Counter
from decimal import Decimal
from pathlib import Path
import openpyxl
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Account, AccountClassification


def txt(v):
    return str(v).strip() if v is not None else ""

def dec(v):
    try: return Decimal(str(v or 0)).quantize(Decimal('0.01'))
    except Exception: return Decimal('0.00')

def main():
    p=argparse.ArgumentParser(); p.add_argument('workbook',type=Path); p.add_argument('--apply',action='store_true'); a=p.parse_args()
    wb=openpyxl.load_workbook(a.workbook,read_only=True,data_only=True)
    if 'Trial balance' not in wb.sheetnames:
        raise SystemExit('لم أجد شيت Trial balance في ملف Excel.')
    ws=wb['Trial balance']; records=[]
    for rownum,row in enumerate(ws.iter_rows(min_row=3,values_only=True),start=3):
        code=txt(row[0] if len(row)>0 else None); name=txt(row[1] if len(row)>1 else None); cls=txt(row[2] if len(row)>2 else None)
        if not code or not name or not cls: continue
        # Keep account codes as text so leading zeroes are not lost after reading.
        debit=dec(row[3] if len(row)>3 else 0); credit=dec(row[4] if len(row)>4 else 0)
        records.append({'row':rownum,'code':code,'name':name,'class':cls,'debit':debit,'credit':credit})
    wb.close()
    # Resolve statement type from the workbook's trial balance sheet when possible.
    statement_votes={}
    try:
        wb2=openpyxl.load_workbook(a.workbook,read_only=True,data_only=True); ws2=wb2['ميزان مراجعة']
        for row in ws2.iter_rows(min_row=5,values_only=True):
            cls=txt(row[2] if len(row)>2 else None); statement=txt(row[3] if len(row)>3 else None)
            if cls and statement:
                statement_votes.setdefault(cls, Counter())['IncomeStatement' if 'دخل' in statement else 'BalanceSheet'] += 1
        wb2.close()
    except Exception: pass
    statement_by_class={name: votes.most_common(1)[0][0] for name,votes in statement_votes.items() if votes}
    with SessionLocal() as db:
        existing_classes={c.name_ar:c for c in db.scalars(select(AccountClassification)).all()}
        existing_accounts={x.account_code:x for x in db.scalars(select(Account)).all()}
        classes=list(OrderedDict((r['class'],None) for r in records))
        new_classes=[c for c in classes if c not in existing_classes]
        new_accounts=[r for r in records if r['code'] not in existing_accounts]
        print(f'الحسابات المقروءة من الملف: {len(records)}')
        print(f'التصنيفات الموجودة: {len(classes)} | تصنيفات جديدة: {len(new_classes)}')
        print(f'حسابات موجودة بالفعل (لن تُستبدل): {len(records)-len(new_accounts)} | حسابات جديدة: {len(new_accounts)}')
        if not a.apply:
            print('وضع المعاينة فقط: لم يتم حفظ أي تغيير. أضف --apply للتنفيذ بعد أخذ نسخة احتياطية.')
            return
        # Create classifications first.
        for name in new_classes:
            db.add(AccountClassification(name_ar=name,statement_type=statement_by_class.get(name,'BalanceSheet')))
        db.flush()
        class_ids={c.name_ar:c.classification_id for c in db.scalars(select(AccountClassification)).all()}
        # Determine parents only when a strict code prefix is an account in this import set.
        all_codes={r['code'] for r in records} | set(existing_accounts)
        for r in records:
            if r['code'] in existing_accounts: continue
            parent_code=None
            for n in range(len(r['code'])-1,0,-1):
                if r['code'][:n] in all_codes:
                    parent_code=r['code'][:n]; break
            parent=existing_accounts.get(parent_code) if parent_code else None
            # A parent created earlier in this import is tracked as rows are processed; second pass below fixes hierarchy.
            balance='CR' if r['credit']>r['debit'] else 'DR'
            db.add(Account(account_code=r['code'],account_name_ar=r['name'],classification_id=class_ids[r['class']],
                parent_account_id=parent.account_id if parent else None,normal_balance=balance,
                opening_debit=r['debit'],opening_credit=r['credit'],is_active=True))
        db.flush()
        # Resolve parents after all new accounts have IDs, preserving full codes as strings.
        by_code={x.account_code:x for x in db.scalars(select(Account)).all()}
        for r in records:
            acc=by_code.get(r['code'])
            if acc is None or acc.parent_account_id is not None: continue
            for n in range(len(r['code'])-1,0,-1):
                parent=by_code.get(r['code'][:n])
                if parent and parent.account_id != acc.account_id:
                    acc.parent_account_id=parent.account_id; break
        db.commit()
        print('تم الاستيراد بنجاح. راجع شجرة الحسابات وميزان المراجعة قبل إدخال حركات فعلية.')
if __name__=='__main__': main()
