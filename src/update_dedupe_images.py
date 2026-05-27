r"""把之前共用同一张图的商品分别指向独立图片，消除重复。

幂等：可重复执行；只在 image 字段不一致时更新。
朋友 git pull 后运行：
    cd src
    .\venv\Scripts\python.exe update_dedupe_images.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import create_app
from models import db, Product

app = create_app()

MAPPING = {
    "冰美式":     "iced-americano.jpg",
    "美式特浓":   "double-espresso.jpg",
    "冰拿铁":     "iced-latte.jpg",
    "燕麦拿铁":   "oat-latte.jpg",
    "香草拿铁":   "vanilla-latte.jpg",
    "澳白":       "flat-white.jpg",
    "茉莉花茶":   "jasmine-tea.jpg",
    "椰香冷萃":   "coconut-cold-brew.jpg",
    "布朗尼":     "brownie.jpg",
    "玛德琳":     "madeleine.jpg",
}

with app.app_context():
    updated = 0
    for name, img in MAPPING.items():
        p = Product.query.filter_by(name=name).first()
        if p and p.image != img:
            print(f"  {name}: {p.image} -> {img}")
            p.image = img
            updated += 1
    db.session.commit()
    print(f"\nOK：去重 {updated} 款商品的图片")
