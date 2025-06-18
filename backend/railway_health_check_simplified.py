#!/usr/bin/env python3
"""
Railway Health Check Script for LlamaIndex API

This script performs a simple health check against either a
local or deployed LlamaIndex API to verify it's working correctly.
"""

import requests
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define endpoints to check
ENDPOINT_ROOT = "/"
ENDPOINT_HEALTH = "/health"
ENDPOINT_DEBUG = "/debug"

# Get target URL from environment or use default
LLAMAINDEX_URL = os.environ.get("LLAMAINDEX_URL", "https://llamaindex-production-633d.up.railway.app")

# Port to check if testing locally
DEFAULT_PORT = 8000
LOCAL_PORT = int(os.environ.get("PORT", DEFAULT_PORT))

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️ {message}{Colors.RESET}")

def check_endpoint(url, endpoint, expected_status=200):
    """Check if an endpoint is available and returning the expected status code"""
    full_url = f"{url}{endpoint}"
    print_info(f"Checking {full_url}...")
    
    try:
        response = requests.get(full_url, timeout=10)
        
        if response.status_code == expected_status:
            print_success(f"{endpoint} returned status {response.status_code} as expected")
            try:
                data = response.json()
                print_info("Response data:")
                print(json.dumps(data, indent=2))
                return True
            except:
                print_warning("Response was not valid JSON")
        else:
            print_error(f"{endpoint} returned status {response.status_code}, expected {expected_status}")
            print_info(f"Response text: {response.text[:200]}...")
            return False
    except Exception as e:
        print_error(f"Failed to connect to {endpoint}: {str(e)}")
        return False

def main():
    """Run health checks on the LlamaIndex API"""
    print(f"{Colors.BOLD}LlamaIndex Railway Health Check{Colors.RESET}")
    print(f"Target URL: {LLAMAINDEX_URL}")
    
    # Check if we should test locally
    if os.environ.get("CHECK_LOCAL", "").lower() in ("true", "1", "yes"):
        local_url = f"http://localhost:{LOCAL_PORT}"
        print_info(f"Testing local deployment at {local_url}")
        
        # Check basic endpoints locally
        root_ok = check_endpoint(local_url, ENDPOINT_ROOT)
        health_ok = check_endpoint(local_url, ENDPOINT_HEALTH)
        debug_ok = check_endpoint(local_url, ENDPOINT_DEBUG)
        
        # Summarize local results
        if root_ok and health_ok:
            print_success("Local health check PASSED")
            return 0
        else:
            print_error("Local health check FAILED")
            return 1
    
    # Otherwise test remote deployment
    root_ok = check_endpoint(LLAMAINDEX_URL, ENDPOINT_ROOT)
    health_ok = check_endpoint(LLAMAINDEX_URL, ENDPOINT_HEALTH)
    
    # Only check debug if others passed (to avoid overwhelming with error messages)
    debug_ok = False
    if root_ok and health_ok:
        debug_ok = check_endpoint(LLAMAINDEX_URL, ENDPOINT_DEBUG)
    
    # Summarize results
    if root_ok and health_ok:
        print_success(f"Railway deployment health check PASSED")
        return 0
    else:
        print_error(f"Railway deployment health check FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
