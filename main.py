import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import mysql.connector
import csv
from datetime import datetime
import os
import webbrowser


class DB:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.db_name = "titanium2"

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.host, user=self.user, password=self.password, database=self.db_name
            )
        except:
            return None

    def execute(self, sql, params=()):
        conn = self.get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except: return False

    def fetch(self, sql, params=()):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except: return []

    def get_config(self, key):
        res = self.fetch("SELECT value FROM settings WHERE key_name=%s", (key,))
        return res[0][0] if res else "0"

    def set_config(self, key, val):
        check = self.fetch("SELECT 1 FROM settings WHERE key_name=%s", (key,))
        if check:
            self.execute("UPDATE settings SET value=%s WHERE key_name=%s", (str(val), key))
        else:
            self.execute("INSERT INTO settings (key_name, value) VALUES (%s, %s)", (key, str(val)))

    def update_wallet(self, amount, type, desc):
        current = float(self.get_config('wallet'))
        new_bal = current + float(amount)
        if new_bal < 0:
            messagebox.showerror("Error", "Insufficient Funds")
            return False
        
        self.set_config('wallet', new_bal)
        self.execute("INSERT INTO wallet_logs (type, amount, description) VALUES (%s, %s, %s)", (type, amount, desc))
        return True

    def update_pool_balance(self, pool_name, amount):
        current = float(self.get_config(pool_name))
        new_bal = current + float(amount)
        self.set_config(pool_name, new_bal)

    def restore_inventory_stock(self, items_str):
        if not items_str: return
        for i in items_str.split(", "):
            try:
                if "x " in i:
                    p = i.split("x ")
                    self.execute("UPDATE menu SET stock = stock + %s WHERE name=%s", (int(p[0]), p[1]))
            except: pass
db = DB()

