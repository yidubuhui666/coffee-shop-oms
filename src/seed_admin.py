r"""幂等地添加/修正管理员账号 xyq / 070203（许跃骞），并保证其有手机号。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_admin.py   # Windows
    ./venv/bin/python seed_admin.py           # macOS / Linux

幂等说明：
  - 账号不存在 → 新建（带手机号）。
  - 账号已存在但没手机号 → 补上手机号。
  - 账号已存在且有手机号 → 跳过。
"""
from datetime import date
from app import create_app
from models import db, Staff

PHONE = "13812340567"

app = create_app()
with app.app_context():
    existing = Staff.query.filter_by(username="xyq").first()
    if existing:
        if not existing.phone:
            existing.phone = PHONE
            db.session.commit()
            print(f"[OK] 已为账号 xyq 补充手机号：{PHONE}")
        else:
            print(f"账号 xyq 已存在（姓名：{existing.name}，手机号：{existing.phone}），跳过。")
    else:
        db.session.add(Staff(
            username="xyq",
            password="070203",
            name="许跃骞",
            role="ADMIN",
            phone=PHONE,
            active=True,
            hire_date=date.today(),
        ))
        db.session.commit()
        print(f"[OK] 已添加管理员账号：xyq / 070203（许跃骞），手机号 {PHONE}")
