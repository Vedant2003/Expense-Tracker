import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk

# ---------- DB Setup ----------
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')
conn.commit()

current_user_id = None

# ---------- Backend Functions ----------
def register_user():
    u = username_entry.get().strip()
    p = password_entry.get().strip()
    try:
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        messagebox.showinfo("Success","Registration successful.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error","Username already exists.")

def login_user():
    global current_user_id
    u = username_entry.get().strip()
    p = password_entry.get().strip()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?",(u,p))
    row = cursor.fetchone()
    if row:
        current_user_id=row[0]
        messagebox.showinfo("Welcome",f"Logged in as {u}")
        login_frame.pack_forget()
        main_frame.pack(fill='both',expand=True)
        refresh_categories()
        refresh_expenses()
    else:
        messagebox.showerror("Error","Invalid credentials.")

def add_category():
    cat = cat_entry.get().strip()
    if not cat: return
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)",(cat,))
        conn.commit()
        messagebox.showinfo("Added","Category added.")
        refresh_categories()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error","Category already exists.")

def refresh_categories():
    cat_combo['values'] = [c[0] for c in cursor.execute("SELECT name FROM categories").fetchall()]

def add_expense():
    if current_user_id is None: return
    date = date_entry.get().strip() or datetime.now().strftime("%Y-%m-%d")
    cat = cat_combo.get()
    if not cat:
        messagebox.showerror("Error","Choose category")
        return
    try:
        amount = float(amount_entry.get().strip())
    except:
        messagebox.showerror("Error","Amount must be number.")
        return
    desc = desc_entry.get().strip()
    cursor.execute("INSERT INTO expenses (user_id,date,category,amount,description) VALUES (?,?,?,?,?)",
                   (current_user_id,date,cat,amount,desc))
    conn.commit()
    messagebox.showinfo("Added","Expense added.")
    refresh_expenses()

def refresh_expenses():
    for row in exp_tree.get_children():
        exp_tree.delete(row)
    for row in cursor.execute("SELECT date,category,amount,description FROM expenses WHERE user_id=?",
                              (current_user_id,)).fetchall():
        exp_tree.insert("",tk.END,values=row)

def monthly_report():
    df = pd.read_sql_query("SELECT date, amount FROM expenses WHERE user_id=?",conn,params=(current_user_id,))
    if df.empty:
        messagebox.showinfo("No Data","No expenses to plot.")
        return
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    report = df.groupby('month')['amount'].sum()
    report.plot(kind='bar')
    plt.title('Monthly Spending')
    plt.ylabel('Amount')
    plt.xlabel('Month')
    plt.tight_layout()
    plt.show()

# ---------- GUI ----------
root = tk.Tk()
root.title("Expense Tracker Pro")

# Login/Register frame
login_frame = tk.Frame(root,padx=10,pady=10)
login_frame.pack(fill='both',expand=True)

tk.Label(login_frame,text="Username:").grid(row=0,column=0,sticky='e')
username_entry=tk.Entry(login_frame)
username_entry.grid(row=0,column=1)

tk.Label(login_frame,text="Password:").grid(row=1,column=0,sticky='e')
password_entry=tk.Entry(login_frame,show="*")
password_entry.grid(row=1,column=1)

tk.Button(login_frame,text="Login",command=login_user).grid(row=2,column=0,pady=5)
tk.Button(login_frame,text="Register",command=register_user).grid(row=2,column=1,pady=5)

# Main frame
main_frame = tk.Frame(root,padx=10,pady=10)

# Category section
tk.Label(main_frame,text="Add Category:").grid(row=0,column=0,sticky='e')
cat_entry=tk.Entry(main_frame)
cat_entry.grid(row=0,column=1)
tk.Button(main_frame,text="Add",command=add_category).grid(row=0,column=2)

# Expense section
tk.Label(main_frame,text="Date (YYYY-MM-DD):").grid(row=1,column=0,sticky='e')
date_entry=tk.Entry(main_frame)
date_entry.grid(row=1,column=1)

tk.Label(main_frame,text="Category:").grid(row=2,column=0,sticky='e')
cat_combo=ttk.Combobox(main_frame,state='readonly')
cat_combo.grid(row=2,column=1)

tk.Label(main_frame,text="Amount:").grid(row=3,column=0,sticky='e')
amount_entry=tk.Entry(main_frame)
amount_entry.grid(row=3,column=1)

tk.Label(main_frame,text="Description:").grid(row=4,column=0,sticky='e')
desc_entry=tk.Entry(main_frame)
desc_entry.grid(row=4,column=1)

tk.Button(main_frame,text="Add Expense",command=add_expense).grid(row=5,column=1,pady=5)

# Expenses table
exp_tree=ttk.Treeview(main_frame,columns=("Date","Category","Amount","Description"),show='headings')
for col in ("Date","Category","Amount","Description"):
    exp_tree.heading(col,text=col)
exp_tree.grid(row=6,column=0,columnspan=3,pady=10)

tk.Button(main_frame,text="Monthly Report",command=monthly_report).grid(row=7,column=1,pady=5)

root.mainloop()

conn.close()