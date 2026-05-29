"""配方管理（商品 ↔ 原料）。"""
from flask import Blueprint, render_template

from models import db, Category, Product, Inventory, ProductIngredient
from decorators import login_required

bp = Blueprint("recipes", __name__)


@bp.route("/recipes")
@login_required
def recipes():
    # 视角1: 按商品分组
    rows = (db.session.query(
            Product.product_id, Product.name, Product.description,
            Product.image, Product.price, Product.stock,
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
    for (pid, pname, pdesc, img, price, pstock,
         cat, ing, unit, qty, alert, consume) in rows:
        if pid not in by_product:
            by_product[pid] = {"name": pname, "desc": pdesc, "img": img,
                               "price": price, "stock": pstock,
                               "cat": cat, "ings": []}
        if ing:
            by_product[pid]["ings"].append({
                "ing": ing, "unit": unit,
                "consume": consume, "stock": qty, "low": qty <= alert
            })

    # 视角2: 按原料分组
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
