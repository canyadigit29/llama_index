#!/usr/bin/env python3
"""
Supabase Authentication Diagnostic Tool

This script specifically tests Supabase authentication mechanisms,
including JWT validation and Row Level Security (RLS) policies.

Usage:
    python supabase_auth_diagnostic.py

Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_ANON_KEY: Your Supabase anon/public key
    - SUPABASE_JWT_SECRET (optional): Your Supabase JWT secret for token validation
"""

import os
import sys
import json
import base64
import time
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")  
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")

print("=== Supabase Authentication Diagnostics ===")

# Check if required environment variables are set
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
    sys.exit(1)

# Try to import required libraries
try:
    from supabase import create_client, Client
    print("✓ Supabase Python client library loaded")
except ImportError:
    print("❌ Error: Could not import Supabase Python client")
    print("  Install with: pip install supabase")
    sys.exit(1)

try:
    import jwt
    print("✓ PyJWT library loaded")
    jwt_available = True
except ImportError:
    print("⚠️ Warning: PyJWT library not found. JWT validation tests will be skipped")
    print("  Install with: pip install PyJWT")
    jwt_available = False

# Initialize Supabase client
print("\n=== Connecting to Supabase ===")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✓ Connected to Supabase at {SUPABASE_URL}")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    sys.exit(1)

# Test direct API access
print("\n=== Testing Direct API Access ===")
try:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
    status = response.status_code
    print(f"✓ Direct API request status: {status} ({'Success' if status < 300 else 'Failed'})")
    if status >= 300:
        print(f"  Response body: {response.text}")
except Exception as e:
    print(f"❌ Direct API request failed: {e}")

# Test JWT functionality
if jwt_available and SUPABASE_JWT_SECRET:
    print("\n=== Testing JWT Creation and Validation ===")
    try:
        # Current time and expiry
        now = int(time.time())
        exp = now + 3600  # 1 hour from now
        
        # Create a sample JWT payload
        payload = {
            "aud": "authenticated",
            "exp": exp,
            "sub": "test-user-id",
            "email": "test@example.com",
            "role": "authenticated",
            "iat": now
        }
        
        print("1. Creating test JWT token with payload:")
        print(json.dumps(payload, indent=2))
        
        # Try to decode the JWT secret from base64
        try:
            jwt_secret_bytes = base64.b64decode(SUPABASE_JWT_SECRET)
            print("✓ Successfully decoded JWT secret from base64")
        except Exception as e:
            print(f"❌ Failed to decode JWT secret: {e}")
            print("  Trying with raw secret...")
            jwt_secret_bytes = SUPABASE_JWT_SECRET.encode()
        
        # Create a test token
        test_token = jwt.encode(payload, jwt_secret_bytes, algorithm="HS256")
        print(f"✓ Created JWT token: {test_token[:20]}...")
        
        # Attempt to validate it
        try:
            decoded = jwt.decode(
                test_token, 
                jwt_secret_bytes,
                algorithms=["HS256"],
                audience="authenticated"
            )
            print("✓ JWT verification successful")
            print("  Decoded token:")
            print(json.dumps(decoded, indent=2))
        except Exception as e:
            print(f"❌ JWT verification failed: {e}")
            print("  Common reasons for JWT verification failures:")
            print("  1. Incorrect JWT secret")
            print("  2. Secret requires base64 decoding but is provided in raw format (or vice versa)")
            print("  3. Wrong algorithm used (should be HS256)")
            print("  4. Incorrect audience")
    except Exception as e:
        print(f"❌ Error in JWT testing: {e}")
else:
    if not jwt_available:
        print("\n⚠️ Skipping JWT tests - PyJWT library not available")
    if not SUPABASE_JWT_SECRET:
        print("\n⚠️ Skipping JWT tests - SUPABASE_JWT_SECRET not provided")

# Test RLS policies
print("\n=== Testing RLS Policies ===")

