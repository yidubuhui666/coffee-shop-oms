r"""把气泡饮和套餐的 image 字段更新为新生成的图片文件名。

幂等：可重复执行。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import create_app
from models import db, Product

app = create_app()

MAPPING = {
    "原味气泡水":   "plain-sparkling.jpg",
    "青柠气泡水":   "lime-sparkling.jpg",
    "莓果气泡水":   "berry-sparkling.jpg",
    "元气早餐套餐": "combo-breakfast.jpg",
    "下午茶套餐":   "combo-afternoon.jpg",
    "商务能量套餐": "combo-business.jpg",
    "闺蜜双人套餐": "combo-duo.jpg",
}

with app.app_context():
    updated = 0
    for name, img in MAPPING.items():
        p = Product.query.filter_by(name=name).first()
        if p and p.image != img:
            p.image = img
            updated += 1
            print(f"  更新 {name} -> {img}")
    db.session.commit()
    print(f"\nOK：更新 {updated} 款商品的图片字段")
