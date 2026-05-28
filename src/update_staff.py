r"""幂等地：删除多余的 xuyueqian（4 号），并给 xyq（5 号）补手机号。

朋友 git pull 后运行：
    cd src
    .\venv\Scripts\python.exe update_staff.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app import create_app
from models import db, Staff, Order

app = create_app()

with app.app_context():
    # 1) 删除 xuyueqian（如果还在）
    dup = Staff.query.filter_by(username="xuyueqian").first()
    if dup:
        # 把这个员工创建过的订单转给 xyq（保留订单完整性）
        xyq = Staff.query.filter_by(username="xyq").first()
        if xyq:
            n = Order.query.filter_by(staff_id=dup.staff_id).update(
                {"staff_id": xyq.staff_id})
            print(f"  {n} 条订单从 xuyueqian 转给 xyq")
        db.session.delete(dup)
        print("  已删除 xuyueqian")
    else:
        print("  xuyueqian 已不存在，跳过")

    # 2) 给 xyq 补手机号
    xyq = Staff.query.filter_by(username="xyq").first()
    if xyq:
        if not xyq.phone:
            xyq.phone = "13812340567"
            print(f"  已给 xyq 添加手机号 {xyq.phone}")
        else:
            print(f"  xyq 已有手机号 {xyq.phone}，跳过")
    else:
        print("  [警告] 未找到 xyq")

    db.session.commit()
    print("\nOK")
