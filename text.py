import sqlite3
import hashlib
import random
import time
from getpass import getpass

# Database Connection
conn = sqlite3.connect("banking.db")
cursor = conn.cursor()

# Create Tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    account_number TEXT NOT NULL UNIQUE,
    balance REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    recipient_account TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES customers (id)
)
''')
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_account_number():
    while True:
        account_number = str(random.randint(10000000, 99999999))
        cursor.execute("SELECT id FROM customers WHERE account_number = ?", (account_number,))
        if cursor.fetchone() is None:
            return account_number

def sign_up():
    print("\n********** SIGN UP **********\n")
    full_name = input("Enter full name: ").strip().title()
    if len(full_name) < 4 or not full_name.replace(" ", "").isalpha():
        print("Invalid full name. Must be at least 4 characters and contain only letters.")
        return
    username = input("Enter username: ").strip()
    if len(username) < 3 or len(username) > 20:
        print("Invalid username. Must be between 3-20 characters.")
        return
    cursor.execute("SELECT id FROM customers WHERE username = ?", (username,))
    if cursor.fetchone():
        print("Username already taken.")
        return
    password = getpass("Enter password: ")
    confirm_password = getpass("Confirm password: ")
    if password != confirm_password:
        print("Passwords do not match.")
        return
    if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password) or not any(char in "!@#$%^&*()" for char in password):
        print("Password must be at least 8 characters long, include a number, an uppercase letter, and a special character.")
        return
    try:
        initial_deposit = float(input("Enter initial deposit (Min: 2000): "))
        if initial_deposit < 2000:
            print("Minimum deposit is 2000.")
            return
    except ValueError:
        print("Invalid amount.")
        return
    account_number = generate_account_number()
    cursor.execute("INSERT INTO customers (full_name, username, password, account_number, balance) VALUES (?, ?, ?, ?, ?)",
                   (full_name, username, hash_password(password), account_number, initial_deposit))
    conn.commit()
    print(f"Account created successfully! Your account number is {account_number}")
    log_in()

def log_in():
    print("\n********** LOG IN **********\n")
    username = input("Enter username: ").strip()
    password = getpass("Enter password: ")
    cursor.execute("SELECT * FROM customers WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = cursor.fetchone()
    if user:
        print("Login successful! Welcome,", user[1])
        mini_menu(user)
    else:
        print("Invalid credentials.")

def mini_menu(user):
    while True:
        print("""
        1. Deposit
        2. Withdraw
        3. Balance Check
        4. Transaction History
        5. Transfer Money
        6. Account Details
        7. Logout
        """)
        choice = input("Choose an option: ")
        if choice == "1":
            deposit(user)
        elif choice == "2":
            withdraw(user)
        elif choice == "3":
            balance_check(user)
        elif choice == "4":
            transaction_history(user)
        elif choice == "5":
            transfer(user)
        elif choice == "6":
            account_details(user)
        elif choice == "7":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Try again.")

def deposit(user):
    try:
        amount = float(input("Enter deposit amount: "))
        if amount <= 0:
            print("Invalid amount.")
            return
        cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (amount, user[0]))
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)", (user[0], "Deposit", amount))
        conn.commit()
        print("Deposit successful.")
    except ValueError:
        print("Invalid input.")

def withdraw(user):
    try:
        amount = float(input("Enter withdrawal amount: "))
        if amount <= 0 or amount > user[5]:
            print("Invalid or insufficient funds.")
            return
        cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (amount, user[0]))
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)", (user[0], "Withdrawal", amount))
        conn.commit()
        print("Withdrawal successful.")
    except ValueError:
        print("Invalid input.")

def balance_check(user):
    print(f"Your balance: {user[5]}")

def transaction_history(user):
    cursor.execute("SELECT transaction_type, amount, timestamp FROM transactions WHERE user_id = ?", (user[0],))
    transactions = cursor.fetchall()
    if not transactions:
        print("No transactions found.")
    else:
        for t in transactions:
            print(f"{t[0]} of {t[1]} on {t[2]}")

def transfer(user):
    recipient_account = input("Enter recipient account number: ")
    cursor.execute("SELECT id, balance FROM customers WHERE account_number = ?", (recipient_account,))
    recipient = cursor.fetchone()
    if not recipient or recipient_account == user[4]:
        print("Invalid recipient.")
        return
    try:
        amount = float(input("Enter transfer amount: "))
        if amount <= 0 or amount > user[5]:
            print("Invalid or insufficient funds.")
            return
        cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (amount, user[0]))
        cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (amount, recipient[0]))
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount, recipient_account) VALUES (?, ?, ?, ?)", (user[0], "Transfer", amount, recipient_account))
        conn.commit()
        print("Transfer successful.")
    except ValueError:
        print("Invalid input.")

def account_details(user):
    print(f"Full Name: {user[1]}, Username: {user[2]}, Account Number: {user[4]}")

sign_up()