# =============================================================================
#  TITANIUM APP
# =============================================================================
class TitaniumApp(tb.Window):
    def __init__(self):
        # 1. Initialize Theme from DB
        current_theme = db.get_config('theme') or 'superhero'
        super().__init__(themename=current_theme)
        
        # 2. Window Config
        self.title(db.get_config('app_name'))
        self.geometry("1600x950")
        
        # 3. App State Variables
        self.current_cart = []
        self.edit_item_id = None # Tracks which item is being edited in Admin
        self.tax_rate = float(db.get_config('tax_rate'))
        self.svc_rate = float(db.get_config('service_rate'))

        # 4. Build UI
        self.create_header()
        self.create_tabs()
        
        # 5. Start background tasks
        self.update_clock()
        self.refresh_all_data()

    def create_header(self):
        """ Futuristic Top Bar with Branding and Clock """
        header_frame = tb.Frame(self, bootstyle="dark")
        header_frame.pack(fill=X, padx=0, pady=0)
        
        # Brand section with futuristic styling
        brand_container = tb.Frame(header_frame, bootstyle="dark")
        brand_container.pack(side=LEFT, padx=20, pady=15)
        
        self.lbl_brand = tb.Label(brand_container, text=f">> {db.get_config('app_name').upper()}", 
                                  font=("Orbitron", 20, "bold"), bootstyle="inverse-dark")
        self.lbl_brand.pack(side=LEFT)
        
        # Status indicator
        status_label = tb.Label(brand_container, text="● ONLINE", 
                               font=("Consolas", 10, "bold"), bootstyle="success")
        status_label.pack(side=LEFT, padx=(15, 0))
        
        # Clock section with futuristic styling
        clock_container = tb.Frame(header_frame, bootstyle="dark")
        clock_container.pack(side=RIGHT, padx=20, pady=15)
        
        time_label = tb.Label(clock_container, text="TIME", 
                             font=("Orbitron", 8), bootstyle="secondary")
        time_label.pack()
        
        self.lbl_clock = tb.Label(clock_container, text="00:00:00", 
                                  font=("Consolas", 16, "bold"), bootstyle="info")
        self.lbl_clock.pack()

    def create_tabs(self):
        """ Main Navigation Notebook with Futuristic Styling """
        self.notebook = tb.Notebook(self, bootstyle="dark")
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Tab 1: Menu View
        self.tab_menu = tb.Frame(self.notebook)
        self.notebook.add(self.tab_menu, text=" [MENU] ")
        self.build_menu_tab()

        # Tab 2: Order
        self.tab_order = tb.Frame(self.notebook)
        self.notebook.add(self.tab_order, text=" [ORDER] ")
        self.build_order_tab()

        # Tab 3: Kitchen
        self.tab_kitchen = tb.Frame(self.notebook)
        self.notebook.add(self.tab_kitchen, text=" [KITCHEN] ")
        self.build_kitchen_tab()

        # Tab 4: Status / Pay
        self.tab_status = tb.Frame(self.notebook)
        self.notebook.add(self.tab_status, text=" [STATUS] ")
        self.build_status_tab()

        # Tab 5: Admin (Locked)
        self.tab_admin = tb.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text=" [ADMIN] ")
        self.build_admin_lock_screen()

    def update_clock(self):
        now = datetime.now().strftime("%A, %d %B %Y | %H:%M:%S")
        self.lbl_clock.config(text=now)
        self.after(1000, self.update_clock)

    def refresh_all_data(self):
        """ Reloads data across all tabs """
        self.tax_rate = float(db.get_config('tax_rate'))
        self.svc_rate = float(db.get_config('service_rate'))
        self.lbl_brand.config(text=f">> {db.get_config('app_name').upper()}")
        
        self.reload_menu_view()
        self.reload_order_form()
        self.reload_kitchen_view()
        self.reload_status_view()

    # =========================================================================
    # TAB 1: MENU VIEW (Visual Grid)
    # =========================================================================
    def build_menu_tab(self):
        # Futuristic control panel
        ctrl_frame = tb.Frame(self.tab_menu, bootstyle="dark")
        ctrl_frame.pack(fill=X, pady=15, padx=20)
        
        title_label = tb.Label(ctrl_frame, text="MENU INVENTORY", 
                               font=("Orbitron", 14, "bold"), bootstyle="info")
        title_label.pack(side=LEFT)
        
        refresh_btn = tb.Button(ctrl_frame, text="[SYNC]", command=self.reload_menu_view, 
                               bootstyle="info-outline", width=12)
        refresh_btn.pack(side=RIGHT)
        
        # Scrollable Area for Menu Cards
        self.menu_canvas = tk.Canvas(self.tab_menu)
        self.menu_scroll = tb.Scrollbar(self.tab_menu, orient="vertical", command=self.menu_canvas.yview)
        self.menu_grid_frame = tb.Frame(self.menu_canvas)
        
        self.menu_grid_frame.bind("<Configure>", lambda e: self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all")))
        self.menu_canvas.create_window((0,0), window=self.menu_grid_frame, anchor="nw")
        self.menu_canvas.configure(yscrollcommand=self.menu_scroll.set)
        
        self.menu_canvas.pack(side="left", fill="both", expand=True, padx=10)
        self.menu_scroll.pack(side="right", fill="y")

    def reload_menu_view(self):
        for widget in self.menu_grid_frame.winfo_children(): widget.destroy()
        
        items = db.fetch("SELECT name, price, stock FROM menu ORDER BY name")
        if not items: return

        row_idx, col_idx = 0, 0
        MAX_COLS = 5
        
        for name, price, stock in items:
            # Futuristic color coding based on stock
            if stock <= 0:
                card_style = "danger"
                status_text = "OUT OF STOCK"
                status_style = "danger"
            elif stock < 10:
                card_style = "warning"
                status_text = f"LOW: {stock}"
                status_style = "warning"
            else:
                card_style = "success"
                status_text = f"AVAILABLE: {stock}"
                status_style = "success"
            
            # Modern card design
            card = tb.Labelframe(self.menu_grid_frame, text=f"  {name.upper()}  ", 
                                bootstyle=card_style, padding=20)
            card.grid(row=row_idx, column=col_idx, padx=12, pady=12, sticky="nsew")
            
            # Price with futuristic styling
            price_label = tb.Label(card, text=f"${price:.2f}", 
                                  font=("Orbitron", 24, "bold"), bootstyle=card_style)
            price_label.pack(pady=(5, 10))
            
            # Stock status with modern design
            stock_frame = tb.Frame(card)
            stock_frame.pack()
            status_label = tb.Label(stock_frame, text=status_text, 
                                   font=("Consolas", 9, "bold"), bootstyle=status_style)
            status_label.pack()
            
            col_idx += 1
            if col_idx >= MAX_COLS:
                col_idx = 0
                row_idx += 1

    # =========================================================================
    # TAB 2: ORDER TAB
    # =========================================================================
    def build_order_tab(self):
        layout = tb.Frame(self.tab_order, padding=25)
        layout.pack(fill=BOTH, expand=True)
        
        left_col = tb.Frame(layout)
        left_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 15))
        
        # Futuristic table selection panel
        f_table = tb.Labelframe(left_col, text=" TABLE SELECTION ", bootstyle="info", padding=15)
        f_table.pack(fill=X, pady=(0, 15))
        
        table_label = tb.Label(f_table, text="Table:", font=("Orbitron", 11, "bold"))
        table_label.pack(side=LEFT, padx=(0, 10))
        self.cb_tables = tb.Combobox(f_table, state="readonly", width=18, font=("Consolas", 11))
        self.cb_tables.pack(side=LEFT, padx=5)
        refresh_btn = tb.Button(f_table, text="[SYNC]", command=self.reload_order_form, 
                               bootstyle="info-outline", width=10)
        refresh_btn.pack(side=LEFT, padx=5)

        # Menu List with modern styling
        menu_label = tb.Label(left_col, text="MENU ITEMS", font=("Orbitron", 12, "bold"), bootstyle="info")
        menu_label.pack(anchor=W, pady=(10, 8))
        self.lst_menu = tk.Listbox(left_col, font=("Consolas", 11), height=18, 
                                   selectbackground="#00bcd4", selectforeground="black")
        self.lst_menu.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Quantity & Add with futuristic design
        f_qty = tb.Labelframe(left_col, text=" QUANTITY CONTROL ", bootstyle="primary", padding=15)
        f_qty.pack(fill=X)
        
        qty_label = tb.Label(f_qty, text="Qty:", font=("Orbitron", 10, "bold"))
        qty_label.pack(side=LEFT, padx=(0, 10))
        self.spin_qty = tb.Spinbox(f_qty, from_=1, to=100, width=8, font=("Consolas", 11))
        self.spin_qty.set(1)
        self.spin_qty.pack(side=LEFT, padx=5)
        add_btn = tb.Button(f_qty, text="[ADD TO CART]", command=self.add_to_cart, 
                           bootstyle="primary", width=18)
        add_btn.pack(side=RIGHT, padx=5)

        # Right Column (Cart) with modern design
        right_col = tb.Labelframe(layout, text=" ORDER SUMMARY ", bootstyle="success", padding=20)
        right_col.pack(side=RIGHT, fill=BOTH, expand=True)
        
        cols = ("Qty", "Item", "Total")
        self.cart_tree = tb.Treeview(right_col, columns=cols, show="headings", height=18)
        # Note: Treeview doesn't support font parameter - using default system font
        self.cart_tree.heading("Qty", text="QTY"); self.cart_tree.column("Qty", width=60, anchor="center")
        self.cart_tree.heading("Item", text="ITEM"); self.cart_tree.column("Item", width=220)
        self.cart_tree.heading("Total", text="TOTAL"); self.cart_tree.column("Total", width=100, anchor="e")
        self.cart_tree.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        # Total display with futuristic styling
        total_frame = tb.Frame(right_col)
        total_frame.pack(fill=X, pady=(0, 15))
        self.lbl_order_total = tb.Label(total_frame, text="TOTAL: $0.00", 
                                       font=("Orbitron", 16, "bold"), bootstyle="success", 
                                       justify=RIGHT)
        self.lbl_order_total.pack(fill=X)
        
        submit_btn = tb.Button(right_col, text="[SUBMIT ORDER]", command=self.submit_order, 
                              bootstyle="success", width=25)
        submit_btn.pack(fill=X)

    def reload_order_form(self):
        self.lst_menu.delete(0, END)
        self.menu_lookup = {} # Fast access to price/stock by name
        
        # Load Menu
        rows = db.fetch("SELECT id, name, price, stock FROM menu ORDER BY name")
        for r in rows:
            self.menu_lookup[r[1]] = {'id':r[0], 'price':float(r[2]), 'stock':r[3]}
            self.lst_menu.insert(END, f"{r[1]} (${r[2]}) - Stock: {r[3]}")
            
        # Load Tables
        tables = db.fetch("SELECT DISTINCT table_num FROM tables WHERE status='Available' ORDER BY table_num")
        self.cb_tables['values'] = [f"Table {t[0]}" for t in tables]
        if tables: self.cb_tables.current(0)

    def add_to_cart(self):
        try:
            selection = self.lst_menu.curselection()
            if not selection: return
            
            item_text = self.lst_menu.get(selection[0])
            name = item_text.split(" (")[0]
            qty = int(self.spin_qty.get())
            info = self.menu_lookup[name]
            
            # Stock Validation
            current_cart_qty = sum(x['qty'] for x in self.current_cart if x['name'] == name)
            if (info['stock'] - current_cart_qty) < qty:
                messagebox.showerror("Inventory Warning", f"Not enough stock for {name}!")
                return

            # Add
            total_line = info['price'] * qty
            self.current_cart.append({'name': name, 'qty': qty, 'price': info['price'], 'total': total_line})
            self.refresh_cart_display()
            
        except Exception as e:
            print(f"Cart Error: {e}")

    def refresh_cart_display(self):
        # Clear Tree
        for item in self.cart_tree.get_children(): self.cart_tree.delete(item)
        
        subtotal = 0
        for item in self.current_cart:
            self.cart_tree.insert("", "end", values=(item['qty'], item['name'], f"${item['total']:.2f}"))
            subtotal += item['total']
            
        # Calc Estimates
        tax = subtotal * (self.tax_rate / 100)
        svc = subtotal * (self.svc_rate / 100)
        final = subtotal + tax + svc
        
        self.lbl_order_total.config(text=f"SUBTOTAL: ${subtotal:.2f}\nTAX: ${tax:.2f} | SERVICE: ${svc:.2f}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nFINAL TOTAL: ${final:.2f}")

    def submit_order(self):
        if not self.current_cart: return
        
        try:
            table_val = self.cb_tables.get()
            if not table_val: return messagebox.showerror("Missing Info", "Please select a table.")
            table_id = table_val.split(" ")[1]
            
            # Recalculate Final Totals for DB
            subtotal = sum(x['total'] for x in self.current_cart)
            tax = subtotal * (self.tax_rate / 100)
            svc = subtotal * (self.svc_rate / 100)
            total = subtotal + tax + svc
            
            # Create Item String
            items_str = ", ".join([f"{x['qty']}x {x['name']}" for x in self.current_cart])
            
            # 1. Deduct Stock
            for x in self.current_cart:
                db.execute("UPDATE menu SET stock = stock - %s WHERE name=%s", (x['qty'], x['name']))
            
            # 2. Update Table
            db.execute("UPDATE tables SET status='Occupied' WHERE table_num=%s", (table_id,))
            
            # 3. Create Order with timestamp
            db.execute(
                "INSERT INTO orders (table_num, items, subtotal, tax, service, total, status, created_at) VALUES (%s,%s,%s,%s,%s,%s,'Kitchen', NOW())",
                (table_id, items_str, subtotal, tax, svc, total)
            )
            
            # 4. Track table occupation time
            db.execute("UPDATE tables SET occupied_at=NOW() WHERE table_num=%s", (table_id,))
            
            # Reset UI
            self.current_cart = []
            self.refresh_cart_display()
            self.refresh_all_data()
            messagebox.showinfo("Success", "Order sent to Kitchen!")
            
        except Exception as e:
            messagebox.showerror("Order Error", str(e))

    # =========================================================================
    # TAB 3: KITCHEN TAB
    # =========================================================================
    def build_kitchen_tab(self):
        # Futuristic header
        header_frame = tb.Frame(self.tab_kitchen, bootstyle="dark")
        header_frame.pack(fill=X, pady=15, padx=20)
        
        title_label = tb.Label(header_frame, text="KITCHEN QUEUE", 
                              font=("Orbitron", 16, "bold"), bootstyle="warning")
        title_label.pack(side=LEFT)
        
        refresh_btn = tb.Button(header_frame, text="[REFRESH]", command=self.reload_kitchen_view, 
                               bootstyle="warning-outline", width=12)
        refresh_btn.pack(side=RIGHT)
        
        # Scrollable Frame
        self.k_canvas = tk.Canvas(self.tab_kitchen)
        self.k_scroll = tb.Scrollbar(self.tab_kitchen, orient="vertical", command=self.k_canvas.yview)
        self.k_frame = tb.Frame(self.k_canvas)
        
        self.k_frame.bind("<Configure>", lambda e: self.k_canvas.configure(scrollregion=self.k_canvas.bbox("all")))
        self.k_canvas.create_window((0,0), window=self.k_frame, anchor="nw")
        self.k_canvas.configure(yscrollcommand=self.k_scroll.set)
        
        self.k_canvas.pack(side="left", fill="both", expand=True)
        self.k_scroll.pack(side="right", fill="y")

    def reload_kitchen_view(self):
        for w in self.k_frame.winfo_children(): w.destroy()
        orders = db.fetch("SELECT id, table_num, items, created_at FROM orders WHERE status='Kitchen'")
        
        if not orders:
            no_orders = tb.Label(self.k_frame, text=">> NO PENDING ORDERS <<", 
                               font=("Orbitron", 18, "bold"), bootstyle="secondary")
            no_orders.pack(pady=50)
            return
        
        for oid, tnum, items, time_placed in orders:
            # Calculate time elapsed
            time_elapsed = self.calculate_time_elapsed(time_placed)
            # Modern card design
            card = tb.Labelframe(self.k_frame, text=f" ORDER #{oid} ", 
                                bootstyle="warning", padding=20)
            card.pack(fill=X, pady=10, padx=20)
            
            info = tb.Frame(card)
            info.pack(side=LEFT, fill=X, expand=True)
            
            # Table number with futuristic styling
            table_label = tb.Label(info, text=f"TABLE {tnum}", 
                                  font=("Orbitron", 20, "bold"), bootstyle="warning")
            table_label.pack(anchor=W, pady=(0, 5))
            
            # Time with modern design and elapsed time
            time_label = tb.Label(info, text=f"⏱ Placed: {time_placed} | Elapsed: {time_elapsed}", 
                                 font=("Consolas", 10), bootstyle="secondary")
            time_label.pack(anchor=W, pady=(0, 10))
            
            # Items with better formatting
            items_label = tb.Label(info, text=items, 
                                  font=("Consolas", 12, "bold"), 
                                  wraplength=650, bootstyle="inverse-warning")
            items_label.pack(anchor=W)
            
            # Action buttons with modern design
            btns = tb.Frame(card)
            btns.pack(side=RIGHT, padx=(15, 0))
            ready_btn = tb.Button(btns, text="[READY]", bootstyle="success", 
                                  command=lambda i=oid: self.kitchen_action(i, 'Ready'),
                                  width=12)
            ready_btn.pack(side=TOP, pady=5, fill=X)
            cancel_btn = tb.Button(btns, text="[CANCEL]", bootstyle="danger", 
                                   command=lambda i=oid: self.kitchen_action(i, 'Cancel'),
                                   width=12)
            cancel_btn.pack(side=TOP, pady=5, fill=X)

    def kitchen_action(self, order_id, action):
        if action == 'Cancel':
            if messagebox.askyesno("Confirm", "Cancel Order? This will return items to stock."):
                # Get items to return stock
                items_row = db.fetch("SELECT items, table_num FROM orders WHERE id=%s", (order_id,))
                items = items_row[0][0] if items_row else ""
                table_num = items_row[0][1] if items_row else None
                db.restore_inventory_stock(items)
                db.execute("UPDATE orders SET status='Cancelled' WHERE id=%s", (order_id,))
                if table_num:
                    # #region agent log
                    import json, time; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log','a',encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"HTABLE","location":"main.py:kitchen_action","message":"Cancel sets table available","data":{"orderId":order_id,"table":table_num,"timestamp":int(time.time()*1000)}})+"\n"); log_file.close()
                    # #endregion
                    db.execute("UPDATE tables SET status='Available', occupied_at=NULL WHERE table_num=%s", (table_num,))
        else:
            db.execute("UPDATE orders SET status='Ready' WHERE id=%s", (order_id,))
        
        self.refresh_all_data()

    # =========================================================================
    # TAB 4: STATUS & PAY (Smart Billing)
    # =========================================================================
    def build_status_tab(self):
        panes = tb.Panedwindow(self.tab_status, orient=HORIZONTAL)
        panes.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Left List with modern design
        left = tb.Labelframe(panes, text=" ACTIVE ORDERS ", bootstyle="info", padding=15)
        panes.add(left, weight=2)
        
        # Header with refresh button
        header_frame = tb.Frame(left)
        header_frame.pack(fill=X, pady=(0, 10))
        title_label = tb.Label(header_frame, text="ORDER QUEUE", 
                              font=("Orbitron", 12, "bold"), bootstyle="info")
        title_label.pack(side=LEFT)
        refresh_btn = tb.Button(header_frame, text="[R]", command=self.reload_status_view, 
                               bootstyle="info-outline", width=4)
        refresh_btn.pack(side=RIGHT)
        
        self.status_tree = tb.Treeview(left, columns=("ID", "Table", "Status", "Time", "Items"), 
                                      show="headings")
        self.status_tree.heading("ID", text="ID"); self.status_tree.column("ID", width=50, anchor="center")
        self.status_tree.heading("Table", text="TABLE"); self.status_tree.column("Table", width=80, anchor="center")
        self.status_tree.heading("Status", text="STATUS"); self.status_tree.column("Status", width=100, anchor="center")
        self.status_tree.heading("Time", text="TIME"); self.status_tree.column("Time", width=80, anchor="center")
        self.status_tree.heading("Items", text="ITEMS")
        self.status_tree.pack(fill=BOTH, expand=True)

        # Right Details with futuristic design
        right = tb.Labelframe(panes, text=" BILL DETAILS ", bootstyle="success", padding=20)
        panes.add(right, weight=1)
        
        # Bill preview with modern styling
        preview_frame = tb.Frame(right)
        preview_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        self.lbl_bill_preview = tb.Label(preview_frame, text=">> SELECT AN ORDER <<", 
                                        font=("Consolas", 11), justify=LEFT, bootstyle="secondary")
        self.lbl_bill_preview.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Action buttons with modern design
        btn_box = tb.Frame(right)
        btn_box.pack(fill=X, side=BOTTOM)
        pay_btn = tb.Button(btn_box, text="[PAY & CLEAR]", command=self.process_payment, 
                           bootstyle="success", width=20)
        pay_btn.pack(fill=X, pady=5)
        cancel_btn = tb.Button(btn_box, text="[CANCEL ORDER]", command=self.cancel_from_status, 
                              bootstyle="danger", width=20)
        cancel_btn.pack(fill=X)

        # Bind selection to show bill details
        self.status_tree.bind("<<TreeviewSelect>>", self.preview_bill)

    def calculate_time_elapsed(self, created_at_str):
        """Calculate time elapsed since order was created"""
        try:
            from datetime import datetime
            if created_at_str:
                created_time = datetime.strptime(str(created_at_str), "%Y-%m-%d %H:%M:%S")
                elapsed = datetime.now() - created_time
                minutes = int(elapsed.total_seconds() / 60)
                if minutes < 60:
                    return f"{minutes}m"
                else:
                    hours = minutes // 60
                    mins = minutes % 60
                    return f"{hours}h {mins}m"
        except:
            pass
        return "N/A"
    
    def reload_status_view(self):
        for i in self.status_tree.get_children(): self.status_tree.delete(i)
        rows = db.fetch("SELECT id, table_num, status, items, created_at FROM orders WHERE status NOT IN ('Paid', 'Cancelled')")
        for r in rows:
            # Calculate time elapsed
            time_elapsed = self.calculate_time_elapsed(r[4] if len(r) > 4 else None)
            # Display: ID, Table, Status, Time, Items
            display_values = (r[0], r[1], r[2], time_elapsed, r[3])
            self.status_tree.insert("", "end", values=display_values)

    def preview_bill(self, e):
        sel = self.status_tree.selection()
        if not sel: return
        oid = self.status_tree.item(sel[0])['values'][0]
        
        data = db.fetch("SELECT subtotal, tax, service, total, items FROM orders WHERE id=%s", (oid,))
        if not data: return
        r = data[0]
        
        txt = f"Items:\n{r[4]}\n\n"
        txt += f"{'Subtotal:':<15} ${r[0]}\n"
        txt += f"{'Tax:':<15} ${r[1]}\n"
        txt += f"{'Service:':<15} ${r[2]}\n"
        txt += "-"*30 + "\n"
        txt += f"{'TOTAL:':<15} ${r[3]}"
        self.lbl_bill_preview.config(text=txt)

    def process_payment(self):
        sel = self.status_tree.selection()
        if not sel: return
        oid = self.status_tree.item(sel[0])['values'][0]
        
        # Get financial details
        row = db.fetch("SELECT table_num, total, tax, service FROM orders WHERE id=%s", (oid,))[0]
        tnum, total, tax, svc = row[0], float(row[1]), float(row[2]), float(row[3])
        
        # Payment Popup
        win = tb.Toplevel(self)
        win.title(f"Pay Order #{oid}")
        
        tb.Label(win, text=f"Amount Due: ${total}", font=("bold", 16)).pack(pady=10)
        
        tb.Label(win, text="Discount ($):").pack()
        ent_disc = tb.Entry(win); ent_disc.pack(); ent_disc.insert(0, "0")
        
        tb.Label(win, text="Tip ($):").pack()
        ent_tip = tb.Entry(win); ent_tip.pack(); ent_tip.insert(0, "0")
        
        def commit_pay():
            try:
                disc = float(ent_disc.get())
                tip = float(ent_tip.get())
                final_collected = total - disc
                
                # 1. Wallet Updates
                db.update_wallet(final_collected, "SALE", f"Order #{oid} (Disc: {disc})")
                db.update_pool_balance('tax_pool', tax)
                db.update_pool_balance('service_pool', svc)
                
                if tip > 0:
                    db.update_pool_balance('tips_pool', tip)
                    db.update_wallet(tip, "TIP_IN", f"Tip for #{oid}")
                
                # 2. Update DB Status
                db.execute("UPDATE orders SET status='Paid', discount=%s, tip=%s WHERE id=%s", (disc, tip, oid))
                db.execute("UPDATE tables SET status='Available', occupied_at=NULL WHERE table_num=%s", (tnum,))
                
                # 3. Generate Receipt Text File - Get actual order data
                order_data = db.fetch("SELECT items, subtotal, tax, service, total FROM orders WHERE id=%s", (oid,))
                if order_data:
                    items, subtotal, tax_amt, svc_amt, order_total = order_data[0]
                    receipt_text = f"""*** TITANIUM OS RECEIPT ***
Order ID: #{oid}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Table: {tnum}
--------------------------------
Items:
{items}
--------------------------------
Subtotal: ${float(subtotal):.2f}
Tax: ${float(tax_amt):.2f}
Service: ${float(svc_amt):.2f}
--------------------------------
Subtotal: ${float(subtotal):.2f}
Discount: -${disc:.2f}
Tip Added: +${tip:.2f}
================================
AMOUNT PAID: ${final_collected + tip:.2f}
================================
Thank you for your business!
"""
                else:
                    receipt_text = f"""*** TITANIUM OS RECEIPT ***
Order ID: #{oid}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
--------------------------------
AMOUNT PAID: ${final_collected + tip:.2f}
================================
Thank you!
"""
                with open(f"receipt_{oid}.txt", "w") as f: f.write(receipt_text)
                
                win.destroy()
                self.refresh_all_data()
                self.lbl_bill_preview.config(text="Select an Order")
                messagebox.showinfo("Success", f"Payment Complete.\nReceipt saved as receipt_{oid}.txt")
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers.")

        tb.Button(win, text="Confirm Payment", command=commit_pay, bootstyle="success").pack(pady=15)

    def cancel_from_status(self):
        sel = self.status_tree.selection()
        if not sel: return
        oid = self.status_tree.item(sel[0])['values'][0]
        
        if messagebox.askyesno("Confirm", "Cancel order and restore stock?"):
            items_row = db.fetch("SELECT items, table_num FROM orders WHERE id=%s", (oid,))
            items = items_row[0][0] if items_row else ""
            table_num = items_row[0][1] if items_row else None
            db.restore_inventory_stock(items)
            db.execute("UPDATE orders SET status='Cancelled' WHERE id=%s", (oid,))
            if table_num:
                # #region agent log
                import json, time; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log','a',encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"HTABLE","location":"main.py:cancel_from_status","message":"Status cancel sets table available","data":{"orderId":oid,"table":table_num,"timestamp":int(time.time()*1000)}})+"\n"); log_file.close()
                # #endregion
                db.execute("UPDATE tables SET status='Available', occupied_at=NULL WHERE table_num=%s", (table_num,))
            self.refresh_all_data()

    # =========================================================================
    # TAB 5: ADMIN (Password Protected)
    # =========================================================================
    def build_admin_lock_screen(self):
        self.admin_lock_frame = tb.Frame(self.tab_admin)
        self.admin_lock_frame.pack(expand=True)
        
        tb.Label(self.admin_lock_frame, text="Restricted Area", font=("bold", 20)).pack(pady=20)
        self.ent_admin_pass = tb.Entry(self.admin_lock_frame, show="*")
        self.ent_admin_pass.pack()
        tb.Button(self.admin_lock_frame, text="Login", command=self.check_admin_pass).pack(pady=10)

    def check_admin_pass(self):
        if self.ent_admin_pass.get() == db.get_config('admin_pass'):
            self.admin_lock_frame.destroy()
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:560","message":"Entering build_admin_dashboard","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
            self.build_admin_dashboard()
        else:
            messagebox.showerror("Access Denied", "Incorrect Password")
    
    def logout_admin(self):
        """Logout from admin dashboard and return to lock screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            # Destroy admin dashboard
            for widget in self.tab_admin.winfo_children():
                widget.destroy()
            # Rebuild lock screen
            self.build_admin_lock_screen()

    def build_admin_dashboard(self):
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:564","message":"build_admin_dashboard entry","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        adm_nb = tb.Notebook(self.tab_admin, bootstyle="info")
        adm_nb.pack(fill=BOTH, expand=True)

        # A. Wallet
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:569","message":"Before Wallet tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_wal = tb.Frame(adm_nb); adm_nb.add(p_wal, text="Wallet")
        self.setup_admin_wallet(p_wal)

        # B. Menu Edit
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:573","message":"Before Menu tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_men = tb.Frame(adm_nb); adm_nb.add(p_men, text="Menu")
        self.setup_admin_menu(p_men)

        # C. Inventory
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:577","message":"Before Inventory tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_inv = tb.Frame(adm_nb); adm_nb.add(p_inv, text="Inventory")
        self.setup_admin_inventory(p_inv)

        # D. Data Logs
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:581","message":"Before Data tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_data = tb.Frame(adm_nb); adm_nb.add(p_data, text="Data")
        self.setup_admin_data(p_data)

        # E. Settings
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:585","message":"Before Settings tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_set = tb.Frame(adm_nb); adm_nb.add(p_set, text="Settings")
        try:
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:586","message":"Calling setup_adm_settings","data":{"hasMethod":hasattr(self,'setup_adm_settings'),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
            self.setup_adm_settings(p_set)
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:586","message":"Settings setup completed","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
        except Exception as e:
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:586","message":"Settings setup exception","data":{"error":str(e),"errorType":type(e).__name__,"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
            raise

        # F. Export
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main.py:589","message":"Before Export tab creation","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        p_exp = tb.Frame(adm_nb); adm_nb.add(p_exp, text="Export")
        
        # G. About
        p_about = tb.Frame(adm_nb); adm_nb.add(p_about, text="About")
        self.setup_admin_about(p_about)
        
        # H. Logout Button in Admin Dashboard
        logout_frame = tb.Frame(self.tab_admin, bootstyle="dark")
        logout_frame.pack(side=BOTTOM, fill=X, padx=10, pady=5)
        logout_btn = tb.Button(logout_frame, text="[LOGOUT]", command=self.logout_admin, 
                              bootstyle="danger-outline", width=15)
        logout_btn.pack(side=RIGHT)
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:589","message":"Export tab frame created and added","data":{"tabCount":adm_nb.index("end"),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        try:
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:590","message":"Calling setup_admin_export","data":{"hasMethod":hasattr(self,'setup_admin_export'),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
            self.setup_admin_export(p_exp)
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:590","message":"Export setup completed","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
        except Exception as e:
            # #region agent log
            import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:590","message":"Export setup exception","data":{"error":str(e),"errorType":type(e).__name__,"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
            # #endregion
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"main.py:590","message":"After all tabs added","data":{"totalTabs":adm_nb.index("end"),"exportTabIndex":adm_nb.index(p_exp) if p_exp in adm_nb.tabs() else -1,"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion

    # --- ADMIN: WALLET ---
    def setup_admin_wallet(self, p):
        # Futuristic wallet header
        header_frame = tb.Frame(p, bootstyle="dark")
        header_frame.pack(fill=X, pady=20, padx=20)
        
        title_label = tb.Label(header_frame, text="WALLET SYSTEM", 
                              font=("Orbitron", 16, "bold"), bootstyle="info")
        title_label.pack()
        
        self.lbl_wallet_bal = tb.Label(p, text="WALLET: $0.00", 
                                      font=("Orbitron", 32, "bold"), bootstyle="success")
        self.lbl_wallet_bal.pack(pady=25)
        
        # Pools with modern design
        fp = tb.Labelframe(p, text=" ACCUMULATED POOLS ", bootstyle="info", padding=20)
        fp.pack(fill=X, padx=20, pady=15)
        
        # Tax Pool
        tax_frame = tb.Frame(fp)
        tax_frame.pack(side=LEFT, padx=15, expand=True)
        self.lbl_pool_tax = tb.Label(tax_frame, text="TAX: $0.00", 
                                     font=("Orbitron", 12, "bold"), bootstyle="danger")
        self.lbl_pool_tax.pack()
        tb.Button(tax_frame, text="PAYOUT", command=lambda: self.payout_pool('tax_pool'), 
                 bootstyle="danger-outline", width=12).pack(pady=5)
        
        # Service Pool
        svc_frame = tb.Frame(fp)
        svc_frame.pack(side=LEFT, padx=15, expand=True)
        self.lbl_pool_svc = tb.Label(svc_frame, text="SERVICE: $0.00", 
                                     font=("Orbitron", 12, "bold"), bootstyle="warning")
        self.lbl_pool_svc.pack()
        tb.Button(svc_frame, text="PAYOUT", command=lambda: self.payout_pool('service_pool'), 
                 bootstyle="warning-outline", width=12).pack(pady=5)
        
        # Tips Pool
        tips_frame = tb.Frame(fp)
        tips_frame.pack(side=LEFT, padx=15, expand=True)
        self.lbl_pool_tips = tb.Label(tips_frame, text="TIPS: $0.00", 
                                      font=("Orbitron", 12, "bold"), bootstyle="info")
        self.lbl_pool_tips.pack()
        tb.Button(tips_frame, text="PAYOUT", command=lambda: self.payout_pool('tips_pool'), 
                 bootstyle="info-outline", width=12).pack(pady=5)

        # Manual Ops with modern design
        fm = tb.Labelframe(p, text=" MANUAL ADJUSTMENT ", bootstyle="primary", padding=20)
        fm.pack(fill=X, padx=20, pady=15)
        
        amount_label = tb.Label(fm, text="Amount:", font=("Orbitron", 10, "bold"))
        amount_label.pack(side=LEFT, padx=(0, 10))
        self.ent_man_amt = tb.Entry(fm, width=15, font=("Consolas", 11))
        self.ent_man_amt.pack(side=LEFT, padx=5)
        deposit_btn = tb.Button(fm, text="[DEPOSIT]", command=lambda: self.manual_wallet_op(1), 
                               bootstyle="success", width=12)
        deposit_btn.pack(side=LEFT, padx=5)
        withdraw_btn = tb.Button(fm, text="[WITHDRAW]", command=lambda: self.manual_wallet_op(-1), 
                                bootstyle="danger", width=12)
        withdraw_btn.pack(side=LEFT, padx=5)
        
        refresh_btn = tb.Button(p, text="[REFRESH DATA]", command=self.refresh_admin_wallet_ui, 
                               bootstyle="info-outline", width=18)
        refresh_btn.pack(pady=15)
        self.refresh_admin_wallet_ui()

    def refresh_admin_wallet_ui(self):
        w = db.get_config('wallet')
        t = db.get_config('tax_pool')
        s = db.get_config('service_pool')
        tp = db.get_config('tips_pool')
        
        self.lbl_wallet_bal.config(text=f"Wallet: ${float(w):.2f}")
        self.lbl_pool_tax.config(text=f"Tax: ${float(t):.2f}")
        self.lbl_pool_svc.config(text=f"Svc: ${float(s):.2f}")
        self.lbl_pool_tips.config(text=f"Tips: ${float(tp):.2f}")

    def manual_wallet_op(self, multiplier):
        try:
            val = float(self.ent_man_amt.get()) * multiplier
            type_str = "DEPOSIT" if multiplier > 0 else "WITHDRAW"
            if db.update_wallet(val, "MANUAL", f"Admin {type_str}"):
                self.refresh_admin_wallet_ui()
        except: pass
        
        

    def payout_pool(self, pool):
        amt = float(db.get_config(pool))
        if amt > 0 and messagebox.askyesno("Confirm Payout", f"Pay out ${amt:.2f}? This removes funds from wallet."):
            # 1. Deduct from Main Wallet
            if db.update_wallet(-amt, "PAYOUT", f"{pool.replace('_pool','').upper()} Cleared"):
                # 2. Reset the Pool Counter to 0
                db.set_config(pool, "0.00")
                self.refresh_admin_wallet_ui()
            else:
                # update_wallet handles the error message
                pass
        elif amt <= 0:
            messagebox.showinfo("Info", "Pool is already empty.")
    

    # --- ADMIN: MENU EDIT ---
    def setup_admin_menu(self, p):
        f = tb.Labelframe(p, text="Edit Selected Item", padding=10); f.pack(fill=X, padx=10, pady=5)
        
        self.ent_m_name = tb.Entry(f); self.ent_m_name.pack(side=LEFT, padx=5)
        self.ent_m_price = tb.Entry(f, width=8); self.ent_m_price.pack(side=LEFT, padx=5)
        self.ent_m_cost = tb.Entry(f, width=8); self.ent_m_cost.pack(side=LEFT, padx=5)
        
        tb.Button(f, text="Add New", command=self.adm_add_item, bootstyle="success").pack(side=LEFT, padx=5)
        tb.Button(f, text="Update Item", command=self.adm_update_item, bootstyle="warning").pack(side=LEFT, padx=5)
        tb.Button(f, text="Delete", command=self.adm_del_item, bootstyle="danger").pack(side=RIGHT)

        cols = ("ID", "Name", "Sell", "Cost", "Stock")
        self.tree_adm_menu = tb.Treeview(p, columns=cols, show="headings")
        for c in cols: self.tree_adm_menu.heading(c, text=c)
        self.tree_adm_menu.pack(fill=BOTH, expand=True, padx=10)
        self.tree_adm_menu.bind("<<TreeviewSelect>>", self.on_adm_menu_select)
        
        # Quick Edit Buttons
        quick_edit_frame = tb.Frame(p, padding=10)
        quick_edit_frame.pack(fill=X, padx=10, pady=5)
        tb.Label(quick_edit_frame, text="Quick Actions:", font=("Orbitron", 10, "bold")).pack(side=LEFT, padx=5)
        tb.Button(quick_edit_frame, text="[+10 Stock]", command=lambda: self.quick_stock_change(10), 
                 bootstyle="success-outline", width=12).pack(side=LEFT, padx=2)
        tb.Button(quick_edit_frame, text="[-10 Stock]", command=lambda: self.quick_stock_change(-10), 
                 bootstyle="warning-outline", width=12).pack(side=LEFT, padx=2)
        tb.Button(quick_edit_frame, text="[+$1 Price]", command=lambda: self.quick_price_change(1), 
                 bootstyle="info-outline", width=12).pack(side=LEFT, padx=2)
        tb.Button(quick_edit_frame, text="[-$1 Price]", command=lambda: self.quick_price_change(-1), 
                 bootstyle="danger-outline", width=12).pack(side=LEFT, padx=2)
        
        self.refresh_adm_menu_list()

    def refresh_adm_menu_list(self):
        for i in self.tree_adm_menu.get_children(): self.tree_adm_menu.delete(i)
        rows = db.fetch("SELECT id, name, price, cost, stock FROM menu")
        for r in rows: self.tree_adm_menu.insert("", "end", values=r)
        self.reload_inventory_dropdown() # Update inventory tab too

    def on_adm_menu_select(self, e):
        sel = self.tree_adm_menu.selection()
        if sel:
            vals = self.tree_adm_menu.item(sel[0])['values']
            self.edit_item_id = vals[0]
            self.ent_m_name.delete(0, END); self.ent_m_name.insert(0, vals[1])
            self.ent_m_price.delete(0, END); self.ent_m_price.insert(0, vals[2])
            self.ent_m_cost.delete(0, END); self.ent_m_cost.insert(0, vals[3])

    def adm_add_item(self):
        db.execute("INSERT INTO menu (name, price, cost, stock) VALUES (%s, %s, %s, 0)", 
                   (self.ent_m_name.get(), self.ent_m_price.get(), self.ent_m_cost.get()))
        self.refresh_adm_menu_list()

    def adm_update_item(self):
        if self.edit_item_id:
            db.execute("UPDATE menu SET name=%s, price=%s, cost=%s WHERE id=%s", 
                       (self.ent_m_name.get(), self.ent_m_price.get(), self.ent_m_cost.get(), self.edit_item_id))
            self.refresh_adm_menu_list()

    def adm_del_item(self):
        if self.edit_item_id:
            db.execute("DELETE FROM menu WHERE id=%s", (self.edit_item_id,))
            self.refresh_adm_menu_list()
    
    def quick_stock_change(self, amount):
        """Quickly change stock by amount - deducts from wallet if adding stock"""
        if self.edit_item_id:
            item_data = db.fetch("SELECT name, stock, cost FROM menu WHERE id=%s", (self.edit_item_id,))
            if not item_data:
                messagebox.showerror("Error", "Item not found")
                return
            
            name, current_stock, item_cost = item_data[0]
            new_stock = max(0, current_stock + amount)
            
            # If adding stock (amount > 0), deduct cost from wallet
            if amount > 0:
                total_cost = float(item_cost) * amount
                if not db.update_wallet(-total_cost, "STOCK", f"Quick stock: {amount} {name}"):
                    return  # update_wallet shows error if insufficient funds
            
            db.execute("UPDATE menu SET stock=%s WHERE id=%s", (new_stock, self.edit_item_id))
            self.refresh_adm_menu_list()
            self.refresh_admin_wallet_ui()
            
            if amount > 0:
                messagebox.showinfo("Success", f"Stock updated to {new_stock}\nCost: ${float(item_cost) * amount:.2f} deducted from wallet")
            else:
                messagebox.showinfo("Success", f"Stock updated to {new_stock}")
        else:
            messagebox.showwarning("No Selection", "Please select an item first")
    
    def quick_price_change(self, amount):
        """Quickly change price by amount"""
        if self.edit_item_id:
            current_price = db.fetch("SELECT price FROM menu WHERE id=%s", (self.edit_item_id,))[0][0]
            new_price = max(0.01, float(current_price) + amount)
            db.execute("UPDATE menu SET price=%s WHERE id=%s", (new_price, self.edit_item_id))
            self.refresh_adm_menu_list()
            messagebox.showinfo("Success", f"Price updated to ${new_price:.2f}")
        else:
            messagebox.showwarning("No Selection", "Please select an item first")

    # --- ADMIN: INVENTORY ---
    def setup_admin_inventory(self, p):
        f = tb.Frame(p, padding=20); f.pack(fill=X)
        tb.Label(f, text="Select Item to Buy Stock (Uses Wallet):").pack()
        self.cb_inv_item = tb.Combobox(f, state="readonly"); self.cb_inv_item.pack(pady=5)
        self.ent_inv_qty = tb.Entry(f, width=10); self.ent_inv_qty.pack(pady=5)
        tb.Button(f, text="Buy Stock", command=self.buy_stock_action, bootstyle="warning").pack()
        self.reload_inventory_dropdown()

    def reload_inventory_dropdown(self):
        if hasattr(self, 'cb_inv_item'):
            items = db.fetch("SELECT name FROM menu")
            self.cb_inv_item['values'] = [i[0] for i in items]

    def buy_stock_action(self):
        name = self.cb_inv_item.get()
        if not name: return
        try:
            qty = int(self.ent_inv_qty.get())
            cost = db.fetch("SELECT cost FROM menu WHERE name=%s", (name,))[0][0] * qty
            
            if db.update_wallet(-cost, "STOCK", f"Bought {qty} {name}"):
                db.execute("UPDATE menu SET stock = stock + %s WHERE name=%s", (qty, name))
                messagebox.showinfo("Success", f"Stock updated. Cost: ${cost}")
                self.refresh_adm_menu_list()
                self.refresh_admin_wallet_ui()
        except: pass

    # --- ADMIN: DATA LOGS ---
    def setup_admin_data(self, p):
        # Profit Margin Calculator Section
        profit_frame = tb.Labelframe(p, text=" PROFIT MARGIN CALCULATOR ", bootstyle="info", padding=15)
        profit_frame.pack(fill=X, padx=10, pady=10)
        
        calc_grid = tb.Frame(profit_frame)
        calc_grid.pack(fill=X)
        
        tb.Label(calc_grid, text="Total Revenue:", font=("Orbitron", 10, "bold")).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.lbl_total_revenue = tb.Label(calc_grid, text="$0.00", font=("Consolas", 12, "bold"), bootstyle="success")
        self.lbl_total_revenue.grid(row=0, column=1, padx=10, pady=5)
        
        tb.Label(calc_grid, text="Total Cost:", font=("Orbitron", 10, "bold")).grid(row=0, column=2, sticky=W, padx=5, pady=5)
        self.lbl_total_cost = tb.Label(calc_grid, text="$0.00", font=("Consolas", 12, "bold"), bootstyle="danger")
        self.lbl_total_cost.grid(row=0, column=3, padx=10, pady=5)
        
        tb.Label(calc_grid, text="Total Profit:", font=("Orbitron", 10, "bold")).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.lbl_total_profit = tb.Label(calc_grid, text="$0.00", font=("Consolas", 14, "bold"), bootstyle="success")
        self.lbl_total_profit.grid(row=1, column=1, padx=10, pady=5)
        
        tb.Label(calc_grid, text="Profit Margin:", font=("Orbitron", 10, "bold")).grid(row=1, column=2, sticky=W, padx=5, pady=5)
        self.lbl_profit_margin = tb.Label(calc_grid, text="0.00%", font=("Consolas", 14, "bold"), bootstyle="info")
        self.lbl_profit_margin.grid(row=1, column=3, padx=10, pady=5)
        
        tb.Button(profit_frame, text="[CALCULATE PROFIT]", command=self.calculate_profit_margin, 
                 bootstyle="info-outline", width=20).pack(pady=10)
        
        # Order History Section
        history_frame = tb.Labelframe(p, text=" ORDER HISTORY ", bootstyle="primary", padding=10)
        history_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        cols = ("ID", "Date", "Table", "Status", "Total")
        self.tree_logs = tb.Treeview(history_frame, columns=cols, show="headings")
        for c in cols: self.tree_logs.heading(c, text=c)
        self.tree_logs.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        btn_frame = tb.Frame(history_frame)
        btn_frame.pack(fill=X, pady=5)
        tb.Button(btn_frame, text="[REFRESH LOGS]", command=self.load_admin_logs, 
                 bootstyle="primary-outline").pack(side=LEFT, padx=5)
        self.load_admin_logs()
        self.calculate_profit_margin()

    def calculate_profit_margin(self):
        """Calculate profit margin from all paid orders"""
        # Get all paid orders
        paid_orders = db.fetch("SELECT items, total, tax, service, subtotal FROM orders WHERE status='Paid'")
        
        total_revenue_net = 0.0
        total_cost = 0.0
        
        for items_str, order_total, tax_amt, svc_amt, subtotal_amt in paid_orders:
            # Exclude taxes/service from profit; prefer stored subtotal, else derive
            if subtotal_amt is not None:
                revenue_net = float(subtotal_amt)
            else:
                revenue_net = float(order_total) - float(tax_amt or 0) - float(svc_amt or 0)
            total_revenue_net += revenue_net
            
            # Calculate cost for each item in the order
            if items_str:
                for item in items_str.split(", "):
                    try:
                        if "x " in item:
                            parts = item.split("x ")
                            qty = int(parts[0])
                            item_name = parts[1].strip()
                            # Get cost from menu
                            cost_data = db.fetch("SELECT cost FROM menu WHERE name=%s", (item_name,))
                            if cost_data:
                                item_cost = float(cost_data[0][0]) * qty
                                total_cost += item_cost
                    except:
                        pass
        
        total_profit = total_revenue_net - total_cost
        profit_margin = (total_profit / total_revenue_net * 100) if total_revenue_net > 0 else 0
        
        # #region agent log
        import json, time; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log','a',encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"pre-fix","hypothesisId":"HPROFIT","location":"main.py:calculate_profit_margin","message":"Computed profit excluding taxes","data":{"revenueNet":total_revenue_net,"cost":total_cost,"profit":total_profit,"margin":profit_margin,"timestamp":int(time.time()*1000)}})+"\n"); log_file.close()
        # #endregion

        self.lbl_total_revenue.config(text=f"${total_revenue_net:.2f}")
        self.lbl_total_cost.config(text=f"${total_cost:.2f}")
        self.lbl_total_profit.config(text=f"${total_profit:.2f}")
        self.lbl_profit_margin.config(text=f"{profit_margin:.2f}%")
    
    def load_admin_logs(self):
        for i in self.tree_logs.get_children(): self.tree_logs.delete(i)
        # Using created_at from V31 database fix
        rows = db.fetch("SELECT id, created_at, table_num, status, total FROM orders ORDER BY id DESC")
        for r in rows: self.tree_logs.insert("", "end", values=r)

    # --- ADMIN: SETTINGS (FIXED) ---
    def setup_adm_settings(self, p):
        # Clear previous widgets if any
        for widget in p.winfo_children(): widget.destroy()

        # Main Settings Frame
        f = tb.Frame(p, padding=20)
        f.pack(fill=X, anchor=N)
        
        # App Name
        tb.Label(f, text="App Name:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W, pady=5)
        self.e_appname = tb.Entry(f, width=30)
        self.e_appname.grid(row=0, column=1, pady=5, padx=10)
        self.e_appname.insert(0, db.get_config('app_name'))
        
        # Tax Rate
        tb.Label(f, text="Tax Rate (%):", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=W, pady=5)
        self.e_taxrate = tb.Entry(f, width=10)
        self.e_taxrate.grid(row=1, column=1, sticky=W, pady=5, padx=10)
        self.e_taxrate.insert(0, db.get_config('tax_rate'))
        
        # Service Charge
        tb.Label(f, text="Service Charge (%):", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=W, pady=5)
        self.e_svcrate = tb.Entry(f, width=10)
        self.e_svcrate.grid(row=2, column=1, sticky=W, pady=5, padx=10)
        self.e_svcrate.insert(0, db.get_config('service_rate'))
        
        # Theme Selector
        tb.Label(f, text="Theme:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=W, pady=5)
        # Dark themes only
        self.cb_theme = tb.Combobox(f, values=['superhero', 'darkly', 'solar', 'cyborg', 'vapor', 'slate'], state="readonly", width=28)
        self.cb_theme.grid(row=3, column=1, pady=5, padx=10)
        self.cb_theme.set(db.get_config('theme'))
        
        # Admin Password Change
        tb.Label(f, text="Admin Password:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=W, pady=5)
        self.e_admin_pass = tb.Entry(f, width=30, show="*")
        self.e_admin_pass.grid(row=4, column=1, pady=5, padx=10)
        tb.Button(f, text="Change Password", command=self.change_admin_password, bootstyle="warning").grid(row=4, column=2, pady=5, padx=5)
        
        # Save Button
        tb.Button(f, text="[SAVE SETTINGS]", command=self.save_all_settings, bootstyle="success").grid(row=5, column=1, pady=20, sticky=W)
        
        # Separator
        ttk.Separator(p, orient='horizontal').pack(fill=X, pady=10)

        # Table Management Section
        ft = tb.Labelframe(p, text="Table Management", padding=15)
        ft.pack(fill=X, padx=20, pady=10)
        
        tb.Button(ft, text="[+ Add New Table]", command=self.add_table, bootstyle="info").pack(side=RIGHT)
        
        tb.Label(ft, text="Delete Table:").pack(side=LEFT)
        self.cb_rem_tbl = tb.Combobox(ft, state="readonly", width=10)
        self.cb_rem_tbl.pack(side=LEFT, padx=10)
        tb.Button(ft, text="[Remove]", command=self.del_table, bootstyle="danger").pack(side=LEFT)
        
        # Initial Load of Tables for the dropdown
        self.reload_adm_tables()

    def change_admin_password(self):
        new_pass = self.e_admin_pass.get()
        if not new_pass:
            messagebox.showerror("Error", "Password cannot be empty")
            return
        if messagebox.askyesno("Confirm", "Change admin password?"):
            db.set_config('admin_pass', new_pass)
            self.e_admin_pass.delete(0, END)
            messagebox.showinfo("Success", "Admin password changed successfully")
    
    def save_all_settings(self):
        try:
            db.set_config('app_name', self.e_appname.get())
            db.set_config('tax_rate', self.e_taxrate.get())
            db.set_config('service_rate', self.e_svcrate.get())
            
            if self.cb_theme.get():
                db.set_config('theme', self.cb_theme.get())
            
            messagebox.showinfo("Success", "Settings Saved!\nRestart the application to apply Theme and Name changes.")
            # Refresh local variables immediately so calculations update without restart
            self.refresh_all_data() 
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")

    def reload_adm_tables(self):
        # Helper to refresh the delete table dropdown
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"T1","location":"main.py:874","message":"reload_adm_tables entry","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        ts = db.fetch("SELECT DISTINCT table_num FROM tables WHERE status='Available' ORDER BY table_num")
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"T1","location":"main.py:876","message":"Database query result","data":{"rawResult":str(ts),"resultCount":len(ts),"firstFew":str(ts[:3]) if len(ts) > 0 else "empty","timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        table_values = []
        seen = set()
        for t in ts:
            if t[0] is not None:
                val = str(int(t[0]))
                if val not in seen:
                    seen.add(val)
                    table_values.append(val)
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"T1","location":"main.py:877","message":"Processed table values","data":{"values":table_values,"valuesCount":len(table_values),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        self.cb_rem_tbl['values'] = table_values
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"T1","location":"main.py:877","message":"Combobox values set","data":{"comboboxValues":list(self.cb_rem_tbl['values']),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        if ts: self.cb_rem_tbl.current(0)
        else: self.cb_rem_tbl.set('')

    def add_table(self):
        m = db.fetch("SELECT MAX(table_num) FROM tables")[0][0] or 0
        db.execute("INSERT INTO tables (table_num) VALUES (%s)", (m+1,))
        self.reload_adm_tables()
        self.refresh_all_data() # Update main UI table list
        messagebox.showinfo("Success", f"Table {m+1} Added")

    def del_table(self):
        t_val = self.cb_rem_tbl.get()
        if t_val: 
            if messagebox.askyesno("Confirm", f"Delete Table {t_val}?"):
                db.execute("DELETE FROM tables WHERE table_num=%s", (t_val,))
                self.reload_adm_tables()
                self.refresh_all_data()

    # --- ADMIN: EXPORT ---
    def setup_admin_export(self, p):
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main.py:844","message":"setup_admin_export entry","data":{"frameExists":p is not None,"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        tb.Label(p, text="Export CSV Data", font=("bold", 16)).pack(pady=20)
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main.py:845","message":"Label added to Export tab","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        tb.Button(p, text="Export Orders", command=lambda: self.export_csv("orders")).pack(fill=X, pady=5, padx=50)
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main.py:846","message":"First button added","data":{"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion
        tb.Button(p, text="Export Wallet", command=lambda: self.export_csv("wallet_logs")).pack(fill=X, pady=5, padx=50)
        # #region agent log
        import json; log_file = open(r'd:\Programmming\@Python\Titanium\.cursor\debug.log', 'a', encoding='utf-8'); log_file.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main.py:847","message":"Second button added, setup_admin_export complete","data":{"childCount":len(p.winfo_children()),"timestamp":__import__('time').time()*1000}}, ensure_ascii=False) + '\n'); log_file.close()
        # #endregion

    def export_csv(self, table):
        f = filedialog.asksaveasfilename(defaultextension=".csv")
        if f:
            rows = db.fetch(f"SELECT * FROM {table}")
            with open(f, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
            messagebox.showinfo("Success", "Data Exported")

    # --- ADMIN: ABOUT ---
    def setup_admin_about(self, p):
        """Setup About tab with software information"""
        # Main container with padding
        main_frame = tb.Frame(p, padding=40)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Title
        title_label = tb.Label(main_frame, text="TITANIUM OS", 
                              font=("Orbitron", 28, "bold"), bootstyle="info")
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tb.Label(main_frame, text="Restaurant Management System", 
                                 font=("Orbitron", 14), bootstyle="secondary")
        subtitle_label.pack(pady=(0, 30))
        
        # Version
        version_frame = tb.Frame(main_frame)
        version_frame.pack(pady=20)
        version_label = tb.Label(version_frame, text="Version", 
                                font=("Orbitron", 12, "bold"), bootstyle="info")
        version_label.pack(side=LEFT, padx=(0, 10))
        version_value = tb.Label(version_frame, text="1.0", 
                                font=("Consolas", 14, "bold"), bootstyle="success")
        version_value.pack(side=LEFT)
        
        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=X, pady=30, padx=50)
        
        # Built by section
        built_by_label = tb.Label(main_frame, text="Built By:", 
                                  font=("Orbitron", 14, "bold"), bootstyle="info")
        built_by_label.pack(pady=(0, 20))
        
        # Developers list
        developers_frame = tb.Frame(main_frame)
        developers_frame.pack(pady=10)
        
        developers = [
            ("Abdelrahman ElBatanouny", "232403"),
            ("Omar Sameh Mohamed Ali", "235153"),
            ("Mohamed Raed Atef", "234197"),
            ("Mahmoud Mohamed", "231437")
        ]
        
        for name, student_id in developers:
            dev_frame = tb.Frame(developers_frame)
            dev_frame.pack(pady=8, fill=X, padx=50)
            
            name_label = tb.Label(dev_frame, text=name, 
                                 font=("Consolas", 12), bootstyle="inverse-dark")
            name_label.pack(side=LEFT)
            
            id_label = tb.Label(dev_frame, text=f"ID: {student_id}", 
                              font=("Consolas", 11), bootstyle="secondary")
            id_label.pack(side=RIGHT)
        
        # Separator
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.pack(fill=X, pady=30, padx=50)
        
        # GitHub link section
        github_frame = tb.Frame(main_frame)
        github_frame.pack(pady=20)
        
        github_label = tb.Label(github_frame, text="GitHub Repository:", 
                               font=("Orbitron", 12, "bold"), bootstyle="info")
        github_label.pack(pady=(0, 10))
        
        github_url = "https://github.com/Batanounyy/TitaniumOS"
        
        # Use a function to open the URL
        def open_github(event=None):
            try:
                webbrowser.open_new(github_url)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open browser: {str(e)}\n\nURL: {github_url}")
        
        # Create clickable link using Label with proper binding
        link_container = tb.Frame(github_frame)
        link_container.pack()
        
        github_link = tb.Label(link_container, text=github_url, 
                              font=("Consolas", 11), 
                              foreground="blue",
                              cursor="hand2")
        github_link.pack()
        github_link.bind("<Button-1>", open_github)
        
        # Add hover effect
        def on_enter(e):
            github_link.config(foreground="darkblue")
            github_link.config(font=("Consolas", 11, "underline"))
        def on_leave(e):
            github_link.config(foreground="blue")
            github_link.config(font=("Consolas", 11))
        
        github_link.bind("<Enter>", on_enter)
        github_link.bind("<Leave>", on_leave)
        
        # Also add a button as alternative
        open_btn = tb.Button(link_container, text="[Open in Browser]", 
                            command=open_github,
                            bootstyle="info-outline",
                            width=20)
        open_btn.pack(pady=(10, 0))
        
        # Footer
        footer_label = tb.Label(main_frame, text="Made with ❤️ using Python", 
                               font=("Consolas", 10), bootstyle="secondary")
        footer_label.pack(side=BOTTOM, pady=20)

if __name__ == "__main__":
    app = TitaniumApp()
    app.mainloop()
