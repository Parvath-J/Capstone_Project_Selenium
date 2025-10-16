# filename: models.py

# -----------------------------
# Importing necessary modules
# -----------------------------
# mysql.connector.IntegrityError - handles unique constraint errors (like duplicate username)
# hashlib - used for hashing passwords securely
# datetime - to record timestamps
# DB - custom database class (from database.py)
from mysql.connector import IntegrityError
import hashlib
from datetime import datetime
from database import DB


# ====================================================================================================
# CLASS: User
# ----------------------------------------------------------------------------------------------------
# Demonstrates:
#   ✅ Encapsulation (class structure, instance variables)
#   ✅ Static method (hash_password)
#   ✅ Class methods (register, login, etc.)
#   ✅ Abstraction (user doesn’t see how DB operations are done)
# ====================================================================================================
class User:
    """Represents a user/customer of the bank."""

    def __init__(self, db: DB, id, username, fullname, phone_number):
        # Public attributes
        self.db = db
        self.id = id
        self.username = username
        self.fullname = fullname
        self.phone_number = phone_number

    # -----------------------------
    # Static Method: hash_password
    # -----------------------------
    # Used to hash sensitive information (like password/UPI pin)
    # Does not depend on any instance or class variables.
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # -----------------------------
    # Class Method: register
    # -----------------------------
    # Used to register a new user.
    # Demonstrates Abstraction — hides DB insertion logic.
    @classmethod
    def register(cls, db: DB, username, fullname, phone, pan, password, upi_pin):
        pw_hash = cls.hash_password(password)
        pin_hash = cls.hash_password(upi_pin)
        now = datetime.utcnow().isoformat()
        try:
            # Inserting a new record into the database
            last_id = db.execute(
                "INSERT INTO users (username, fullname, phone_number, pan_number, password_hash, upi_pin_hash, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, fullname, phone, pan, pw_hash, pin_hash, now)
            )

            # Default account created for each user (shows code reusability and abstraction)
            create_account_for_user(db, last_id, "Savings", 500.0, 0.04)
            return True
        except IntegrityError:
            # Exception handling if username already exists
            return False

    # -----------------------------
    # Class Method: login
    # -----------------------------
    # Demonstrates Abstraction and Class-level method use.
    @classmethod
    def login(cls, db: DB, username, password):
        pw_hash = cls.hash_password(password)
        rows = db.query("SELECT * FROM users WHERE username = %s AND password_hash = %s", (username, pw_hash))
        if rows:
            row = rows[0]
            return cls(db, row["id"], row["username"], row["fullname"], row["phone_number"])
        return None

    # -----------------------------
    # Other Utility Class Methods
    # -----------------------------
    @classmethod
    def get_user_by_phone(cls, db: DB, phone_number):
        rows = db.query("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
        if rows:
            row = rows[0]
            return cls(db, row["id"], row["username"], row["fullname"], row["phone_number"])
        return None

    @classmethod
    def verify_upi_pin(cls, db: DB, phone_number, pin):
        pin_hash = cls.hash_password(pin)
        rows = db.query("SELECT * FROM users WHERE phone_number = %s AND upi_pin_hash = %s", (phone_number, pin_hash))
        if rows:
            return User.get_user_by_phone(db, phone_number)
        return None

    @classmethod
    def verify_phone_for_reset(cls, db: DB, username, phone_number):
        return bool(db.query("SELECT * FROM users WHERE username = %s AND phone_number = %s", (username, phone_number)))

    @classmethod
    def update_password(cls, db: DB, username, new_password):
        new_pw_hash = cls.hash_password(new_password)
        db.execute("UPDATE users SET password_hash = %s WHERE username = %s", (new_pw_hash, username))

    # -----------------------------
    # Instance Methods
    # -----------------------------
    def get_accounts(self):
        # Returns all accounts belonging to this user
        return [Account.from_row(self.db, r) for r in self.db.query("SELECT * FROM accounts WHERE user_id = %s", (self.id,))]

    def get_primary_account(self):
        # Returns first account (primary)
        accounts = self.get_accounts()
        return accounts[0] if accounts else None


# ====================================================================================================
# CLASS: BankAccount
# ----------------------------------------------------------------------------------------------------
# Demonstrates:
#   ✅ Encapsulation (balance variable, private attribute)
#   ✅ Abstraction (database operations hidden inside methods)
#   ✅ Methods for Deposit/Withdraw - modifying internal state
#   ✅ Protected and Private members
# ====================================================================================================
class BankAccount:
    def __init__(self, db: DB, id, user_id, account_number, account_type, balance=0.0, interest_rate=0.0):
        # Public attributes
        self.db = db
        self.id = id
        self.user_id = user_id
        self.account_number = account_number
        self.account_type = account_type
        self.balance = float(balance)
        self.interest_rate = float(interest_rate)

        # Private member (Encapsulation)
        # Private variable is declared using __ (double underscore)
        # It cannot be accessed directly outside the class
        self.__secure_balance = self.balance

    # -----------------------------
    # Getter and Setter Methods
    # -----------------------------
    # Used to control access to private members
    def get_secure_balance(self):
        return self.__secure_balance

    def set_secure_balance(self, amount):
        if amount >= 0:
            self.__secure_balance = amount
        else:
            raise ValueError("Balance cannot be negative")

    # -----------------------------
    # Class Method: from_row
    # -----------------------------
    # Converts a DB record to an object instance
    @classmethod
    def from_row(cls, db, row):
        return cls(db, row["id"], row["user_id"], row["account_number"], row["account_type"], row["balance"], row["interest_rate"])

    # -----------------------------
    # Deposit Method
    # -----------------------------
    # Demonstrates Abstraction (hides DB query details)
    def deposit(self, amount, note=None):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount

        # If DB connection exists, update; else skip (for demo)
        if self.db is not None:
            self.db.execute("UPDATE accounts SET balance = %s WHERE id = %s", (self.balance, self.id))
            self._record_txn("DEPOSIT", amount, note)
        else:
            print(f"[Demo Mode] Deposited {amount}. (No DB update performed.)")

    # -----------------------------
    # Withdraw Method
    # -----------------------------
    def withdraw(self, amount, note=None):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount

        if self.db is not None:
            self.db.execute("UPDATE accounts SET balance = %s WHERE id = %s", (self.balance, self.id))
            self._record_txn("WITHDRAW", amount, note)
        else:
            print(f"[Demo Mode] Withdrew {amount}. (No DB update performed.)")

    # -----------------------------
    # Protected Method
    # -----------------------------
    # Prefix with single underscore `_record_txn` → indicates it's for internal use
    def _record_txn(self, ttype, amount, note=None, related_account=None):
        now = datetime.utcnow().isoformat()
        if self.db is not None:
            self.db.execute(
                "INSERT INTO transactions (account_id, type, amount, timestamp, note, related_account) VALUES (%s, %s, %s, %s, %s, %s)",
                (self.id, ttype, amount, now, note, related_account))
        else:
            print(f"[Demo Mode] Transaction recorded: {ttype} of {amount}")

    # -----------------------------
    # Retrieve Transactions
    # -----------------------------
    def get_transactions(self, limit=100):
        return self.db.query("SELECT * FROM transactions WHERE account_id = %s ORDER BY timestamp DESC LIMIT %s", (self.id, limit))


# ====================================================================================================
# CLASS: SavingsAccount
# ----------------------------------------------------------------------------------------------------
# Demonstrates:
#   ✅ Inheritance (inherits from BankAccount)
#   ✅ Polymorphism (overrides apply_interest behavior)
# ====================================================================================================
class SavingsAccount(BankAccount):
    def apply_interest(self):
        if self.interest_rate <= 0:
            return 0.0
        interest = self.balance * self.interest_rate
        if interest > 0:
            # Calls deposit() from parent class (method overriding = polymorphism)
            self.deposit(interest, f"Applied interest at {self.interest_rate * 100:.2f}%")
        return interest


# Simple subclass (used for account compatibility)
class Account(BankAccount):
    pass


# ====================================================================================================
# Utility Functions
# ----------------------------------------------------------------------------------------------------
# Demonstrate procedural abstraction: user doesn’t need to know SQL details.
# ====================================================================================================
def create_account_for_user(db: DB, user_id, account_type='Checking', initial_deposit=0.0, interest_rate=0.0):
    acct_num = f"AC{int(datetime.utcnow().timestamp())}{user_id}"
    now = datetime.utcnow().isoformat()
    last_id = db.execute(
        "INSERT INTO accounts (user_id, account_number, account_type, balance, interest_rate, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, acct_num, account_type, initial_deposit, interest_rate, now))
    row = db.query("SELECT * FROM accounts WHERE id = %s", (last_id,))[0]
    return Account.from_row(db, row)


def submit_feedback(db: DB, message, user_id=None):
    now = datetime.utcnow().isoformat()
    db.execute("INSERT INTO feedback (user_id, message, timestamp) VALUES (%s, %s, %s)", (user_id, message, now))


def admin_login(db: DB, username, password):
    pw_hash = User.hash_password(password)
    rows = db.query("SELECT * FROM admins WHERE username = %s AND password_hash = %s", (username, pw_hash))
    return bool(rows)


def get_all_users(db: DB):
    return db.query("SELECT id, fullname, username, phone_number, pan_number FROM users ORDER BY fullname")


def delete_user(db: DB, user_id):
    db.execute("DELETE FROM users WHERE id = %s", (user_id,))


def get_users_by_balance(db: DB, limit=5):
    return db.query("""
        SELECT u.fullname, SUM(a.balance) as balance
        FROM users u
        JOIN accounts a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY balance DESC
        LIMIT %s
    """, (limit,))


def get_users_by_transaction_count(db: DB, limit=5):
    return db.query("""
        SELECT u.fullname, COUNT(t.id) as transaction_count
        FROM users u
        JOIN accounts a ON u.id = a.user_id
        JOIN transactions t ON a.id = t.account_id
        GROUP BY u.id
        ORDER BY transaction_count DESC
        LIMIT %s
    """, (limit,))


# ====================================================================================================
# DEMONSTRATION SECTION
# ----------------------------------------------------------------------------------------------------
# Runs only when this file is executed directly.
# Demonstrates OOP concepts with sample data using print statements.
# ====================================================================================================
if __name__ == "__main__":
    print("\n--- Demonstrating OOP Concepts in Banking Application ---\n")

    # 1️⃣ Encapsulation (Private + Public)
    demo_account = BankAccount(None, 1, 1, "AC001", "Savings", 1000.0, 0.04)
    print(f"Initial Public Balance: {demo_account.balance}")
    print(f"Accessing Private Secure Balance using getter: {demo_account.get_secure_balance()}")
    demo_account.set_secure_balance(1200)
    print(f"Updated Private Secure Balance: {demo_account.get_secure_balance()}")

    # 2️⃣ Inheritance + Polymorphism
    savings = SavingsAccount(None, 2, 2, "AC002", "Savings", 2000.0, 0.05)
    print(f"\nApplying interest (SavingsAccount overrides behavior): {savings.apply_interest()}")

    # 3️⃣ Abstraction — internal logic hidden from the user
    demo_account.deposit(500)
    demo_account.withdraw(200)

    # 4️⃣ Demonstrating List, Dictionary, Set usage
    customers = [
        {"id": 1, "name": "Parvath", "balance": 1500},
        {"id": 2, "name": "Aryan", "balance": 2500},
        {"id": 3, "name": "Vaishnavi", "balance": 3000},
    ]
    print("\nCustomer Data (List of Dictionaries):")
    for c in customers:
        print(c)

    customer_dict = {c["id"]: c for c in customers}
    print("\nCustomer with ID=2:", customer_dict[2])

    customer_names = {c["name"] for c in customers}
    print("\nUnique Customer Names (Set):", customer_names)

    print("\n✅ All OOP Concepts Demonstrated Successfully!\n")
