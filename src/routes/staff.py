"""员工 CRUD（仅管理员）。"""
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, abort)

from models import db, Staff
from decorators import login_required, admin_required

bp = Blueprint("staff", __name__)


@bp.route("/staff")
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


@bp.route("/staff/new", methods=["GET", "POST"])
@login_required
@admin_required
def staff_new():
    if request.method == "POST":
        uname = request.form["username"].strip()
        if Staff.query.filter_by(username=uname).first():
            flash("该用户名已被占用。", "error")
            return redirect(url_for("staff.staff_new"))
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
        return redirect(url_for("staff.staff_list"))
    return render_template("staff_form.html", staff=None)


@bp.route("/staff/<int:sid>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("staff.staff_list"))
    return render_template("staff_form.html", staff=s)


@bp.route("/staff/<int:sid>/toggle", methods=["POST"])
@login_required
@admin_required
def staff_toggle(sid):
    s = db.session.get(Staff, sid) or abort(404)
    if s.staff_id == session.get("staff_id"):
        flash("不能停用当前登录的账号。", "error")
        return redirect(url_for("staff.staff_list"))
    s.active = not s.active
    db.session.commit()
    flash(f"员工 {s.name} 已{'启用' if s.active else '停用'}。", "ok")
    return redirect(url_for("staff.staff_list"))
