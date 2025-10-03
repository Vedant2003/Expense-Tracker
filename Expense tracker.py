import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT UNIQUE,
    dob TEXT  -- Date of Birth column added
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

def register_user():
    u = username_entry.get().strip()
    p = password_entry.get().strip()
    email = email_entry.get().strip()
    dob = dob_entry.get_date().strftime('%Y-%m-%d')  # Get DOB from calendar
    try:
        cursor.execute("INSERT INTO users (username, password, email, dob) VALUES (?, ?, ?, ?)", (u, p, email, dob))
        conn.commit()
        messagebox.showinfo("Success", "Registration successful.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Username or email already exists.")

def login_user():
    global current_user_id
    u = username_entry.get().strip()
    p = password_entry.get().strip()
    cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (u, p))
    row = cursor.fetchone()
    if row:
        current_user_id = row[0]
        messagebox.showinfo("Welcome", f"Logged in as {u}")
        login_frame.pack_forget()
        main_frame.pack(fill='both', expand=True)
        refresh_categories()
        refresh_expenses()
    else:
        messagebox.showerror("Error", "Invalid credentials.")

def toggle_password():
    if password_entry.cget('show') == '*':
        password_entry.config(show='')
    else:
        password_entry.config(show='*')

def forgot_password():
    u = username_entry.get().strip()
    dob = dob_entry.get_date().strftime('%Y-%m-%d')  # Get DOB from calendar
    cursor.execute("SELECT password FROM users WHERE username=? AND dob=?", (u, dob))
    row = cursor.fetchone()
    if row:
        password = row[0]
        # Show the password on the screen
        messagebox.showinfo("Your Password", f"Your password is: {password}")
    else:
        messagebox.showerror("Error", "Invalid username or Date of Birth.")

def add_category():
    cat = cat_entry.get().strip()
    if not cat: return
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        conn.commit()
        messagebox.showinfo("Added", "Category added.")
        refresh_categories()
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Category already exists.")

def refresh_categories():
    cat_combo['values'] = [c[0] for c in cursor.execute("SELECT name FROM categories").fetchall()]

def suggest_category():
    desc = desc_entry.get().strip().lower()
    if "food" in desc or "restaurant" in desc:
        cat_combo.set("Food")
    elif "travel" in desc or "bus" in desc:
        cat_combo.set("Transport")
    elif "movie" in desc or "netflix" in desc:
        cat_combo.set("Entertainment")

def add_expense():
    if current_user_id is None: return
    date = date_entry.get_date().strftime("%Y-%m-%d")
    cat = cat_combo.get()
    if not cat:
        messagebox.showerror("Error", "Choose category")
        return
    try:
        amount = float(amount_entry.get().strip())
    except:
        messagebox.showerror("Error", "Amount must be number.")
        return
    desc = desc_entry.get().strip()
    cursor.execute("INSERT INTO expenses (user_id, date, category, amount, description) VALUES (?,?,?,?,?)",
                   (current_user_id, date, cat, amount, desc))
    conn.commit()
    messagebox.showinfo("Added", "Expense added.")
    refresh_expenses()

def refresh_expenses():
    for row in exp_tree.get_children():
        exp_tree.delete(row)
    for row in cursor.execute("SELECT date, category, amount, description FROM expenses WHERE user_id=?",
                              (current_user_id,)).fetchall():
        exp_tree.insert("", tk.END, values=row)
def show_total_spent():
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id=?", (current_user_id,))
    total = cursor.fetchone()[0]
    total = total if total else 0  # Handle None if no expenses
    messagebox.showinfo("Total Spent", f"You have spent ₹{total:.2f} in total.")


def monthly_report():
    df = pd.read_sql_query("SELECT date, category, amount FROM expenses WHERE user_id=?", conn, params=(current_user_id,))
    if df.empty:
        messagebox.showinfo("No Data", "No expenses to plot.")
        return

    df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
    report = df.groupby(['month', 'category'])['amount'].sum().unstack().fillna(0)

    report.plot(kind='bar', stacked=True)
    plt.title('Monthly Spending by Category')
    plt.ylabel('Amount')
    plt.xlabel('Month')
    plt.tight_layout()
    plt.show()

    report_file = "monthly_report.csv"
    report.to_csv(report_file)
    messagebox.showinfo("Report Ready", f"Monthly report generated as {report_file}")

def category_report():
    df = pd.read_sql_query("SELECT category, amount FROM expenses WHERE user_id=?", conn, params=(current_user_id,))
    if df.empty:
        messagebox.showinfo("No Data", "No expenses to plot.")
        return
    report = df.groupby('category')['amount'].sum()
    report.plot(kind='pie', autopct='%1.1f%%')
    plt.title('Spending by Category')
    plt.ylabel('')
    plt.tight_layout()
    plt.show()

