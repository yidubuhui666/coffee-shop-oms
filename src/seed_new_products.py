r"""幂等地新增 10 款菜单商品并配置完整原料配方。

朋友 git pull 后运行一次即可：
    cd src
    .\venv\Scripts\python.exe seed_new_products.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from decimal import Decimal
from app import create_app
from models import db, Category, Product, Inventory, ProductIngredient

app = create_app()

# (分类名, 商品名, 描述, 价格, 库存, 图片文件名, [(原料, 单杯消耗量), ...])
NEW_PRODUCTS = [
    ("浓缩咖啡", "冰美式", "经典浓缩 + 冰水，夏日必备",
     20, 200, "iced-americano.jpg", [
        ("意式拼配豆", 0.020), ("冷饮塑料杯", 1), ("杯盖", 1),
        ("吸管", 1), ("纸巾", 0.02),
    ]),

    ("浓缩咖啡", "美式特浓", "双份浓缩咖啡萃取，醇厚提神",
     22, 150, "double-espresso.jpg", [
        ("意式拼配豆", 0.036), ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
    ]),

    ("牛奶咖啡", "冰拿铁", "冰镇浓缩咖啡配冷鲜奶",
     28, 150, "iced-latte.jpg", [
        ("意式拼配豆", 0.020), ("全脂牛奶", 0.20),
        ("冷饮塑料杯", 1), ("杯盖", 1), ("吸管", 1), ("纸巾", 0.02),
    ]),

    ("牛奶咖啡", "燕麦拿铁", "浓缩咖啡配燕麦奶，植物基轻盈口感",
     30, 120, "oat-latte.jpg", [
        ("意式拼配豆", 0.020), ("燕麦奶", 0.20),
        ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
    ]),

    ("牛奶咖啡", "香草拿铁", "浓缩咖啡 + 鲜奶 + 香草糖浆",
     28, 120, "vanilla-latte.jpg", [
        ("意式拼配豆", 0.020), ("全脂牛奶", 0.18), ("香草糖浆", 0.020),
        ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
    ]),

    ("牛奶咖啡", "澳白", "双份浓缩配蒸奶，平衡口感",
     30, 100, "flat-white.jpg", [
        ("意式拼配豆", 0.030), ("全脂牛奶", 0.16),
        ("热饮纸杯", 1), ("杯盖", 1), ("纸巾", 0.02),
    ]),

    ("茶饮", "茉莉花茶", "清香茉莉配蜜，温润回甘",
     16, 100, "jasmine-tea.jpg", [
        ("锡兰红茶包", 1), ("蜂蜜", 0.008),
        ("热饮纸杯", 1), ("杯盖", 1), ("搅拌棒", 1), ("纸巾", 0.02),
    ]),

    ("冷萃饮品", "椰香冷萃", "12 小时冷萃配椰浆奶盖",
     28, 80, "coconut-cold-brew.jpg", [
        ("单品咖啡豆", 0.025), ("淡奶油", 0.030), ("白砂糖", 0.008),
        ("冷饮塑料杯", 1), ("杯盖", 1), ("吸管", 1), ("纸巾", 0.02),
    ]),

    ("甜品", "布朗尼", "浓郁巧克力布朗尼，撒可可粉",
     22, 50, "brownie.jpg", [
        ("低筋面粉", 0.040), ("鸡蛋", 1), ("黄油", 0.025),
        ("巧克力酱", 0.030), ("可可粉", 0.010), ("白砂糖", 0.030),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),

    ("甜品", "玛德琳", "法式贝壳蛋糕，柠檬清香",
     20, 50, "madeleine.jpg", [
        ("低筋面粉", 0.035), ("鸡蛋", 1), ("黄油", 0.025),
        ("白砂糖", 0.025), ("柠檬", 0.1), ("香草精", 0.001),
        ("蛋糕盒", 1), ("蛋糕纸托", 1),
    ]),
]


with app.app_context():
    cats = {c.name: c.category_id for c in Category.query.all()}
    inv  = {i.name: i.ingredient_id for i in Inventory.query.all()}

    added, skipped, patched, recipe_added = 0, 0, 0, 0

    for cat_name, name, desc, price, stock, img, recipe in NEW_PRODUCTS:
        existing = Product.query.filter_by(name=name).first()
        if existing:
            # 商品已存在：把缺失或过期的 image 字段补上，保证脚本真正幂等
            # （历史上由更早版本插入但 image 留空 / 填错）
            if existing.image != img:
                existing.image = img
                patched += 1
            skipped += 1
            continue
        if cat_name not in cats:
            print(f"  ⚠ 跳过 {name}：分类「{cat_name}」不存在")
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
                print(f"  ⚠ {name} 的原料「{ing_name}」不存在，跳过")

        added += 1

    db.session.commit()
    print(f"OK：新增商品 {added} 款，跳过 {skipped} 款已存在"
          f"（其中补全 image 字段 {patched} 款），"
          f"新增配方记录 {recipe_added} 条")
    print(f"\n现在菜单共有 {Product.query.count()} 款商品。")
