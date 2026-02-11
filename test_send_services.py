import requests
import json

API_URL = "http://localhost:8000/api/inventory"

data = {
    "hostname": "TEST-MACHINE",
    "ip_address": "127.0.0.1",
    "os_info": "Windows 10 Test",
    "processor": "Intel Test",
    "ram_gb": 16.0,
    "disk_gb": 500.0,
    "manufacturer": "Test Corp",
    "model": "Test Model",
    "serial_number": "TEST-123",
    "cpu_usage": 10.5,
    "memory_usage": 45.2,
    "disk_usage": 20.1,
    "softwares": [
        {"name": "Test Software", "version": "1.0", "publisher": "Test Corp"}
    ],
    "services": [
        {"name": "Spooler", "display_name": "Print Spooler", "status": "running", "start_type": "automatic"},
        {"name": "TestService", "display_name": "Test Service", "status": "stopped", "start_type": "manual"}
    ]
}

try:
    print("Sending test data...")
    response = requests.post(API_URL, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
