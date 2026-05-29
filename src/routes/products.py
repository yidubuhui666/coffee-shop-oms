"""菜单 / 商品 CRUD。"""
from decimal import Decimal

from flask import (Blueprint, render_template, request, redirect, url_for, flash)
from sqlalchemy import or_

from models import db, Category, Product
from decorators import login_required, admin_required

bp = Blueprint("products", __name__)


@bp.route("/menu")
@login_required
def menu():
    kw = request.args.get("q", "").strip()
    cat_id = request.args.get("cat", type=int)
    cats = Category.query.order_by(Category.sort_order).all()

    pq = Product.query
    if cat_id:
        pq = pq.filter(Product.category_id == cat_id)
    if kw:
        like = f"%{kw}%"
        pq = pq.filter(or_(Product.name.like(like),
                           Product.description.like(like)))
    prods = pq.order_by(Product.product_id).all()

    by_cat = {}
    for p in prods:
        by_cat.setdefault(p.category_id, []).append(p)
    # 只保留有匹配商品的分类，按分类排序
    groups = [(c, by_cat[c.category_id]) for c in cats if c.category_id in by_cat]

    return render_template("menu.html", groups=groups, all_cats=cats,
                           kw=kw, cat_id=cat_id, total=len(prods))


@bp.route("/products/new", methods=["GET", "POST"])
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
        return redirect(url_for("products.menu"))
    return render_template("product_form.html",
                           categories=Category.query.all(), product=None)


@bp.route("/products/<int:pid>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("products.menu"))
    return render_template("product_form.html",
                           categories=Category.query.all(), product=p)


@bp.route("/products/<int:pid>/delete", methods=["POST"])
@login_required
@admin_required
def product_delete(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("商品已删除。", "ok")
    return redirect(url_for("products.menu"))
