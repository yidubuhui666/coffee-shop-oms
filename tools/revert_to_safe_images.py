r"""把所有商品的图片字段映射回项目自带的 12 张已验证图片。

放弃下载的随机网图，复用原图（视觉重复但内容 100% 正确）。
图片文件本身随 git 同步，朋友 git pull 后运行此脚本即可。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import create_app
from models import db, Product

# 商品名 -> 复用的原图
SAFE_MAP = {
    # 浓缩咖啡
    "冰美式":         "americano.jpg",
    "美式特浓":       "espresso.jpg",

    # 牛奶咖啡
    "冰拿铁":         "latte.jpg",
    "燕麦拿铁":       "latte.jpg",
    "香草拿铁":       "latte.jpg",
    "澳白":           "cappuccino.jpg",

    # 茶饮
    "茉莉花茶":       "earl-grey-tea.jpg",

    # 冷萃
    "椰香冷萃":       "cold-brew.jpg",

    # 甜品
    "布朗尼":         "cheesecake.jpg",
    "玛德琳":         "cheesecake.jpg",

    # 气泡饮（用清饮代替）
    "原味气泡水":     "iced-lemon-tea.jpg",
    "青柠气泡水":     "iced-lemon-tea.jpg",
    "莓果气泡水":     "iced-lemon-tea.jpg",

    # 超值套餐 - 用主打商品的图
    "元气早餐套餐":   "americano.jpg",      # 美式 + 玛德琳
    "下午茶套餐":     "latte.jpg",          # 拿铁 + 提拉米苏
    "商务能量套餐":   "espresso.jpg",       # 美式特浓 + 布朗尼
    "闺蜜双人套餐":   "cheesecake.jpg",     # 香草拿铁 + 芝士蛋糕
}

app = create_app()

with app.app_context():
    updated = 0
    skipped = 0
    for name, img in SAFE_MAP.items():
        p = Product.query.filter_by(name=name).first()
        if not p:
            print(f"  [跳过] 未找到商品「{name}」")
            skipped += 1
            continue
        if p.image == img:
            continue  # 已经是目标值
        old = p.image
        p.image = img
        print(f"  {name}: {old} -> {img}")
        updated += 1

    db.session.commit()
    print(f"\nOK：更新 {updated} 个商品的图片字段，跳过 {skipped} 个未找到")
