"""订单管理。"""
from datetime import date
from decimal import Decimal

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash)
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from models import (db, Customer, Product, Order, OrderItem,
                    Promotion, ProductIngredient, Inventory, MemberDiscount)
from decorators import login_required

bp = Blueprint("orders", __name__)


@bp.route("/orders")
@login_required
def orders():
    # N+1 修复：预加载关联对象
    q = (Order.query
         .options(joinedload(Order.customer),
                  joinedload(Order.staff),
                  selectinload(Order.items))
         .order_by(Order.order_time.desc()))
    status = request.args.get("status")
    when = request.args.get("when", "today")
    page = request.args.get("page", 1, type=int)
    per_page = 30

    today = date.today()
    if when == "today":
        q = q.filter(func.date(Order.order_time) == today)
    elif when == "history":
        q = q.filter(func.date(Order.order_time) < today)
    if status:
        q = q.filter_by(status=status)

    base = Order.query
    if status:
        base = base.filter_by(status=status)
    cnt_today   = base.filter(func.date(Order.order_time) == today).count()
    cnt_history = base.filter(func.date(Order.order_time) <  today).count()
    cnt_all     = base.count()

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    return render_template("orders.html",
                           orders=pagination.items,
                           pagination=pagination,
                           cur_status=status, when=when,
                           cnt_today=cnt_today, cnt_history=cnt_history,
                           cnt_all=cnt_all)


@bp.route("/orders/new", methods=["GET", "POST"])
@login_required
def order_new():
    if request.method == "POST":
        cid_raw = request.form.get("customer_id")
        promo_code = request.form.get("promo_code", "").strip()

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
        consume_map = {}

        for pid, qty, sz in zip(ids, qtys, sizes):
            if not pid or int(qty) <= 0:
                continue
            p = Product.query.get(int(pid))
            qty_int = int(qty)
            item = OrderItem(order_id=order.order_id, product_id=p.product_id,
                             quantity=qty_int, unit_price=p.price, size=sz or "M")
            subtotal += p.price * qty_int
            db.session.add(item)

            for link in ProductIngredient.query.filter_by(product_id=p.product_id).all():
                consume_map[link.ingredient_id] = (
                    consume_map.get(link.ingredient_id, Decimal("0"))
                    + Decimal(str(link.consume_qty)) * qty_int)

        # 会员折扣
        discount_rate = Decimal("1.00")
        if order.customer_id:
            md = (db.session.query(MemberDiscount)
                  .join(Customer, Customer.member_level == MemberDiscount.level)
                  .filter(Customer.customer_id == order.customer_id).first())
            if md:
                discount_rate = Decimal(str(md.discount))
        if promo:
            promo_rate = Decimal(str(promo.discount))
            if promo_rate < discount_rate:
                discount_rate = promo_rate
        total = (subtotal * discount_rate).quantize(Decimal("0.01"))
        order.total_amount = total

        # 扣库存
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
        return redirect(url_for("orders.order_detail", oid=order.order_id))

    md_map = {m.level: float(m.discount) for m in MemberDiscount.query.all()}
    return render_template("order_new.html",
                           products=Product.query.filter_by(available=True).all(),
                           customers=Customer.query.all(),
                           md_map=md_map)


@bp.route("/orders/<int:oid>")
@login_required
def order_detail(oid):
    o = (Order.query
         .options(joinedload(Order.customer),
                  joinedload(Order.staff),
                  selectinload(Order.items).joinedload(OrderItem.product))
         .filter_by(order_id=oid).first_or_404())
    return render_template("order_detail.html", order=o)


@bp.route("/orders/<int:oid>/status", methods=["POST"])
@login_required
def order_status(oid):
    o = Order.query.get_or_404(oid)
    new_status = request.form["status"]
    if new_status == "PAID" and o.status != "PAID" and o.customer_id:
        cust = Customer.query.get(o.customer_id)
        if cust:
            cust.points += int(o.total_amount or 0)
    o.status = new_status
    if new_status == "PAID":
        o.paid_amount = o.total_amount
    db.session.commit()
    flash(f"订单 #{oid} 状态已更新为 {new_status}", "ok")
    return redirect(url_for("orders.order_detail", oid=oid))
