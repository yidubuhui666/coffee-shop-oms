"""共享的视图装饰器与小工具。"""
from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "staff_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "ADMIN":
            flash("需要管理员权限。", "error")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)
    return wrapper


def prod_emoji(name):
    """商品没图时根据名字选 emoji 占位符。"""
    if not name:
        return "☕"
    kw = [
        (["气泡", "苏打", "汽水"], "🥤"),
        (["套餐", "组合"], "🍱"),
        (["茶"], "🍵"),
        (["冷萃", "冰"], "🧊"),
        (["蛋糕", "提拉", "布朗尼", "司康", "玛德琳", "芝士", "甜品"], "🍰"),
        (["柠檬"], "🍋"),
    ]
    for words, emoji in kw:
        if any(w in name for w in words):
            return emoji
    return "☕"
