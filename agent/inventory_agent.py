import platform
import psutil
import json
import requests
import socket
import sys

import time

import os
import argparse

# Configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000/api/inventory",
    "client_code": "DEFAULT",
    "interval_seconds": 60,
    "api_key": ""
}
CONFIG_FILE = "agent_config.json"

def load_config():
    """Load configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        return create_default_config()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {os.path.abspath(CONFIG_FILE)}")
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def create_default_config():
    """Create default configuration file"""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def setup_agent():
    """Interactive setup for the agent"""
    print("--- IT Inventory Agent Setup ---")
    config = load_config()
    
    url = input(f"Enter API URL [{config['api_url']}]: ").strip()
    if url:
        config['api_url'] = url
        
    interval = input(f"Enter Collection Interval (seconds) [{config['interval_seconds']}]: ").strip()
    if interval:
        try:
            config['interval_seconds'] = int(interval)
        except ValueError:
            print("Invalid interval. Using previous value.")
            
    code = input(f"Enter Client Code [{config.get('client_code', 'DEFAULT')}]: ").strip()
    if code:
        config['client_code'] = code.upper()

    key = input(f"Enter API Key (optional) [{config.get('api_key', '')}]: ").strip()
    if key:
        config['api_key'] = key
        
    save_config(config)
    print("Setup complete.")

# Global config variable
AGENT_CONFIG = load_config()
API_URL = AGENT_CONFIG['api_url']
INTERVAL_SECONDS = AGENT_CONFIG['interval_seconds']
CLIENT_CODE = AGENT_CONFIG.get('client_code', 'DEFAULT')

def get_size(bytes, suffix="GB"):
    """
    Scale bytes to its proper format
    """
    factor = 1024
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}"
        bytes /= factor
    return f"{bytes:.2f}{suffix}"

def get_installed_software():
    """
    Get installed software using Windows Registry (scans both 32-bit and 64-bit keys)
    """
    softwares = []
    if platform.system() != "Windows":
        return softwares

    import winreg

    def get_software_list(hive, flag):
        software_list = []
        try:
            aReg = winreg.ConnectRegistry(None, hive)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0, winreg.KEY_READ | flag)
            
            count_subkeys = winreg.QueryInfoKey(aKey)[0]
            
            for i in range(count_subkeys):
                try:
                    asubkey_name = winreg.EnumKey(aKey, i)
                    with winreg.OpenKey(aKey, asubkey_name) as asubkey:
                        try:
                            name = winreg.QueryValueEx(asubkey, "DisplayName")[0]
                        except OSError:
                            continue # Skip if no DisplayName

                        try:
                            version = winreg.QueryValueEx(asubkey, "DisplayVersion")[0]
                        except OSError:
                            version = "Unknown"
                        
                        try:
                            publisher = winreg.QueryValueEx(asubkey, "Publisher")[0]
                        except OSError:
                            publisher = "Unknown"

                        software_list.append({
                            "name": name,
                            "version": version,
                            "publisher": publisher
                        })
                except OSError:
                    continue
        except OSError as e:
            print(f"Error accessing registry hive {hive}: {e}")
        return software_list

    # Scan both HKLM keys (64-bit and 32-bit views)
    softwares.extend(get_software_list(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY))
    softwares.extend(get_software_list(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY))
    
    # Deduplicate based on name and version
    unique_softwares = {}
    for sw in softwares:
        key = (sw["name"], sw["version"])
        unique_softwares[key] = sw
        
    return list(unique_softwares.values())

def get_running_services():
    """
    Get running services using psutil
    """
    services = []
    try:
        for service in psutil.win_service_iter():
            try:
                # Try getting full info
                # as_dict can be flaky with permissions, lets use direct property access which is more robust
                info = {
                    'name': service.name(),
                    'display_name': service.display_name(),
                    'status': service.status(),
                    'start_type': "unknown"
                }
                try:
                    info['start_type'] = service.start_type()
                except:
                    pass
                
                if info.get('status') == 'running':
                    services.append(info)

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                continue
            except Exception as e:
                continue 
    except Exception as e:
        print(f"Error getting services: {e}")
    
    print(f"DEBUG: Found {len(services)} running services")
    return services

def get_system_details():
    """
    Get hardware details using WMI
    """
    details = {
        "manufacturer": "Unknown",
        "model": "Unknown",
        "serial_number": "Unknown"
    }
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            sys_info = c.Win32_ComputerSystem()[0]
            bios_info = c.Win32_BIOS()[0]
            details["manufacturer"] = sys_info.Manufacturer
            details["model"] = sys_info.Model
            details["serial_number"] = bios_info.SerialNumber
        except Exception as e:
            print(f"Error getting system details: {e}")
    return details

def collect_system_info():
    sys_details = get_system_details()
    info = {
        "hostname": socket.gethostname(),
        "client_code": CLIENT_CODE,
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "os_info": f"{platform.system()} {platform.release()}",
        "processor": platform.processor(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
        "manufacturer": sys_details["manufacturer"],
        "model": sys_details["model"],
        "serial_number": sys_details["serial_number"],
        # Real-time metrics
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "softwares": get_installed_software(),
        "services": get_running_services()
    }
    return info

def send_data(data):
    try:
        headers = {'Content-Type': 'application/json'}
        # Filter out circular refs or non-serializable if any (though we built dicts)
        response = requests.post(API_URL, json=data, headers=headers)
        if response.status_code == 200:
            print(f"[{datetime.now()}] Successfully sent inventory data!")
        else:
            print(f"[{datetime.now()}] Failed to send data: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] Error connecting to server: {e}")

# --- Remote Command Execution ---
import subprocess
import threading

API_BASE_URL = "http://localhost:8000/api"

def execute_command(command_id, command_str):
    print(f"[{datetime.now()}] Executing command: {command_str}")
    try:
        # Run powershell command
        # Use shell=True to allow shell built-ins, but capture output
        # '-Command' handles the string as a command
        proc = subprocess.run(["powershell", "-Command", command_str], capture_output=True, text=True, timeout=60)
        
        output = proc.stdout
        if proc.stderr:
            output += f"\nERROR:\n{proc.stderr}"
            
        status = "completed" if proc.returncode == 0 else "error"
        
    except Exception as e:
        output = f"Execution failed: {str(e)}"
        status = "error"
        
    # Check for Admin rights if error
    if status == "error":
        try:
             import ctypes
             is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
             if not is_admin:
                 output += "\n\n[DICA]: O Agente NÃO está rodando como Administrador.\nO Windows exige privilégios de Admin para iniciar/parar serviços.\nPor favor, feche e abra o terminal como Administrador."
        except:
             pass
        
    # Send result back
    try:
        data = {"output": output, "status": status}
        requests.post(f"{API_BASE_URL}/commands/{command_id}/result", json=data)
        print(f"[{datetime.now()}] Command {command_id} result sent (Status: {status})")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to send command result: {e}")


def poll_commands():
    """
    Polls for pending commands every few seconds
    """
    hostname = socket.gethostname()
    while True:
        try:
            response = requests.get(f"{API_BASE_URL}/commands/pending", params={"hostname": hostname})
            if response.status_code == 200:
                commands = response.json()
                for cmd in commands:
                    # Execute in another thread to not block polling? 
                    # For now scalar execution is safer to avoid overload
                    execute_command(cmd['id'], cmd['command'])
            else:
                pass # No commands or error, just wait
        except Exception as e:
            print(f"polling error: {e}")
        
        time.sleep(3) # Poll every 3 seconds

if __name__ == "__main__":
    from datetime import datetime
    parser = argparse.ArgumentParser(description="IT Inventory Agent")
    parser.add_argument("--setup", action="store_true", help="Run interactive setup")
    args = parser.parse_args()

    if args.setup:
        setup_agent()
        sys.exit(0)

    # Reload config in case it was just updated (though we loaded it globally, setup updates the file)
    AGENT_CONFIG = load_config()
    API_URL = AGENT_CONFIG['api_url']
    INTERVAL_SECONDS = AGENT_CONFIG['interval_seconds']

    print(f"Starting IT Inventory Agent... (Target: {API_URL})")
    
    # Check Admin (Simple check on Windows)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            print("WARNING: Agent is NOT running as Administrator. Some commands may fail.")
    except:
        pass

    # Start Command Polling Thread
    cmd_thread = threading.Thread(target=poll_commands, daemon=True)
    cmd_thread.start()
    print("Command polling started.")

    # Initial run
    try:
        print("Collecting system info...")
        data = collect_system_info()
        print(f"Sending data for {data['hostname']}...")
        send_data(data)
    except Exception as e:
         print(f"Initial collection failed: {e}")

    # Loop
    while True:
        time.sleep(INTERVAL_SECONDS)
        try:
            print("Collecting system info...")
            data = collect_system_info()
            print(f"Sending data for {data['hostname']}...")
            send_data(data)
        except KeyboardInterrupt:
            print("\nStopping Agent.")
            break
        except Exception as e:
            print(f"Error in loop: {e}")
