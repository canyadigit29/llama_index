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
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ All required Pinecone environment variables are set")
        return True

def validate_pinecone_connection():
    """Validate connection to Pinecone."""
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    
    if not api_key or not environment:
        print("❌ Cannot validate Pinecone connection: Missing API key or environment")
        return False
    
    try:
        # First try to import
        try:
            import pinecone
            print("✅ Successfully imported pinecone module")
        except ImportError as e:
            print(f"❌ Failed to import pinecone module: {str(e)}")
            print("Please ensure pinecone-client is installed: pip install pinecone-client>=3.0.0")
            return False
        
        # Try new Pinecone API (v3+)
        try:
            if hasattr(pinecone, "Pinecone"):
                print("Detected modern Pinecone API (v3+)")
                pc = pinecone.Pinecone(api_key=api_key)
                
                # Get list of indexes
                indexes = pc.list_indexes().names()
                print(f"Available indexes: {indexes}")
                
                if index_name in indexes:
                    # Validate index access
                    index = pc.Index(index_name)
                    # Get stats to validate connection
                    stats = index.describe_index_stats()
                    print(f"Index stats: {stats}")
                    print("✅ Successfully connected to Pinecone index")
                    return True
                else:
                    print(f"❌ Index '{index_name}' not found in your Pinecone account.")
                    print("Available indexes:")
                    for idx in indexes:
                        print(f"  - {idx}")
                    return False
            else:
                # Legacy API
                print("Detected legacy Pinecone API (<v3)")
                # Initialize legacy API
                pinecone.init(api_key=api_key, environment=environment)
                
                # Get list of indexes
                indexes = pinecone.list_indexes()
                print(f"Available indexes: {indexes}")
                
                if index_name in indexes:
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
            print(f"❌ Error connecting to Pinecone: {str(e)}")
            return False
        
        # Try alternate/legacy API
        try:
            if not hasattr(pinecone, "Pinecone"):
                # Initialize legacy API
                pinecone.init(api_key=api_key, environment=environment)
                
                # Get list of indexes
                indexes = pinecone.list_indexes()
                print(f"Available indexes: {indexes}")
                
                if index_name in indexes:
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
