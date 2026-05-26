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
        # 基础咖啡原料
        ("咖啡豆",       "kg", 30,  5),
        ("意式拼配豆",   "kg", 20,  4),
        ("单品咖啡豆",   "kg", 10,  2),

        # 乳制品
        ("全脂牛奶",     "L",  40,  10),
        ("脱脂牛奶",     "L",  20,  5),
        ("燕麦奶",       "L",  15,  3),
        ("淡奶油",       "L",  8,   2),
        ("黄油",         "kg", 4,   1),
        ("奶油奶酪",     "kg", 5,   1),
        ("马斯卡彭奶酪", "kg", 3,   1),

        # 糖与糖浆
        ("白砂糖",       "kg", 15,  3),
        ("红糖",         "kg", 5,   1),
        ("香草糖浆",     "L",  6,   1),
        ("焦糖糖浆",     "L",  6,   1),
        ("榛子糖浆",     "L",  4,   1),
        ("蜂蜜",         "kg", 3,   1),

        # 风味与配料
        ("巧克力酱",     "kg", 5,   1),
        ("可可粉",       "kg", 3,   1),
        ("抹茶粉",       "kg", 2,   1),
        ("肉桂粉",       "kg", 1,   0.3),
        ("香草精",       "L",  1,   0.2),

        # 茶饮原料
        ("伯爵红茶包",   "个", 200, 30),
        ("锡兰红茶包",   "个", 150, 30),
        ("柠檬",         "个", 60,  10),
        ("薄荷叶",       "kg", 1,   0.2),

        # 烘焙原料
        ("面粉",         "kg", 10,  2),
        ("低筋面粉",     "kg", 8,   2),
        ("鸡蛋",         "个", 120, 24),
        ("饼干底",       "kg", 5,   1),
        ("可可饼干",     "kg", 3,   1),

        # 包装与耗材
        ("热饮纸杯",     "个", 400, 50),
        ("冷饮塑料杯",   "个", 300, 50),
        ("杯盖",         "个", 500, 80),
        ("吸管",         "个", 300, 50),
        ("搅拌棒",       "个", 200, 40),
        ("纸巾",         "包", 50,  10),
        ("蛋糕盒",       "个", 60,  10),
        ("蛋糕纸托",     "个", 100, 20),
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
        # —— 浓缩咖啡（精细到每杯的杯/盖/搅拌棒）——
        "美式咖啡": [
            ("意式拼配豆", 0.020), ("热饮纸杯", 1), ("杯盖", 1), ("搅拌棒", 1), ("纸巾", 0.02),
        ],
        "浓缩咖啡": [
            ("意式拼配豆", 0.018), ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
        ],

        # —— 牛奶咖啡（含奶/奶油/可可粉装饰等）——
        "拿铁": [
            ("意式拼配豆", 0.020), ("全脂牛奶", 0.20),
            ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
        ],
        "卡布奇诺": [
            ("意式拼配豆", 0.020), ("全脂牛奶", 0.15), ("可可粉", 0.002),
            ("肉桂粉", 0.001), ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
        ],
        "摩卡": [
            ("意式拼配豆", 0.020), ("全脂牛奶", 0.15), ("巧克力酱", 0.020),
            ("淡奶油", 0.020), ("可可粉", 0.003),
            ("热饮纸杯", 1), ("杯盖", 1), ("搅拌棒", 1), ("纸巾", 0.02),
        ],
        "焦糖玛奇朵": [
            ("意式拼配豆", 0.020), ("全脂牛奶", 0.18), ("焦糖糖浆", 0.025),
            ("香草糖浆", 0.010),
            ("热饮纸杯", 1), ("杯盖", 1), ("搅拌棒", 1), ("纸巾", 0.02),
        ],

        # —— 茶饮 ——
        "伯爵红茶": [
            ("伯爵红茶包", 1), ("蜂蜜", 0.008),
            ("热饮纸杯", 1), ("杯盖", 1), ("搅拌棒", 1), ("纸巾", 0.02),
        ],
        "抹茶拿铁": [
            ("抹茶粉", 0.015), ("全脂牛奶", 0.20), ("白砂糖", 0.010),
            ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
        ],

        # —— 冷萃饮品（冷杯+吸管，无热饮杯）——
        "冷萃咖啡": [
            ("单品咖啡豆", 0.025), ("冷饮塑料杯", 1), ("杯盖", 1),
            ("吸管", 1), ("纸巾", 0.02),
        ],
        "冰柠檬茶": [
            ("锡兰红茶包", 1), ("柠檬", 0.5), ("白砂糖", 0.012),
            ("薄荷叶", 0.002),
            ("冷饮塑料杯", 1), ("杯盖", 1), ("吸管", 1), ("纸巾", 0.02),
        ],

        # —— 甜品（精细到饼干底/纸托）——
        "提拉米苏": [
            ("可可饼干", 0.030), ("鸡蛋", 1), ("马斯卡彭奶酪", 0.080),
            ("淡奶油", 0.050), ("单品咖啡豆", 0.010),
            ("可可粉", 0.005), ("白砂糖", 0.020), ("香草精", 0.002),
            ("蛋糕盒", 1), ("蛋糕纸托", 1),
        ],
        "纽约芝士蛋糕": [
            ("奶油奶酪", 0.120), ("鸡蛋", 1), ("饼干底", 0.040),
            ("黄油", 0.030), ("白砂糖", 0.030), ("低筋面粉", 0.015),
            ("淡奶油", 0.020), ("香草精", 0.002),
            ("蛋糕盒", 1), ("蛋糕纸托", 1),
        ],
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
