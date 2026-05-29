"""会员 CRUD。"""
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort)
from sqlalchemy import func

from models import db, Customer, Order
from decorators import login_required, admin_required

bp = Blueprint("customers", __name__)


@bp.route("/customers")
@login_required
def customers():
    kw = request.args.get("q", "").strip()
    level = request.args.get("level", "")
    page = request.args.get("page", 1, type=int)
    q = Customer.query
    if level:
        q = q.filter_by(member_level=level)
    if kw:
        like = f"%{kw}%"
        q = q.filter((Customer.name.like(like)) | (Customer.phone.like(like)))

    counts = dict(db.session.query(Customer.member_level,
                                   func.count(Customer.customer_id))
                            .group_by(Customer.member_level).all())
    counts["ALL"] = Customer.query.count()

    pagination = (q.order_by(Customer.customer_id.desc())
                   .paginate(page=page, per_page=20, error_out=False))

    return render_template("customers.html",
                           customers=pagination.items,
                           pagination=pagination,
                           kw=kw, level=level, counts=counts)


@bp.route("/customers/new", methods=["GET", "POST"])
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
        return redirect(url_for("customers.customers"))
    return render_template("customer_form.html", customer=None)


@bp.route("/customers/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def customer_edit(cid):
    c = db.session.get(Customer, cid) or abort(404)
    if request.method == "POST":
        c.name = request.form["name"].strip()
        c.phone = request.form.get("phone") or None
        c.email = request.form.get("email") or None
        c.member_level = request.form.get("member_level", c.member_level)
        db.session.commit()
        flash("会员信息已更新。", "ok")
        return redirect(url_for("customers.customers"))
    return render_template("customer_form.html", customer=c)


@bp.route("/customers/<int:cid>/delete", methods=["POST"])
@login_required
@admin_required
def customer_delete(cid):
    c = db.session.get(Customer, cid) or abort(404)
    Order.query.filter_by(customer_id=cid).update({"customer_id": None})
    db.session.delete(c)
    db.session.commit()
    flash(f"会员 {c.name} 已删除（其历史订单转为散客）。", "ok")
    return redirect(url_for("customers.customers"))
