import sqlite3 as sql
import hashlib as hasher

class AccountDatabase:
    def __init__(self, db_name):
        self.conn = sql.connect(db_name)
        self.cursor = self.conn.cursor()
        self.init_db()
    
    def hash_password(self, password: str) -> str:
        return hasher.sha256(password.encode()).hexdigest()

    def init_db(self):
        """Initialize the user database if it doesn't exist."""
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )"""
        )
        self.conn.commit()

    def add_account(self, username: str, password: str) -> bool:
        """Adds an account to the user database given a `username` and `password`. 
           Returns `True` on success and `False` on failure, for instance
           if an account already exists with the provided `username`.
        """
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            print(f"Account '{username}' added successfully.")
            return True
        except sql.IntegrityError:
            print("Error: Username already exists.")
            return False
    
    def verify_account(self, username: str, password: str) -> bool:
        """Check if username and password match."""
        self.cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result:
            print("Username and password match.")
            return self.hash_password(password) == result[0]
        print("Account doesn't exist.")
        return False
    
    def delete_account(self, username: str) -> bool:
        """Deletes an account by username. Returns True on success, False if account doesn't exist."""
        self.cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone() is None:
            print("Error: Account not found.")
            return False
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()
        print(f"Account '{username}' deleted successfully.")
        return True
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    raise RuntimeError("This should not be run directly. Import it as a module instead.")
