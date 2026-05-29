"""首次启动时灌入演示数据（仅当 staff 表为空时生效）。"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from models import db, Customer, Staff, Category, Product, Order, OrderItem, Inventory


def bootstrap_demo_data() -> None:
    if Staff.query.first():
        return

    demo_staff = [
        Staff(username="admin",     password="admin123",   name="杨帆",   role="ADMIN"),
        Staff(username="barista",   password="barista123", name="李明",   role="BARISTA"),
        Staff(username="cashier",   password="cashier123", name="王磊",   role="CASHIER"),
    ]
    cats = [Category(name=n, sort_order=i + 1) for i, n in enumerate(
        ["浓缩咖啡", "牛奶咖啡", "茶饮", "冷萃饮品", "甜品"])]
    db.session.add_all(demo_staff + cats)
    db.session.commit()

    catmap = {c.name: c.category_id for c in cats}
    seed = [
        ("浓缩咖啡", "美式咖啡",       "经典浓缩 + 热水",            18, 200, "americano.jpg"),
        ("浓缩咖啡", "浓缩咖啡",       "单份意式浓缩",                15, 200, "espresso.jpg"),
        ("牛奶咖啡", "拿铁",           "浓缩咖啡配蒸奶",              25, 150, "latte.jpg"),
        ("牛奶咖啡", "卡布奇诺",       "浓缩咖啡配奶泡",              25, 150, "cappuccino.jpg"),
        ("牛奶咖啡", "摩卡",           "浓缩 + 巧克力 + 牛奶",        28, 120, "mocha.jpg"),
        ("牛奶咖啡", "焦糖玛奇朵",     "浓缩 + 焦糖 + 奶泡",          30, 120, "caramel-macchiato.jpg"),
        ("茶饮",     "伯爵红茶",       "佛手柑香味的红茶",            18, 100, "earl-grey-tea.jpg"),
        ("茶饮",     "抹茶拿铁",       "日式抹茶配牛奶",              28, 100, "matcha-latte.jpg"),
        ("冷萃饮品", "冷萃咖啡",       "12 小时慢萃冷萃咖啡",         26,  80, "cold-brew.jpg"),
        ("冷萃饮品", "冰柠檬茶",       "新鲜柠檬冰茶",                20,  80, "iced-lemon-tea.jpg"),
        ("甜品",     "提拉米苏",       "经典意式甜点",                32,  40, "tiramisu.jpg"),
        ("甜品",     "纽约芝士蛋糕",   "纽约风味芝士蛋糕",            30,  40, "cheesecake.jpg"),
    ]
    db.session.add_all([Product(category_id=catmap[c], name=n, description=d,
                                price=p, stock=s, image=img) for c, n, d, p, s, img in seed])

    # 20 个会员
    surnames = ["张", "李", "王", "赵", "刘", "陈", "杨", "黄", "周", "吴",
                "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
    given   = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "洋", "艳",
               "杰", "涛", "明", "超", "秀英", "霞", "平", "刚", "桂英", "建国"]
    levels  = ["BRONZE"] * 10 + ["SILVER"] * 6 + ["GOLD"] * 3 + ["PLATINUM"] * 1
    customers = [Customer(name=surnames[i] + given[i], phone=f"139{i:08d}",
                          email=f"user{i+1:02d}@example.com",
                          member_level=levels[i], points=0) for i in range(20)]
    db.session.add_all(customers)

    db.session.add_all([
        Inventory(name="咖啡豆",   unit="kg", quantity=30),
        Inventory(name="牛奶",     unit="L",  quantity=40),
        Inventory(name="白糖",     unit="kg", quantity=15),
        Inventory(name="巧克力",   unit="kg", quantity=5),
        Inventory(name="抹茶粉",   unit="kg", quantity=2),
        Inventory(name="柠檬",     unit="个", quantity=60),
        Inventory(name="一次性杯", unit="个", quantity=400),
        Inventory(name="吸管",     unit="个", quantity=300),
    ])
    db.session.commit()

    # 150 条订单
    products = Product.query.all()
    staff_list = Staff.query.filter(Staff.role != "ADMIN").all()
    all_customers = Customer.query.all()
    pays   = ["WECHAT", "WECHAT", "WECHAT", "ALIPAY", "ALIPAY", "CARD", "CASH"]
    sizes  = ["S", "M", "M", "M", "L"]
    statuses = ["COMPLETED"] * 50 + ["PAID"] * 25 + ["READY"] * 8 + \
               ["PREPARING"] * 6 + ["PENDING"] * 4 + ["CANCELLED"] * 7

    rng = random.Random(42)
    now = datetime.now()

    for _ in range(150):
        days_ago = rng.randint(0, 13)
        hour     = rng.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        minute   = rng.randint(0, 59)
        order_time = (now - timedelta(days=days_ago)).replace(
            hour=hour, minute=minute, second=rng.randint(0, 59), microsecond=0)

        cust = rng.choice(all_customers) if rng.random() > 0.25 else None
        order = Order(
            customer_id=cust.customer_id if cust else None,
            staff_id=rng.choice(staff_list).staff_id,
            order_time=order_time,
            payment_method=rng.choice(pays),
            dine_in=rng.random() > 0.4,
            status=rng.choice(statuses),
            remark=rng.choice([None, None, None, "少糖", "去冰", "多加一份糖", "打包"]),
        )
        db.session.add(order)
        db.session.flush()

        chosen = rng.sample(products, k=rng.randint(1, 4))
        total = Decimal("0")
        for p in chosen:
            qty = rng.randint(1, 3)
            item = OrderItem(order_id=order.order_id, product_id=p.product_id,
                             quantity=qty, unit_price=p.price,
                             size=rng.choice(sizes))
            total += p.price * qty
            db.session.add(item)
        order.total_amount = total
        if order.status in ("PAID", "PREPARING", "READY", "COMPLETED"):
            order.paid_amount = total
            if cust:
                cust.points = (cust.points or 0) + int(total)

    db.session.commit()
