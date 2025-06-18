#!/usr/bin/env python3
"""
Railway Application Health Check

This script provides a comprehensive health check for the Railway-hosted
LlamaIndex backend application, checking all required services and connectivity.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️ {text}{Colors.ENDC}")

# Check if the application is running locally or we need to check the remote URL
LLAMAINDEX_URL = os.environ.get("LLAMAINDEX_URL", "https://llamaindex-production-633d.up.railway.app")
LLAMAINDEX_API_KEY = os.environ.get("LLAMAINDEX_API_KEY")

if not LLAMAINDEX_API_KEY:
    print_warning("LLAMAINDEX_API_KEY not set. Authentication tests will be skipped.")
    LLAMAINDEX_API_KEY = "missing-api-key"

print_header("RAILWAY APPLICATION HEALTH CHECK")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Target URL: {LLAMAINDEX_URL}")
print("")

# Check if Railway service is up
print_header("CHECKING BASIC CONNECTIVITY")
try:
    response = requests.get(f"{LLAMAINDEX_URL}/health", timeout=10)
    if response.status_code == 200:
        print_success(f"Service is UP (HTTP {response.status_code})")
        try:
            health_data = response.json()
            print_info(f"Health details: {json.dumps(health_data, indent=2)}")
        except:
            print_warning("Could not parse health response as JSON")
    else:
        print_error(f"Service returned non-200 status: HTTP {response.status_code}")
        print_info(f"Response: {response.text[:200]}...")
except requests.exceptions.ConnectionError:
    print_error("CONNECTION REFUSED - Railway service is not running or not accessible")
    print_warning("This matches the error in your logs - the service is not running or not accessible")
    print_info("Possible causes:")
    print_info("1. Railway service is down or crashed")
    print_info("2. Railway configuration is incorrect")
    print_info("3. Network connectivity issues between Vercel and Railway")
except requests.exceptions.Timeout:
    print_error("Connection timed out - Railway service is slow or unresponsive")
except Exception as e:
    print_error(f"Error connecting to service: {str(e)}")

# Check API key authentication
print_header("CHECKING API AUTHENTICATION")
try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLAMAINDEX_API_KEY}"
    }
    response = requests.get(f"{LLAMAINDEX_URL}/health", headers=headers, timeout=10)
    if response.status_code == 200:
        print_success("API key authentication successful")
    else:
        print_error(f"API key authentication failed: HTTP {response.status_code}")
        print_info(f"Response: {response.text[:200]}...")
except Exception as e:
    print_error(f"Error during API key test: {str(e)}")

# Check debug endpoint
print_header("CHECKING DEBUG ENDPOINT")
try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLAMAINDEX_API_KEY}"
    }
    response = requests.get(f"{LLAMAINDEX_URL}/debug/supabase", headers=headers, timeout=15)
    if response.status_code == 200:
        print_success("Debug endpoint accessible")
        try:
            debug_data = response.json()
            print_info(f"Debug summary:")
            print_info(f"- Supabase client: {'Available' if debug_data.get('supabase_client_exists') else 'Not available'}")
            print_info(f"- Auth header: {'Present' if debug_data.get('auth_header_present') else 'Missing'}")
            print_info(f"- Token: {'Present' if debug_data.get('token_present') else 'Missing'}")
            
            env_vars = debug_data.get('environment_variables', {})
            for key, value in env_vars.items():
                print_info(f"- {key}: {value}")
                
            if 'storage_list' in debug_data:
                storage = debug_data.get('storage_list', {})
                if storage.get('status') == 'Success':
                    print_success(f"Storage accessible: {storage.get('count')} files found")
                    if storage.get('examples'):
                        print_info(f"Example files: {', '.join(storage['examples'])}")
                else:
                    print_error(f"Storage access failed: {storage.get('status')}")
        except:
            print_warning("Could not parse debug response as JSON")
    else:
        print_error(f"Debug endpoint returned non-200 status: HTTP {response.status_code}")
        print_info(f"Response: {response.text[:200]}...")
except Exception as e:
    print_error(f"Error accessing debug endpoint: {str(e)}")

# Check file processing endpoint with a mock test
print_header("SIMULATING FILE PROCESSING REQUEST")
try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLAMAINDEX_API_KEY}"
    }
    test_data = {
        "file_id": "test-file-id-123",
        "supabase_file_path": "test-user/test-file-id-123",
        "name": "test-file.txt",
        "type": "text/plain",
        "size": 1000,
        "description": "Test file for diagnostics",
        "user_id": "test-user"
    }
    
    print_info("Sending test file processing request...")
    response = requests.post(
        f"{LLAMAINDEX_URL}/process", 
        headers=headers,
        json=test_data,
        timeout=20
    )
    
    if response.status_code == 200:
        print_success("Test request processed successfully")
        print_info(f"Response: {response.json()}")
    elif response.status_code == 404:
        print_error("File not found (expected for test file)")
        print_info(f"Response: {response.text[:200]}...")
    else:
        print_error(f"Test request failed: HTTP {response.status_code}")
        print_info(f"Response: {response.text[:200]}...")
except requests.exceptions.ConnectionError:
    print_error("CONNECTION REFUSED - Cannot connect to process endpoint")
except requests.exceptions.Timeout:
    print_error("Request timed out - Processing endpoint is slow or unresponsive")
except Exception as e:
    print_error(f"Error testing process endpoint: {str(e)}")

print_header("RAILWAY STATUS SUMMARY")

print_info("Based on the diagnostics, your issue appears to be:")
print_error("The Railway service is not running or has crashed.")
print_info("Recommendations:")
print_info("1. Check Railway dashboard for service status")
print_info("2. Check Railway logs for application crashes")
print_info("3. Verify that all environment variables are set correctly in Railway")
print_info("4. Restart the Railway service")
print_info("5. Check that the service role key is set: SUPABASE_SERVICE_ROLE_KEY")

print("")
print("To run this script with your local environment variables:")
print("python railway_health_check.py")
