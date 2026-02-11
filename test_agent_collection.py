from agent.inventory_agent import collect_system_info, get_running_services
import json

try:
    print("Testing get_running_services()...")
    services = get_running_services()
    print(f"Found {len(services)} services.")
    if len(services) > 0:
        print(f"Sample Service: {services[0]}")
    else:
        print("NO SERVICES FOUND from direct call.")

    print("\nTesting collect_system_info()...")
    info = collect_system_info()
    print("Collection successful.")
    print(f"Services in info: {len(info['services'])}")
    if len(info['services']) > 0:
        print(f"First service in payload: {info['services'][0]}")

except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
