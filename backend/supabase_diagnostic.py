#!/usr/bin/env python3
"""
Supabase Diagnostic Tool

This script tests your Supabase connection and authentication.
It verifies:
1. Connection to Supabase using the provided credentials
2. JWT validation capability
3. Access to necessary tables and storage buckets

Usage:
    python supabase_diagnostic.py

Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_ANON_KEY: Your Supabase anon/public key
    - SUPABASE_JWT_SECRET (optional): Your Supabase JWT secret for token validation
"""

import os
import sys
import json
import base64
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Attempt to import supabase and related libraries with version info
try:
    from supabase import create_client, Client
    import pkg_resources
    supabase_version = pkg_resources.get_distribution("supabase").version
    print(f"✓ Supabase Python client installed (version {supabase_version})")
except ImportError as e:
    print(f"✗ Error importing Supabase: {e}")
    print("  Try installing with: pip install supabase")
    sys.exit(1)

# Try to import JWT libraries for token verification
try:
    import jwt
    jwt_available = True
    print("✓ JWT library available for token verification")
except ImportError:
    jwt_available = False
    print("✗ JWT library not available - install with: pip install pyjwt")

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")  
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")

# Display environment status
print("\n=== Environment Variables ===")
print(f"SUPABASE_URL: {'✓ Set' if SUPABASE_URL else '✗ Missing'}")
print(f"SUPABASE_ANON_KEY: {'✓ Set' if SUPABASE_KEY else '✗ Missing'}")
print(f"SUPABASE_JWT_SECRET: {'✓ Set' if SUPABASE_JWT_SECRET else '⚠ Not set (needed for JWT verification)'}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Missing required environment variables. Please set them and try again.")
    sys.exit(1)

# Initialize Supabase client
print("\n=== Testing Supabase Connection ===")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Supabase client: {e}")
    
    # Try alternative initialization format in case of version differences
    try:
        print("  Attempting alternative initialization...")
        supabase = create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
        print("✓ Supabase client initialized successfully with alternative format")
    except Exception as alt_e:
        print(f"✗ Alternative initialization also failed: {alt_e}")
        sys.exit(1)

# Test table access
print("\n=== Testing Database Access ===")
tables_to_test = ["documents", "llama_index_documents"]
for table in tables_to_test:
    try:
        response = supabase.table(table).select("count", count="exact").limit(1).execute()
        count = response.count if hasattr(response, 'count') else "unknown"
        print(f"✓ '{table}' table accessible (count: {count})")
    except Exception as e:
        print(f"✗ Error accessing '{table}' table: {e}")

# Test storage access
print("\n=== Testing Storage Access ===")
try:
    buckets = supabase.storage.list_buckets()
    print(f"✓ Storage buckets retrieved: {', '.join([b['name'] for b in buckets]) if buckets else 'No buckets found'}")
    
    # Test documents bucket specifically
    try:
        files = supabase.storage.from_("documents").list()
        print(f"✓ 'documents' bucket accessible ({len(files)} files found)")
    except Exception as e:
        print(f"✗ Error accessing 'documents' bucket: {e}")
except Exception as e:
    print(f"✗ Error accessing storage: {e}")

# Test JWT functionality if available
if jwt_available and SUPABASE_JWT_SECRET:
    print("\n=== Testing JWT Verification ===")
    # Create a sample JWT for testing
    try:
        # Create a test payload
        payload = {
            "aud": "authenticated",
            "exp": 1999999999,  # Far in the future
            "sub": "test-user-id",
            "email": "test@example.com",
            "role": "authenticated"
        }
        
        # JWT validation requires the secret in base64 
        jwt_secret_bytes = base64.b64decode(SUPABASE_JWT_SECRET)
        
        # Create a test token
        test_token = jwt.encode(payload, jwt_secret_bytes, algorithm="HS256")
        print("✓ Created test JWT token")
        
        # Attempt to validate it
        try:
            decoded = jwt.decode(
                test_token, 
                jwt_secret_bytes,
                algorithms=["HS256"],
                audience="authenticated"
            )
            print("✓ JWT verification successful")
        except Exception as e:
            print(f"✗ JWT verification failed: {e}")
    except Exception as e:
        print(f"✗ Error creating/testing JWT: {e}")
else:
    print("\n⚠ Skipping JWT verification test (missing library or secret)")

# Connection test using direct HTTP request
print("\n=== Testing Direct API Access ===")
try:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    response = requests.get(f"{SUPABASE_URL}/rest/v1/documents?limit=1", headers=headers)
    status = response.status_code
    print(f"✓ Direct API request status: {status} ({'Success' if status < 300 else 'Failed'})")
except Exception as e:
    print(f"✗ Direct API request failed: {e}")

print("\n=== Diagnostic Summary ===")
print("If you see any failures above, address them before continuing.")
print("Common issues:")
print("1. Incorrect environment variables")
print("2. Network connectivity to Supabase (check firewall rules)")
print("3. Missing or incorrectly set up tables/buckets")
print("4. JWT secret not properly configured")
print("5. Permissions issues (check RLS policies)")
