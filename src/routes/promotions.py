"""促销码管理（仅管理员）。"""
from datetime import date, datetime
from decimal import Decimal

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort)

from models import db, Promotion, Order
from decorators import login_required, admin_required

bp = Blueprint("promotions", __name__)


@bp.route("/promotions")
@login_required
@admin_required
def promotions():
    all_promos = Promotion.query.order_by(
        Promotion.active.desc(), Promotion.promo_id.desc()).all()
    return render_template("promotions.html", promos=all_promos, today=date.today())


@bp.route("/promotions/new", methods=["GET", "POST"])
@login_required
@admin_required
def promotion_new():
    if request.method == "POST":
        code = request.form["code"].strip().upper()
        if Promotion.query.filter_by(code=code).first():
            flash(f"优惠码「{code}」已存在。", "error")
            return redirect(url_for("promotions.promotion_new"))
        db.session.add(Promotion(
            code=code,
            name=request.form["name"].strip(),
            discount=Decimal(request.form["discount"]),
            start_date=datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
                       if request.form.get("start_date") else date.today(),
            end_date=datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
                     if request.form.get("end_date") else None,
            active=True,
        ))
        db.session.commit()
        flash(f"优惠码「{code}」已创建。", "ok")
        return redirect(url_for("promotions.promotions"))
    return render_template("promotion_form.html")


@bp.route("/promotions/<int:pid>/toggle", methods=["POST"])
@login_required
@admin_required
def promotion_toggle(pid):
    p = db.session.get(Promotion, pid) or abort(404)
    p.active = not p.active
    db.session.commit()
    flash(f"优惠码「{p.code}」已{'启用' if p.active else '停用'}。", "ok")
    return redirect(url_for("promotions.promotions"))


@bp.route("/promotions/<int:pid>/delete", methods=["POST"])
@login_required
@admin_required
def promotion_delete(pid):
    p = db.session.get(Promotion, pid) or abort(404)
    used = Order.query.filter_by(promo_id=pid).count()
    if used > 0:
        flash(f"无法删除「{p.code}」：已被 {used} 个订单使用，请改为停用。", "error")
        return redirect(url_for("promotions.promotions"))
    db.session.delete(p)
    db.session.commit()
    flash(f"优惠码「{p.code}」已删除。", "ok")
    return redirect(url_for("promotions.promotions"))
