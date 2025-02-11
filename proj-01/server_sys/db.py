import sqlite3 as sql
import threading
from datetime import datetime

class AccountDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.local = threading.local()  # Thread-local storage
        self.query_lock = threading.Lock()
        
        self.init_db()

    def init_db(self):
        """Initialize the user database, conversations, and messages tables if they don't exist."""
        conn = self.get_conn()
        cursor = conn.cursor()

        # Create users table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )"""
        )

        # Create conversations table (to store chat between two users)
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_1 INTEGER,
                user_id_2 INTEGER,
                FOREIGN KEY (user_id_1) REFERENCES users (id),
                FOREIGN KEY (user_id_2) REFERENCES users (id)
            )"""
        )

        # Create messages table (stores messages for each conversation)
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                user_id INTEGER,
                message_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )"""
        )
        conn.commit()

    def get_conn(self):
        """Return a thread-local SQLite connection."""
        if not hasattr(self.local, 'conn'):
            # Create a new connection for this thread
            self.local.conn = sql.connect(self.db_name, check_same_thread=False)
        return self.local.conn

    def create_account(self, username: str, hashed_password: str) -> bool:
        """Adds an account to the user database given a `username` and `password`."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                print(f"[Server] Account '{username}' added successfully.")
                return True
            except sql.IntegrityError:
                print("[Server] Error: Username already exists.")
                return False

    def login_account(self, username: str, hashed_password: str) -> bool:
        """Check if username and password match."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                return hashed_password == result[0]
            return False

    def create_conversation(self, username_1: str, username_2: str) -> bool:
        """Create a conversation (chat) between two users."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM users WHERE username = ?", (username_1,))
            user_1 = cursor.fetchone()

            cursor.execute("SELECT id FROM users WHERE username = ?", (username_2,))
            user_2 = cursor.fetchone()

            if user_1 and user_2:
                user_1_id, user_2_id = user_1[0], user_2[0]
                cursor.execute("""
                    INSERT INTO conversations (user_id_1, user_id_2) 
                    VALUES (?, ?)
                """, (user_1_id, user_2_id))
                conn.commit()
                print(f"[Server] Conversation between '{username_1}' and '{username_2}' created.")
                return True
            else:
                print("[Server] Error: One or more users not found.")
                return False

    def send_text_message(self, username_1: str, username_2: str, message_text: str) -> bool:
        """Add a message to a conversation between two users where `username_1` is sender and `username_2` is receiver."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            def cursor_fetch_execute():
                cursor.execute("""
                    SELECT c.conversation_id 
                    FROM conversations c
                    JOIN users u1 ON u1.id = c.user_id_1
                    JOIN users u2 ON u2.id = c.user_id_2
                    WHERE (u1.username = ? AND u2.username = ?) 
                    OR (u1.username = ? AND u2.username = ?)
                """, (username_1, username_2, username_2, username_1))

            cursor_fetch_execute()
            conversation = cursor.fetchone()
            if not conversation:
                status = self.create_conversation(username_1, username_2)
                if not status:
                    print("[Server] Message could not be delivered.")
                    return False
                cursor_fetch_execute()
                conversation = cursor.fetchone()
                if not conversation:
                    print("[Server] Message could not be delivered.")
                    return False
            conversation_id = conversation[0]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.') + f"{datetime.now().microsecond}"
            cursor.execute("""
                INSERT INTO messages (conversation_id, user_id, message_text, timestamp) 
                VALUES (?, ?, ?, ?)
            """, (conversation_id, username_1, message_text, timestamp)) 
            conn.commit()
            print(f"[Server] Message '{message_text}' added to conversation between '{username_1}' and '{username_2}'.")
            return True

    def fetch_text_messages(self, username_1: str, username_2: str, k: int) -> list[str]:
        """Retrieve the k most recent messages between two users."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.message_text, m.timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.conversation_id
                JOIN users u1 ON u1.id = c.user_id_1
                JOIN users u2 ON u2.id = c.user_id_2
                WHERE (u1.username = ? AND u2.username = ?) 
                OR (u1.username = ? AND u2.username = ?)
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (username_1, username_2, username_2, username_1, k))

            fetched_messages = cursor.fetchall()
            messages = [message[0] for message in fetched_messages]
            if messages:
                print(f"[Server] The k={k} most recent messages between '{username_1}' and '{username_2}':")
                for message in messages:
                    print("[+]", message)
            else:
                print(f"[Server] No messages found between '{username_1}' and '{username_2}'.")
            return messages

    def close(self):
        """Close the connection for the current thread."""
        with self.query_lock:
            if hasattr(self.local, 'conn'):
                self.local.conn.close()