# Anonymous access test
print("\n1. Testing anonymous access (should be restricted)")
try:
    # Try to access a RLS-protected table without auth
    response = supabase.table("llama_index_documents").select("*").limit(1).execute()
    print(f"  Response status: {response.status_code if hasattr(response, 'status_code') else 'Unknown'}")
    count = response.count if hasattr(response, 'count') else None
    
    if count is None or count == 0:
        print("✓ Anonymous access appears to be correctly restricted")
    else:
        print("⚠️ WARNING: Anonymous access might be allowed - received data without auth!")
        print(f"  Received {count} rows")
except Exception as e:
    if "permission denied" in str(e).lower():
        print(f"✓ Expected error for anonymous access: {e}")
    else:
        print(f"❌ Unexpected error during anonymous access test: {e}")

# Create a signed JWT for testing
print("\n2. Testing with self-signed JWT (simulating an authenticated user)")
if jwt_available and SUPABASE_JWT_SECRET:
    try:
        # Current time for token validity
        now = int(time.time())
        
        # Create a test user JWT
        payload = {
            "aud": "authenticated",
            "exp": now + 3600,  # 1 hour expiry
            "sub": "00000000-0000-0000-0000-000000000000",  # Test UUID
            "email": "test@example.com",
            "role": "authenticated",
            "user_id": "00000000-0000-0000-0000-000000000000",  # Important for RLS
            "app_metadata": {
                "provider": "email"
            },
            "user_metadata": {},
            "iat": now
        }
        
        # Sign JWT
        try:
            jwt_secret_bytes = base64.b64decode(SUPABASE_JWT_SECRET)
        except:
            jwt_secret_bytes = SUPABASE_JWT_SECRET.encode()
            
        test_token = jwt.encode(payload, jwt_secret_bytes, algorithm="HS256")
        print(f"  Created test authentication token")
        
        # Try to use the token for API access
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {test_token}",
            "Content-Type": "application/json"
        }
        
        # Attempt to query a protected table
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/llama_index_documents?limit=1", 
            headers=headers
        )
        
        if response.status_code == 200:
            print("✓ Successfully accessed data with self-signed JWT")
            data = response.json()
            print(f"  Received {len(data)} rows")
        else:
            print(f"❌ Failed to access data with self-signed JWT: {response.status_code}")
            print(f"  Error: {response.text}")
            print("  This could indicate RLS policies are not correctly configured")
            print("  or that your JWT secret is incorrect")
    except Exception as e:
        print(f"❌ Error during authenticated JWT test: {e}")
else:
    print("  Skipping JWT authentication test - missing JWT library or secret")

# Check table existence
print("\n=== Checking Required Tables ===")
tables_to_check = ["documents", "llama_index_documents"]

for table in tables_to_check:
    try:
        # Using raw HTTP request to avoid auth requirements
        response = requests.head(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={"apikey": SUPABASE_KEY}
        )
        if response.status_code < 300:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"❌ Table '{table}' not found: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking table '{table}': {e}")

# Display summary and recommendations
print("\n=== Diagnostic Summary ===")
print("Common authentication issues and solutions:")
print("1. Missing or incorrect JWT secret")
print("   - Ensure SUPABASE_JWT_SECRET is set correctly in environment")
print("   - It should be the base64-encoded secret from Supabase project settings")
print("2. Incorrect RLS policies")
print("   - Check your Row Level Security policies in Supabase dashboard")
print("   - Make sure policies exist for 'llama_index_documents' table")
print("3. Using wrong Supabase key")
print("   - Ensure you're using the anon/public key for SUPABASE_ANON_KEY")
print("   - Different keys have different permissions")
print("4. Network/firewall issues")
print("   - Ensure your deployment environment can reach Supabase")
print("")
print("Follow up steps:")
print("1. Check RLS policies in Supabase dashboard")
print("2. Verify JWT settings and authentication flow")
print("3. Run the main app with logging enabled to see actual auth token usage")
