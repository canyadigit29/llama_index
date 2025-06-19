#!/usr/bin/env python
"""
Railway Health Check Debugger
This script makes a direct request to the health endpoint and prints detailed information
about the response to help diagnose deployment issues.
"""

import os
import sys
import time
import json
import traceback
import requests
from datetime import datetime

# Configuration
PORT = os.environ.get("PORT", 8000)
HEALTH_URL = f"http://localhost:{PORT}/health"
RETRIES = 5
RETRY_DELAY = 2  # seconds

def main():
    """
    Main function to check health endpoint and print debug information.
    """
    print(f"[{datetime.now().isoformat()}] RAILWAY HEALTHCHECK DEBUGGER")
    print(f"Testing health endpoint: {HEALTH_URL}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Contents of current directory: {os.listdir('.')}")
    
    # Environment information
    print("\nENVIRONMENT INFORMATION:")
    for key in ['PORT', 'RAILWAY_SERVICE_ID', 'RAILWAY_ENVIRONMENT_NAME', 
               'RAILWAY_SERVICE_NAME', 'PINECONE_API_KEY', 'SUPABASE_URL']:
        value = os.environ.get(key, 'Not set')
        if key.endswith('_KEY') and value != 'Not set':
            value = f"{value[0:4]}...{value[-4:]}" if len(value) > 8 else "[Set]"
        print(f"  {key}: {value}")
    
    success = False
    status_code = None
    response_text = None
    
    for attempt in range(RETRIES):
        try:
            print(f"\nAttempt {attempt+1}/{RETRIES}...")
            response = requests.get(HEALTH_URL, timeout=10)
            status_code = response.status_code
            response_text = response.text
            
            print(f"Status code: {status_code}")
            print(f"Headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Try to parse response as JSON
            try:
                json_response = response.json()
                print(f"Response (JSON): {json.dumps(json_response, indent=2)}")
            except:
                print(f"Response (text): {response_text[:500]}...")
            
            # Check if status code is 200
            if status_code == 200:
                success = True
                print("\n✅ HEALTH CHECK PASSED! Status code 200 received.")
                break
            else:
                print(f"\n⚠️ Status code {status_code} received. Health check did not pass.")
        
        except requests.RequestException as e:
            print(f"\n❌ REQUEST ERROR: {e}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Stack trace: {traceback.format_exc()}")
            
        except Exception as e:
            print(f"\n❌ GENERAL ERROR: {e}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Stack trace: {traceback.format_exc()}")
        
        # Wait before retrying
        if attempt < RETRIES - 1:
            print(f"Waiting {RETRY_DELAY} seconds before next attempt...")
            time.sleep(RETRY_DELAY)
    
    # Final verdict
    if success:
        print("\n✅ HEALTH CHECK DEBUGGER: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ HEALTH CHECK DEBUGGER: FAILED")
        print(f"  Status code: {status_code}")
        print(f"  Response: {response_text[:100]}..." if response_text else "No response")
        sys.exit(1)

if __name__ == "__main__":
    main()
