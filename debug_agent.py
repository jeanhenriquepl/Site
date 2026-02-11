import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

API_URL = "http://localhost:8000/api/inventory"

data = {
    "hostname": "TEST-PC",
    "ip_address": "192.168.1.100",
    "os_info": "Windows 10",
    "processor": "Intel Core i7",
    "ram_gb": 16.0,
    "disk_gb": 512.0,
    "manufacturer": "Dell",
    "model": "XPS 15",
    "serial_number": "12345ABC",
    "softwares": [
        {"name": "Chrome", "version": "1.0", "publisher": "Google"}
    ],
    "services": [
        {"name": "Spooler", "display_name": "Print Spooler", "status": "running", "start_type": "automatic"}
    ]
}

try:
    print("Sending data...")
    print(json.dumps(data, indent=2))
    response = requests.post(API_URL, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
