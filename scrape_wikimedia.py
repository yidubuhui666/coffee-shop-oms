r"""用 Wikimedia Commons 开放 API 爬取咖啡商品候选图。

无需登录、无反爬、图都是 CC 开放协议。
每款商品下载 4 张候选到 _candidates/<key>/，
之后人工挑选满意的。
"""
import sys, os, shutil, time, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "_candidates")
os.makedirs(CAND, exist_ok=True)

# 每款商品的英文搜索关键词（Wikimedia 上英文标签更丰富）
QUERIES = {
    "espresso":          "espresso coffee cup",
    "americano":         "americano coffee",
    "iced-americano":    "iced americano coffee",
    "double-espresso":   "double espresso doppio",
    "latte":             "caffe latte cup",
    "iced-latte":        "iced latte glass",
    "oat-latte":         "oat milk coffee",
    "vanilla-latte":     "vanilla latte coffee",
    "cappuccino":        "cappuccino cup",
    "flat-white":        "flat white coffee",
    "mocha":             "caffe mocha chocolate",
    "caramel-macchiato": "caramel macchiato coffee",
    "earl-grey-tea":     "earl grey tea",
    "matcha-latte":      "matcha latte",
    "jasmine-tea":       "jasmine tea",
    "cold-brew":         "cold brew coffee",
    "coconut-cold-brew": "coconut coffee drink",
    "iced-lemon-tea":    "iced lemon tea",
    "tiramisu":          "tiramisu dessert",
    "cheesecake":        "cheesecake new york",
    "brownie":           "chocolate brownie",
    "madeleine":         "madeleine cake french",
    "plain-sparkling":   "sparkling water glass",
    "lime-sparkling":    "lime soda drink",
    "berry-sparkling":   "raspberry drink soda",
    "combo-breakfast":   "coffee breakfast croissant",
    "combo-afternoon":   "afternoon tea cake",
    "combo-business":    "espresso brownie chocolate",
    "combo-duo":         "two coffee cups",
}

UA = "CoffeeShopOMS/1.0 (educational project)"


def http_get(url, retries=3):
    """带 UA 的 GET 请求，返回 bytes。429 时指数退避重试。"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def search_commons(keyword, limit=6):
    """搜 Commons，返回 ['File:xxx.jpg', ...]
    优先用'incategory:'语法限定在指定分类中，结果更准。
    """
    url = ("https://commons.wikimedia.org/w/api.php?"
           f"action=query&list=search&srsearch={urllib.parse.quote(keyword)}"
           f"&srnamespace=6&srlimit={limit}&format=json")
    data = json.loads(http_get(url).decode("utf-8"))
    return [item["title"] for item in data["query"]["search"]
            if item["title"].lower().endswith((".jpg", ".jpeg", ".png"))]


def list_category(category, limit=8):
    """直接列分类下的文件（比关键词搜索准）"""
    url = ("https://commons.wikimedia.org/w/api.php?"
           f"action=query&list=categorymembers"
           f"&cmtitle={urllib.parse.quote('Category:' + category)}"
           f"&cmtype=file&cmlimit={limit}&format=json")
    data = json.loads(http_get(url).decode("utf-8"))
    members = data.get("query", {}).get("categorymembers", [])
    return [m["title"] for m in members
            if m["title"].lower().endswith((".jpg", ".jpeg", ".png"))]


def download_for_category(key, category, target_count=4):
    """通过 Wikimedia 分类获取候选图。"""
    folder = os.path.join(CAND, key)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

    print(f"→ {key}：Category:{category}")
    try:
        titles = list_category(category, limit=12)
    except Exception as e:
        print(f"   列分类失败: {e}")
        return 0

    if not titles:
        print("   无结果")
        return 0

    saved = 0
    for title in titles:
        if saved >= target_count:
            break
        try:
            url = get_thumb_url(title, width=600)
            if not url:
                continue
            blob = http_get(url)
            if len(blob) < 5000:
                continue
            with open(os.path.join(folder, f"{saved + 1}.jpg"), "wb") as f:
                f.write(blob)
            saved += 1
            time.sleep(1.5)
        except Exception:
            continue
    time.sleep(2.0)
    print(f"   下载 {saved} 张")
    return saved


def get_thumb_url(title, width=600):
    """获取指定标题文件的缩略图直链。"""
    url = ("https://commons.wikimedia.org/w/api.php?"
           f"action=query&titles={urllib.parse.quote(title)}"
           f"&prop=imageinfo&iiprop=url&iiurlwidth={width}&format=json")
    data = json.loads(http_get(url).decode("utf-8"))
    pages = data["query"]["pages"]
    for _, p in pages.items():
        if "imageinfo" in p:
            ii = p["imageinfo"][0]
            return ii.get("thumburl") or ii.get("url")
    return None


def download_for(key, keyword, target_count=4):
    folder = os.path.join(CAND, key)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

    print(f"→ {key}：「{keyword}」")
    try:
        titles = search_commons(keyword, limit=8)
    except Exception as e:
        print(f"   搜索失败: {e}")
        return 0

    if not titles:
        print("   无结果")
        return 0

    saved = 0
    for title in titles:
        if saved >= target_count:
            break
        try:
            url = get_thumb_url(title, width=600)
            if not url:
                continue
            blob = http_get(url)
            if len(blob) < 5000:  # 太小可能是占位图
                continue
            out_name = f"{saved + 1}.jpg"
            with open(os.path.join(folder, out_name), "wb") as f:
                f.write(blob)
            saved += 1
            time.sleep(1.5)  # 限速，避免 429
        except Exception:
            continue
    time.sleep(2.0)  # 每款商品之间多等等
    print(f"   下载 {saved} 张")
    return saved


if __name__ == "__main__":
    only = sys.argv[1:] or list(QUERIES.keys())
    print(f"准备爬取 {len(only)} 款商品的候选图\n")
    total = 0
    for key in only:
        if key in QUERIES:
            total += download_for(key, QUERIES[key])
    print(f"\n总计下载 {total} 张候选图，位于 {CAND}")
