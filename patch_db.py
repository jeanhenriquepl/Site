import sqlite3
import os

db_paths = [os.path.join("backend", "inventory.db"), "inventory.db"]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"Patching database at: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column exists
            cursor.execute("PRAGMA table_info(machine)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "client_code" not in columns:
                print("Adding client_code column...")
                try:
                    cursor.execute("ALTER TABLE machine ADD COLUMN client_code VARCHAR DEFAULT 'DEFAULT'")
                    conn.commit()
                    print("SUCCESS: Column added.")
                except Exception as e:
                    print(f"Error adding column: {e}")
            else:
                print("Column client_code already exists.")
                
            # Also check InventoryReport if it was a table? No, it's a model but not a table usually suitable for this context.
            # actually InventoryReport is not a table in my models.py (table=True is only on Machine, Software, Service, Command, User)
            
            conn.close()
        except Exception as e:
            print(f"Error connecting to DB: {e}")
