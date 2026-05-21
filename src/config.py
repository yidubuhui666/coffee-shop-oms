"""Application configuration."""
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "coffee-shop-secret-key")

    # Default to MySQL; override with env DATABASE_URL for SQLite or other DSN.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@127.0.0.1:3306/coffee_shop?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
