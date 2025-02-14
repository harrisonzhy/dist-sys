import sqlite3 as sql

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
