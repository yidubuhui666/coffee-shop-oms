"""填充 product_ingredient 关联表 与 member_discount 表"""
from decimal import Decimal
from app import create_app
from models import db, Product, Inventory, ProductIngredient, MemberDiscount

app = create_app()

with app.app_context():
    db.create_all()

    # 1) 会员折扣
    if not MemberDiscount.query.first():
        db.session.add_all([
            MemberDiscount(level="BRONZE",   discount=Decimal("1.00"), label="青铜（无折扣）"),
            MemberDiscount(level="SILVER",   discount=Decimal("0.95"), label="白银 95 折"),
            MemberDiscount(level="GOLD",     discount=Decimal("0.90"), label="黄金 9 折"),
            MemberDiscount(level="PLATINUM", discount=Decimal("0.85"), label="铂金 85 折"),
        ])

    # 2) 商品-原料配方表
    if not ProductIngredient.query.first():
        inv = {i.name: i.ingredient_id for i in Inventory.query.all()}

        # 配方表：商品名 -> [(原料名, 每杯消耗量)]
        recipes = {
            "美式咖啡":     [("咖啡豆", 0.020), ("一次性杯", 1), ("白糖", 0.005)],
            "浓缩咖啡":     [("咖啡豆", 0.018), ("一次性杯", 1)],
            "拿铁":         [("咖啡豆", 0.020), ("牛奶", 0.20), ("一次性杯", 1)],
            "卡布奇诺":     [("咖啡豆", 0.020), ("牛奶", 0.15), ("一次性杯", 1)],
            "摩卡":         [("咖啡豆", 0.020), ("牛奶", 0.15), ("巧克力", 0.020), ("一次性杯", 1)],
            "焦糖玛奇朵":   [("咖啡豆", 0.020), ("牛奶", 0.18), ("白糖", 0.010), ("一次性杯", 1)],
            "伯爵红茶":     [("一次性杯", 1), ("白糖", 0.005)],
            "抹茶拿铁":     [("抹茶粉", 0.015), ("牛奶", 0.20), ("一次性杯", 1)],
            "冷萃咖啡":     [("咖啡豆", 0.025), ("一次性杯", 1), ("吸管", 1)],
            "冰柠檬茶":     [("柠檬", 0.5), ("白糖", 0.010), ("一次性杯", 1), ("吸管", 1)],
            "提拉米苏":     [("一次性杯", 1)],
            "纽约芝士蛋糕": [("一次性杯", 1)],
        }

        added = 0
        for prod in Product.query.all():
            recipe = recipes.get(prod.name)
            if not recipe:
                continue
            for ing_name, qty in recipe:
                if ing_name not in inv:
                    continue
                db.session.add(ProductIngredient(
                    product_id=prod.product_id,
                    ingredient_id=inv[ing_name],
                    consume_qty=Decimal(str(qty)),
                ))
                added += 1
        print(f"配方记录已插入：{added} 条")

    db.session.commit()
    print("OK")
