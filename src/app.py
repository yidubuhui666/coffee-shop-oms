"""Coffee Shop Order Management System - Flask entry point."""
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort)
from sqlalchemy import func

from config import Config
from models import (db, Customer, Staff, Category, Product,
                    Order, OrderItem, Inventory, Promotion,
                    ProductIngredient, MemberDiscount)


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
        Staff(username="admin",     password="admin123",   name="杨帆",   role="ADMIN"),
        Staff(username="xuyueqian", password="xuyq123",    name="许跃骞", role="ADMIN"),
        Staff(username="barista",   password="barista123", name="李明",   role="BARISTA"),
        Staff(username="cashier",   password="cashier123", name="王磊",   role="CASHIER"),
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
            uname = request.form.get("username", "").strip()
            pwd   = request.form.get("password", "")
            user  = Staff.query.filter_by(username=uname).first()

            if not user:
                flash("账号无效。", "error")
            elif not user.active:
                flash("该账号已被停用，请联系管理员。", "error")
            elif user.password != pwd:
                flash("密码错误。", "error")
            else:
                session["staff_id"], session["name"], session["role"] = (
                    user.staff_id, user.name, user.role)
                flash(f"欢迎，{user.name}！", "ok")
                return redirect(url_for("dashboard"))
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
        yesterday = today - timedelta(days=1)

        today_order_list = Order.query.filter(func.date(Order.order_time) == today).all()
        today_revenue = sum((o.total_amount or 0) for o in today_order_list
                            if o.status != "CANCELLED")

        # 昨日数据（用于环比）
        yest_orders_q = Order.query.filter(func.date(Order.order_time) == yesterday)
        yest_orders = yest_orders_q.count()
        yest_revenue = (db.session.query(func.sum(Order.total_amount))
                        .filter(func.date(Order.order_time) == yesterday)
                        .filter(Order.status != "CANCELLED").scalar() or 0)

        # 今日畅销 TOP5（含商品图）
        top = (db.session.query(Product.name, Product.image,
                                func.sum(OrderItem.quantity).label("qty"))
               .join(OrderItem, OrderItem.product_id == Product.product_id)
               .join(Order, Order.order_id == OrderItem.order_id)
               .filter(func.date(Order.order_time) == today)
               .filter(Order.status != "CANCELLED")
               .group_by(Product.product_id)
               .order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())

        # 近 7 天营收（用于迷你柱状图）
        seven = (db.session.query(func.date(Order.order_time),
                                  func.sum(Order.total_amount))
                 .filter(Order.status != "CANCELLED")
                 .filter(Order.order_time >= datetime.now() - timedelta(days=7))
                 .group_by(func.date(Order.order_time))
                 .order_by(func.date(Order.order_time)).all())

        # 待处理订单
        pending_count = Order.query.filter(
            Order.status.in_(["PENDING", "PREPARING", "READY"])).count()

        # 库存预警
        low_stock = (Inventory.query
                     .filter(Inventory.quantity <= Inventory.alert_threshold)
                     .order_by(Inventory.quantity).all())

        # 会员等级分布
        level_counts = dict(db.session.query(
            Customer.member_level, func.count(Customer.customer_id)
        ).group_by(Customer.member_level).all())

        # 环比计算
        def pct(now, prev):
            if not prev: return None
            return round((now - prev) / prev * 100, 1)

        return render_template("dashboard.html",
                               today_orders=len(today_order_list),
                               today_revenue=today_revenue,
                               yest_orders=yest_orders,
                               yest_revenue=yest_revenue,
                               pct_orders=pct(len(today_order_list), yest_orders),
                               pct_revenue=pct(float(today_revenue), float(yest_revenue)),
                               total_products=Product.query.count(),
                               total_customers=Customer.query.count(),
                               top_products=top,
                               seven_days=seven,
                               pending_count=pending_count,
                               low_stock=low_stock,
                               level_counts=level_counts)

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
        when = request.args.get("when", "today")  # today / history / all

        today = date.today()
        if when == "today":
            q = q.filter(func.date(Order.order_time) == today)
        elif when == "history":
            q = q.filter(func.date(Order.order_time) < today)

        if status:
            q = q.filter_by(status=status)

        # 统计 3 个 tab 各自的数量（带 status 过滤一起算）
        base = Order.query
        if status:
            base = base.filter_by(status=status)
        cnt_today   = base.filter(func.date(Order.order_time) == today).count()
        cnt_history = base.filter(func.date(Order.order_time) <  today).count()
        cnt_all     = base.count()

        return render_template("orders.html", orders=q.limit(300).all(),
                               cur_status=status, when=when,
                               cnt_today=cnt_today, cnt_history=cnt_history,
                               cnt_all=cnt_all)

    @app.route("/orders/new", methods=["GET", "POST"])
    @login_required
    def order_new():
        if request.method == "POST":
            cid_raw = request.form.get("customer_id")
            promo_code = request.form.get("promo_code", "").strip()

            # 优惠券查找
            promo = None
            if promo_code:
                promo = Promotion.query.filter_by(code=promo_code, active=True).first()
                if not promo:
                    flash(f"优惠码 {promo_code} 无效或已失效。", "error")

            order = Order(customer_id=int(cid_raw) if cid_raw else None,
                          staff_id=session["staff_id"],
                          promo_id=promo.promo_id if promo else None,
                          payment_method=request.form.get("payment_method", "WECHAT"),
                          dine_in=("dine_in" in request.form),
                          remark=request.form.get("remark"))
            db.session.add(order)
            db.session.flush()

            ids   = request.form.getlist("product_id[]")
            qtys  = request.form.getlist("quantity[]")
            sizes = request.form.getlist("size[]")
            subtotal = Decimal("0")
            consume_map = {}   # ingredient_id -> 总消耗量

            for pid, qty, sz in zip(ids, qtys, sizes):
                if not pid or int(qty) <= 0:
                    continue
                p = Product.query.get(int(pid))
                qty_int = int(qty)
                item = OrderItem(order_id=order.order_id, product_id=p.product_id,
                                 quantity=qty_int, unit_price=p.price, size=sz or "M")
                subtotal += p.price * qty_int
                db.session.add(item)

                # 累计原料消耗
                for link in ProductIngredient.query.filter_by(product_id=p.product_id).all():
                    consume_map[link.ingredient_id] = (
                        consume_map.get(link.ingredient_id, Decimal("0"))
                        + Decimal(str(link.consume_qty)) * qty_int)

            # 会员折扣（多表 JOIN：customer + member_discount）
            total = subtotal
            discount_rate = Decimal("1.00")
            if order.customer_id:
                md = (db.session.query(MemberDiscount)
                      .join(Customer, Customer.member_level == MemberDiscount.level)
                      .filter(Customer.customer_id == order.customer_id).first())
                if md:
                    discount_rate = Decimal(str(md.discount))
            # 优惠券折扣（取更优惠）
            if promo:
                promo_rate = Decimal(str(promo.discount))
                if promo_rate < discount_rate:
                    discount_rate = promo_rate
            total = (subtotal * discount_rate).quantize(Decimal("0.01"))

            order.total_amount = total

            # 自动扣减原料库存
            for iid, qty_consumed in consume_map.items():
                inv = db.session.get(Inventory, iid)
                if inv:
                    inv.quantity = (Decimal(str(inv.quantity)) - qty_consumed)

            db.session.commit()
            msg = f"订单 #{order.order_id} 已创建（原价 ¥{subtotal:.2f}"
            if discount_rate < 1:
                msg += f"，{int(discount_rate*100)}折后 ¥{total:.2f}"
            msg += "）"
            flash(msg, "ok")
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
        level = request.args.get("level", "")  # "" / BRONZE / SILVER / GOLD / PLATINUM
        q = Customer.query
        if level:
            q = q.filter_by(member_level=level)
        if kw:
            like = f"%{kw}%"
            q = q.filter((Customer.name.like(like)) | (Customer.phone.like(like)))

        # 各等级人数
        counts = dict(db.session.query(Customer.member_level,
                                       func.count(Customer.customer_id))
                                .group_by(Customer.member_level).all())
        counts["ALL"] = Customer.query.count()

        return render_template("customers.html",
                               customers=q.order_by(Customer.customer_id.desc()).all(),
                               kw=kw, level=level, counts=counts)

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

    # ---- Staff (admin only) ----
    @app.route("/staff")
    @login_required
    @admin_required
    def staff_list():
        kw = request.args.get("q", "").strip()
        q = Staff.query
        if kw:
            like = f"%{kw}%"
            q = q.filter((Staff.name.like(like)) | (Staff.username.like(like)))
        return render_template("staff.html",
                               staff_list=q.order_by(Staff.staff_id).all(),
                               kw=kw)

    @app.route("/staff/new", methods=["GET", "POST"])
    @login_required
    @admin_required
    def staff_new():
        if request.method == "POST":
            uname = request.form["username"].strip()
            if Staff.query.filter_by(username=uname).first():
                flash("该用户名已被占用。", "error")
                return redirect(url_for("staff_new"))
            db.session.add(Staff(
                username=uname,
                password=request.form["password"],
                name=request.form["name"].strip(),
                role=request.form.get("role", "CASHIER"),
                phone=request.form.get("phone"),
                active=True,
            ))
            db.session.commit()
            flash("员工已添加。", "ok")
            return redirect(url_for("staff_list"))
        return render_template("staff_form.html", staff=None)

    @app.route("/staff/<int:sid>/edit", methods=["GET", "POST"])
    @login_required
    @admin_required
    def staff_edit(sid):
        s = db.session.get(Staff, sid) or abort(404)
        if request.method == "POST":
            s.name = request.form["name"].strip()
            s.role = request.form.get("role", s.role)
            s.phone = request.form.get("phone")
            new_pwd = request.form.get("password", "").strip()
            if new_pwd:
                s.password = new_pwd
            db.session.commit()
            flash("员工信息已更新。", "ok")
            return redirect(url_for("staff_list"))
        return render_template("staff_form.html", staff=s)

    @app.route("/staff/<int:sid>/toggle", methods=["POST"])
    @login_required
    @admin_required
    def staff_toggle(sid):
        s = db.session.get(Staff, sid) or abort(404)
        if s.staff_id == session.get("staff_id"):
            flash("不能停用当前登录的账号。", "error")
            return redirect(url_for("staff_list"))
        s.active = not s.active
        db.session.commit()
        flash(f"员工 {s.name} 已{'启用' if s.active else '停用'}。", "ok")
        return redirect(url_for("staff_list"))

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

    # 旧 /stats 重定向到合并后的 /analytics
    @app.route("/stats")
    @login_required
    def stats():
        return redirect(url_for("analytics"))

    # ---- JSON API (lookup) ----
    @app.route("/api/product/<int:pid>")
    @login_required
    def api_product(pid):
        p = Product.query.get_or_404(pid)
        return jsonify({"id": p.product_id, "name": p.name, "price": float(p.price)})

    # ---- 配方管理（商品-原料关系）----
    @app.route("/recipes")
    @login_required
    def recipes():
        # 视角1: 按商品分组（products ⋈ categories ⋈ product_ingredient ⋈ inventory）
        rows = (db.session.query(
                Product.product_id, Product.name, Product.image, Product.price,
                Category.name.label("cat"),
                Inventory.name.label("ing"), Inventory.unit,
                Inventory.quantity, Inventory.alert_threshold,
                ProductIngredient.consume_qty)
            .join(Category, Category.category_id == Product.category_id)
            .outerjoin(ProductIngredient,
                       ProductIngredient.product_id == Product.product_id)
            .outerjoin(Inventory,
                       Inventory.ingredient_id == ProductIngredient.ingredient_id)
            .order_by(Category.sort_order, Product.product_id).all())

        by_product = {}
        for pid, pname, img, price, cat, ing, unit, qty, alert, consume in rows:
            if pid not in by_product:
                by_product[pid] = {"name": pname, "img": img, "price": price,
                                   "cat": cat, "ings": []}
            if ing:
                by_product[pid]["ings"].append({
                    "ing": ing, "unit": unit,
                    "consume": consume, "stock": qty, "low": qty <= alert
                })

        # 视角2: 按原料分组（inventory ⋈ product_ingredient ⋈ products ⋈ categories）
        rows2 = (db.session.query(
                Inventory.ingredient_id, Inventory.name, Inventory.unit,
                Inventory.quantity, Inventory.alert_threshold,
                Product.name.label("pname"), Product.image.label("pimg"),
                Category.name.label("cat"),
                ProductIngredient.consume_qty)
            .outerjoin(ProductIngredient,
                       ProductIngredient.ingredient_id == Inventory.ingredient_id)
            .outerjoin(Product, Product.product_id == ProductIngredient.product_id)
            .outerjoin(Category, Category.category_id == Product.category_id)
            .order_by(Inventory.name, Product.product_id).all())

        by_ing = {}
        for iid, iname, unit, qty, alert, pname, pimg, cat, consume in rows2:
            if iid not in by_ing:
                by_ing[iid] = {"name": iname, "unit": unit, "stock": qty,
                               "low": qty <= alert, "prods": []}
            if pname:
                by_ing[iid]["prods"].append({
                    "name": pname, "img": pimg, "cat": cat, "consume": consume
                })

        return render_template("recipes.html",
                               by_product=by_product.values(),
                               by_ing=by_ing.values())

    # ---- 数据分析（综合：基础统计 + 多表联查报表）----
    @app.route("/analytics")
    @login_required
    def analytics():
        # 基础统计 A: 近 14 天营收
        daily = (db.session.query(func.date(Order.order_time),
                                  func.count(Order.order_id),
                                  func.sum(Order.total_amount))
                 .filter(Order.status != "CANCELLED")
                 .group_by(func.date(Order.order_time))
                 .order_by(func.date(Order.order_time).desc()).limit(14).all())

        # 基础统计 B: 商品销量排行
        prod_rank = (db.session.query(Product.name,
                                      func.sum(OrderItem.quantity),
                                      func.sum(OrderItem.quantity * OrderItem.unit_price))
                     .join(OrderItem, OrderItem.product_id == Product.product_id)
                     .group_by(Product.product_id)
                     .order_by(func.sum(OrderItem.quantity).desc()).all())

        # 1. 会员消费 TOP10（customers + orders + order_items 三表 JOIN）
        top_customers = (db.session.query(
                Customer.name, Customer.member_level,
                func.count(Order.order_id.distinct()).label("order_cnt"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("amt"))
            .join(Order,     Order.customer_id == Customer.customer_id)
            .join(OrderItem, OrderItem.order_id == Order.order_id)
            .filter(Order.status != "CANCELLED")
            .group_by(Customer.customer_id)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .limit(10).all())

        # 2. 员工业绩排行（staff + orders + order_items 三表 JOIN）
        top_staff = (db.session.query(
                Staff.name, Staff.role,
                func.count(Order.order_id.distinct()).label("order_cnt"),
                func.sum(OrderItem.quantity).label("item_cnt"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("amt"))
            .join(Order,     Order.staff_id == Staff.staff_id)
            .join(OrderItem, OrderItem.order_id == Order.order_id)
            .filter(Order.status != "CANCELLED")
            .group_by(Staff.staff_id)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc()).all())

        # 3. 分类销售分析（categories + products + order_items 三表 JOIN）
        cat_sales = (db.session.query(
                Category.name,
                func.count(Product.product_id.distinct()).label("prod_cnt"),
                func.sum(OrderItem.quantity).label("qty"),
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("amt"))
            .join(Product,   Product.category_id == Category.category_id)
            .join(OrderItem, OrderItem.product_id == Product.product_id)
            .join(Order,     Order.order_id == OrderItem.order_id)
            .filter(Order.status != "CANCELLED")
            .group_by(Category.category_id)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc()).all())

        # 4. 商品搭配分析（order_items 自连接 + products 两次 JOIN）
        oi1 = db.aliased(OrderItem)
        oi2 = db.aliased(OrderItem)
        p1  = db.aliased(Product)
        p2  = db.aliased(Product)
        pairs = (db.session.query(
                p1.name.label("a"), p2.name.label("b"),
                func.count().label("times"))
            .select_from(oi1)
            .join(oi2, (oi1.order_id == oi2.order_id) & (oi1.product_id < oi2.product_id))
            .join(p1, p1.product_id == oi1.product_id)
            .join(p2, p2.product_id == oi2.product_id)
            .group_by(p1.name, p2.name)
            .order_by(func.count().desc()).limit(10).all())

        # 5. 时段热度（按下单小时聚合，orders + order_items）
        hourly = (db.session.query(
                func.hour(Order.order_time).label("h"),
                func.count(Order.order_id.distinct()).label("orders"),
                func.sum(OrderItem.quantity).label("cups"))
            .join(OrderItem, OrderItem.order_id == Order.order_id)
            .filter(Order.status != "CANCELLED")
            .group_by(func.hour(Order.order_time))
            .order_by(func.hour(Order.order_time)).all())

        # 6. 原料消耗预测（inventory + product_ingredient + order_items + products 四表 JOIN）
        ing_use = (db.session.query(
                Inventory.name, Inventory.unit, Inventory.quantity,
                Inventory.alert_threshold,
                func.coalesce(func.sum(
                    ProductIngredient.consume_qty * OrderItem.quantity), 0).label("used"))
            .outerjoin(ProductIngredient,
                       ProductIngredient.ingredient_id == Inventory.ingredient_id)
            .outerjoin(OrderItem,
                       OrderItem.product_id == ProductIngredient.product_id)
            .outerjoin(Order,
                       (Order.order_id == OrderItem.order_id) & (Order.status != "CANCELLED"))
            .group_by(Inventory.ingredient_id)
            .order_by(func.coalesce(func.sum(
                ProductIngredient.consume_qty * OrderItem.quantity), 0).desc()).all())

        # 7. 滞销商品（products LEFT JOIN order_items，最近 7 天未销售）
        cutoff = datetime.now() - timedelta(days=7)
        sold_recently = (db.session.query(OrderItem.product_id)
            .join(Order, Order.order_id == OrderItem.order_id)
            .filter(Order.order_time >= cutoff).distinct().subquery())
        slow_movers = (db.session.query(
                Product.name, Category.name.label("cat"),
                Product.price, Product.stock)
            .join(Category, Category.category_id == Product.category_id)
            .filter(~Product.product_id.in_(db.session.query(sold_recently)))
            .order_by(Product.stock.desc()).all())

        # 8. 会员等级分布与消费力对比（customers + member_discount + orders）
        level_stat = (db.session.query(
                MemberDiscount.label, MemberDiscount.discount,
                func.count(Customer.customer_id.distinct()).label("cust_cnt"),
                func.coalesce(func.sum(Order.total_amount), 0).label("amt"))
            .outerjoin(Customer, Customer.member_level == MemberDiscount.level)
            .outerjoin(Order,
                       (Order.customer_id == Customer.customer_id) & (Order.status != "CANCELLED"))
            .group_by(MemberDiscount.level, MemberDiscount.discount, MemberDiscount.label)
            .order_by(MemberDiscount.discount).all())

        return render_template("analytics.html",
                               daily=daily,
                               prod_rank=prod_rank,
                               top_customers=top_customers,
                               top_staff=top_staff,
                               cat_sales=cat_sales,
                               pairs=pairs,
                               hourly=hourly,
                               ing_use=ing_use,
                               slow_movers=slow_movers,
                               level_stat=level_stat)


# ----------------------------------------------------------------------
if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5050, debug=True)
