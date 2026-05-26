"""幂等地添加管理员账号 xyq / 070203（许跃骞）

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_admin.py   # Windows
    ./venv/bin/python seed_admin.py           # macOS / Linux
"""
from datetime import date
from app import create_app
from models import db, Staff

app = create_app()
with app.app_context():
    existing = Staff.query.filter_by(username="xyq").first()
    if existing:
        print(f"账号 xyq 已存在（姓名：{existing.name}，角色：{existing.role}），跳过。")
    else:
        db.session.add(Staff(
            username="xyq",
            password="070203",
            name="许跃骞",
            role="ADMIN",
            active=True,
            hire_date=date.today(),
        ))
        db.session.commit()
        print("✓ 已添加管理员账号：xyq / 070203（许跃骞）")
