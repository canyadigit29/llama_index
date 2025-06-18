#!/usr/bin/env python3
"""
Service Role Authentication Test

This script tests the service role authentication method to verify if
it can properly access files in Supabase storage regardless of user permissions.
"""

import os
import sys
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Required environment variables
REQUIRED_VARS = [
    "SUPABASE_URL", 
    "SUPABASE_ANON_KEY", 
    "SUPABASE_SERVICE_ROLE_KEY"
]

# Check for required environment variables
missing_vars = [var for var in REQUIRED_VARS if not os.environ.get(var)]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in your .env file or environment")
    sys.exit(1)

# Import Supabase client
try:
    from supabase import create_client, Client
    print("✓ Supabase client library loaded successfully")
except ImportError:
    print("❌ Failed to import Supabase client. Run: pip install supabase")
    sys.exit(1)

def test_regular_auth():
    """Test storage access with regular authentication"""
    print("\n=== Testing Regular Authentication ===")
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    
    try:
        # Create regular client
        print("Creating Supabase client with anon key...")
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Regular client created")
        
        # Try to list storage buckets
        try:
            print("Listing storage buckets...")
            buckets = supabase.storage.list_buckets()
            print(f"✓ Found {len(buckets)} buckets: {[b['name'] for b in buckets]}")
            
            # Check if files bucket exists
            if any(b['name'] == 'files' for b in buckets):
                print("✓ 'files' bucket found")
                
                # Try to list files
                try:
                    files = supabase.storage.from_("files").list()
                    print(f"✓ Listed {len(files)} files in 'files' bucket")
                    if files:
                        print(f"  Sample files: {[f['name'] for f in files[:3]]}")
                except Exception as e:
                    print(f"❌ Failed to list files: {str(e)}")
            else:
                print("❌ 'files' bucket not found")
        except Exception as e:
            print(f"❌ Failed to list buckets: {str(e)}")
    except Exception as e:
        print(f"❌ Failed to create regular client: {str(e)}")

def test_service_role_auth():
    """Test storage access with service role authentication"""
    print("\n=== Testing Service Role Authentication ===")
    
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    try:
        # Create service role client
        print("Creating Supabase client with service role key...")
        service_client = create_client(supabase_url, service_role_key)
        print("✓ Service role client created")
        
        # Try to list storage buckets
        try:
            print("Listing storage buckets...")
            buckets = service_client.storage.list_buckets()
            print(f"✓ Found {len(buckets)} buckets: {[b['name'] for b in buckets]}")
            
            # Check if files bucket exists
            if any(b['name'] == 'files' for b in buckets):
                print("✓ 'files' bucket found")
                
                # Try to list files
                try:
                    files = service_client.storage.from_("files").list()
                    print(f"✓ Listed {len(files)} files in 'files' bucket")
                    if files:
                        print(f"  Sample files: {[f['name'] for f in files[:3]]}")
                        
                        # Try to download first file
                        if files:
                            first_file = files[0]['name']
                            try:
                                print(f"Trying to download file: {first_file}")
                                file_content = service_client.storage.from_("files").download(first_file)
                                file_size = len(file_content) if file_content else 0
                                print(f"✓ Successfully downloaded file ({file_size} bytes)")
                            except Exception as e:
                                print(f"❌ Failed to download file: {str(e)}")
                except Exception as e:
                    print(f"❌ Failed to list files: {str(e)}")
            else:
                print("❌ 'files' bucket not found")
        except Exception as e:
            print(f"❌ Failed to list buckets: {str(e)}")
    except Exception as e:
        print(f"❌ Failed to create service role client: {str(e)}")

def test_file_download(file_path):
    """Test downloading a specific file path with both auth methods"""
    print(f"\n=== Testing File Download: {file_path} ===")
    
    # Get credentials
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    # Test with regular auth
    print("\nRegular authentication:")
    try:
        regular_client = create_client(supabase_url, supabase_key)
        regular_content = regular_client.storage.from_("files").download(file_path)
        print(f"✓ Regular auth: Downloaded successfully ({len(regular_content)} bytes)")
    except Exception as e:
        print(f"❌ Regular auth: Download failed - {str(e)}")
    
    # Test with service role auth
    print("\nService role authentication:")
    try:
        service_client = create_client(supabase_url, service_role_key)
        service_content = service_client.storage.from_("files").download(file_path)
        print(f"✓ Service role auth: Downloaded successfully ({len(service_content)} bytes)")
    except Exception as e:
        print(f"❌ Service role auth: Download failed - {str(e)}")

if __name__ == "__main__":
    # Run tests
    test_regular_auth()
    test_service_role_auth()
    
    # Test specific file if provided
    if len(sys.argv) > 1:
        test_file_path = sys.argv[1]
        test_file_download(test_file_path)
    else:
        print("\nTo test a specific file path, run:")
        print("python service_role_test.py <file_path>")
