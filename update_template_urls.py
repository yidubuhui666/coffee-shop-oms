"""一次性批量替换模板中的 url_for() 端点名，添加 Blueprint 前缀。"""
import os
import re

MAP = {
    # auth
    "login": "auth.login",
    "logout": "auth.logout",
    "switch_to": "auth.switch_to",
    # main
    "dashboard": "main.dashboard",
    # products
    "menu": "products.menu",
    "product_new": "products.product_new",
    "product_edit": "products.product_edit",
    "product_delete": "products.product_delete",
    # orders
    "orders": "orders.orders",
    "order_new": "orders.order_new",
    "order_detail": "orders.order_detail",
    "order_status": "orders.order_status",
    # customers
    "customers": "customers.customers",
    "customer_new": "customers.customer_new",
    "customer_edit": "customers.customer_edit",
    "customer_delete": "customers.customer_delete",
    # staff
    "staff_list": "staff.staff_list",
    "staff_new": "staff.staff_new",
    "staff_edit": "staff.staff_edit",
    "staff_toggle": "staff.staff_toggle",
    # inventory
    "inventory": "inventory.inventory",
    "inventory_new": "inventory.inventory_new",
    "inventory_delete": "inventory.inventory_delete",
    # promotions
    "promotions": "promotions.promotions",
    "promotion_new": "promotions.promotion_new",
    "promotion_toggle": "promotions.promotion_toggle",
    "promotion_delete": "promotions.promotion_delete",
    # recipes
    "recipes": "recipes.recipes",
    # analytics
    "analytics": "analytics.analytics",
    "stats": "analytics.stats",
    # api
    "api_product": "api.api_product",
}

# url_for('xxx') 或 url_for("xxx") - 第一个参数是端点名
PATTERN = re.compile(r"""url_for\(\s*(['"])([^'"]+)\1""")

tpl_dir = os.path.join(os.path.dirname(__file__), "src", "templates")
total_files, total_replacements = 0, 0

for fname in os.listdir(tpl_dir):
    if not fname.endswith(".html"):
        continue
    path = os.path.join(tpl_dir, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    file_count = 0

    def replace_endpoint(match):
        global file_count
        quote, endpoint = match.group(1), match.group(2)
        if endpoint in MAP:
            file_count += 1
            return f"url_for({quote}{MAP[endpoint]}{quote}"
        return match.group(0)

    new_content = PATTERN.sub(replace_endpoint, content)
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  {fname}: {file_count} 处替换")
        total_files += 1
        total_replacements += file_count

print(f"\nOK：{total_files} 个文件，共 {total_replacements} 处替换")
