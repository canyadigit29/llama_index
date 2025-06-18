#!/usr/bin/env python3
"""
Environment Variable Debug Script

This script checks critical environment variables needed for the application
to function properly and verifies their values are set correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Critical environment variables to check
ENV_VARS = [
    # Supabase
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    
    # OpenAI
    "OPENAI_API_KEY",
    
    # Pinecone
    "PINECONE_API_KEY",
    "PINECONE_ENVIRONMENT",
    "PINECONE_INDEX_NAME",
    
    # LlamaIndex API key
    "LLAMAINDEX_API_KEY"
]

print("=== Environment Variable Diagnostic ===")

# Check all environment variables
for var in ENV_VARS:
    value = os.environ.get(var)
    if not value:
        print(f"❌ Missing: {var}")
    else:
        # For sensitive values, just show a few chars
        masked = value[:4] + "..." + value[-4:] if len(value) > 12 else "[SET]"
        print(f"✅ {var}: {masked}")

# Check if API key matches
llamaindex_api_key = os.environ.get("LLAMAINDEX_API_KEY")
if not llamaindex_api_key:
    print("\n❌ LLAMAINDEX_API_KEY is not set! This is required for API authentication.")
else:
    print("\n✓ LLAMAINDEX_API_KEY is set")
    # The expected value from the screenshot provided is:
    expected = "vNEhARgFnx39THmoe4ykJBLa5Gw8P7C0"
    if llamaindex_api_key == expected:
        print("✓ LLAMAINDEX_API_KEY matches the expected value from Vercel")
    else:
        print("❌ LLAMAINDEX_API_KEY does NOT match the expected value from Vercel!")
        print("  This will cause authentication failures between frontend and backend.")

# Check TLS/HTTPS settings
https_proxy = os.environ.get("HTTPS_PROXY")
if https_proxy:
    print(f"\nℹ️ HTTPS_PROXY is set to: {https_proxy}")
    print("  This might affect connections to external services")

print("\n=== Supabase Connection Test ===")
# Try to import and test Supabase connection
try:
    from supabase import create_client, Client
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY") 
    
    if supabase_url and supabase_key:
        print("Attempting to connect to Supabase...")
        supabase = create_client(supabase_url, supabase_key)
        print("✓ Supabase client created")
        
        # Try a simple query to test connection
        try:
            response = supabase.table("files").select("count", count="exact").limit(1).execute()
            file_count = response.count if hasattr(response, 'count') else "unknown"
            print(f"✓ Successfully queried Supabase 'files' table. Count: {file_count}")
        except Exception as query_err:
            print(f"❌ Error querying files table: {str(query_err)}")
    else:
        print("❌ Cannot test Supabase connection due to missing credentials")
except ImportError:
    print("❌ Supabase library not installed")
except Exception as e:
    print(f"❌ Error testing Supabase connection: {str(e)}")

print("\nDiagnostic complete.")
