r"""冒烟测试：验证主要页面可访问、下单会正确扣减库存。

运行方式（两种都行）：
    # 1) 直接运行
    cd 项目根目录
    .\src\venv\Scripts\python.exe tests\test_smoke.py
    # 2) 用 pytest（需先 pip install pytest）
    .\src\venv\Scripts\python.exe -m pytest tests\ -v

测试使用临时 SQLite 数据库，不会碰你的 MySQL 数据。
注意：/analytics 用到 MySQL 专有的 EXTRACT 函数，SQLite 不支持，故不在冒烟范围内。
"""
import os
import sys
import tempfile
from decimal import Decimal

# 必须在导入 app 之前设置环境变量，让 config 走临时 SQLite。
_TMP_DB = os.path.join(tempfile.gettempdir(), "coffee_test.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["SECRET_KEY"] = "test-secret"

# 把 src 加入模块搜索路径。
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import create_app          # noqa: E402
from models import (db, Category, Product, Inventory,  # noqa: E402
                    ProductIngredient, Staff)

PAGES = ["/", "/orders", "/menu", "/customers",
         "/inventory", "/staff", "/promotions", "/recipes"]


def _make_client():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    # 用演示管理员登录
    client.post("/login", data={"username": "admin", "password": "admin123"})
    return app, client


def test_pages_return_200():
    """登录后主要页面都应返回 200。"""
    app, client = _make_client()
    for path in PAGES:
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} 返回了 {resp.status_code}"


def test_login_required_redirect():
    """未登录访问受保护页面应重定向到登录页。"""
    app = create_app()
    client = app.test_client()          # 不登录
    resp = client.get("/orders")
    assert resp.status_code == 302
    assert "/login" in resp.headers.get("Location", "")


def test_404_page():
    """不存在的地址返回自定义 404 页面。"""
    app, client = _make_client()
    resp = client.get("/this-page-does-not-exist")
    assert resp.status_code == 404


def test_order_deducts_inventory():
    """下单后，对应原料库存应按配方扣减。"""
    app, client = _make_client()
    with app.app_context():
        # 造一份可控的测试数据：1 个商品 + 1 种原料 + 配方（每杯耗 5 单位）
        cat = Category.query.first()
        prod = Product(category_id=cat.category_id, name="测试拿铁",
                       price=Decimal("20.00"), stock=100, available=True)
        inv = Inventory(name="测试牛奶", unit="ml",
                        quantity=Decimal("1000"), alert_threshold=Decimal("100"))
        db.session.add_all([prod, inv])
        db.session.flush()
        db.session.add(ProductIngredient(product_id=prod.product_id,
                                         ingredient_id=inv.ingredient_id,
                                         consume_qty=Decimal("5")))
        db.session.commit()
        pid, iid = prod.product_id, inv.ingredient_id
        before = db.session.get(Inventory, iid).quantity

    # 下单：买 3 杯
    client.post("/orders/new", data={
        "product_id[]": [str(pid)],
        "quantity[]": ["3"],
        "size[]": ["M"],
        "payment_method": "WECHAT",
    })

    with app.app_context():
        after = db.session.get(Inventory, iid).quantity
        assert float(before) - float(after) == 15.0, \
            f"库存应扣减 15（3杯×5），实际 {float(before)}→{float(after)}"


# ---- 支持不装 pytest 也能直接运行 ----
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n结果：{passed}/{len(tests)} 通过")
    sys.exit(0 if passed == len(tests) else 1)
