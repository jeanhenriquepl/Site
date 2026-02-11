import requests
import json

url = "http://localhost:8000/api/inventory"
payload = {
    "hostname": "TEST-PC",
    "client_code": "TEST-CLIENT",
    "ip_address": "127.0.0.1",
    "os_info": "Windows 10",
    "processor": "Intel",
    "ram_gb": 16,
    "disk_gb": 512,
    "softwares": [],
    "services": []
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
