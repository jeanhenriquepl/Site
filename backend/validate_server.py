import sys
import os

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Validating server configuration...")
    # Attempt to import main application and run startup event
    from main import on_startup
    
    print("Running startup check...")
    on_startup()
    print("Server validation successful!")
    sys.exit(0)
except Exception as e:
    print(f"\nCRITICAL ERROR: Server startup failed!\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
