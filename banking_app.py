import re
import sys
import sqlite3
import hashlib
import random
import time
from getpass import getpass

conn = sqlite3.connect("customers.db")
cursor = conn.cursor()
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

def generate_unique_account_number():
    """Generate a unique 8-digit account number."""
    while True:
        account_number = str(random.randint(10000000, 99999999))
        cursor.execute("SELECT id FROM customers WHERE account_number = ?", (account_number,))
        if cursor.fetchone() is None:
            return account_number
        
def validate_initial_deposit(deposit, min_balance=2000):
    """Ensure deposit is numeric and meets minimum balance."""
    try:
        deposit = float(deposit)  
        if deposit < 0:
            return False, "Deposit cannot be negative."
        elif deposit < min_balance:
            return False, f"Minimum deposit required is {min_balance} naira."
        return True, deposit  # Return True and the valid deposit amount
    except ValueError:
        return False, "Invalid input. Please enter a numeric value."


def is_valid_password(password):
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,33}$"
    return bool(re.match(pattern, password))

def sign_up():
    print("\n******************** Sign Up ********************\n")

    while True:
        full_name = input("Enter your full name: ").strip().title()
        if len(full_name) < 4 or len(full_name) > 255 or not full_name.replace(" ", "").isalpha():
            print("Invalid full name. Must be at least 4 characters and contain only letters.")
            continue
        break

    while True:
        username =  input("Enter username: ").strip()
        if len(username) < 3 or len(username) > 20 or not username.isalpha():
            print("Invalid username. Must be between 3-20 characters and contain only alphabet.")
            return
        cursor.execute("SELECT id FROM customers WHERE username = ?", (username,))
        if cursor.fetchone():
            print("Username already taken.")
            continue
        break


    while True:
        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password field should not be empty")
            continue

        if not is_valid_password(password):
            print("Password must be 8-33 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
            continue

        confirm_password = getpass("Confirm your password: ").strip()
        if password != confirm_password:
            print("Passwords do not match.")
            continue
        break  
    while True:
        deposit_amount = input("Enter initial deposit amount (min 2000 naira): ").strip()
        is_valid, result = validate_initial_deposit(deposit_amount)

        if not is_valid:
            print(result)  
            continue

        deposit_amount = result  
        break

    account_number = generate_unique_account_number()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("""
        INSERT INTO customers (full_name, username, password, account_number, balance) 
        VALUES (?, ?, ?, ?, ?);
        """, (full_name, username, hashed_password, account_number, deposit_amount))
        conn.commit()
        print(f"Sign-up successful! Your account number is {account_number}.")
        log_in()
    except sqlite3.IntegrityError:
        print("A user with that username already exists.")




def log_in():
    """User login with credential verification."""
    while True:
        print("\n******************** Log In ********************\n")

        username = input("Enter your username: ").strip().lower()
        password = getpass("Enter your password: ").strip()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        user = cursor.execute("""
        SELECT * FROM customers WHERE username = ? AND password = ?;
        """, (username, hashed_password)).fetchone()

        if user is None:
            print("Invalid username or password.")
            return
        else:
            print("Log in Successful!")
            mini_menu(user)


def mini_menu(user):
    print("\n******************** User Dashboard ********************\n")

    full_name = user[1]  
    print(f"Welcome, {full_name}!")
    print("Accessing account features...")

    menu = """
        1. Deposit
        2. Withdraw
        3. Balance Check
        4. Transaction History
        5. Transfer Money
        6. Account Details
        7. Logout
    """

    while True:
        pass
    
        print(menu)
        choice = input("Choose an option: ").strip()

    
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
            print("Logging out... Thank you for using our service! 😊")
            sys.exit()
        else:
            print("Invalid choice. Try again.")
        
def deposit(user):
    """Handles deposit transactions."""
    while True:
        deposit_amount = input("Enter deposit amount: ").strip()
        if not deposit_amount.isnumeric() or float(deposit_amount) <= 0:
            print("Invalid deposit. Enter a positive numeric value.")
            continue

        deposit_amount = float(deposit_amount)
        cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (deposit_amount, user[0]))
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)", (user[0], "Deposit", deposit_amount))
        conn.commit()

        # Retrieve the updated balance from the database
        updated_balance = cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],)).fetchone()[0]

        print(f"Deposit successful! New Balance: {updated_balance}")
        time.sleep(1)
        break




def withdraw(user):
    try:
        amount = float(input("Enter withdrawal amount: "))
        
        if amount <= 0:
            print("Amount must be greater than zero.")
            return
        
        cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],))
        result = cursor.fetchone()
        
        if result is None:
            print("Error: User not found.")
            return
        
        balance = result[0]  
        
        if amount > balance:
            print(f"Insufficient funds. Your current balance is {balance:.2f}.")
            return

        # 
        cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (amount, user[0]))
        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)", (user[0], "Withdrawal", amount))
        conn.commit()

        cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],))
        new_balance = cursor.fetchone()[0]

        print(f"Withdrawal successful! You withdrew {amount:.2f}. Your new balance is {new_balance:.2f}.")

    except ValueError:
        print("Invalid input. Please enter a valid number.")

    

def balance_check(user):
    updated_balance = cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],)).fetchone()[0]
    print(f"Your balance: {updated_balance}")

def transaction_history(user):
    cursor.execute("SELECT transaction_type, amount, timestamp FROM transactions WHERE user_id = ?", (user[0],))
    transactions = cursor.fetchall()
    if not transactions:
        print("No transactions found.")
    else:
        for t in transactions:
            print(f"{t[0]} of {t[1]} on {t[2]}")


def transfer(user):
    recipient_account = input("Enter recipient account number: ").strip()
    
    cursor.execute("SELECT id, balance FROM customers WHERE account_number = ?", (recipient_account,))
    recipient = cursor.fetchone()
    
    if not recipient:
        print("Invalid recipient account number.")
        return
    
    if recipient_account == user[4]:  
        print("You cannot transfer money to yourself.")
        return

    try:
        amount = input("Enter transfer amount: ").strip()
        
        try:
            amount = round(float(amount), 2)
        except ValueError:
            print("Invalid input. Please enter a valid numeric amount.")
            return
        
        if amount <= 0:
            print("Amount must be greater than zero.")
            return
        
        cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],))
        sender_balance = cursor.fetchone()
        
        if sender_balance is None:
            print("Error: User not found.")
            return
        
        sender_balance = sender_balance[0]  

        if amount > sender_balance:
            print(f"Insufficient funds. Your current balance is {sender_balance:.2f}.")
            return

        cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (amount, user[0]))
        cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (amount, recipient[0]))

        cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount, recipient_account) VALUES (?, ?, ?, ?)", (user[0], "Transfer", amount, recipient_account))
        
        conn.commit()

        cursor.execute("SELECT balance FROM customers WHERE id = ?", (user[0],))
        new_sender_balance = cursor.fetchone()[0]

        print(f"Transfer successful! You sent {amount:.2f} to account {recipient_account}. Your new balance is {new_sender_balance:.2f}.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def account_details(user):
    print(f"Full Name: {user[1]}, Username: {user[2]}, Account Number: {user[4]}") 

def main():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        balance REAL DEFAULT 0
        
    )
    """)

    
    menu = """
    1. Sign Up.
    2. Log In.
    3. Quit.
    """


    while True:
        print(menu)
        choice = input("Choose an option from the menu above: ").strip()

        if choice == "3":
            print("Exiting the program...")
            conn.close()
            break

        if choice == "1":
            sign_up()
        elif choice == "2":
            log_in()
        else:
            print("Invalid choice, please try again.")



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.close()

