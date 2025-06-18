#!/usr/bin/env python3
"""
Railway Endpoint Connectivity Tester

This script tests connectivity to your Railway endpoint with different paths
to determine if the issue is with the URL construction or endpoint configuration.
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up colors for terminal output
class Colors:
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

# Get Railway URL
RAILWAY_URL = os.environ.get("LLAMAINDEX_URL", "https://llamaindex-production-633d.up.railway.app")

print_header("RAILWAY ENDPOINT CONNECTIVITY TEST")
print(f"Testing URL: {RAILWAY_URL}")
print(f"Timestamp: {datetime.now().isoformat()}")
print("")

# List of endpoints to test
endpoints = [
    "/",                    # Root endpoint
    "/health",              # Health check
    "/process",             # Process endpoint (using GET for testing only)
    "/api/process",         # Alternative path with /api prefix
]

# Test basic connectivity to different paths
print_header("TESTING ENDPOINT PATHS")

for endpoint in endpoints:
    full_url = f"{RAILWAY_URL}{endpoint}"
    print(f"Testing: {full_url}")
    
    try:
        response = requests.get(full_url, timeout=10)
        status = response.status_code
        
        if status == 200:
            print_success(f"Success! HTTP {status}")
        elif status == 404:
            print_warning(f"Endpoint not found: HTTP {status}")
        elif status == 405:
            print_warning(f"Method not allowed: HTTP {status} (endpoint exists but doesn't accept GET)")
        else:
            print_error(f"Unexpected status: HTTP {status}")
        
        # Try to get content type and a bit of response
        content_type = response.headers.get('Content-Type', 'unknown')
        print(f"  Content-Type: {content_type}")
        
        if 'json' in content_type:
            try:
                data = response.json()
                print(f"  Response preview: {json.dumps(data)[:100]}...")
            except:
                print(f"  Response preview: {response.text[:100]}...")
        else:
            print(f"  Response preview: {response.text[:100]}...")
            
    except requests.exceptions.ConnectionError:
        print_error("CONNECTION REFUSED - Could not connect to endpoint")
    except requests.exceptions.Timeout:
        print_error("TIMEOUT - Request timed out")
    except Exception as e:
        print_error(f"ERROR: {str(e)}")
    
    print("")

# Test process endpoint with POST
print_header("TESTING /process WITH POST")
process_url = f"{RAILWAY_URL}/process"
print(f"Testing POST to: {process_url}")

try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('LLAMAINDEX_API_KEY', 'test-key')}"
    }
    
    test_data = {
        "file_id": "test-file",
        "supabase_file_path": "test/path",
        "name": "test.txt",
        "type": "text/plain",
        "size": 100,
        "description": "Test file",
        "user_id": "test-user"
    }
    
    response = requests.post(process_url, headers=headers, json=test_data, timeout=10)
    status = response.status_code
    
    if status == 200:
        print_success(f"Success! HTTP {status}")
    elif status in [400, 401, 403, 404]:
        print_warning(f"Expected error during testing: HTTP {status}")
    else:
        print_error(f"Unexpected status: HTTP {status}")
    
    # Try to get content type and a bit of response
    content_type = response.headers.get('Content-Type', 'unknown')
    print(f"  Content-Type: {content_type}")
    
    if 'json' in content_type:
        try:
            data = response.json()
            print(f"  Response preview: {json.dumps(data)[:100]}...")
        except:
            print(f"  Response preview: {response.text[:100]}...")
    else:
        print(f"  Response preview: {response.text[:100]}...")
        
except requests.exceptions.ConnectionError:
    print_error("CONNECTION REFUSED - Could not connect to endpoint")
    print_warning("This matches the error in your frontend logs")
except requests.exceptions.Timeout:
    print_error("TIMEOUT - Request timed out")
except Exception as e:
    print_error(f"ERROR: {str(e)}")

print("\nTEST COMPLETED")
