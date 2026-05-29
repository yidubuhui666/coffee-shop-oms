r"""幂等地删除重复的许跃骞账号（用户名 xuyueqian）。

背景：早期演示数据里有两个许跃骞账号——xuyueqian 和 xyq。
现已统一保留 xyq，删除多余的 xuyueqian。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_cleanup_staff.py   # Windows
    ./venv/bin/python seed_cleanup_staff.py           # macOS / Linux

幂等说明：
  - 账号不存在 → 跳过。
  - 账号存在但已下过订单（有外键关联）→ 不删除，仅停用（active=False）并提示。
  - 账号存在且无订单 → 直接删除。
"""
from app import create_app
from models import db, Staff, Order

app = create_app()
with app.app_context():
    s = Staff.query.filter_by(username="xuyueqian").first()
    if not s:
        print("账号 xuyueqian 不存在，跳过。")
    else:
        order_cnt = Order.query.filter_by(staff_id=s.staff_id).count()
        if order_cnt > 0:
            s.active = False
            db.session.commit()
            print(f"账号 xuyueqian 有 {order_cnt} 条关联订单，无法删除，已改为停用（active=False）。")
        else:
            db.session.delete(s)
            db.session.commit()
            print("✓ 已删除重复账号：xuyueqian（许跃骞）")
