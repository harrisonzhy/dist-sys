import sqlite3 as sql
import hashlib as hasher
from db import AccountDatabase
import multiprocessing
import tempfile

def display_db_contents(db_name):
    """Connect to SQLite database and display its tables and contents."""
    conn = sql.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if tables:
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
            # Display contents of each table
            cursor.execute(f"SELECT * FROM {table[0]};")
            rows = cursor.fetchall()
            print(f"Contents of table '{table[0]}':")
            for row in rows:
                print(row)
            print("-" * 50)
    else:
        print("No tables found in the database.")
    conn.close()

if __name__ == "__main__":
    # Use a file-based SQLite database instead of in-memory
    temp_db_path = tempfile.NamedTemporaryFile(suffix=".db").name
    test_db = AccountDatabase(temp_db_path)

    test_db.create_account("multi_user1", "pass1")
    test_db.create_account("multi_user2", "pass2")

    def send_messages():
        # Each process should create its own connection to the database
        db = AccountDatabase(temp_db_path)
        for _ in range(10):
            db.send_text_message("multi_user1", "multi_user2", "Hello!")
        db.close()

    process1 = multiprocessing.Process(target=send_messages)
    process2 = multiprocessing.Process(target=send_messages)

    process1.start()
    process2.start()
    process1.join()
    process2.join()

    messages = test_db.fetch_text_messages("multi_user1", 20)

    test_db.close()
