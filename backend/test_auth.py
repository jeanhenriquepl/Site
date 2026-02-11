from auth import get_password_hash, verify_password
try:
    print("Testing hash...")
    pwd = "admin"
    hashed = get_password_hash(pwd)
    print(f"Hash: {hashed}")
    
    print("Testing verify...")
    valid = verify_password("admin", hashed)
    print(f"Valid: {valid}")
except Exception as e:
    print(f"Auth FAILED: {e}")
    import traceback
    traceback.print_exc()