def filter_expenses():
    keyword = search_entry.get().strip().lower()
    start = start_date_entry.get_date().strftime('%Y-%m-%d')
    end = end_date_entry.get_date().strftime('%Y-%m-%d')

    query = "SELECT date, category, amount, description FROM expenses WHERE user_id=?"
    params = [current_user_id]

    if start and end:
        query += " AND date BETWEEN ? AND ?"
        params += [start, end]

    rows = cursor.execute(query, params).fetchall()
    exp_tree.delete(*exp_tree.get_children())
    for row in rows:
        if keyword in row[1].lower() or keyword in row[3].lower():
            exp_tree.insert("", tk.END, values=row)
def export_csv():
    df = pd.read_sql_query("SELECT date, category, amount, description FROM expenses WHERE user_id=?", conn, params=(current_user_id,))
    if df.empty:
        messagebox.showinfo("No Data", "No expenses to export.")
        return
    df.to_csv("my_expenses.csv", index=False)
    messagebox.showinfo("Exported", "Expenses exported to my_expenses.csv")
def logout_user():
    global current_user_id
    current_user_id = None
    main_frame.pack_forget()
    login_frame.pack(fill='both', expand=True)
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)

root = tk.Tk()
root.title("Expense Tracker Pro")

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill='both', expand=True)

tk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky='e')
username_entry = tk.Entry(login_frame)
username_entry.grid(row=0, column=1)

tk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky='e')
password_entry = tk.Entry(login_frame, show="*")
password_entry.grid(row=1, column=1)

tk.Label(login_frame, text="Email:").grid(row=2, column=0, sticky='e')
email_entry = tk.Entry(login_frame)
email_entry.grid(row=2, column=1)

tk.Label(login_frame, text="Date of Birth:").grid(row=3, column=0, sticky='e')
dob_entry = DateEntry(login_frame)
dob_entry.grid(row=3, column=1)

tk.Button(login_frame, text="Show/Hide", command=toggle_password).grid(row=1, column=2)
tk.Button(login_frame, text="Login", command=login_user).grid(row=4, column=0, pady=5)
tk.Button(login_frame, text="Register", command=register_user).grid(row=4, column=1, pady=5)
tk.Button(login_frame, text="Forgot Password", command=forgot_password).grid(row=5, column=0, pady=5)

main_frame = tk.Frame(root, padx=10, pady=10)

tk.Label(main_frame, text="Add Category:").grid(row=0, column=0, sticky='e')
cat_entry = tk.Entry(main_frame)
cat_entry.grid(row=0, column=1)
tk.Button(main_frame, text="Add", command=add_category).grid(row=0, column=2)

tk.Label(main_frame, text="Date:").grid(row=1, column=0, sticky='e')
date_entry = DateEntry(main_frame)
date_entry.grid(row=1, column=1)

tk.Label(main_frame, text="Category:").grid(row=2, column=0, sticky='e')
cat_combo = ttk.Combobox(main_frame, state='readonly')
cat_combo.grid(row=2, column=1)

tk.Label(main_frame, text="Amount:").grid(row=3, column=0, sticky='e')
amount_entry = tk.Entry(main_frame)
amount_entry.grid(row=3, column=1)

tk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky='e')
desc_entry = tk.Entry(main_frame)
desc_entry.grid(row=4, column=1)

tk.Button(main_frame, text="Suggest Category", command=suggest_category).grid(row=4, column=2)

tk.Button(main_frame, text="Add Expense", command=add_expense).grid(row=5, column=1, pady=5)

exp_tree = ttk.Treeview(main_frame, columns=("Date", "Category", "Amount", "Description"), show='headings')
for col in ("Date", "Category", "Amount", "Description"):
    exp_tree.heading(col, text=col)
exp_tree.grid(row=6, column=0, columnspan=3, pady=10)
tk.Button(main_frame, text="Show Total Spent", command=show_total_spent).grid(row=12, column=0, pady=5)
tk.Button(main_frame, text="Monthly Report", command=monthly_report).grid(row=7, column=1, pady=5)
tk.Button(main_frame, text="Category Report", command=category_report).grid(row=7, column=2, pady=5)

tk.Label(main_frame, text="Search:").grid(row=8, column=0)
search_entry = tk.Entry(main_frame)
search_entry.grid(row=8, column=1)

tk.Label(main_frame, text="Start Date:").grid(row=9, column=0)
start_date_entry = DateEntry(main_frame)
start_date_entry.grid(row=9, column=1)

tk.Label(main_frame, text="End Date:").grid(row=10, column=0)
end_date_entry = DateEntry(main_frame)
end_date_entry.grid(row=10, column=1)

tk.Button(main_frame, text="Filter", command=filter_expenses).grid(row=11, column=1, pady=5)
tk.Button(main_frame, text="Export to CSV", command=export_csv).grid(row=12, column=1, pady=5)
tk.Button(main_frame, text="Logout", command=logout_user).grid(row=12, column=2, pady=5)
root.mainloop()
