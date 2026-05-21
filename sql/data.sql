-- =====================================================================
-- Sample seed data for Coffee Shop Order Management System
-- Run AFTER schema.sql
-- =====================================================================
USE coffee_shop;

-- ---- Staff (password is plain-text demo value; in app a hash is stored)
INSERT INTO staff(username, password, name, role, phone, hire_date) VALUES
('admin',  'admin123',  'Yang Fan',  'ADMIN',   '13800000001', '2024-09-01'),
('barista','barista123','Li Ming',   'BARISTA', '13800000002', '2025-03-15'),
('cashier','cashier123','Wang Lei',  'CASHIER', '13800000003', '2025-04-01');

-- ---- Categories
INSERT INTO categories(name, sort_order) VALUES
('Espresso',     1),
('Milk Coffee',  2),
('Tea',          3),
('Cold Brew',    4),
('Dessert',      5);

-- ---- Products
INSERT INTO products(category_id, name, description, price, stock, image) VALUES
(1,'美式咖啡',        '经典浓缩 + 热水',                18.00, 200, 'americano.jpg'),
(1,'浓缩咖啡',        '单份意式浓缩',                   15.00, 200, 'espresso.jpg'),
(2,'拿铁',            '浓缩咖啡配蒸奶',                 25.00, 150, 'latte.jpg'),
(2,'卡布奇诺',        '浓缩咖啡配奶泡',                 25.00, 150, 'cappuccino.jpg'),
(2,'摩卡',            '浓缩 + 巧克力 + 牛奶',           28.00, 120, 'mocha.jpg'),
(2,'焦糖玛奇朵',      '浓缩 + 焦糖 + 奶泡',             30.00, 120, 'caramel-macchiato.jpg'),
(3,'伯爵红茶',        '佛手柑香味的红茶',               18.00, 100, 'earl-grey-tea.jpg'),
(3,'抹茶拿铁',        '日式抹茶配牛奶',                 28.00, 100, 'matcha-latte.jpg'),
(4,'冷萃咖啡',        '12 小时慢萃冷萃咖啡',            26.00,  80, 'cold-brew.jpg'),
(4,'冰柠檬茶',        '新鲜柠檬冰茶',                   20.00,  80, 'iced-lemon-tea.jpg'),
(5,'提拉米苏',        '经典意式甜点',                   32.00,  40, 'tiramisu.jpg'),
(5,'纽约芝士蛋糕',    '纽约风味芝士蛋糕',               30.00,  40, 'cheesecake.jpg');

-- ---- Inventory
INSERT INTO inventory(name, unit, quantity, alert_threshold) VALUES
('Coffee bean', 'kg',  30.00, 5.00),
('Milk',        'L',   40.00, 10.00),
('Sugar',       'kg',  15.00, 3.00),
('Chocolate',   'kg',   5.00, 1.00),
('Matcha',      'kg',   2.00, 0.50),
('Lemon',       'pcs', 60.00, 10.00);

-- ---- Recipes
INSERT INTO product_ingredients(product_id, ingredient_id, amount) VALUES
(1,1,0.02),                       -- Americano: 20g beans
(2,1,0.02),
(3,1,0.02),(3,2,0.20),            -- Latte: beans + milk
(4,1,0.02),(4,2,0.15),
(5,1,0.02),(5,2,0.18),(5,4,0.02),
(6,1,0.02),(6,2,0.18),(6,3,0.01),
(8,2,0.20),(8,5,0.01),
(10,6,1);

-- ---- Customers
INSERT INTO customers(name, phone, email, member_level, points) VALUES
('Zhang San','13900000001','zs@example.com','GOLD',     320),
('Li Si',    '13900000002','ls@example.com','SILVER',   140),
('Wang Wu',  '13900000003','ww@example.com','BRONZE',    30),
('Zhao Liu', '13900000004','zl@example.com','PLATINUM', 880);

-- ---- Promotions
INSERT INTO promotions(code, name, discount, start_date, end_date) VALUES
('WELCOME10','New customer 10% off', 0.10, '2025-01-01','2026-12-31'),
('VIP20',    'VIP 20% off',          0.20, '2025-01-01','2026-12-31');

-- ---- Demo orders (use the place-order procedure for one of them)
INSERT INTO orders(customer_id, staff_id, status, payment_method, dine_in)
VALUES (1, 3, 'PAID', 'WECHAT', 1);
SET @o1 = LAST_INSERT_ID();
INSERT INTO order_items(order_id, product_id, quantity, unit_price, size) VALUES
(@o1, 3, 2, 25.00, 'M'),
(@o1, 11, 1, 32.00, 'M');

INSERT INTO orders(customer_id, staff_id, status, payment_method, dine_in)
VALUES (2, 3, 'COMPLETED', 'ALIPAY', 0);
SET @o2 = LAST_INSERT_ID();
INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES
(@o2, 1, 1, 18.00),
(@o2, 9, 1, 26.00);

INSERT INTO orders(customer_id, staff_id, status, payment_method)
VALUES (4, 3, 'PAID', 'CARD');
SET @o3 = LAST_INSERT_ID();
INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES
(@o3, 6, 2, 30.00),
(@o3, 8, 1, 28.00);
