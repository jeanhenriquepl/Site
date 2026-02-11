from sqlmodel import Session, select
from backend.database import engine
from backend.models import Machine

try:
    with Session(engine) as session:
        # Try to select from Machine table
        # If schema is old, it might succeed on select * but fail on specific access if not mapped, 
        # or it might fail immediately if we try to inspect.
        # Let's try to verify if 'client_code' column exists by raw SQL or by trying to insert/read.
        
        # Simplest: Try to get a machine and access client_code, or check table info.
        print("Checking schema...")
        results = session.exec("PRAGMA table_info(machine)").all()
        columns = [row[1] for row in results]
        print(f"Columns in machine table: {columns}")
        
        if "client_code" in columns:
            print("SUCCESS: client_code column exists.")
        else:
            print("FAILURE: client_code column MISSING.")
            
except Exception as e:
    print(f"Error checking DB: {e}")
