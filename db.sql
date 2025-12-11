-- 1. DROP OLD DATA (Ensures a clean slate)
DROP DATABASE IF EXISTS titanium_db;

-- 2. CREATE NEW DATABASE
CREATE DATABASE titanium_db;
USE titanium_db;

-- 3. SETTINGS (Config & Admin Pass)
CREATE TABLE settings (
    key_name VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255)
);
INSERT INTO settings (key_name, value) VALUES 
('app_name', 'Titanium OS'), 
('admin_pass', '1234'), 
('theme', 'superhero'), 
('wallet', '0.00'), 
('tax_pool', '0.00'), 
('service_pool', '0.00'), 
('tips_pool', '0.00'),
('tax_rate', '10'), 
('service_rate', '5');

-- 4. MENU (Inventory)
CREATE TABLE menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100), 
    price DECIMAL(10, 2), 
    cost DECIMAL(10, 2), 
    stock INT DEFAULT 0
);

-- 5. TABLES (Floor Plan)
CREATE TABLE tables (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    table_num INT UNIQUE, 
    status VARCHAR(20) DEFAULT 'Available',
    occupied_at DATETIME NULL
);
-- Create 10 Tables
INSERT INTO tables (table_num) VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10);

-- 6. ORDERS (Active & History)
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    table_num INT, 
    items TEXT,
    subtotal DECIMAL(10, 2), 
    tax DECIMAL(10, 2), 
    service DECIMAL(10, 2), 
    total DECIMAL(10, 2),
    discount DECIMAL(10, 2) DEFAULT 0.00, 
    tip DECIMAL(10, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'Kitchen',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. WALLET LOGS (Audit Trail)
CREATE TABLE wallet_logs (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    type VARCHAR(50), 
    amount DECIMAL(10, 2), 
    description VARCHAR(255), 
    date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 8. SALES LOG (Analytics)
CREATE TABLE sales_log (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    item_name VARCHAR(100), 
    price DECIMAL(10, 2), 
    cost DECIMAL(10, 2), 
    date_sold DATETIME DEFAULT CURRENT_TIMESTAMP
);
