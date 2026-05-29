"""首页/仪表盘。"""
from datetime import datetime, date, timedelta

from flask import Blueprint, render_template
from sqlalchemy import func

from models import db, Customer, Product, Order, OrderItem, Inventory
from decorators import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    today = date.today()
    yesterday = today - timedelta(days=1)

    today_order_list = Order.query.filter(func.date(Order.order_time) == today).all()
    today_revenue = sum((o.total_amount or 0) for o in today_order_list
                        if o.status != "CANCELLED")

    yest_orders = Order.query.filter(func.date(Order.order_time) == yesterday).count()
    yest_revenue = (db.session.query(func.sum(Order.total_amount))
                    .filter(func.date(Order.order_time) == yesterday)
                    .filter(Order.status != "CANCELLED").scalar() or 0)

    # 今日畅销 TOP5
    top = (db.session.query(Product.name, Product.image,
                            func.sum(OrderItem.quantity).label("qty"))
           .join(OrderItem, OrderItem.product_id == Product.product_id)
           .join(Order, Order.order_id == OrderItem.order_id)
           .filter(func.date(Order.order_time) == today)
           .filter(Order.status != "CANCELLED")
           .group_by(Product.product_id)
           .order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())

    # 近 7 天营收
    seven = (db.session.query(func.date(Order.order_time),
                              func.sum(Order.total_amount))
             .filter(Order.status != "CANCELLED")
             .filter(Order.order_time >= datetime.now() - timedelta(days=7))
             .group_by(func.date(Order.order_time))
             .order_by(func.date(Order.order_time)).all())

    pending_count = Order.query.filter(
        Order.status.in_(["PENDING", "PREPARING", "READY"])).count()

    low_stock = (Inventory.query
                 .filter(Inventory.quantity <= Inventory.alert_threshold)
                 .order_by(Inventory.quantity).all())

    level_counts = dict(db.session.query(
        Customer.member_level, func.count(Customer.customer_id)
    ).group_by(Customer.member_level).all())

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
