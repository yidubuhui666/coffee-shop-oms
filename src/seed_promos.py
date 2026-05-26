r"""幂等地插入演示促销码数据。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_promos.py   # Windows
    ./venv/bin/python seed_promos.py           # macOS / Linux
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from datetime import date, timedelta
from decimal import Decimal
from app import create_app
from models import db, Promotion

app = create_app()

DEMO_PROMOS = [
    # code,    name,        discount, days_valid
    ("WELCOME10", "新客 10 元立减体验",   Decimal("0.90"), 60),
    ("SUMMER20",  "夏季全场 8 折",         Decimal("0.80"), 30),
    ("VIP15",     "VIP 限定 85 折",        Decimal("0.85"), 90),
    ("WEEKEND",   "周末专享 95 折",        Decimal("0.95"), 365),
    ("BIRTHDAY",  "生日特惠 75 折",        Decimal("0.75"), 365),
    ("EXPIRED",   "已过期测试码",           Decimal("0.50"), -10),  # 已过期
]

with app.app_context():
    today = date.today()
    added, skipped = 0, 0
    for code, name, disc, days in DEMO_PROMOS:
        if Promotion.query.filter_by(code=code).first():
            skipped += 1
            continue
        db.session.add(Promotion(
            code=code, name=name, discount=disc,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=days),
            active=(days > 0),
        ))
        added += 1
    db.session.commit()
    print(f"OK：新增 {added} 个促销码，跳过 {skipped} 个已存在")
    print("\n可用促销码：")
    for p in Promotion.query.filter_by(active=True).all():
        print(f"  {p.code:<12} {int(p.discount*100)}折  {p.name}")
