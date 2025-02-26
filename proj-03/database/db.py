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
        if not username or not hashed_password:
            print("[Server] Error: Empty username or password.")
            return False

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
        if username_1 == username_2:
            print("[Server] Error: Users are the same.")
            return False

        conn = self.get_conn()
        cursor = conn.cursor()

        # Get user IDs for both users
        cursor.execute("SELECT id FROM users WHERE username = ?", (username_1,))
        user_1 = cursor.fetchone()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username_2,))
        user_2 = cursor.fetchone()

        if user_1 and user_2:
            user_1_id, user_2_id = user_1[0], user_2[0]

            # Check if conversation already exists
            cursor.execute("""
                SELECT conversation_id FROM conversations 
                WHERE (user_id_1 = ? AND user_id_2 = ?) 
                OR (user_id_1 = ? AND user_id_2 = ?)
            """, (user_1_id, user_2_id, user_2_id, user_1_id))

            existing_conversation = cursor.fetchone()
            if existing_conversation:
                print(f"[Server] Error: Conversation between '{username_1}' and '{username_2}' already exists.")
                return False

            # Insert new conversation if none exists
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
        if not message_text:
            print("[Server] Error: Empty message.")
            return False
        
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

    def fetch_text_messages(self, username_1: str, k: int) -> list[str]:
        """Retrieve the k most recent messages between two users."""
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.message_id, u1.username, u2.username, m.message_text
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.conversation_id
                JOIN users u1 ON u1.id = c.user_id_1
                JOIN users u2 ON u2.id = c.user_id_2
                WHERE (u1.username = ?) 
                OR (u2.username = ?)
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (username_1, username_1, k))

            fetched_messages = cursor.fetchall()
            messages = []
            for row in fetched_messages:
                message_data = []
                for i in range(4):
                    message_data.append(str(row[i]))
                messages.append('|'.join(message_data))

            if messages:
                print(f"[Server] The k={k} most recent messages involving '{username_1}':")
                for message in messages:
                    print("[+]", message)
            else:
                print(f"[Server] No messages found involving'{username_1}'.")
                messages.append("")
            return messages

    def delete_text_message(self, message_id):
        """
        Deletes a message from the database based on the given message_id.
        If the deleted message was the last in its conversation, the conversation is also deleted.
        """
        message_id = int(message_id)
        conn = self.get_conn()
        cursor = conn.cursor()

        # Find the conversation_id of the message to be deleted
        cursor.execute("SELECT conversation_id FROM messages WHERE message_id = ?", (message_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.close()
            return False  # Message not found

        conversation_id = row[0]

        # Delete the message
        cursor.execute("DELETE FROM messages WHERE message_id = ?", (message_id,))
        conn.commit()

        # Check if there are any remaining messages in the conversation
        cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,))
        remaining_messages = cursor.fetchone()[0]

        if remaining_messages == 0:
            # Delete the conversation if no messages are left
            cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            conn.commit()

        cursor.close()
        return True

    def delete_account(self, username: str) -> bool:
        """
        Deletes the specified user's account and all messages (and conversations) 
        associated with that user.
        """
        with self.query_lock:
            conn = self.get_conn()
            cursor = conn.cursor()

            # 1. Find the user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                print(f"[Server] Error: User '{username}' does not exist.")
                return False
            user_id = row[0]

            # 2. Find all conversations in which this user participates (as user_id_1 or user_id_2)
            cursor.execute(
                "SELECT conversation_id FROM conversations WHERE user_id_1 = ? OR user_id_2 = ?",
                (user_id, user_id)
            )
            conversation_ids = cursor.fetchall()

            # 3. For each conversation, delete all messages and then delete the conversation
            for (conv_id,) in conversation_ids:
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
                cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conv_id,))

            # 4. Finally, delete the user record
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            cursor.close()

            print(f"[Server] Account '{username}' and all associated data removed successfully.")
            return True

    def close(self):
        """Close the connection for the current thread."""
        with self.query_lock:
            if hasattr(self.local, 'conn'):
                self.local.conn.close()
