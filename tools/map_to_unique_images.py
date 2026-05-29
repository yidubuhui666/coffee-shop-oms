r"""把所有商品的 image 字段映射到各自专属的图片文件（AI 生成版）。

此脚本接替 revert_to_safe_images.py，朋友 git pull 后运行即可同步。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app import create_app
from models import db, Product

MAP = {
    # 浓缩咖啡
    "美式咖啡":       "americano.jpg",
    "浓缩咖啡":       "espresso.jpg",
    "冰美式":         "iced-americano.jpg",
    "美式特浓":       "double-espresso.jpg",
    # 牛奶咖啡
    "拿铁":           "latte.jpg",
    "卡布奇诺":       "cappuccino.jpg",
    "摩卡":           "mocha.jpg",
    "焦糖玛奇朵":     "caramel-macchiato.jpg",
    "冰拿铁":         "iced-latte.jpg",
    "燕麦拿铁":       "oat-latte.jpg",
    "香草拿铁":       "vanilla-latte.jpg",
    "澳白":           "flat-white.jpg",
    # 茶饮
    "伯爵红茶":       "earl-grey-tea.jpg",
    "抹茶拿铁":       "matcha-latte.jpg",
    "茉莉花茶":       "jasmine-tea.jpg",
    # 冷萃
    "冷萃咖啡":       "cold-brew.jpg",
    "冰柠檬茶":       "iced-lemon-tea.jpg",
    "椰香冷萃":       "coconut-cold-brew.jpg",
    # 甜品
    "提拉米苏":       "tiramisu.jpg",
    "纽约芝士蛋糕":   "cheesecake.jpg",
    "布朗尼":         "brownie.jpg",
    "玛德琳":         "madeleine.jpg",
    # 气泡饮
    "原味气泡水":     "plain-sparkling.jpg",
    "青柠气泡水":     "lime-sparkling.jpg",
    "莓果气泡水":     "berry-sparkling.jpg",
    # 超值套餐
    "元气早餐套餐":   "combo-breakfast.jpg",
    "下午茶套餐":     "combo-afternoon.jpg",
    "商务能量套餐":   "combo-business.jpg",
    "闺蜜双人套餐":   "combo-duo.jpg",
}

app = create_app()
with app.app_context():
    updated = 0
    for name, img in MAP.items():
        p = Product.query.filter_by(name=name).first()
        if not p:
            print(f"  [跳过] 未找到 {name}")
            continue
        if p.image != img:
            print(f"  {name}: {p.image} -> {img}")
            p.image = img
            updated += 1
    db.session.commit()
    print(f"\nOK：更新 {updated} 个商品的 image 字段")
