-- =====================================================================
-- Coffee Shop Order Management System - Database Schema
-- Author : 114 Yang Fan
-- DBMS   : MySQL 8.0+
-- Charset: utf8mb4
-- =====================================================================

DROP DATABASE IF EXISTS coffee_shop;
CREATE DATABASE coffee_shop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE coffee_shop;

-- ---------------------------------------------------------------------
-- 1. Customers
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(50)  NOT NULL,
    phone         VARCHAR(20)  UNIQUE,
    email         VARCHAR(80)  UNIQUE,
    member_level  ENUM('BRONZE','SILVER','GOLD','PLATINUM') DEFAULT 'BRONZE',
    points        INT DEFAULT 0,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. Staff
-- ---------------------------------------------------------------------
CREATE TABLE staff (
    staff_id   INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(40)  NOT NULL UNIQUE,
    password   VARCHAR(128) NOT NULL,
    name       VARCHAR(50)  NOT NULL,
    role       ENUM('ADMIN','BARISTA','CASHIER') DEFAULT 'CASHIER',
    phone      VARCHAR(20),
    hire_date  DATE,
    active     TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. Product categories
-- ---------------------------------------------------------------------
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    sort_order  INT DEFAULT 0
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. Products (menu items)
-- ---------------------------------------------------------------------
CREATE TABLE products (
    product_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_id  INT NOT NULL,
    name         VARCHAR(80)  NOT NULL,
    description  VARCHAR(255),
    price        DECIMAL(8,2) NOT NULL CHECK (price >= 0),
    available    TINYINT(1) DEFAULT 1,
    stock        INT DEFAULT 0,
    image        VARCHAR(120),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
    INDEX idx_cat (category_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. Promotions
-- ---------------------------------------------------------------------
CREATE TABLE promotions (
    promo_id   INT AUTO_INCREMENT PRIMARY KEY,
    code       VARCHAR(20) UNIQUE NOT NULL,
    name       VARCHAR(80) NOT NULL,
    discount   DECIMAL(4,2) NOT NULL,   -- e.g. 0.20 = 20% off
    start_date DATE,
    end_date   DATE,
    active     TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. Orders
-- ---------------------------------------------------------------------
CREATE TABLE orders (
    order_id       INT AUTO_INCREMENT PRIMARY KEY,
    customer_id    INT,
    staff_id       INT NOT NULL,
    promo_id       INT,
    order_time     DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount   DECIMAL(10,2) NOT NULL DEFAULT 0,
    paid_amount    DECIMAL(10,2) NOT NULL DEFAULT 0,
    status         ENUM('PENDING','PAID','PREPARING','READY','COMPLETED','CANCELLED')
                   NOT NULL DEFAULT 'PENDING',
    payment_method ENUM('CASH','CARD','WECHAT','ALIPAY') DEFAULT 'WECHAT',
    dine_in        TINYINT(1) DEFAULT 1,
    remark         VARCHAR(200),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id)    REFERENCES staff(staff_id),
    FOREIGN KEY (promo_id)    REFERENCES promotions(promo_id) ON DELETE SET NULL,
    INDEX idx_time   (order_time),
    INDEX idx_status (status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. Order items
-- ---------------------------------------------------------------------
CREATE TABLE order_items (
    item_id        INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    product_id     INT NOT NULL,
    quantity       INT NOT NULL CHECK (quantity > 0),
    unit_price     DECIMAL(8,2) NOT NULL,
    size           ENUM('S','M','L') DEFAULT 'M',
    customization  VARCHAR(120),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_order (order_id)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 8. Inventory (raw ingredients)
-- ---------------------------------------------------------------------
CREATE TABLE inventory (
    ingredient_id   INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(60) NOT NULL UNIQUE,
    unit            VARCHAR(10) NOT NULL,
    quantity        DECIMAL(10,2) NOT NULL DEFAULT 0,
    alert_threshold DECIMAL(10,2) DEFAULT 10,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 9. Product / ingredient recipe (many-to-many)
-- ---------------------------------------------------------------------
CREATE TABLE product_ingredients (
    product_id    INT NOT NULL,
    ingredient_id INT NOT NULL,
    amount        DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (product_id, ingredient_id),
    FOREIGN KEY (product_id)    REFERENCES products(product_id)    ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES inventory(ingredient_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- VIEWS
-- =====================================================================

-- Daily revenue view
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT  DATE(order_time)         AS biz_date,
        COUNT(*)                 AS order_count,
        SUM(total_amount)        AS revenue
FROM    orders
WHERE   status IN ('PAID','PREPARING','READY','COMPLETED')
GROUP BY DATE(order_time);

-- Best-selling products view
CREATE OR REPLACE VIEW v_product_sales AS
SELECT  p.product_id,
        p.name,
        SUM(oi.quantity)                AS sold_qty,
        SUM(oi.quantity * oi.unit_price) AS sold_amount
FROM    order_items oi
JOIN    products    p ON p.product_id = oi.product_id
JOIN    orders      o ON o.order_id   = oi.order_id
WHERE   o.status <> 'CANCELLED'
GROUP BY p.product_id, p.name;

-- =====================================================================
-- TRIGGERS
-- =====================================================================

DELIMITER //

-- Recompute order total when an item is added
CREATE TRIGGER trg_item_after_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
       SET total_amount = (
           SELECT COALESCE(SUM(quantity * unit_price),0)
           FROM order_items WHERE order_id = NEW.order_id)
     WHERE order_id = NEW.order_id;
END//

-- Recompute when an item is deleted
CREATE TRIGGER trg_item_after_delete
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
       SET total_amount = (
           SELECT COALESCE(SUM(quantity * unit_price),0)
           FROM order_items WHERE order_id = OLD.order_id)
     WHERE order_id = OLD.order_id;
END//

-- Award loyalty points when an order is marked PAID
CREATE TRIGGER trg_order_after_update
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'PAID' AND OLD.status <> 'PAID' AND NEW.customer_id IS NOT NULL THEN
        UPDATE customers
           SET points = points + FLOOR(NEW.total_amount)
         WHERE customer_id = NEW.customer_id;
    END IF;
END//

DELIMITER ;

-- =====================================================================
-- STORED PROCEDURE  (example: place an order in one call)
-- =====================================================================
DELIMITER //
CREATE PROCEDURE sp_place_order(
    IN  p_customer_id INT,
    IN  p_staff_id    INT,
    IN  p_product_id  INT,
    IN  p_quantity    INT,
    OUT p_order_id    INT)
BEGIN
    DECLARE v_price DECIMAL(8,2);
    SELECT price INTO v_price FROM products WHERE product_id = p_product_id;

    INSERT INTO orders(customer_id, staff_id) VALUES (p_customer_id, p_staff_id);
    SET p_order_id = LAST_INSERT_ID();

    INSERT INTO order_items(order_id, product_id, quantity, unit_price)
    VALUES (p_order_id, p_product_id, p_quantity, v_price);
END//
DELIMITER ;
