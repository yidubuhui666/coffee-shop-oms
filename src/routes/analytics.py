"""统计分析：基础统计 + 8 个多表 JOIN 报表。"""
from datetime import datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for
from sqlalchemy import func

from models import (db, Customer, Staff, Category, Product, Order, OrderItem,
                    Inventory, ProductIngredient, MemberDiscount)
from decorators import login_required

bp = Blueprint("analytics", __name__)


@bp.route("/analytics")
@login_required
def analytics():
    # A. 近 14 天营收
    daily = (db.session.query(func.date(Order.order_time),
                              func.count(Order.order_id),
                              func.sum(Order.total_amount))
             .filter(Order.status != "CANCELLED")
             .group_by(func.date(Order.order_time))
             .order_by(func.date(Order.order_time).desc()).limit(14).all())

    # B. 商品销量排行
    prod_rank = (db.session.query(Product.name,
                                  func.sum(OrderItem.quantity),
                                  func.sum(OrderItem.quantity * OrderItem.unit_price))
                 .join(OrderItem, OrderItem.product_id == Product.product_id)
                 .group_by(Product.product_id)
                 .order_by(func.sum(OrderItem.quantity).desc()).all())

    # 1. 会员消费 TOP10
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

    # 2. 员工业绩排行
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

    # 3. 分类销售
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

    # 4. 商品搭配
    oi1 = db.aliased(OrderItem); oi2 = db.aliased(OrderItem)
    p1  = db.aliased(Product);   p2  = db.aliased(Product)
    pairs = (db.session.query(
            p1.name.label("a"), p2.name.label("b"),
            func.count().label("times"))
        .select_from(oi1)
        .join(oi2, (oi1.order_id == oi2.order_id) & (oi1.product_id < oi2.product_id))
        .join(p1, p1.product_id == oi1.product_id)
        .join(p2, p2.product_id == oi2.product_id)
        .group_by(p1.name, p2.name)
        .order_by(func.count().desc()).limit(10).all())

    # 5. 时段热度
    hourly = (db.session.query(
            func.extract("hour", Order.order_time).label("h"),
            func.count(Order.order_id.distinct()).label("orders"),
            func.sum(OrderItem.quantity).label("cups"))
        .join(OrderItem, OrderItem.order_id == Order.order_id)
        .filter(Order.status != "CANCELLED")
        .group_by(func.extract("hour", Order.order_time))
        .order_by(func.extract("hour", Order.order_time)).all())

    # 6. 原料消耗预测
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

    # 7. 滞销商品
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

    # 8. 会员等级分布
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
                           daily=daily, prod_rank=prod_rank,
                           top_customers=top_customers, top_staff=top_staff,
                           cat_sales=cat_sales, pairs=pairs, hourly=hourly,
                           ing_use=ing_use, slow_movers=slow_movers,
                           level_stat=level_stat)


@bp.route("/stats")
@login_required
def stats():
    """旧地址 /stats 重定向到合并后的 /analytics。"""
    return redirect(url_for("analytics.analytics"))
