"""原料库存管理（仅管理员）。"""
from datetime import datetime, timedelta
from decimal import Decimal

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort)
from sqlalchemy import func

from models import (db, Product, Order, OrderItem, Inventory, ProductIngredient)
from decorators import login_required, admin_required

bp = Blueprint("inventory", __name__)


@bp.route("/inventory", methods=["GET", "POST"])
@login_required
@admin_required
def inventory():
    if request.method == "POST":
        iid = int(request.form["ingredient_id"])
        item = Inventory.query.get_or_404(iid)
        mode = request.form.get("mode", "set")
        new_qty = Decimal(request.form["quantity"])
        if mode == "add":
            item.quantity = Decimal(str(item.quantity)) + new_qty
        else:
            item.quantity = new_qty
        if request.form.get("alert_threshold"):
            item.alert_threshold = Decimal(request.form["alert_threshold"])
        db.session.commit()
        flash(f"原料「{item.name}」已更新（当前 {item.quantity} {item.unit}）。", "ok")
        return redirect(url_for("inventory.inventory", selected=iid))

    all_items = Inventory.query.order_by(Inventory.name).all()

    def cat_of(name):
        n = name
        if any(k in n for k in ["咖啡豆"]): return ("coffee",  "☕ 咖啡豆", 1)
        if any(k in n for k in ["牛奶","奶油","奶酪","黄油","奶"]): return ("dairy",   "🥛 乳制品", 2)
        if any(k in n for k in ["糖","糖浆","蜂蜜"]): return ("sugar",   "🍯 糖与糖浆", 3)
        if any(k in n for k in ["巧克力","可可","抹茶","肉桂","香草精"]): return ("flavor",  "🌿 风味配料", 4)
        if any(k in n for k in ["茶","柠檬","薄荷"]): return ("tea",     "🍵 茶饮原料", 5)
        if any(k in n for k in ["面粉","鸡蛋","饼干"]): return ("bakery",  "🍰 烘焙原料", 6)
        return ("pack", "📦 包装耗材", 7)

    groups = {}
    for it in all_items:
        key, label, order = cat_of(it.name)
        groups.setdefault((order, key, label), []).append(it)
    groups = [(label, key, items_) for (order, key, label), items_ in sorted(groups.items())]

    selected_id = request.args.get("selected", type=int)
    selected = None
    if selected_id:
        selected = db.session.get(Inventory, selected_id)
    if not selected and all_items:
        selected = all_items[0]

    info = {}
    if selected:
        used_in = (db.session.query(Product.name, ProductIngredient.consume_qty)
                   .join(ProductIngredient,
                         ProductIngredient.product_id == Product.product_id)
                   .filter(ProductIngredient.ingredient_id == selected.ingredient_id)
                   .all())
        info["used_in"] = used_in

        week_ago = datetime.now() - timedelta(days=7)
        consumed = (db.session.query(
            func.sum(OrderItem.quantity * ProductIngredient.consume_qty))
            .join(ProductIngredient,
                  ProductIngredient.product_id == OrderItem.product_id)
            .join(Order, Order.order_id == OrderItem.order_id)
            .filter(ProductIngredient.ingredient_id == selected.ingredient_id)
            .filter(Order.order_time >= week_ago)
            .filter(Order.status != "CANCELLED").scalar()) or 0
        info["consumed_7d"] = float(consumed)
        avg_per_day = float(consumed) / 7 if consumed else 0
        info["days_left"] = round(float(selected.quantity) / avg_per_day, 1) if avg_per_day > 0 else None

    return render_template("inventory.html",
                           groups=groups, selected=selected, info=info)


@bp.route("/inventory/new", methods=["GET", "POST"])
@login_required
@admin_required
def inventory_new():
    if request.method == "POST":
        name = request.form["name"].strip()
        if Inventory.query.filter_by(name=name).first():
            flash(f"原料「{name}」已存在。", "error")
            return redirect(url_for("inventory.inventory_new"))
        db.session.add(Inventory(
            name=name,
            unit=request.form["unit"].strip(),
            quantity=Decimal(request.form.get("quantity") or "0"),
            alert_threshold=Decimal(request.form.get("alert_threshold") or "10"),
        ))
        db.session.commit()
        flash(f"原料「{name}」已添加。", "ok")
        return redirect(url_for("inventory.inventory"))
    return render_template("inventory_form.html")


@bp.route("/inventory/<int:iid>/delete", methods=["POST"])
@login_required
@admin_required
def inventory_delete(iid):
    item = db.session.get(Inventory, iid) or abort(404)
    used = ProductIngredient.query.filter_by(ingredient_id=iid).count()
    if used > 0:
        flash(f"无法删除「{item.name}」：还有 {used} 个商品的配方在使用。", "error")
        return redirect(url_for("inventory.inventory"))
    db.session.delete(item)
    db.session.commit()
    flash(f"原料「{item.name}」已删除。", "ok")
    return redirect(url_for("inventory.inventory"))
