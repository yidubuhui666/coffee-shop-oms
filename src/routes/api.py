"""JSON API。"""
from flask import Blueprint, jsonify

from models import Product
from decorators import login_required

bp = Blueprint("api", __name__)


@bp.route("/api/product/<int:pid>")
@login_required
def api_product(pid):
    p = Product.query.get_or_404(pid)
    return jsonify({"id": p.product_id, "name": p.name, "price": float(p.price)})
