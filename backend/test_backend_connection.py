import requests
import os
import json

"""
Simple diagnostic script to test if the frontend can reach the backend.
This will help determine if there's a network/firewall issue.
"""

# Get the backend URL from the environment or use default
BACKEND_URL = os.environ.get("BACKEND_URL", "https://llamaindex-production-633d.up.railway.app")

print(f"Testing connection to backend: {BACKEND_URL}")

# Simple GET request to the /ping endpoint
try:
    response = requests.get(f"{BACKEND_URL}/ping", timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ Successfully connected to backend!")
    else:
        print("❌ Received non-200 response from backend")
except Exception as e:
    print(f"❌ Failed to connect to backend: {e}")
    
# Test the /health endpoint
try:
    print("\nChecking backend health...")
    response = requests.get(f"{BACKEND_URL}/health", timeout=10)
    print(f"Status code: {response.status_code}")
    try:
        health_data = response.json()
        print(json.dumps(health_data, indent=2))
        
        # Check specific services
        services = health_data.get("services", {})
        for service, status in services.items():
            if "connected" in status:
                print(f"✅ {service}: {status}")
            else:
                print(f"❌ {service}: {status}")
    except:
        print(f"Response (not JSON): {response.text[:100]}...")
except Exception as e:
    print(f"❌ Failed to check health: {e}")

# Try connecting to /process with a test payload
try:
    print("\nTesting /process endpoint with minimal payload...")
    payload = {
        "file_id": "test-file-id",
        "supabase_file_path": "test-path",
        "name": "test-file.txt",
        "type": "text/plain",
        "size": 100
    }
    
    # Add simple auth header
    headers = {
        "Content-Type": "application/json"
    }
    
    # See if we have a backend API key
    backend_api_key = os.environ.get("BACKEND_API_KEY")
    if backend_api_key:
        headers["Authorization"] = f"Bearer {backend_api_key}"
        print("Added API key to request")
    
    # Send the request
    response = requests.post(
        f"{BACKEND_URL}/process",
        json=payload,
        headers=headers,
        timeout=10
    )
    
    print(f"Status code: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Response (not JSON): {response.text[:100]}...")
    
    # We expect this to fail with a 404 (file not found) or similar
    # but NOT with a 500 or connection error
    if response.status_code != 500 and "failed to respond" not in response.text.lower():
        print("✅ Process endpoint responded (even with an error)")
    else:
        print("❌ Process endpoint failed with a server error")
    
except Exception as e:
    print(f"❌ Failed to test process endpoint: {e}")

print("\nDiagnostic test completed.")
