#!/usr/bin/env python3
"""
End-to-End Integration Test Script for LlamaIndex + Chatbot-UI + Supabase

This script tests the full workflow from file upload to search:
1. Creates a simple test file
2. Uploads it to Supabase storage
3. Triggers processing in the LlamaIndex backend
4. Verifies the file can be searched
"""

import os
import sys
import requests
import json
import time
import tempfile
import uuid
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

# ANSI colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== {text} ==={Colors.RESET}")
    
def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")
    
def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.RESET}")

def print_step(step_num, description):
    print(f"\n{Colors.BOLD}[STEP {step_num}] {description}{Colors.RESET}")

# Get configuration from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
BACKEND_URL = os.environ.get("LLAMAINDEX_URL", "http://localhost:8000")
API_KEY = os.environ.get("LLAMAINDEX_API_KEY")

# Verify configuration
missing_vars = []
for var_name, var_value in [
    ("SUPABASE_URL", SUPABASE_URL),
    ("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY), 
    ("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_KEY),
    ("LLAMAINDEX_URL", BACKEND_URL),
    ("LLAMAINDEX_API_KEY", API_KEY)
]:
    if not var_value:
        missing_vars.append(var_name)

if missing_vars:
    print_error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Import Supabase client library
try:
    from supabase import create_client, Client
except ImportError:
    print_error("Supabase client library not installed. Please run: pip install supabase")
    print("You can also install all requirements with: pip install -r requirements.txt")
    sys.exit(1)

def create_test_file(content="This is a test document for LlamaIndex integration testing."):
    """Create a simple test text file"""
    print_step(1, "Creating test file")
    try:
        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as temp:
            temp.write(content)
            temp_path = temp.name
            print_success(f"Created test file at: {temp_path}")
        return temp_path
    except Exception as e:
        print_error(f"Failed to create test file: {str(e)}")
        sys.exit(1)

def upload_to_supabase(file_path):
    """Upload file to Supabase storage"""
    print_step(2, "Uploading to Supabase storage")
    
    try:
        # Create Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        user_id = "test-user"  # In production this would be a real user ID
        
        # Construct storage path
        storage_path = f"{user_id}/{file_id}"
        
        # Open and upload the file
        with open(file_path, "rb") as f:
            file_contents = f.read()
            
            result = supabase.storage.from_("files").upload(
                path=storage_path,
                file=file_contents,
                file_options={"content-type": "text/plain"}
            )
            
            print_success(f"File uploaded to Supabase storage: {storage_path}")
            return file_id, user_id, storage_path
            
    except Exception as e:
        print_error(f"Failed to upload to Supabase: {str(e)}")
        return None, None, None

def process_in_backend(file_id, user_id):
    """Trigger file processing in LlamaIndex backend"""
    print_step(3, "Triggering backend processing")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare request data
    data = {
        "file_id": file_id,
        "user_id": user_id
    }
    
    try:
        # Send request to process endpoint
        process_url = f"{BACKEND_URL}/process"
        print(f"Sending request to: {process_url}")
        response = requests.post(
            process_url,
            headers=headers,
            json=data,
            timeout=60  # Allow up to 60 seconds for processing
        )
        
        # Check response
        if response.status_code == 200:
            print_success(f"Backend processing successful: {response.status_code}")
            return True
        else:
            print_error(f"Backend processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error during backend processing: {str(e)}")
        return False

def verify_search(query="test document"):
    """Verify search functionality"""
    print_step(4, "Testing search functionality")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare search data
    data = {
        "query": query
    }
    
    try:
        # Send search request
        search_url = f"{BACKEND_URL}/search"
        print(f"Sending search request: '{query}'")
        response = requests.post(
            search_url,
            headers=headers,
            json=data
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print_success(f"Search successful: {response.status_code}")
            print(json.dumps(result, indent=2))
            return True
        else:
            print_error(f"Search failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error during search: {str(e)}")
        return False

def cleanup(file_path, storage_path=None):
    """Clean up test resources"""
    print_step(5, "Cleaning up test resources")
    
    # Delete local file
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            print_success(f"Deleted local test file: {file_path}")
    except Exception as e:
        print_warning(f"Failed to delete local file: {str(e)}")
    
    # Delete from storage if needed
    if storage_path and SUPABASE_SERVICE_KEY:
        try:
            service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            service_client.storage.from_("files").remove([storage_path])
            print_success(f"Deleted file from storage: {storage_path}")
        except Exception as e:
            print_warning(f"Failed to delete storage file: {str(e)}")

def run_full_test():
    """Run the complete end-to-end test"""
    print_header("LLAMA INDEX + CHATBOT-UI + SUPABASE INTEGRATION TEST")
    
    file_path = create_test_file()
    file_id, user_id, storage_path = upload_to_supabase(file_path)
    
    if not file_id:
        print_error("Test failed: Could not upload file to Supabase")
        cleanup(file_path)
        return False
    
    # Wait briefly to ensure storage propagation
    print("Waiting 3 seconds for storage propagation...")
    time.sleep(3)
    
    processing_ok = process_in_backend(file_id, user_id)
    
    if not processing_ok:
        print_error("Test failed: Backend processing failed")
        cleanup(file_path, storage_path)
        return False
    
    # Wait for processing to complete
    print("Waiting 10 seconds for processing to complete...")
    time.sleep(10)
    
    search_ok = verify_search()
    
    # Clean up
    cleanup(file_path, storage_path)
    
    # Final status
    if processing_ok and search_ok:
        print_header("END-TO-END TEST SUCCESSFUL")
        return True
    else:
        print_header("END-TO-END TEST FAILED")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run end-to-end integration test")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip cleanup step")
    args = parser.parse_args()
    
    if args.skip_cleanup:
        print_warning("Cleanup step will be skipped")
    
    success = run_full_test()
    sys.exit(0 if success else 1)
