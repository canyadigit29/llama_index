"""
Pinecone Connection Test for Railway

This script tests the Pinecone connection during Railway deployment.
It will run automatically as part of the deployment process.
"""

import os
import sys

print("=" * 80)
print("RAILWAY PINECONE CONNECTION TEST")
print("=" * 80)

# Check environment variables
print("\nEnvironment variables:")
print(f"PINECONE_API_KEY: {'SET' if os.environ.get('PINECONE_API_KEY') else 'NOT SET'}")
print(f"PINECONE_ENVIRONMENT: {os.environ.get('PINECONE_ENVIRONMENT', 'NOT SET')}")
print(f"PINECONE_INDEX_NAME: {os.environ.get('PINECONE_INDEX_NAME', 'developer-quickstart-py')}")
print(f"OPENAI_API_KEY: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")

# Try to import Pinecone
try:
    import pinecone
    print(f"\nPinecone version: {getattr(pinecone, '__version__', 'unknown')}")
    print(f"Has modern API: {hasattr(pinecone, 'Pinecone')}")
except ImportError:
    print("\nFailed to import pinecone. Is it installed?")
    sys.exit(1)

# Try modern API first
if hasattr(pinecone, "Pinecone"):
    print("\nTesting modern Pinecone API...")
    try:
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            print("PINECONE_API_KEY environment variable is not set")
            sys.exit(1)
            
        index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        
        print(f"Connecting to Pinecone with API key: {api_key[:4]}...{api_key[-4:]} (masked)")
        pc = pinecone.Pinecone(api_key=api_key)
        print("Successfully created Pinecone client")
        
        print("Listing available indexes...")
        try:
            indexes = pc.list_indexes().names()
            print(f"Available indexes: {indexes}")
            
            if index_name not in indexes:
                print(f"WARNING: Index '{index_name}' not found in available indexes")
                print("Please create the index in the Pinecone console first")
        except Exception as e:
            print(f"Error listing indexes: {e}")
            print("Continuing anyway...")
            
        print(f"Connecting to index '{index_name}'...")
        index = pc.Index(index_name)
        print("Successfully connected to index")
        
        print("Getting index statistics...")
        try:
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            print("\nPinecone connection successful!")
        except Exception as e:
            print(f"Error getting index statistics: {e}")
            print("This may indicate a problem with the index configuration")
    except Exception as e:
        print(f"Error testing modern Pinecone API: {e}")
        print("\nFalling back to legacy API...")
        
        # Legacy API fallback
        try:
            api_key = os.environ.get("PINECONE_API_KEY")
            environment = os.environ.get("PINECONE_ENVIRONMENT")
            
            if not environment:
                print("PINECONE_ENVIRONMENT environment variable is not set (required for legacy API)")
                sys.exit(1)
                
            index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
            
            print(f"Initializing Pinecone with API key: {api_key[:4]}...{api_key[-4:]} (masked)")
            print(f"Environment: {environment}")
            pinecone.init(api_key=api_key, environment=environment)
            print("Successfully initialized Pinecone")
            
            print("Listing available indexes...")
            try:
                indexes = pinecone.list_indexes()
                print(f"Available indexes: {indexes}")
                
                if index_name not in indexes:
                    print(f"WARNING: Index '{index_name}' not found in available indexes")
                    print("Please create the index in the Pinecone console first")
            except Exception as e:
                print(f"Error listing indexes: {e}")
                print("Continuing anyway...")
                
            print(f"Connecting to index '{index_name}'...")
            index = pinecone.Index(index_name)
            print("Successfully connected to index")
            
            print("Getting index statistics...")
            try:
                stats = index.describe_index_stats()
                print(f"Index stats: {stats}")
                print("\nPinecone connection successful!")
            except Exception as e:
                print(f"Error getting index statistics: {e}")
                print("This may indicate a problem with the index configuration")
        except Exception as e:
            print(f"Error testing legacy Pinecone API: {e}")
            print("\nAll Pinecone API tests failed.")
            sys.exit(1)
else:
    # Legacy API only
    print("\nTesting legacy Pinecone API...")
    try:
        api_key = os.environ.get("PINECONE_API_KEY")
        environment = os.environ.get("PINECONE_ENVIRONMENT")
        
        if not environment:
            print("PINECONE_ENVIRONMENT environment variable is not set (required for legacy API)")
            sys.exit(1)
            
        index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        
        print(f"Initializing Pinecone with API key: {api_key[:4]}...{api_key[-4:]} (masked)")
        print(f"Environment: {environment}")
        pinecone.init(api_key=api_key, environment=environment)
        print("Successfully initialized Pinecone")
        
        print("Listing available indexes...")
        try:
            indexes = pinecone.list_indexes()
            print(f"Available indexes: {indexes}")
            
            if index_name not in indexes:
                print(f"WARNING: Index '{index_name}' not found in available indexes")
                print("Please create the index in the Pinecone console first")
        except Exception as e:
            print(f"Error listing indexes: {e}")
            print("Continuing anyway...")
            
        print(f"Connecting to index '{index_name}'...")
        index = pinecone.Index(index_name)
        print("Successfully connected to index")
        
        print("Getting index statistics...")
        try:
            stats = index.describe_index_stats()
            print(f"Index stats: {stats}")
            print("\nPinecone connection successful!")
        except Exception as e:
            print(f"Error getting index statistics: {e}")
            print("This may indicate a problem with the index configuration")
    except Exception as e:
        print(f"Error testing legacy Pinecone API: {e}")
        print("\nAll Pinecone API tests failed.")
        sys.exit(1)

print("\nTest complete!")
