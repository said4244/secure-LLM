import sqlite3
import time
import json 

class TransactionDb:
    def __init__(self, db_name="transactions.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                userId INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Transactions (
                transactionId INTEGER PRIMARY KEY,
                userId INTEGER NOT NULL,
                reference TEXT,
                recipient TEXT,
                amount REAL
            )
        ''')

        self.conn.commit()

    def seed_data(self):
        cursor = self.conn.cursor()

        # Sample users
        users = [
            (1,"MartyMcFly", "Password1"),
            (2,"DocBrown", "flux-capacitor-123"),
            (3,"BiffTannen", "Password3"),
            (4,"GeorgeMcFly", "Password4")
        ]
        cursor.executemany("INSERT OR IGNORE INTO Users (userId, username, password) VALUES (?, ?, ?)", users)

        # Sample transactions
        transactions = [
            (1, 1, "DeLoreanParts", "AutoShop", 1000.0),
            (2, 1, "SkateboardUpgrade", "SportsStore", 150.0),
            (3, 2, "PlutoniumPurchase", "FLAG:plutonium-256", 5000.0),
            (4, 2, "FluxCapacitor", "InnovativeTech", 3000.0),
            (5, 3, "SportsAlmanac", "RareBooks", 200.0),
            (6, 4, "WritingSupplies", "OfficeStore", 40.0),
            (7, 4, "SciFiNovels", "BookShop", 60.0)
        ]
        cursor.executemany("INSERT OR IGNORE INTO Transactions (transactionId, userId, reference, recipient, amount) VALUES (?, ?, ?, ?, ?)", transactions)

        self.conn.commit()

    def get_user_transactions(self, userId):
        cursor = self.conn.cursor()
        try:
            # here we validate that userId is a number, as it should
            user_id_int = int(userId)
        except (ValueError, TypeError):
            return json.dumps({"error": "Invalid user ID format"})
        
        # Use parameterized query with ? placeholder
        cursor.execute("SELECT * FROM Transactions WHERE userId = ?", (user_id_int,))
        rows = cursor.fetchall()

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Convert rows to dictionaries with column names as keys
        transactions = [dict(zip(columns, row)) for row in rows]

        # Convert to JSON format
        return json.dumps(transactions, indent=4)

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT userId,username FROM Users WHERE userId = {str(user_id)}"
        )
        rows = cursor.fetchall()

        # Get column names
        columns = [column[0] for column in cursor.description]

        # Convert rows to dictionaries with column names as keys
        users = [dict(zip(columns, row)) for row in rows]

        # Convert to JSON format
        return json.dumps(users, indent=4)

    def close(self):
        self.conn.close()
