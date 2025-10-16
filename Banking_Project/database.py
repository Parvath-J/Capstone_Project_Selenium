# filename: database.py
import mysql.connector
from mysql.connector import errorcode
import hashlib
import random
import string
from datetime import datetime

from config import DB_CONFIG, DB_NAME


class DB:
    def __init__(self, config=DB_CONFIG):
        self.config = config
        self.conn = None
        self._connect()
        self.create_tables()
        self._seed_admin()  # Add default admin user if one doesn't exist
        self._seed_customers()  # Add default customer users if they don't exist

    def _connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            cursor = self.conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
            cursor.close()
            self.conn.database = DB_NAME
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Access Denied: Please check your username or password in config.py")
            else:
                print(err)
            exit(1)

    def create_tables(self):
        cursor = self.conn.cursor()
        # Customer-facing tables
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           username
                           VARCHAR
                       (
                           255
                       ) UNIQUE NOT NULL,
                           fullname VARCHAR
                       (
                           255
                       ),
                           phone_number VARCHAR
                       (
                           20
                       ) UNIQUE NOT NULL,
                           pan_number VARCHAR
                       (
                           10
                       ) UNIQUE NOT NULL,
                           password_hash VARCHAR
                       (
                           255
                       ) NOT NULL,
                           upi_pin_hash VARCHAR
                       (
                           255
                       ) NOT NULL,
                           created_at VARCHAR
                       (
                           255
                       )
                           )""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS accounts
                       (
                           id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT
                           NOT
                           NULL,
                           account_number
                           VARCHAR
                       (
                           255
                       ) UNIQUE NOT NULL,
                           account_type VARCHAR
                       (
                           255
                       ) NOT NULL,
                           balance DECIMAL
                       (
                           15,
                           2
                       ) DEFAULT 0.00,
                           interest_rate DECIMAL
                       (
                           5,
                           4
                       ) DEFAULT 0.0000,
                           created_at VARCHAR
                       (
                           255
                       ),
                           FOREIGN KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           id
                       ) ON DELETE CASCADE
                           )""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS transactions
                       (
                           id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           account_id
                           INT
                           NOT
                           NULL,
                           type
                           VARCHAR
                       (
                           255
                       ) NOT NULL,
                           amount DECIMAL
                       (
                           15,
                           2
                       ) NOT NULL,
                           timestamp VARCHAR
                       (
                           255
                       ),
                           note TEXT,
                           related_account VARCHAR
                       (
                           255
                       ),
                           FOREIGN KEY
                       (
                           account_id
                       ) REFERENCES accounts
                       (
                           id
                       ) ON DELETE CASCADE
                           )""")
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS feedback
                       (
                           id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           user_id
                           INT,
                           message
                           TEXT
                           NOT
                           NULL,
                           timestamp
                           VARCHAR
                       (
                           255
                       ),
                           status VARCHAR
                       (
                           50
                       ) DEFAULT 'New',
                           FOREIGN KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           id
                       ) ON DELETE SET NULL
                           )""")

        # Admin table
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS admins
                       (
                           id
                           INT
                           AUTO_INCREMENT
                           PRIMARY
                           KEY,
                           username
                           VARCHAR
                       (
                           255
                       ) UNIQUE NOT NULL,
                           password_hash VARCHAR
                       (
                           255
                       ) NOT NULL
                           )""")

        self.conn.commit()
        cursor.close()

    def _seed_admin(self):
        """Creates a default admin user if no admins exist."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM admins LIMIT 1")
        if not cursor.fetchone():
            print("Creating default admin user...")
            username = "admin"
            password = "password"
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            cursor.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)", (username, pw_hash))
            self.conn.commit()
            print("Default Admin Created -> Username: admin, Password: password")
        cursor.close()

    # Replace the existing _seed_customers method in database.py with this one

    def _seed_customers(self):
        """Creates 25 default customer users if the users table is empty."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1")
        if cursor.fetchone():
            cursor.close()
            return  # Skip seeding if users already exist

        print("Seeding default customer data...")

        customer_names = [
            "Akanksha Singh", "Akhil Dadhich", "Amisha Nath", "Aryan Nishen", "Bhavana Uliyar",
            "Gaurav Kumar J", "Hareesh Nayak", "Kunaljit Roy", "Madhuchandra R", "Melvin Basutkar",
            "Mohith Reddy PN", "Monisha K M", "Nanthitha M S", "Nikhil P", "Parvath J",
            "Peram Varshitha", "Pratyush Jaishankar", "Rahul K S", "Ramya Hunagund", "Ritesh R",
            "Siddalingesha G", "Sushma Dodamani", "Taran Vadivelan", "Vaishnavi M", "Vaishnavi Shrikanth"
        ]

        used_mobiles = set()
        used_pans = set()

        # Keep track of the first 5 users to add transactions for them
        users_for_transactions = []

        for full_name in customer_names:
            # 1. Generate Username
            name_parts = full_name.lower().split()
            username = f"{name_parts[0]}.{name_parts[-1][0]}"

            # 2. Generate unique 10-digit mobile number
            while True:
                mobile = str(random.randint(6, 9)) + "".join([str(random.randint(0, 9)) for _ in range(9)])
                if mobile not in used_mobiles:
                    used_mobiles.add(mobile)
                    break

            # 3. Generate unique 10-digit PAN number
            while True:
                pan = "".join(random.choices(string.ascii_uppercase, k=5)) + \
                      "".join(random.choices(string.digits, k=4)) + \
                      random.choice(string.ascii_uppercase)
                if pan not in used_pans:
                    used_pans.add(pan)
                    break

            # 4. Create password and UPI PIN
            password = f"{username}.123"
            upi_pin = mobile[:4]
            pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            upi_pin_hash = hashlib.sha256(upi_pin.encode("utf-8")).hexdigest()

            # 5. Insert user into the database
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_sql = """INSERT INTO users (username, fullname, phone_number, pan_number, password_hash, \
                                             upi_pin_hash, created_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(user_sql, (username, full_name, mobile, pan, pw_hash, upi_pin_hash, now))
            user_id = cursor.lastrowid

            # 6. Create a savings account with a balance of 32500
            account_number = f"SAV{user_id:011d}"
            account_sql = """INSERT INTO accounts (user_id, account_number, account_type, balance, created_at)
                             VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(account_sql, (user_id, account_number, "Savings", 32500.00, now))
            account_id = cursor.lastrowid

            # Store the first 5 account IDs to add transactions to them
            if len(users_for_transactions) < 5:
                users_for_transactions.append({'account_id': account_id, 'balance': 32500.00})

        # --- NEW SECTION TO ADD SAMPLE TRANSACTIONS ---
        print("Adding sample transactions for analytics...")
        txn_sql = "INSERT INTO transactions (account_id, type, amount, timestamp, note) VALUES (%s, %s, %s, %s, %s)"

        # User 1: 3 transactions
        acc1 = users_for_transactions[0]
        cursor.execute(txn_sql, (acc1['account_id'], 'DEPOSIT', 1500.00, now, 'Salary Credit'))
        cursor.execute(txn_sql, (acc1['account_id'], 'WITHDRAW', 200.00, now, 'ATM Withdrawal'))
        cursor.execute(txn_sql, (acc1['account_id'], 'DEPOSIT', 50.00, now, 'Cashback'))
        cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s",
                       (acc1['balance'] + 1350.00, acc1['account_id']))

        # User 2: 2 transactions
        acc2 = users_for_transactions[1]
        cursor.execute(txn_sql, (acc2['account_id'], 'DEPOSIT', 5000.00, now, 'Initial Deposit'))
        cursor.execute(txn_sql, (acc2['account_id'], 'WITHDRAW', 1000.00, now, 'Online Shopping'))
        cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s",
                       (acc2['balance'] + 4000.00, acc2['account_id']))

        # User 3: 1 transaction
        acc3 = users_for_transactions[2]
        cursor.execute(txn_sql, (acc3['account_id'], 'WITHDRAW', 500.00, now, 'Bill Payment'))
        cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s",
                       (acc3['balance'] - 500.00, acc3['account_id']))
        # --- END OF NEW SECTION ---

        self.conn.commit()
        print(f"Successfully seeded {len(customer_names)} customers and added sample transactions.")
        cursor.close()

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        last_row_id = cursor.lastrowid
        cursor.close()
        return last_row_id

    def query(self, query, params=()):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result