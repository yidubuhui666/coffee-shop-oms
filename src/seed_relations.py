"""填充 product_ingredient 关联表 与 member_discount 表

可重复执行：会补齐缺失的原料，并用最新配方覆盖 product_ingredient 表。
"""
from decimal import Decimal
from app import create_app
from models import db, Product, Inventory, ProductIngredient, MemberDiscount

app = create_app()

with app.app_context():
    db.create_all()

    # 1) 会员等级折扣
    if not MemberDiscount.query.first():
        db.session.add_all([
            MemberDiscount(level="BRONZE",   discount=Decimal("1.00"), label="青铜（无折扣）"),
            MemberDiscount(level="SILVER",   discount=Decimal("0.95"), label="白银 95 折"),
            MemberDiscount(level="GOLD",     discount=Decimal("0.90"), label="黄金 9 折"),
            MemberDiscount(level="PLATINUM", discount=Decimal("0.85"), label="铂金 85 折"),
        ])
        db.session.commit()

    # 2) 补齐原料库存（按名称去重）
    desired_inv = [
        ("咖啡豆",       "kg", 30,  5),
        ("牛奶",         "L",  40,  10),
        ("白糖",         "kg", 15,  3),
        ("巧克力",       "kg", 5,   1),
        ("抹茶粉",       "kg", 2,   1),
        ("柠檬",         "个", 60,  10),
        ("一次性杯",     "个", 400, 50),
        ("吸管",         "个", 300, 50),
        # —— 新增 ——
        ("红茶包",       "个", 200, 30),
        ("面粉",         "kg", 10,  2),
        ("鸡蛋",         "个", 120, 24),
        ("淡奶油",       "L",  8,   2),
        ("黄油",         "kg", 4,   1),
        ("奶油奶酪",     "kg", 5,   1),
        ("马斯卡彭奶酪", "kg", 3,   1),
        ("蛋糕盒",       "个", 60,  10),
    ]
    for name, unit, qty, alert in desired_inv:
        inv = Inventory.query.filter_by(name=name).first()
        if not inv:
            db.session.add(Inventory(name=name, unit=unit,
                                     quantity=Decimal(str(qty)),
                                     alert_threshold=Decimal(str(alert))))
    db.session.commit()

    # 3) 重新生成商品-原料配方（每次执行都覆盖，保证一致）
    inv_map = {i.name: i.ingredient_id for i in Inventory.query.all()}

    # 配方：商品名 -> [(原料名, 单杯/单份消耗量)]
    recipes = {
        # —— 浓缩咖啡 ——
        "美式咖啡":   [("咖啡豆", 0.020), ("一次性杯", 1)],
        "浓缩咖啡":   [("咖啡豆", 0.018), ("一次性杯", 1)],
        # —— 牛奶咖啡 ——
        "拿铁":       [("咖啡豆", 0.020), ("牛奶", 0.20), ("一次性杯", 1)],
        "卡布奇诺":   [("咖啡豆", 0.020), ("牛奶", 0.15), ("一次性杯", 1)],
        "摩卡":       [("咖啡豆", 0.020), ("牛奶", 0.15), ("巧克力", 0.020), ("一次性杯", 1)],
        "焦糖玛奇朵": [("咖啡豆", 0.020), ("牛奶", 0.18), ("白糖", 0.010), ("一次性杯", 1)],
        # —— 茶饮 ——
        "伯爵红茶":   [("红茶包", 1), ("一次性杯", 1)],
        "抹茶拿铁":   [("抹茶粉", 0.015), ("牛奶", 0.20), ("一次性杯", 1)],
        # —— 冷萃饮品 ——
        "冷萃咖啡":   [("咖啡豆", 0.025), ("一次性杯", 1), ("吸管", 1)],
        "冰柠檬茶":   [("红茶包", 1), ("柠檬", 0.5), ("白糖", 0.010),
                       ("一次性杯", 1), ("吸管", 1)],
        # —— 甜品 ——
        "提拉米苏":   [("面粉", 0.050), ("鸡蛋", 1), ("马斯卡彭奶酪", 0.080),
                       ("淡奶油", 0.050), ("咖啡豆", 0.010),
                       ("巧克力", 0.005), ("蛋糕盒", 1)],
        "纽约芝士蛋糕": [("奶油奶酪", 0.120), ("鸡蛋", 1), ("面粉", 0.040),
                       ("黄油", 0.030), ("白糖", 0.030), ("蛋糕盒", 1)],
    }

    # 清空旧关系再重建（保证幂等）
    ProductIngredient.query.delete()
    db.session.commit()

    added = 0
    for prod in Product.query.all():
        recipe = recipes.get(prod.name)
        if not recipe:
            continue
        for ing_name, qty in recipe:
            if ing_name not in inv_map:
                continue
            db.session.add(ProductIngredient(
                product_id=prod.product_id,
                ingredient_id=inv_map[ing_name],
                consume_qty=Decimal(str(qty)),
            ))
            added += 1

    db.session.commit()
    print(f"OK：原料 {Inventory.query.count()} 种，配方记录 {added} 条")
