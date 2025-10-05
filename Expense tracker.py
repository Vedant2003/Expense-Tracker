import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3, hashlib
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- Database ----------------
conn = sqlite3.connect("expense_tracker.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    dob TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    user_id TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
)""")
conn.commit()

current_user = None

# ---------------- Utility ----------------
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def switch_frame(new_frame):
    for widget in root.winfo_children():
        widget.destroy()
    new_frame()

# ---------------- Login/Register/Forgot ----------------
def show_login():
    def login_user():
        global current_user
        uname = username.get()
        pwd = hash_password(password.get())
        row = cursor.execute("SELECT username FROM users WHERE username=? AND password=?",
                             (uname, pwd)).fetchone()
        if row:
            current_user = row[0]
            messagebox.showinfo("Success", "Login Successful")
            switch_frame(show_main)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    frame = tk.Frame(root)
    frame.pack(pady=50)

    tk.Label(frame, text="Login", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(frame, text="Username").grid(row=1, column=0, pady=5)
    tk.Label(frame, text="Password").grid(row=2, column=0, pady=5)

    username = tk.Entry(frame)
    password = tk.Entry(frame, show="*")
    username.grid(row=1, column=1, pady=5)
    password.grid(row=2, column=1, pady=5)

    tk.Button(frame, text="Login", command=login_user).grid(row=3, column=0, columnspan=2, pady=10)
    tk.Button(frame, text="Register", command=lambda: switch_frame(show_register)).grid(row=4, column=0, pady=5)
    tk.Button(frame, text="Forgot Password", command=lambda: switch_frame(show_forgot_password)).grid(row=4, column=1, pady=5)

def show_register():
    def register_user():
        uname = username.get()
        pwd = hash_password(password.get())
        dob_val = dob.get()
        if not uname or not pwd or not dob_val:
            messagebox.showerror("Error", "All fields are required")
            return
        try:
            cursor.execute("INSERT INTO users (username,password,dob) VALUES (?,?,?)",
                           (uname, pwd, dob_val))
            conn.commit()
            messagebox.showinfo("Success", "Registration Successful")
            switch_frame(show_login)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")

    frame = tk.Frame(root)
    frame.pack(pady=50)

    tk.Label(frame, text="Register", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(frame, text="Username").grid(row=1, column=0, pady=5)
    tk.Label(frame, text="Password").grid(row=2, column=0, pady=5)
    tk.Label(frame, text="Date of Birth").grid(row=3, column=0, pady=5)

    username = tk.Entry(frame)
    password = tk.Entry(frame, show="*")
    dob = DateEntry(frame, date_pattern="yyyy-mm-dd")

    username.grid(row=1, column=1, pady=5)
    password.grid(row=2, column=1, pady=5)
    dob.grid(row=3, column=1, pady=5)

    tk.Button(frame, text="Register", command=register_user).grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(frame, text="Back", command=lambda: switch_frame(show_login)).grid(row=5, column=0, columnspan=2, pady=5)

def show_forgot_password():
    def reset_password():
        uname = username.get()
        dob_val = dob.get()
        new_pwd = hash_password(password.get())
        row = cursor.execute("SELECT username FROM users WHERE username=? AND dob=?", (uname, dob_val)).fetchone()
        if row:
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pwd, uname))
            conn.commit()
            messagebox.showinfo("Success", "Password Reset Successful")
            switch_frame(show_login)
        else:
            messagebox.showerror("Error", "Username and DOB do not match")

    frame = tk.Frame(root)
    frame.pack(pady=50)

    tk.Label(frame, text="Forgot Password", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(frame, text="Username").grid(row=1, column=0, pady=5)
    tk.Label(frame, text="Date of Birth").grid(row=2, column=0, pady=5)
    tk.Label(frame, text="New Password").grid(row=3, column=0, pady=5)

    username = tk.Entry(frame)
    dob = DateEntry(frame, date_pattern="yyyy-mm-dd")
    password = tk.Entry(frame, show="*")

    username.grid(row=1, column=1, pady=5)
    dob.grid(row=2, column=1, pady=5)
    password.grid(row=3, column=1, pady=5)

    tk.Button(frame, text="Reset", command=reset_password).grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(frame, text="Back", command=lambda: switch_frame(show_login)).grid(row=5, column=0, columnspan=2, pady=5)

# ---------------- Main Expense Tracker ----------------
def show_main():
    global cat_entry, cat_combo, date_entry, amount_entry, desc_entry
    global exp_tree, search_entry, start_date_entry, end_date_entry

    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Expense Tracker Pro", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

    tk.Label(frame, text="Add Category:").grid(row=1, column=0, sticky='e')
    cat_entry = tk.Entry(frame)
    cat_entry.grid(row=1, column=1)
    tk.Button(frame, text="Add", command=add_category).grid(row=1, column=2)

    tk.Label(frame, text="Date:").grid(row=2, column=0, sticky='e')
    date_entry = DateEntry(frame)
    date_entry.grid(row=2, column=1)

    tk.Label(frame, text="Category:").grid(row=3, column=0, sticky='e')
    cat_combo = ttk.Combobox(frame, state='readonly')
    cat_combo.grid(row=3, column=1)

    tk.Label(frame, text="Amount:").grid(row=4, column=0, sticky='e')
    amount_entry = tk.Entry(frame)
    amount_entry.grid(row=4, column=1)

    tk.Label(frame, text="Description:").grid(row=5, column=0, sticky='e')
    desc_entry = tk.Entry(frame)
    desc_entry.grid(row=5, column=1)
    tk.Button(frame, text="Suggest Category", command=suggest_category).grid(row=5, column=2)

    tk.Button(frame, text="Add Expense", command=add_expense).grid(row=6, column=1, pady=5)

    exp_tree = ttk.Treeview(frame, columns=("Date", "Category", "Amount", "Description"), show='headings')
    for col in ("Date", "Category", "Amount", "Description"):
        exp_tree.heading(col, text=col)
    exp_tree.grid(row=7, column=0, columnspan=3, pady=10)

    tk.Button(frame, text="Show Total Spent", command=show_total_spent).grid(row=8, column=0, pady=5)
    tk.Button(frame, text="Monthly Report", command=lambda: show_chart_report("monthly")).grid(row=8, column=1, pady=5)
    tk.Button(frame, text="Category Report", command=lambda: show_chart_report("category")).grid(row=8, column=2, pady=5)

    tk.Label(frame, text="Search:").grid(row=9, column=0)
    search_entry = tk.Entry(frame)
    search_entry.grid(row=9, column=1)

    tk.Label(frame, text="Start Date:").grid(row=10, column=0)
    start_date_entry = DateEntry(frame)
    start_date_entry.grid(row=10, column=1)

    tk.Label(frame, text="End Date:").grid(row=11, column=0)
    end_date_entry = DateEntry(frame)
    end_date_entry.grid(row=11, column=1)

    tk.Button(frame, text="Filter", command=filter_expenses).grid(row=12, column=1, pady=5)
    tk.Button(frame, text="Export to CSV", command=export_csv).grid(row=13, column=1, pady=5)
    tk.Button(frame, text="Logout", command=lambda: switch_frame(show_login)).grid(row=13, column=2, pady=5)

    refresh_categories()
    refresh_expenses()

# ---------------- Expense Functions ----------------
def add_category():
    cat = cat_entry.get().strip()
    if not cat: return
    cursor.execute("INSERT INTO categories (name,user_id) VALUES (?,?)", (cat,current_user))
    conn.commit()
    refresh_categories()

def refresh_categories():
    cat_combo['values'] = [c[0] for c in cursor.execute("SELECT name FROM categories WHERE user_id=?", (current_user,)).fetchall()]

def suggest_category():
    desc = desc_entry.get().lower()
    if "food" in desc: cat_combo.set("Food")
    elif "travel" in desc: cat_combo.set("Transport")
    elif "movie" in desc: cat_combo.set("Entertainment")

def add_expense():
    date = date_entry.get_date().strftime("%Y-%m-%d")
    cat = cat_combo.get()
    amt = amount_entry.get()
    try: amt = float(amt)
    except: return messagebox.showerror("Error","Invalid amount")
    desc = desc_entry.get()
    cursor.execute("INSERT INTO expenses (user_id,date,category,amount,description) VALUES (?,?,?,?,?)",
                   (current_user,date,cat,amt,desc))
    conn.commit()
    refresh_expenses()

def refresh_expenses():
    for row in exp_tree.get_children():
        exp_tree.delete(row)
    for row in cursor.execute("SELECT date,category,amount,description FROM expenses WHERE user_id=?",(current_user,)).fetchall():
        exp_tree.insert("",tk.END,values=row)

def show_total_spent():
    total = cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?",(current_user,)).fetchone()[0]
    total = total if total else 0
    messagebox.showinfo("Total Spent", f"₹{total:.2f}")

# ---------------- Chart Reports in new window ----------------
def show_chart_report(report_type):
    df = pd.read_sql_query("SELECT date,category,amount FROM expenses WHERE user_id=?", conn, params=(current_user,))
    if df.empty:
        messagebox.showinfo("No Data", "No expenses yet")
        return

    win = tk.Toplevel(root)
    win.title(f"{report_type.capitalize()} Report")
    win.geometry("800x600")

    canvas = tk.Canvas(win)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    if report_type=="monthly":
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        report = df.groupby(['month','category'])['amount'].sum().unstack().fillna(0)
        fig, ax = plt.subplots(figsize=(8,4))
        report.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title("Monthly Spending by Category")
        ax.set_ylabel("Amount")
        ax.set_xlabel("Month")
    else:
        report = df.groupby('category')['amount'].sum()
        fig, ax = plt.subplots(figsize=(6,4))
        report.plot(kind='pie', autopct='%1.1f%%', ax=ax)
        ax.set_ylabel('')
        ax.set_title("Spending by Category")

    fig.tight_layout()
    FigureCanvasTkAgg(fig, master=scroll_frame).get_tk_widget().pack()

def filter_expenses():
    key=search_entry.get().lower()
    start=start_date_entry.get_date().strftime("%Y-%m-%d")
    end=end_date_entry.get_date().strftime("%Y-%m-%d")
    rows=cursor.execute("SELECT date,category,amount,description FROM expenses WHERE user_id=? AND date BETWEEN ? AND ?",(current_user,start,end)).fetchall()
    exp_tree.delete(*exp_tree.get_children())
    for row in rows:
        if key in row[1].lower() or key in row[3].lower():
            exp_tree.insert("",tk.END,values=row)

def export_csv():
    df = pd.read_sql_query("SELECT date,category,amount,description FROM expenses WHERE user_id=?", conn, params=(current_user,))
    if df.empty: return messagebox.showinfo("No Data","No expenses yet")
    df.to_csv("my_expenses.csv",index=False)
    messagebox.showinfo("Exported","Saved as my_expenses.csv")

# ---------------- Run ----------------
root = tk.Tk()
root.title("Expense Tracker Pro")
root.geometry("800x700")
show_login()
root.mainloop()
