r"""使用 icrawler 从 Bing 图片搜索批量下载咖啡商品候选图。

每个商品下载 4 张候选到 _candidates/<key>/，
之后人工挑选满意的，再用 commit_picks.py 提交到正式位置。
"""
import sys, os, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from icrawler.builtin import BingImageCrawler, GoogleImageCrawler, BaiduImageCrawler

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "_candidates")
os.makedirs(CAND, exist_ok=True)

# 每款商品对应的英文搜索关键词
QUERIES = {
    "espresso":          "意式浓缩咖啡 ESPRESSO",
    "americano":         "美式咖啡 黑咖啡",
    "iced-americano":    "冰美式咖啡",
    "double-espresso":   "双份浓缩咖啡",
    "latte":             "拿铁咖啡 拉花",
    "iced-latte":        "冰拿铁",
    "oat-latte":         "燕麦拿铁",
    "vanilla-latte":     "香草拿铁",
    "cappuccino":        "卡布奇诺咖啡",
    "flat-white":        "澳白咖啡",
    "mocha":             "摩卡咖啡",
    "caramel-macchiato": "焦糖玛奇朵",
    "earl-grey-tea":     "伯爵红茶",
    "matcha-latte":      "抹茶拿铁",
    "jasmine-tea":       "茉莉花茶",
    "cold-brew":         "冷萃咖啡",
    "coconut-cold-brew": "椰香冷萃咖啡",
    "iced-lemon-tea":    "冰柠檬茶",
    "tiramisu":          "提拉米苏",
    "cheesecake":        "纽约芝士蛋糕",
    "brownie":           "巧克力布朗尼",
    "madeleine":         "玛德琳蛋糕",
    "plain-sparkling":   "原味气泡水",
    "lime-sparkling":    "青柠气泡水",
    "berry-sparkling":   "莓果气泡水",
    "combo-breakfast":   "咖啡早餐套餐",
    "combo-afternoon":   "下午茶套餐",
    "combo-business":    "咖啡甜点套餐",
    "combo-duo":         "两杯咖啡",
}

if __name__ == "__main__":
    only = sys.argv[1:] or list(QUERIES.keys())
    print(f"准备爬取 {len(only)} 款商品的候选图，每款 4 张\n")

    for key in only:
        if key not in QUERIES:
            print(f"  [跳过] 未知商品 {key}")
            continue
        kw = QUERIES[key]
        folder = os.path.join(CAND, key)

        # 清空旧的候选
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

        print(f"→ {key}：搜索「{kw}」")
        crawler = BaiduImageCrawler(
            storage={"root_dir": folder},
            log_level=40,
            feeder_threads=1, parser_threads=1, downloader_threads=2,
        )
        try:
            crawler.crawl(keyword=kw, max_num=4,
                          min_size=(300, 300),
                          file_idx_offset=0)
            n = len([f for f in os.listdir(folder)
                     if f.lower().endswith((".jpg", ".jpeg", ".png"))])
            print(f"   下载 {n} 张")
        except Exception as e:
            print(f"   失败: {e}")

    print(f"\n候选图全部保存在 {CAND}")
