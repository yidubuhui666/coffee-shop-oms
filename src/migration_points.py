r"""⚠️ 协作者需运行：为 orders 表新增 points_used 列（积分抵扣功能）。

幂等：执行前先 SHOW COLUMNS 判断，已存在则跳过，可重复运行。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe migration_points.py   # Windows
    ./venv/bin/python migration_points.py           # macOS / Linux
"""
from sqlalchemy import text
from app import create_app
from models import db

app = create_app()
with app.app_context():
    cols = [row[0] for row in db.session.execute(
        text("SHOW COLUMNS FROM orders")).fetchall()]
    if "points_used" in cols:
        print("orders.points_used 已存在，跳过。")
    else:
        db.session.execute(text(
            "ALTER TABLE orders ADD COLUMN points_used INT NOT NULL DEFAULT 0"))
        db.session.commit()
        print("[OK] 已为 orders 表新增 points_used 列。")
