r"""幂等地新增「气泡饮」分类（3 款气泡水）+「超值套餐」分类（4 款套餐）。

每个套餐的原料 = 套餐内各商品原料之和（一并扣库存）。
图片暂留 NULL，由模板根据名称智能匹配 emoji 占位符。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_bubble_combo.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decimal import Decimal
from app import create_app
from models import db, Category, Product, Inventory, ProductIngredient

app = create_app()

# 需要的新原料（用于气泡水，幂等添加）
NEW_INV = [
    ("苏打气泡水基底", "L",  20, 3),
    ("青柠",           "个", 50, 10),
    ("莓果糖浆",       "L",  4,  1),
]

# 新分类
NEW_CATS = [
    ("气泡饮",     6),
    ("超值套餐",  7),
]

# 新商品
NEW_PRODUCTS = [
    # 气泡饮（3 款）
    ("气泡饮", "原味气泡水", "纯净苏打水 + 冰块，零卡解腻", 12, 150, None, [
        ("苏打气泡水基底", 0.30), ("冷饮塑料杯", 1), ("杯盖", 1),
        ("吸管", 1), ("纸巾", 0.02),
    ]),
    ("气泡饮", "青柠气泡水", "苏打 + 鲜青柠 + 蜂蜜", 16, 120, None, [
        ("苏打气泡水基底", 0.30), ("青柠", 0.5), ("蜂蜜", 0.010),
        ("冷饮塑料杯", 1), ("杯盖", 1), ("吸管", 1), ("纸巾", 0.02),
    ]),
    ("气泡饮", "莓果气泡水", "苏打 + 混合莓果糖浆 + 薄荷", 18, 100, None, [
        ("苏打气泡水基底", 0.30), ("莓果糖浆", 0.030), ("薄荷叶", 0.003),
        ("冷饮塑料杯", 1), ("杯盖", 1), ("吸管", 1), ("纸巾", 0.02),
    ]),

    # 超值套餐（4 款，原料 = 各商品原料之和）
    ("超值套餐", "元气早餐套餐",
     "美式咖啡 + 玛德琳，醒神又抗饿", 36, 80, None, [
        # 美式咖啡
        ("意式拼配豆", 0.020), ("热饮纸杯", 1), ("杯盖", 1),
        ("搅拌棒", 1), ("纸巾", 0.04),
        # 玛德琳
        ("低筋面粉", 0.035), ("鸡蛋", 1), ("黄油", 0.025),
        ("白砂糖", 0.025), ("柠檬", 0.1), ("香草精", 0.001),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),
    ("超值套餐", "下午茶套餐",
     "拿铁 + 提拉米苏，慵懒午后", 52, 60, None, [
        # 拿铁
        ("意式拼配豆", 0.020), ("全脂牛奶", 0.20),
        ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.04),
        # 提拉米苏
        ("可可饼干", 0.030), ("鸡蛋", 1), ("马斯卡彭奶酪", 0.080),
        ("淡奶油", 0.050), ("单品咖啡豆", 0.010),
        ("可可粉", 0.005), ("白砂糖", 0.020), ("香草精", 0.002),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),
    ("超值套餐", "商务能量套餐",
     "美式特浓 + 布朗尼，加班战神", 38, 60, None, [
        # 美式特浓
        ("意式拼配豆", 0.036), ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.04),
        # 布朗尼
        ("低筋面粉", 0.040), ("鸡蛋", 1), ("黄油", 0.025),
        ("巧克力酱", 0.030), ("可可粉", 0.010), ("白砂糖", 0.030),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),
    ("超值套餐", "闺蜜双人套餐",
     "2 杯香草拿铁 + 1 块芝士蛋糕", 78, 40, None, [
        # 2 杯香草拿铁
        ("意式拼配豆", 0.040), ("全脂牛奶", 0.36), ("香草糖浆", 0.040),
        ("热饮纸杯", 2), ("杯盖", 2), ("纸巾", 0.08),
        # 纽约芝士蛋糕
        ("奶油奶酪", 0.120), ("鸡蛋", 1), ("饼干底", 0.040),
        ("黄油", 0.030), ("白砂糖", 0.030), ("低筋面粉", 0.015),
        ("淡奶油", 0.020), ("香草精", 0.002),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),
]


with app.app_context():
    # 1) 补齐新原料
    inv_added = 0
    for name, unit, qty, alert in NEW_INV:
        if not Inventory.query.filter_by(name=name).first():
            db.session.add(Inventory(name=name, unit=unit,
                                     quantity=Decimal(str(qty)),
                                     alert_threshold=Decimal(str(alert))))
            inv_added += 1
    db.session.commit()

    # 2) 补齐新分类
    cat_added = 0
    for name, order in NEW_CATS:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, sort_order=order))
            cat_added += 1
    db.session.commit()

    # 3) 添加商品 + 配方
    cats = {c.name: c.category_id for c in Category.query.all()}
    inv  = {i.name: i.ingredient_id for i in Inventory.query.all()}

    prod_added, prod_skipped, recipe_added = 0, 0, 0
    for cat_name, name, desc, price, stock, img, recipe in NEW_PRODUCTS:
        if Product.query.filter_by(name=name).first():
            prod_skipped += 1
            continue
        p = Product(category_id=cats[cat_name], name=name,
                    description=desc, price=Decimal(str(price)),
                    stock=stock, image=img, available=True)
        db.session.add(p)
        db.session.flush()

        for ing_name, qty in recipe:
            if ing_name in inv:
                db.session.add(ProductIngredient(
                    product_id=p.product_id,
                    ingredient_id=inv[ing_name],
                    consume_qty=Decimal(str(qty)),
                ))
                recipe_added += 1
            else:
                print(f"  [警告] {name} 的原料「{ing_name}」不存在")

        prod_added += 1

    db.session.commit()

    print(f"OK：新增 {inv_added} 种原料、{cat_added} 个分类、"
          f"{prod_added} 款商品（跳过 {prod_skipped} 款）、"
          f"{recipe_added} 条配方记录")
    print(f"\n现在菜单共有 {Product.query.count()} 款商品、"
          f"{Category.query.count()} 个分类。")
