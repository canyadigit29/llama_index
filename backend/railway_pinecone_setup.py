#!/usr/bin/env python3
"""
Railway Pinecone Setup Utility

This script validates and configures the Pinecone connection for Railway deployment.
Run this script before starting the main application to ensure Pinecone is properly configured.
"""

import os
import sys

def check_pinecone_env_vars():
    """Check required Pinecone environment variables."""
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    
    issues = []
    if not api_key:
        issues.append("PINECONE_API_KEY is not set")
    if not environment:
        issues.append("PINECONE_ENVIRONMENT is not set")
    
    print(f"Pinecone Configuration:")
    print(f"- API Key: {'Set (not shown for security)' if api_key else 'NOT SET'}")
    print(f"- Environment: {environment or 'NOT SET'}")
    print(f"- Index Name: {index_name}")
    
    if issues:
        print("\n⚠️ Issues found:")
        for issue in issues:
            print(f"- {issue}")
        return False
    
    print("\n✅ Pinecone environment variables are properly set")
    return True

def validate_pinecone_connection():
    """Test connection to Pinecone."""
    try:
        # Try importing pinecone
        try:
            import pinecone
            print("✅ Pinecone module is installed")
        except ImportError:
            print("❌ Failed to import pinecone module")
            print("Make sure pinecone-client is installed: pip install pinecone-client>=3.0.0")
            return False
            
        # Check for both modern and legacy API
        api_key = os.environ.get("PINECONE_API_KEY")
        environment = os.environ.get("PINECONE_ENVIRONMENT")
        index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        
        # Try modern API first
        if hasattr(pinecone, "Pinecone"):
            print("Using modern Pinecone API (v3+)...")
            try:
                pc = pinecone.Pinecone(api_key=api_key)
                indexes = pc.list_indexes().names()
                print(f"Available indexes: {indexes}")
                
                if index_name in indexes:
                    print(f"✅ Index '{index_name}' exists")
                    # Validate index access
                    index = pc.Index(index_name)
                    # Just get stats to validate connection
                    stats = index.describe_index_stats()
                    print(f"Index stats: {stats}")
                    print("✅ Successfully connected to Pinecone index")
                    return True
                else:
                    print(f"❌ Index '{index_name}' not found in your Pinecone account")
                    print("Please create this index in the Pinecone console or specify an existing index")
                    return False
            except Exception as e:
                print(f"❌ Error connecting to Pinecone (modern API): {str(e)}")
                print("Trying legacy API...")
        else:
            print("Modern Pinecone API not available, using legacy API...")
            
        # Try legacy API
        try:
            pinecone.init(api_key=api_key, environment=environment)
            indexes = pinecone.list_indexes()
            print(f"Available indexes (legacy API): {indexes}")
            
            if index_name in indexes:
                print(f"✅ Index '{index_name}' exists (legacy API)")
                # Validate index access
                index = pinecone.Index(index_name)
                # Get stats to validate connection
                stats = index.describe_index_stats()
                print(f"Index stats: {stats}")
                print("✅ Successfully connected to Pinecone index (legacy API)")
                return True
            else:
                print(f"❌ Index '{index_name}' not found in your Pinecone account (legacy API)")
                return False
        except Exception as e:
            print(f"❌ Error connecting to Pinecone (legacy API): {str(e)}")
            return False
    
    except Exception as e:
        print(f"❌ Unexpected error during Pinecone validation: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("RAILWAY PINECONE SETUP UTILITY")
    print("=" * 60)
    
    env_ok = check_pinecone_env_vars()
    if not env_ok:
        print("\n⚠️ Please set the required Pinecone environment variables in Railway")
        # Don't exit - just inform
    
    conn_ok = validate_pinecone_connection()
    if not conn_ok:
        print("\n⚠️ Pinecone connection validation failed")
        # Don't exit - just inform
    
    if env_ok and conn_ok:
        print("\n✅ Pinecone is correctly configured for Railway")
    else:
        print("\n⚠️ Please fix Pinecone configuration issues before deploying to Railway")
    
    print("=" * 60)
