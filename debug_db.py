import sqlite3
import os

db_path = os.path.join("backend", "inventory.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    # try root
    db_path = "inventory.db"

if os.path.exists(db_path):
    print(f"Checking database at: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(machine)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns in machine table: {columns}")
        if "client_code" in columns:
            print("SUCCESS: client_code column found.")
        else:
            print("FAILURE: client_code column MISSING.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No database file found.")
