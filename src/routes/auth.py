"""认证：登录 / 登出 / 切换账号。"""
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash)

from models import db, Staff
from decorators import login_required, admin_required

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd   = request.form.get("password", "")
        user  = Staff.query.filter_by(username=uname).first()

        if not user:
            flash("账号无效。", "error")
        elif not user.active:
            flash("该账号已被停用，请联系管理员。", "error")
        elif user.password != pwd:
            flash("密码错误。", "error")
        else:
            session["staff_id"], session["name"], session["role"] = (
                user.staff_id, user.name, user.role)
            flash(f"欢迎，{user.name}！", "ok")
            return redirect(url_for("main.dashboard"))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/switch_to/<int:sid>", methods=["POST"])
@login_required
@admin_required
def switch_to(sid):
    """快速切换到另一个员工账号（仅管理员可用，无需密码）。"""
    target = db.session.get(Staff, sid)
    if not target or not target.active:
        flash("目标账号无效或已停用。", "error")
        return redirect(request.referrer or url_for("main.dashboard"))
    session["staff_id"] = target.staff_id
    session["name"]     = target.name
    session["role"]     = target.role
    flash(f"已切换为 {target.name}（{target.role}）。", "ok")
    return redirect(url_for("main.dashboard"))
