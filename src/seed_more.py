"""补充：增加更多会员 + 增加今日订单 + 增加最近 30 天历史订单。

可重复执行：会先清除标记为"补充"的数据再重新生成（通过 remark 字段标识）。
"""
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

from app import create_app
from models import db, Customer, Staff, Product, Order, OrderItem

app = create_app()

SEED_TAG = "[demo]"  # 用 remark 中的标识符标记补充数据

with app.app_context():
    # ---------- 1) 补充会员 ----------
    extra_customers = [
        # 铂金（高消费 VIP）
        ("陈志远", "13800001001", "PLATINUM"),
        ("林婉清", "13800001002", "PLATINUM"),
        ("赵明轩", "13800001003", "PLATINUM"),
        # 黄金
        ("吴雪婷", "13800001011", "GOLD"),
        ("钱昊然", "13800001012", "GOLD"),
        ("周思雨", "13800001013", "GOLD"),
        ("郑文博", "13800001014", "GOLD"),
        ("孙佳怡", "13800001015", "GOLD"),
        # 白银
        ("胡晓东", "13800001021", "SILVER"),
        ("黄丽华", "13800001022", "SILVER"),
        ("徐天宇", "13800001023", "SILVER"),
        ("曹梦琪", "13800001024", "SILVER"),
        ("梁俊杰", "13800001025", "SILVER"),
        ("韩梓萱", "13800001026", "SILVER"),
        ("姚泽凯", "13800001027", "SILVER"),
        # 青铜
        ("许若楠", "13800001031", "BRONZE"),
        ("董嘉豪", "13800001032", "BRONZE"),
        ("沈雨桐", "13800001033", "BRONZE"),
        ("罗一鸣", "13800001034", "BRONZE"),
        ("江悦然", "13800001035", "BRONZE"),
        ("唐子谦", "13800001036", "BRONZE"),
        ("方晓彤", "13800001037", "BRONZE"),
        ("石浩然", "13800001038", "BRONZE"),
    ]
    added_c = 0
    for name, phone, lvl in extra_customers:
        if not Customer.query.filter_by(phone=phone).first():
            db.session.add(Customer(name=name, phone=phone,
                                    email=f"{phone}@example.com",
                                    member_level=lvl, points=0))
            added_c += 1
    db.session.commit()

    # ---------- 2) 清除旧的补充订单 ----------
    old = (Order.query
           .filter(Order.remark.like(f"%{SEED_TAG}%")).all())
    for o in old:
        db.session.delete(o)
    db.session.commit()

    # ---------- 3) 生成新订单 ----------
    products   = Product.query.filter_by(available=True).all()
    staff_list = Staff.query.filter(Staff.role != "ADMIN").all()
    all_custs  = Customer.query.all()

    pays     = ["WECHAT","WECHAT","WECHAT","ALIPAY","ALIPAY","CARD","CASH"]
    sizes    = ["S","M","M","M","L"]

    rng = random.Random()  # 不固定种子，每次跑不同数据
    now = datetime.now()

    def make_order(when_dt, status, remark_extra=""):
        cust = rng.choice(all_custs) if rng.random() > 0.20 else None
        order = Order(
            customer_id=cust.customer_id if cust else None,
            staff_id=rng.choice(staff_list).staff_id,
            order_time=when_dt,
            payment_method=rng.choice(pays),
            dine_in=rng.random() > 0.4,
            status=status,
            remark=f"{remark_extra} {SEED_TAG}".strip(),
        )
        db.session.add(order)
        db.session.flush()
        total = Decimal("0")
        for p in rng.sample(products, k=rng.randint(1, 4)):
            qty = rng.randint(1, 3)
            db.session.add(OrderItem(order_id=order.order_id,
                                     product_id=p.product_id,
                                     quantity=qty, unit_price=p.price,
                                     size=rng.choice(sizes)))
            total += p.price * qty
        order.total_amount = total
        if status in ("PAID","PREPARING","READY","COMPLETED"):
            order.paid_amount = total
            if cust:
                cust.points = (cust.points or 0) + int(total)

    # 今日订单：50 条，分布在 8-21 点
    today = date.today()
    today_statuses = (
        ["COMPLETED"] * 18 + ["PAID"] * 12 + ["READY"] * 6 +
        ["PREPARING"] * 5 + ["PENDING"] * 6 + ["CANCELLED"] * 3
    )
    rng.shuffle(today_statuses)
    for i in range(50):
        hour = rng.choice([8, 9, 10, 11, 12, 12, 13, 14, 15, 16, 17, 18, 18, 19, 20])
        # 避免生成"未来"时间
        if hour > now.hour or (hour == now.hour and rng.random() > 0.5):
            hour = max(8, now.hour - rng.randint(0, 2))
        minute = rng.randint(0, 59)
        when_dt = datetime.combine(today, datetime.min.time()).replace(
            hour=hour, minute=minute, second=rng.randint(0, 59))
        if when_dt > now:
            when_dt = now - timedelta(minutes=rng.randint(1, 30))
        make_order(when_dt, today_statuses[i % len(today_statuses)], "今日")

    # 历史订单：最近 30 天，每天 8-15 条
    hist_statuses = ["COMPLETED"] * 12 + ["PAID"] * 3 + ["CANCELLED"] * 1
    for days_ago in range(1, 31):
        day_count = rng.randint(8, 15)
        for _ in range(day_count):
            hour = rng.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
            minute = rng.randint(0, 59)
            when_dt = datetime.combine(today - timedelta(days=days_ago),
                                       datetime.min.time()).replace(
                hour=hour, minute=minute, second=rng.randint(0, 59))
            make_order(when_dt, rng.choice(hist_statuses), "历史")

    db.session.commit()
    total_orders = Order.query.count()
    today_orders = Order.query.filter(
        db.func.date(Order.order_time) == today).count()
    print(f"OK：新增会员 {added_c} 人，今日订单 {today_orders} 条，订单总数 {total_orders} 条")
