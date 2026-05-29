"""ORM models that mirror the SQL schema in sql/schema.sql."""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = "customers"
    customer_id   = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(50), nullable=False)
    phone         = db.Column(db.String(20), unique=True)
    email         = db.Column(db.String(80), unique=True)
    member_level  = db.Column(db.String(10), default="BRONZE")
    points        = db.Column(db.Integer, default=0)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)


class Staff(db.Model):
    __tablename__ = "staff"
    staff_id  = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(40), unique=True, nullable=False)
    password  = db.Column(db.String(128), nullable=False)
    name      = db.Column(db.String(50), nullable=False)
    role      = db.Column(db.String(10), default="CASHIER")
    phone     = db.Column(db.String(20))
    hire_date = db.Column(db.Date, default=date.today)
    active    = db.Column(db.Boolean, default=True)


class Category(db.Model):
    __tablename__ = "categories"
    category_id = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), nullable=False, unique=True)
    sort_order  = db.Column(db.Integer, default=0)
    products    = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    product_id  = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"), nullable=False)
    name        = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(255))
    price       = db.Column(db.Numeric(8, 2), nullable=False)
    available   = db.Column(db.Boolean, default=True)
    stock       = db.Column(db.Integer, default=0)
    image       = db.Column(db.String(120))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Promotion(db.Model):
    __tablename__ = "promotions"
    promo_id   = db.Column(db.Integer, primary_key=True)
    code       = db.Column(db.String(20), unique=True, nullable=False)
    name       = db.Column(db.String(80), nullable=False)
    discount   = db.Column(db.Numeric(4, 2), nullable=False)
    start_date = db.Column(db.Date)
    end_date   = db.Column(db.Date)
    active     = db.Column(db.Boolean, default=True)


class Order(db.Model):
    __tablename__ = "orders"
    order_id       = db.Column(db.Integer, primary_key=True)
    customer_id    = db.Column(db.Integer, db.ForeignKey("customers.customer_id"))
    staff_id       = db.Column(db.Integer, db.ForeignKey("staff.staff_id"), nullable=False)
    promo_id       = db.Column(db.Integer, db.ForeignKey("promotions.promo_id"))
    order_time     = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount   = db.Column(db.Numeric(10, 2), default=0)
    paid_amount    = db.Column(db.Numeric(10, 2), default=0)
    status         = db.Column(db.String(20), default="PENDING")
    payment_method = db.Column(db.String(10), default="WECHAT")
    dine_in        = db.Column(db.Boolean, default=True)
    remark         = db.Column(db.String(200))
    points_used    = db.Column(db.Integer, default=0)   # 本单抵扣的积分

    customer = db.relationship("Customer", backref="orders")
    staff    = db.relationship("Staff",    backref="orders")
    items    = db.relationship("OrderItem", backref="order",
                               cascade="all, delete-orphan", lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_items"
    item_id       = db.Column(db.Integer, primary_key=True)
    order_id      = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    product_id    = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    quantity      = db.Column(db.Integer, nullable=False)
    unit_price    = db.Column(db.Numeric(8, 2), nullable=False)
    size          = db.Column(db.String(2), default="M")
    customization = db.Column(db.String(120))

    product = db.relationship("Product")


class Inventory(db.Model):
    __tablename__ = "inventory"
    ingredient_id   = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(60), unique=True, nullable=False)
    unit            = db.Column(db.String(10), nullable=False)
    quantity        = db.Column(db.Numeric(10, 2), default=0)
    alert_threshold = db.Column(db.Numeric(10, 2), default=10)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)


class ProductIngredient(db.Model):
    """商品-原料关联表（多对多）：每杯商品消耗的原料种类与数量。"""
    __tablename__ = "product_ingredient"
    product_id    = db.Column(db.Integer,
                              db.ForeignKey("products.product_id"),
                              primary_key=True)
    ingredient_id = db.Column(db.Integer,
                              db.ForeignKey("inventory.ingredient_id"),
                              primary_key=True)
    consume_qty   = db.Column(db.Numeric(8, 3), nullable=False)

    product    = db.relationship("Product",   backref="ingredient_links")
    ingredient = db.relationship("Inventory", backref="product_links")


class MemberDiscount(db.Model):
    """会员等级折扣表：BRONZE/SILVER/GOLD/PLATINUM 各自的折扣率。"""
    __tablename__ = "member_discount"
    level    = db.Column(db.String(10), primary_key=True)
    discount = db.Column(db.Numeric(4, 2), nullable=False)
    label    = db.Column(db.String(20), nullable=False)
