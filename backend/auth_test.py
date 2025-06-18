#!/usr/bin/env python3
"""
API Key Authentication Test Script

This script tests the authentication between frontend and backend
by simulating how the frontend makes API calls to the backend.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API key and URL
API_KEY = os.environ.get("LLAMAINDEX_API_KEY")
BACKEND_URL = os.environ.get("LLAMAINDEX_URL", "https://llamaindex-production-633d.up.railway.app")

if not API_KEY:
    print("❌ LLAMAINDEX_API_KEY environment variable is not set.")
    print("Please set it to the same value as in your Vercel environment.")
    print("Expected value: vNEhARgFnx39THmoe4ykJBLa5Gw8P7C0")
    sys.exit(1)

print(f"Testing authentication with API key: {API_KEY[:4]}...{API_KEY[-4:]}")
print(f"Backend URL: {BACKEND_URL}")

# Test the health endpoint first
print("\n=== Testing Health Endpoint ===")
try:
    health_response = requests.get(f"{BACKEND_URL}/health")
    print(f"Status code: {health_response.status_code}")
    if health_response.status_code == 200:
        print(f"Response: {health_response.json()}")
    else:
        print(f"Error response: {health_response.text}")
except Exception as e:
    print(f"❌ Error connecting to health endpoint: {str(e)}")

# Now test the debug endpoint
print("\n=== Testing Debug Endpoint ===")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

try:
    debug_response = requests.get(f"{BACKEND_URL}/debug/supabase", headers=headers)
    print(f"Status code: {debug_response.status_code}")
    if debug_response.status_code == 200:
        result = debug_response.json()
        # Pretty print the JSON with indentation
        print(json.dumps(result, indent=2))
    else:
        print(f"Error response: {debug_response.text}")
except Exception as e:
    print(f"❌ Error connecting to debug endpoint: {str(e)}")

# Test an actual file processing (optional - only if file_id provided)
if len(sys.argv) > 1:
    file_id = sys.argv[1]
    print(f"\n=== Testing File Processing with file_id: {file_id} ===")
    
    data = {
        "file_id": file_id,
        "supabase_file_path": file_id,  # Will try multiple formats
        "name": "Test file",
        "type": "text/plain",
        "size": 1000,
        "description": "Test file for debugging",
        "user_id": "test-user"
    }
    
    try:
        process_response = requests.post(
            f"{BACKEND_URL}/process", 
            headers=headers,
            json=data
        )
        print(f"Status code: {process_response.status_code}")
        if process_response.status_code == 200:
            print("✓ File processing successful!")
            print(json.dumps(process_response.json(), indent=2))
        else:
            print(f"❌ File processing failed: {process_response.text}")
    except Exception as e:
        print(f"❌ Error during file processing: {str(e)}")

print("\nTest complete.")
