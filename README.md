# 🚀 Titanium OS - Restaurant Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=for-the-badge&logo=mysql)
![XAMPP](https://img.shields.io/badge/XAMPP-Required-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**A futuristic, feature-rich restaurant management system built with Python and MySQL**

> ⚠️ **Note:** This application is designed to run on **XAMPP MySQL**. Make sure XAMPP is installed and MySQL service is running before starting the application.

<div align="center">

📄 **[Download Project Report (PDF)](https://github.com/Batanounyy/TitaniumOS/blob/01d098b3409fb047ec1e6f6778de861b6fab120c/Project%20Report.pdf)** 📄

</div>

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Screenshots](#-screenshots) • [Tech Stack](#-tech-stack)

</div>

---

## 📋 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Installation](#-installation)
- [Database Setup with XAMPP](#-database-setup-with-xampp)
- [Usage](#-usage)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Developers](#-developers)

---

## 🎯 About

**Titanium OS** is a comprehensive restaurant management system designed to streamline operations from order taking to payment processing. With its modern, futuristic UI and robust backend, it provides everything you need to manage a restaurant efficiently.

### Key Highlights
- ⚡ **Real-time Updates** - Live order tracking and inventory management
- 💰 **Financial Management** - Built-in wallet system with tax, service, and tips tracking
- 📊 **Analytics** - Profit margin calculator and sales reporting
- 🎨 **Customizable** - Multiple themes and configurable settings
- 🔒 **Secure** - Password-protected admin panel

---

## ✨ Features

### 🍽️ Menu Management
- Visual menu grid with stock status indicators
- Real-time inventory tracking
- Low stock warnings
- Quick price and stock adjustments

### 📝 Order Processing
- Intuitive table selection
- Cart management with quantity controls
- Automatic tax and service charge calculation
- Order submission to kitchen queue

### 👨‍🍳 Kitchen Queue
- Real-time order display
- Time elapsed tracking
- Ready/Cancel order actions
- Automatic stock restoration on cancellation

### 💳 Payment & Billing
- Smart billing system
- Discount and tip support
- Automatic receipt generation
- Table status management

### 💼 Admin Dashboard
- **Wallet Management**
  - Main wallet with deposit/withdraw
  - Tax pool, service pool, and tips pool
  - Complete transaction audit trail
  
- **Menu Editor**
  - Add, edit, delete menu items
  - Quick stock adjustments
  - Price modifications
  
- **Inventory Control**
  - Purchase stock using wallet funds
  - Cost tracking
  
- **Analytics & Reports**
  - Profit margin calculator
  - Order history
  - Revenue and cost analysis
  
- **Settings**
  - App name customization
  - Tax and service rate configuration
  - Theme selection (6 dark themes)
  - Admin password management
  - Table management (add/remove tables)
  
- **Data Export**
  - Export orders to CSV
  - Export wallet logs to CSV

---

## 🚀 Installation

### Prerequisites

- **Python 3.7 or higher**
- **XAMPP** (with MySQL included) - [Download XAMPP](https://www.apachefriends.org/)
- **VS Code** (recommended) or any Python IDE
- **pip** (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/titanium-os.git
cd titanium-os
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `tkinter` (usually comes with Python)
- `ttkbootstrap`
- `mysql-connector-python`

If `requirements.txt` doesn't exist, install manually:

```bash
pip install ttkbootstrap mysql-connector-python
```

### Step 3: Database Setup

See [Database Setup](#-database-setup-with-xampp) section below.

---

## 🗄️ Database Setup with XAMPP

This application is designed to work with **XAMPP MySQL**. Follow these steps to set up the database:

### Step 1: Install and Start XAMPP

1. **Download XAMPP** from [https://www.apachefriends.org/](https://www.apachefriends.org/)
2. **Install XAMPP** (default installation path: `C:\xampp`)
3. **Start XAMPP Control Panel**
4. **Start MySQL Service** - Click the "Start" button next to MySQL in XAMPP Control Panel
   - ✅ MySQL status should show "Running" (green)

### Step 2: Access phpMyAdmin (Recommended Method)

1. **Open phpMyAdmin**
   - In XAMPP Control Panel, click "Admin" button next to MySQL
   - Or navigate to: `http://localhost/phpmyadmin` in your browser

2. **Import SQL File**
   - Click on the **"Import"** tab in phpMyAdmin
   - Click **"Choose File"** button
   - Select the `db.sql` file from your project directory
   - Click **"Go"** at the bottom
   - ✅ You should see a success message

### Step 3: Alternative Method - Using VS Code SQL Extension

If you prefer using VS Code:

1. **Install MySQL Extension in VS Code**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "MySQL" and install a MySQL extension (e.g., "MySQL" by cweijan)

2. **Connect to XAMPP MySQL**
   - Open Command Palette (Ctrl+Shift+P)
   - Type "MySQL: Connect"
   - Enter connection details:
     - **Host:** `localhost`
     - **Port:** `3306`
     - **User:** `root`
     - **Password:** (leave empty - XAMPP default)
     - **Database:** (leave empty for now)

3. **Execute SQL Script**
   - Open `db.sql` file in VS Code
   - Right-click in the SQL file
   - Select "Run MySQL Query" or use the extension's execute command
   - ✅ Database and tables will be created

### Step 4: Verify Database Connection

1. **Check Database Creation**
   - In phpMyAdmin, you should see `titanium2` database in the left sidebar
   - Click on it to view all tables:
     - ✅ `settings`
     - ✅ `menu`
     - ✅ `tables`
     - ✅ `orders`
     - ✅ `wallet_logs`
     - ✅ `sales_log`

2. **Verify Default Settings**
   - Click on `settings` table
   - You should see pre-configured values (app_name, admin_pass, etc.)

### Step 5: Configure Database Connection in Code

The default configuration in `main.py` is already set for XAMPP:

```python
class DB:
    def __init__(self):
        self.host = "localhost"      # XAMPP default
        self.user = "root"            # XAMPP default username
        self.password = ""           # XAMPP default (empty password)
        self.db_name = "titanium2"    # Database name from db.sql
```

**If you changed XAMPP MySQL password:**
- Edit `main.py` and update the `password` field in the `DB` class

### Step 6: Test the Connection

1. **Make sure MySQL is running** in XAMPP Control Panel
2. **Run the application:**
   ```bash
   python main.py
   ```
3. If connection fails, check:
   - ✅ MySQL service is running in XAMPP
   - ✅ Database `titanium2` exists
   - ✅ Username is `root` and password is empty (or matches your XAMPP config)

---

## 💻 Usage

### Starting the Application

**Important:** Make sure XAMPP MySQL is running before starting the application!

1. **Start XAMPP MySQL**
   - Open XAMPP Control Panel
   - Click "Start" next to MySQL
   - Wait for status to show "Running"

2. **Run the Application**
   
   **Using VS Code:**
   - Open the project folder in VS Code
   - Open terminal (Ctrl + `)
   - Run: `python main.py`
   
   **Using Command Line:**
   ```bash
   cd path/to/Titanium
   python main.py
   ```
   
   **Using Python IDLE:**
   - Right-click `main.py`
   - Select "Edit with IDLE"
   - Press F5 to run

### Default Login

- **Admin Password:** `1234` (change this in Settings after first login)

### Quick Start Guide

1. **Add Menu Items**
   - Go to Admin tab → Login with password `1234`
   - Navigate to Menu tab
   - Add items with name, price, and cost

2. **Take an Order**
   - Go to Order tab
   - Select a table
   - Choose items from menu
   - Add to cart and submit

3. **Process in Kitchen**
   - Go to Kitchen tab
   - View pending orders
   - Mark as Ready when complete

4. **Process Payment**
   - Go to Status tab
   - Select an order
   - Click Pay & Clear
   - Enter discount/tip if needed
   - Receipt will be generated automatically

5. **Manage Inventory**
   - Admin → Inventory tab
   - Select item and quantity
   - Purchase stock (deducts from wallet)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **GUI Framework** | Tkinter + TTKBootstrap |
| **Database** | MySQL 8.0 (via XAMPP) |
| **Language** | Python 3.x |
| **Development Environment** | VS Code (recommended) |
| **Local Server** | XAMPP |
| **Themes** | TTKBootstrap (Superhero, Darkly, Solar, Cyborg, Vapor, Slate) |

### Dependencies

```
ttkbootstrap          # Modern UI components
mysql-connector-python # MySQL database connector
```

---

## 📁 Project Structure

```
Titanium/
│
├── main.py              # Main application file
├── db.sql              # Database schema and setup
├── backup.py           # Backup utility (if exists)
├── README.md           # This file
│
└── receipts/           # Generated receipt files
    ├── receipt_*.txt
    └── ...
```

---

## 🎨 Screenshots

> **Note:** Add screenshots of your application here!

### Menu View
![Menu View](screenshots/menu.png)

### Order Processing
![Order Processing](screenshots/order.png)

### Kitchen Queue
![Kitchen Queue](screenshots/kitchen.png)

### Admin Dashboard
![Admin Dashboard](screenshots/admin.png)

---

## 🔧 Configuration

### XAMPP MySQL Settings

**Default XAMPP Configuration:**
- **Host:** `localhost`
- **Port:** `3306`
- **Username:** `root`
- **Password:** (empty by default)

If you need to change these settings, edit the `DB` class in `main.py`:

```python
class DB:
    def __init__(self):
        self.host = "localhost"      # Change if MySQL is on different host
        self.user = "root"           # Change if using different username
        self.password = ""          # Add password if you set one in XAMPP
        self.db_name = "titanium2"   # Database name
```

### Application Settings

- **App Name** - Customize application title
- **Tax Rate** - Set tax percentage (default: 10%)
- **Service Rate** - Set service charge percentage (default: 5%)
- **Theme** - Choose from 6 dark themes
- **Admin Password** - Change admin access password

### Database Tables

- `settings` - Application configuration
- `menu` - Menu items with pricing and stock
- `tables` - Restaurant table management
- `orders` - Order history and active orders
- `wallet_logs` - Financial transaction audit trail
- `sales_log` - Sales analytics data

---

## 🔧 Troubleshooting

### Common XAMPP Issues

#### MySQL Won't Start
- **Port 3306 already in use:**
  - Check if another MySQL service is running
  - Stop other MySQL services or change XAMPP MySQL port in `my.ini`

#### Connection Refused Error
- **Check XAMPP MySQL is running:**
  - Open XAMPP Control Panel
  - Ensure MySQL shows "Running" status
  - If not, click "Start" and check for error messages

#### Database Not Found
- **Database not created:**
  - Make sure you imported `db.sql` successfully
  - Check phpMyAdmin to verify `titanium2` database exists
  - Re-import `db.sql` if needed

#### Access Denied Error
- **Wrong credentials:**
  - XAMPP default username is `root`
  - XAMPP default password is empty (blank)
  - If you set a password, update it in `main.py`

#### VS Code MySQL Extension Issues
- **Can't connect:**
  - Verify MySQL is running in XAMPP
  - Use `localhost` as host, not `127.0.0.1`
  - Port should be `3306`
  - Leave password empty if using default XAMPP setup

### Quick Fixes

1. **Restart XAMPP MySQL:**
   - Stop MySQL in XAMPP Control Panel
   - Wait 5 seconds
   - Start MySQL again

2. **Re-import Database:**
   - Drop `titanium2` database in phpMyAdmin
   - Import `db.sql` again

3. **Check Python Connection:**
   ```python
   # Test connection in Python
   import mysql.connector
   conn = mysql.connector.connect(
       host="localhost",
       user="root",
       password=""
   )
   print("Connected!" if conn else "Failed!")
   ```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👥 Developers

This project was developed by:

- **Abdelrahman ElBatanouny** - 232403
- **Omar Sameh Mohamed Ali** - 235153
- **Mohamed Raed Atef** - 234197
- **Mahmoud Mohamed** - 231437

---

## 📧 Contact

**Project Maintainer** - Abdelrahman ElBatanouny

Project Link: [https://github.com/Batanounyy/TitaniumOS](https://github.com/Batanounyy/TitaniumOS)

---

<div align="center">

**Made with ❤️ using Python**

⭐ Star this repo if you find it helpful!

</div>
