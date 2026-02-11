import psutil
try:
    print("Testing psutil.win_service_iter()...")
    services = list(psutil.win_service_iter())
    print(f"Total services found: {len(services)}")
    
    running = [s for s in services if s.status() == 'running']
    print(f"Running services: {len(running)}")
    
    if len(running) > 0:
        s = running[0]
        print(f"First running service: {s.name()}")
        try:
            print(f"Start Type: {s.start_type()}")
        except Exception as e:
            print(f"Start Type Error: {e}")
            
except Exception as e:
    print(f"Error: {e}")
