============================================================
 Coffee Shop Order Management System
 Team:  114 Yang Fan  (Leader)
        092 Xu Yueqian
============================================================

1. ENVIRONMENT
   - Python 3.10+
   - MySQL 8.0+   (default; can switch to SQLite for quick demo)

2. INSTALL
   cd src
   python -m venv venv
   source venv/bin/activate            # Windows: venv\Scripts\activate
   pip install -r requirements.txt

3. DATABASE
   (A) MySQL (default, matches sql/schema.sql exactly)
       mysql -uroot -p < ../sql/schema.sql
       mysql -uroot -p coffee_shop < ../sql/data.sql

       Connection string (override via env var if needed):
           DATABASE_URL=mysql+pymysql://root:root@127.0.0.1:3306/coffee_shop?charset=utf8mb4

   (B) SQLite quick start (no MySQL required, app auto-seeds demo data):
           export DATABASE_URL=sqlite:///coffee.db        # macOS / Linux
           set    DATABASE_URL=sqlite:///coffee.db        # Windows cmd

4. RUN
   python app.py
   Open http://127.0.0.1:5050
   (Port 5050 instead of 5000 because macOS AirPlay Receiver occupies 5000.)

5. LOGIN ACCOUNTS
   ----------------------------------------
   role     | username | password
   ----------------------------------------
   Admin    | admin    | admin123
   Barista  | barista  | barista123
   Cashier  | cashier  | cashier123
   ----------------------------------------

6. MAIN FEATURES
   - Staff login / role-based access
   - Menu management (add / edit / delete products by admin)
   - New order creation with multi-line cart, dine-in flag,
     payment method, customer attachment
   - Order list with status filter, order detail page, status workflow
     (PENDING -> PAID -> PREPARING -> READY -> COMPLETED / CANCELLED)
   - Customer management with membership level & loyalty points
   - Ingredient inventory with low-stock alert
   - Statistics: daily revenue (last 14 days) + product ranking

7. NOTES
   - Demo passwords are plain text for grading convenience.
     In production, use werkzeug.security.generate_password_hash().
   - SQL schema includes triggers, views and a stored procedure;
     when running on SQLite only the ORM-level logic applies.
