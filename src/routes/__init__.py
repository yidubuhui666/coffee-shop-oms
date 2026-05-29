"""集中注册所有 Blueprint。"""
from .auth import bp as auth_bp
from .main import bp as main_bp
from .products import bp as products_bp
from .orders import bp as orders_bp
from .customers import bp as customers_bp
from .staff import bp as staff_bp
from .inventory import bp as inventory_bp
from .promotions import bp as promotions_bp
from .recipes import bp as recipes_bp
from .analytics import bp as analytics_bp
from .api import bp as api_bp


def register_blueprints(app):
    for bp in (auth_bp, main_bp, products_bp, orders_bp, customers_bp,
               staff_bp, inventory_bp, promotions_bp, recipes_bp,
               analytics_bp, api_bp):
        app.register_blueprint(bp)
