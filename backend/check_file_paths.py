#!/usr/bin/env python3
"""
File Storage Path Diagnostic Script

This script checks the structure of file paths in the Supabase storage 
and compares them with the paths stored in the files table to identify 
any inconsistencies.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import required libraries
try:
    from supabase import create_client, Client
    print("✓ Supabase client library loaded successfully")
except ImportError:
    print("✗ Error importing Supabase client. Please install with 'pip install supabase'")
    sys.exit(1)

# Get Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("✗ Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
    sys.exit(1)

print(f"Connecting to Supabase at {SUPABASE_URL}...")

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Connected to Supabase successfully")
except Exception as e:
    print(f"✗ Error connecting to Supabase: {str(e)}")
    sys.exit(1)

# Check storage buckets
try:
    buckets = supabase.storage.list_buckets()
    print(f"✓ Found {len(buckets)} storage buckets:")
    for bucket in buckets:
        print(f"  - {bucket['name']}")
    
    # Check if 'files' bucket exists
    if not any(b['name'] == 'files' for b in buckets):
        print("✗ ERROR: 'files' bucket not found!")
        print("  Create it with this SQL in Supabase SQL Editor:")
        print("  INSERT INTO storage.buckets (id, name, public) VALUES ('files', 'files', false);")
        sys.exit(1)
    else:
        print("✓ 'files' bucket exists")
except Exception as e:
    print(f"✗ Error accessing storage buckets: {str(e)}")
    sys.exit(1)

# List files in the storage bucket
try:
    files_in_storage = supabase.storage.from_("files").list()
    print(f"✓ Found {len(files_in_storage)} files in storage bucket")
    
    # Show some examples
    if files_in_storage:
        print("  Sample files in storage:")
        for f in files_in_storage[:5]:
            print(f"  - {f['name']}")
        if len(files_in_storage) > 5:
            print(f"  ... and {len(files_in_storage) - 5} more")
except Exception as e:
    print(f"✗ Error listing files in storage: {str(e)}")
    sys.exit(1)

# Check files in the database table
try:
    response = supabase.table("files").select("*").execute()
    files_in_db = response.data
    print(f"✓ Found {len(files_in_db)} files in database table")
    
    # Show some examples
    if files_in_db:
        print("  Sample files in database:")
        for f in files_in_db[:5]:
            print(f"  - ID: {f['id']}, Path: {f['file_path']}, Name: {f['name']}")
        if len(files_in_db) > 5:
            print(f"  ... and {len(files_in_db) - 5} more")
except Exception as e:
    print(f"✗ Error querying files table: {str(e)}")
    sys.exit(1)

# Compare paths to check for inconsistencies
print("\n=== Analyzing file path formats ===")
if files_in_db and files_in_storage:
    # Extract path formats from storage
    storage_paths = [f['name'] for f in files_in_storage]
    db_paths = [f['file_path'] for f in files_in_db]
    
    # Check if any storage paths match the pattern "user_id/file_id"
    storage_with_userid = [p for p in storage_paths if '/' in p]
    print(f"Storage paths with user_id prefix format: {len(storage_with_userid)}/{len(storage_paths)}")
    
    # Check if DB paths match storage paths
    found_in_storage = 0
    for db_path in db_paths[:10]:  # Check first 10 for performance
        if db_path in storage_paths:
            found_in_storage += 1
    
    if found_in_storage == 0 and len(db_paths) > 0:
        print("⚠️ WARNING: None of the paths in the database match paths in storage!")
        print("This indicates a path format mismatch between database and storage.")
        
        # Try to verify if pattern is user_id/file_id
        for f in files_in_db[:5]:
            potential_path = f"{f.get('user_id')}/{f['id']}"
            if potential_path in storage_paths:
                print(f"✓ Found match with pattern 'user_id/file_id' for file {f['id']}")
            else:
                print(f"✗ No match with pattern 'user_id/file_id' for file {f['id']}")
    
    print("\nExample paths comparison:")
    if files_in_db and files_in_storage:
        db_path = files_in_db[0]['file_path']
        db_id = files_in_db[0]['id']
        user_id = files_in_db[0].get('user_id', 'unknown')
        
        print(f"Database file: ID={db_id}, path={db_path}")
        print(f"Alternative path to try: {user_id}/{db_id}")
    
    # Provide recommendations
    print("\n=== Recommendations ===")
    print("1. Check if the file_path in the database is the same format used in storage")
    print("2. Common path format is 'user_id/file_id' in the 'files' bucket")
    print("3. When downloading files, you may need to construct the correct path")
    print("4. Add more logging to your backend to see the exact paths being used")

print("\nDiagnostic complete. Use this information to update your backend code accordingly.")
