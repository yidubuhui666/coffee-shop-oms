"""Coffee Shop OMS - Flask 应用工厂。

业务路由全部拆分到 routes/ 下的 Blueprint，
本文件只负责：创建应用、加载配置、初始化数据库、注册蓝图、注入模板上下文。
"""
from flask import Flask, session

from config import Config
from models import db, Staff
from decorators import prod_emoji
from bootstrap import bootstrap_demo_data
from routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        bootstrap_demo_data()

    register_blueprints(app)

    @app.context_processor
    def inject_helpers():
        return {"prod_emoji": prod_emoji}

    @app.context_processor
    def inject_switchable_staff():
        """供右上角"切换账号"下拉用：返回除当前用户外的所有活跃员工。"""
        if "staff_id" not in session or session.get("role") != "ADMIN":
            return {"switchable_staff": []}
        try:
            staff_list = (Staff.query.filter_by(active=True)
                          .order_by(Staff.role.desc(), Staff.staff_id).all())
            return {"switchable_staff": [
                s for s in staff_list if s.staff_id != session.get("staff_id")
            ]}
        except Exception:
            return {"switchable_staff": []}

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5050, debug=True)
