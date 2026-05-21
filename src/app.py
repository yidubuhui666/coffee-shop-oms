"""Coffee Shop Order Management System - Flask entry point."""
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from sqlalchemy import func

from config import Config
from models import (db, Customer, Staff, Category, Product,
                    Order, OrderItem, Inventory, Promotion)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _bootstrap_demo_data()

    _register_routes(app)
    return app


# ----------------------------------------------------------------------
#  Auth helpers
# ----------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "staff_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "ADMIN":
            flash("需要管理员权限。", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapper


# ----------------------------------------------------------------------
#  Demo data bootstrap (only fires if tables are empty)
# ----------------------------------------------------------------------
def _bootstrap_demo_data() -> None:
    if Staff.query.first():
        return

    demo_staff = [
        Staff(username="admin",   password="admin123",   name="杨帆",   role="ADMIN"),
        Staff(username="barista", password="barista123", name="李明",   role="BARISTA"),
        Staff(username="cashier", password="cashier123", name="王磊",   role="CASHIER"),
    ]
    cats = [Category(name=n, sort_order=i + 1) for i, n in enumerate(
        ["浓缩咖啡", "牛奶咖啡", "茶饮", "冷萃饮品", "甜品"])]
    db.session.add_all(demo_staff + cats)
    db.session.commit()

    catmap = {c.name: c.category_id for c in cats}
    seed = [
        ("浓缩咖啡", "美式咖啡",       "经典浓缩 + 热水",            18, 200, "americano.jpg"),
        ("浓缩咖啡", "浓缩咖啡",       "单份意式浓缩",                15, 200, "espresso.jpg"),
        ("牛奶咖啡", "拿铁",           "浓缩咖啡配蒸奶",              25, 150, "latte.jpg"),
        ("牛奶咖啡", "卡布奇诺",       "浓缩咖啡配奶泡",              25, 150, "cappuccino.jpg"),
        ("牛奶咖啡", "摩卡",           "浓缩 + 巧克力 + 牛奶",        28, 120, "mocha.jpg"),
        ("牛奶咖啡", "焦糖玛奇朵",     "浓缩 + 焦糖 + 奶泡",          30, 120, "caramel-macchiato.jpg"),
        ("茶饮",     "伯爵红茶",       "佛手柑香味的红茶",            18, 100, "earl-grey-tea.jpg"),
        ("茶饮",     "抹茶拿铁",       "日式抹茶配牛奶",              28, 100, "matcha-latte.jpg"),
        ("冷萃饮品", "冷萃咖啡",       "12 小时慢萃冷萃咖啡",         26,  80, "cold-brew.jpg"),
        ("冷萃饮品", "冰柠檬茶",       "新鲜柠檬冰茶",                20,  80, "iced-lemon-tea.jpg"),
        ("甜品",     "提拉米苏",       "经典意式甜点",                32,  40, "tiramisu.jpg"),
        ("甜品",     "纽约芝士蛋糕",   "纽约风味芝士蛋糕",            30,  40, "cheesecake.jpg"),
    ]
    db.session.add_all([Product(category_id=catmap[c], name=n, description=d,
                                price=p, stock=s, image=img) for c, n, d, p, s, img in seed])

    # ---- 20 个会员，覆盖四个等级 ----
    surnames = ["张", "李", "王", "赵", "刘", "陈", "杨", "黄", "周", "吴",
                "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
    given   = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "洋", "艳",
               "杰", "涛", "明", "超", "秀英", "霞", "平", "刚", "桂英", "建国"]
    levels  = ["BRONZE"] * 10 + ["SILVER"] * 6 + ["GOLD"] * 3 + ["PLATINUM"] * 1
    customers = []
    for i in range(20):
        customers.append(Customer(
            name=surnames[i] + given[i],
            phone=f"139{i:08d}",
            email=f"user{i+1:02d}@example.com",
            member_level=levels[i],
            points=0,
        ))
    db.session.add_all(customers)

    db.session.add_all([
        Inventory(name="咖啡豆",   unit="kg", quantity=30),
        Inventory(name="牛奶",     unit="L",  quantity=40),
        Inventory(name="白糖",     unit="kg", quantity=15),
        Inventory(name="巧克力",   unit="kg", quantity=5),
        Inventory(name="抹茶粉",   unit="kg", quantity=2),
        Inventory(name="柠檬",     unit="个", quantity=60),
        Inventory(name="一次性杯", unit="个", quantity=400),
        Inventory(name="吸管",     unit="个", quantity=300),
    ])
    db.session.commit()

    # ---- 150 条订单，分布在近 14 天 ----
    products = Product.query.all()
    staff_list = Staff.query.filter(Staff.role != "ADMIN").all()
    all_customers = Customer.query.all()
    pays   = ["WECHAT", "WECHAT", "WECHAT", "ALIPAY", "ALIPAY", "CARD", "CASH"]
    sizes  = ["S", "M", "M", "M", "L"]
    # 加权：让大多数订单已完成/已付款，少数处于其他状态
    statuses = ["COMPLETED"] * 50 + ["PAID"] * 25 + ["READY"] * 8 + \
               ["PREPARING"] * 6 + ["PENDING"] * 4 + ["CANCELLED"] * 7

    rng = random.Random(42)  # 固定种子让数据可复现
    now = datetime.now()

    for _ in range(150):
        # 时间：过去 14 天内的某个营业时段
        days_ago = rng.randint(0, 13)
        hour     = rng.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        minute   = rng.randint(0, 59)
        order_time = (now - timedelta(days=days_ago)).replace(
            hour=hour, minute=minute, second=rng.randint(0, 59), microsecond=0)

        cust = rng.choice(all_customers) if rng.random() > 0.25 else None
        order = Order(
            customer_id=cust.customer_id if cust else None,
            staff_id=rng.choice(staff_list).staff_id,
            order_time=order_time,
            payment_method=rng.choice(pays),
            dine_in=rng.random() > 0.4,
            status=rng.choice(statuses),
            remark=rng.choice([None, None, None, "少糖", "去冰", "多加一份糖", "打包"]),
        )
        db.session.add(order)
        db.session.flush()

        # 每单 1~4 个商品
        chosen = rng.sample(products, k=rng.randint(1, 4))
        total = Decimal("0")
        for p in chosen:
            qty = rng.randint(1, 3)
            item = OrderItem(order_id=order.order_id, product_id=p.product_id,
                             quantity=qty, unit_price=p.price,
                             size=rng.choice(sizes))
            total += p.price * qty
            db.session.add(item)
        order.total_amount = total
        # 已付/已完成/制作中/待取 都视作付款过
        if order.status in ("PAID", "PREPARING", "READY", "COMPLETED"):
            order.paid_amount = total
            if cust:
                cust.points = (cust.points or 0) + int(total)

    db.session.commit()


# ----------------------------------------------------------------------
#  Routes
# ----------------------------------------------------------------------
def _register_routes(app: Flask) -> None:

    # ---- Auth ----
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = Staff.query.filter_by(username=request.form["username"]).first()
            if user and user.password == request.form["password"] and user.active:
                session["staff_id"], session["name"], session["role"] = (
                    user.staff_id, user.name, user.role)
                flash(f"欢迎，{user.name}！", "ok")
                return redirect(url_for("dashboard"))
            flash("用户名或密码错误。", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---- Dashboard ----
    @app.route("/")
    @login_required
    def dashboard():
        today = date.today()
        today_orders = Order.query.filter(func.date(Order.order_time) == today).all()
        today_revenue = sum((o.total_amount or 0) for o in today_orders
                            if o.status != "CANCELLED")
        top = (db.session.query(Product.name,
                                func.sum(OrderItem.quantity).label("qty"))
               .join(OrderItem, OrderItem.product_id == Product.product_id)
               .group_by(Product.product_id)
               .order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())
        return render_template("dashboard.html",
                               today_orders=len(today_orders),
                               today_revenue=today_revenue,
                               total_products=Product.query.count(),
                               total_customers=Customer.query.count(),
                               top_products=top)

    # ---- Menu / Products ----
    @app.route("/menu")
    @login_required
    def menu():
        cats = Category.query.order_by(Category.sort_order).all()
        return render_template("menu.html", categories=cats)

    @app.route("/products/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def product_new():
        if request.method == "POST":
            db.session.add(Product(
                category_id=int(request.form["category_id"]),
                name=request.form["name"],
                description=request.form.get("description"),
                price=Decimal(request.form["price"]),
                stock=int(request.form.get("stock", 0)),
            ))
            db.session.commit()
            flash("商品已添加。", "ok")
            return redirect(url_for("menu"))
        return render_template("product_form.html",
                               categories=Category.query.all(), product=None)

    @app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def product_edit(pid):
        p = Product.query.get_or_404(pid)
        if request.method == "POST":
            p.name        = request.form["name"]
            p.description = request.form.get("description")
            p.price       = Decimal(request.form["price"])
            p.stock       = int(request.form.get("stock", 0))
            p.category_id = int(request.form["category_id"])
            p.available   = "available" in request.form
            db.session.commit()
            flash("商品已更新。", "ok")
            return redirect(url_for("menu"))
        return render_template("product_form.html",
                               categories=Category.query.all(), product=p)

    @app.route("/products/<int:pid>/delete", methods=["POST"])
    @login_required
    @admin_required
    def product_delete(pid):
        p = Product.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        flash("商品已删除。", "ok")
        return redirect(url_for("menu"))

    # ---- Orders ----
    @app.route("/orders")
    @login_required
    def orders():
        q = Order.query.order_by(Order.order_time.desc())
        status = request.args.get("status")
        if status:
            q = q.filter_by(status=status)
        return render_template("orders.html", orders=q.limit(200).all(),
                               cur_status=status)

    @app.route("/orders/new", methods=["GET", "POST"])
    @login_required
    def order_new():
        if request.method == "POST":
            cid_raw = request.form.get("customer_id")
            order = Order(customer_id=int(cid_raw) if cid_raw else None,
                          staff_id=session["staff_id"],
                          payment_method=request.form.get("payment_method", "WECHAT"),
                          dine_in=("dine_in" in request.form),
                          remark=request.form.get("remark"))
            db.session.add(order)
            db.session.flush()

            ids   = request.form.getlist("product_id[]")
            qtys  = request.form.getlist("quantity[]")
            sizes = request.form.getlist("size[]")
            total = Decimal("0")
            for pid, qty, sz in zip(ids, qtys, sizes):
                if not pid or int(qty) <= 0:
                    continue
                p = Product.query.get(int(pid))
                item = OrderItem(order_id=order.order_id, product_id=p.product_id,
                                 quantity=int(qty), unit_price=p.price, size=sz or "M")
                total += p.price * int(qty)
                db.session.add(item)

            order.total_amount = total
            db.session.commit()
            flash(f"订单 #{order.order_id} 已创建。", "ok")
            return redirect(url_for("order_detail", oid=order.order_id))

        return render_template("order_new.html",
                               products=Product.query.filter_by(available=True).all(),
                               customers=Customer.query.all())

    @app.route("/orders/<int:oid>")
    @login_required
    def order_detail(oid):
        o = Order.query.get_or_404(oid)
        return render_template("order_detail.html", order=o)

    @app.route("/orders/<int:oid>/status", methods=["POST"])
    @login_required
    def order_status(oid):
        o = Order.query.get_or_404(oid)
        new_status = request.form["status"]
        # award loyalty points the same way the SQL trigger does
        if new_status == "PAID" and o.status != "PAID" and o.customer_id:
            cust = Customer.query.get(o.customer_id)
            if cust:
                cust.points += int(o.total_amount or 0)
        o.status = new_status
        if new_status == "PAID":
            o.paid_amount = o.total_amount
        db.session.commit()
        flash(f"订单 #{oid} 状态已更新为 {new_status}", "ok")
        return redirect(url_for("order_detail", oid=oid))

    # ---- Customers ----
    @app.route("/customers")
    @login_required
    def customers():
        kw = request.args.get("q", "").strip()
        q = Customer.query
        if kw:
            like = f"%{kw}%"
            q = q.filter((Customer.name.like(like)) | (Customer.phone.like(like)))
        return render_template("customers.html",
                               customers=q.order_by(Customer.customer_id.desc()).all(),
                               kw=kw)

    @app.route("/customers/new", methods=["GET", "POST"])
    @login_required
    def customer_new():
        if request.method == "POST":
            db.session.add(Customer(
                name=request.form["name"],
                phone=request.form.get("phone"),
                email=request.form.get("email"),
                member_level=request.form.get("member_level", "BRONZE"),
            ))
            db.session.commit()
            flash("会员已添加。", "ok")
            return redirect(url_for("customers"))
        return render_template("customer_form.html")

    # ---- Inventory ----
    @app.route("/inventory", methods=["GET", "POST"])
    @login_required
    @admin_required
    def inventory():
        if request.method == "POST":
            iid = int(request.form["ingredient_id"])
            item = Inventory.query.get_or_404(iid)
            item.quantity = Decimal(request.form["quantity"])
            db.session.commit()
            flash("库存已更新。", "ok")
            return redirect(url_for("inventory"))
        return render_template("inventory.html",
                               items=Inventory.query.order_by(Inventory.name).all())

    # ---- Stats ----
    @app.route("/stats")
    @login_required
    def stats():
        rev = (db.session.query(func.date(Order.order_time),
                                func.count(Order.order_id),
                                func.sum(Order.total_amount))
               .filter(Order.status != "CANCELLED")
               .group_by(func.date(Order.order_time))
               .order_by(func.date(Order.order_time).desc()).limit(14).all())
        prod = (db.session.query(Product.name,
                                 func.sum(OrderItem.quantity),
                                 func.sum(OrderItem.quantity * OrderItem.unit_price))
                .join(OrderItem, OrderItem.product_id == Product.product_id)
                .group_by(Product.product_id)
                .order_by(func.sum(OrderItem.quantity).desc()).all())
        return render_template("stats.html", daily=rev, products=prod)

    # ---- JSON API (lookup) ----
    @app.route("/api/product/<int:pid>")
    @login_required
    def api_product(pid):
        p = Product.query.get_or_404(pid)
        return jsonify({"id": p.product_id, "name": p.name, "price": float(p.price)})


# ----------------------------------------------------------------------
if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5050, debug=True)
