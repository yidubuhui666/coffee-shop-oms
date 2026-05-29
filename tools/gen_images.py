r"""为新产品生成漂亮的占位图片。

用 PIL 画渐变背景 + 大号 emoji + 商品名称，保存为 jpg。
朋友 git pull 即可拿到所有图片（图片会随仓库一起上传），无需重跑此脚本。
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFont

DEST = os.path.join(os.path.dirname(__file__), "static", "img", "products")
os.makedirs(DEST, exist_ok=True)

# (文件名, 主标题, 副标题, emoji, 颜色1, 颜色2)
ITEMS = [
    # 气泡饮 - 蓝绿色调
    ("plain-sparkling.jpg",  "原味气泡水", "Sparkling Water",   "💧", "#a8dadc", "#457b9d"),
    ("lime-sparkling.jpg",   "青柠气泡水", "Lime Sparkling",    "🍋", "#cce5b3", "#5ea66b"),
    ("berry-sparkling.jpg",  "莓果气泡水", "Berry Sparkling",   "🫐", "#e6b1d9", "#9b3973"),

    # 套餐 - 暖橙色调
    ("combo-breakfast.jpg",  "元气早餐套餐", "Morning Combo",   "🌅", "#ffd6a5", "#e07b39"),
    ("combo-afternoon.jpg",  "下午茶套餐",   "Afternoon Tea",   "🫖", "#f4d4b3", "#a06641"),
    ("combo-business.jpg",   "商务能量套餐", "Business Combo",  "💼", "#cfc3b6", "#3e2723"),
    ("combo-duo.jpg",        "闺蜜双人套餐", "Duo Combo",       "💕", "#f7c8d0", "#c44569"),
]

SIZE = (500, 500)

def find_font(size, want_emoji=False):
    """寻找系统字体；优先中文 / emoji 支持的字体。"""
    candidates = ["seguiemj.ttf"] if want_emoji else []
    candidates += [
        "msyh.ttc", "msyh.ttf", "msyhbd.ttc",        # 微软雅黑
        "simhei.ttf", "simsun.ttc",                  # 黑体/宋体
        "PingFang.ttc", "STHeiti Medium.ttc",        # macOS
        "Arial.ttf", "arial.ttf",
    ]
    for f in candidates:
        for d in ["C:\\Windows\\Fonts", "/System/Library/Fonts",
                  "/usr/share/fonts/truetype/dejavu"]:
            p = os.path.join(d, f)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
    return ImageFont.load_default()


def make_gradient(c1, c2, size):
    """生成对角线渐变背景"""
    img = Image.new("RGB", size, c1)
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
    r2, g2, b2 = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
    w, h = size
    for y in range(h):
        t = y / h
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def draw_circle(draw, center, radius, color, alpha=255):
    """画半透明圆点装饰"""
    cx, cy = center
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=color)


def render(item):
    name, title, subtitle, emoji, c1, c2 = item
    img = make_gradient(c1, c2, SIZE)
    draw = ImageDraw.Draw(img, "RGBA")

    # 装饰圆点（半透明）
    draw_circle(draw, (80, 80), 60,  (255, 255, 255, 60))
    draw_circle(draw, (420, 100), 40, (255, 255, 255, 80))
    draw_circle(draw, (450, 420), 80, (255, 255, 255, 50))
    draw_circle(draw, (60, 440), 50,  (255, 255, 255, 60))

    # 中心白色圆背景（让 emoji 更突出）
    cx, cy = SIZE[0] // 2, SIZE[1] // 2 - 30
    draw_circle(draw, (cx, cy), 110, (255, 255, 255, 160))

    # Emoji（大号）
    font_emoji = find_font(140, want_emoji=True)
    bbox = draw.textbbox((0, 0), emoji, font=font_emoji, embedded_color=True)
    ew = bbox[2] - bbox[0]
    eh = bbox[3] - bbox[1]
    try:
        draw.text((cx - ew // 2, cy - eh // 2 - 15), emoji,
                  font=font_emoji, embedded_color=True)
    except Exception:
        # 部分系统不支持 embedded_color
        draw.text((cx - ew // 2, cy - eh // 2 - 15), emoji,
                  font=font_emoji, fill="#3e2723")

    # 中文标题（白色，粗体效果）
    font_title = find_font(36)
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((SIZE[0] - tw) // 2 + 1, 380 + 1), title, font=font_title, fill=(0, 0, 0, 60))
    draw.text(((SIZE[0] - tw) // 2, 380), title, font=font_title, fill="white")

    # 英文副标题
    font_sub = find_font(18)
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = bbox[2] - bbox[0]
    draw.text(((SIZE[0] - sw) // 2, 430), subtitle, font=font_sub, fill=(255, 255, 255, 200))

    path = os.path.join(DEST, name)
    img.convert("RGB").save(path, "JPEG", quality=88)
    print(f"  生成 {name}")


if __name__ == "__main__":
    print(f"输出目录：{DEST}\n")
    for item in ITEMS:
        render(item)
    print(f"\n完成！共生成 {len(ITEMS)} 张图片。")
