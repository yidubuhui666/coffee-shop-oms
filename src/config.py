"""应用配置。

敏感信息（数据库连接串、密钥）一律通过环境变量注入，不硬编码到代码里。
本地开发请在 src/.env.bat（已 gitignore）中设置：
    set DATABASE_URL=mysql+pymysql://用户:密码@127.0.0.1:3306/coffee_shop?charset=utf8mb4
    set SECRET_KEY=任意随机字符串
"""
import os


def _require_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "未检测到环境变量 DATABASE_URL。\n"
            "请在 src/.env.bat 中设置数据库连接串后再启动，例如：\n"
            "  set DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/coffee_shop?charset=utf8mb4\n"
            "（自动化测试可设置为 sqlite:///:memory:）"
        )
    return url


class Config:
    # 没设 SECRET_KEY 时用开发兜底值；生产/演示建议通过环境变量覆盖。
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = _require_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
