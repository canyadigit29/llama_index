#!/usr/bin/env python3
"""
Pinecone Connection Test

Tests both the modern Pinecone API and the legacy REST API approaches
to help debug connection issues with Pinecone.
"""

import os
import sys
import importlib.util
import requests
import json

def test_modern_pinecone_api():
    """Test connection using the modern Pinecone API (Pinecone() class)."""
    print("Testing connection with modern Pinecone API...")
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    
    if not api_key:
        print("❌ PINECONE_API_KEY environment variable not set")
        return False
    
    try:
        # Check if pinecone module is available
        pinecone_spec = importlib.util.find_spec("pinecone")
        if not pinecone_spec:
            print("❌ Pinecone module not found. Make sure it's installed.")
            return False
        
        # Import the module
        pinecone = importlib.import_module("pinecone")
        
        # Check if the new API is available
        if not hasattr(pinecone, "Pinecone"):
            print("❌ Modern Pinecone API not available. This module might be too old.")
            return False
        
        # Try to initialize the client
        print(f"Initializing Pinecone client with API key: {api_key[:4]}...{api_key[-4:]} in environment: {environment}")
        pc = pinecone.Pinecone(api_key=api_key)
        
        # Try to list indexes
        print("Listing indexes...")
        try:
            indexes = pc.list_indexes().names()
            print(f"✅ Successfully connected! Found indexes: {indexes}")
            
            # Check if the specified index exists
            if index_name in indexes:
                print(f"✅ Index '{index_name}' exists")
            else:
                print(f"⚠️ Index '{index_name}' does not exist")
            
            return True
        except Exception as e:
            print(f"❌ Error listing indexes: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error with modern Pinecone API: {str(e)}")
        return False

def test_rest_api():
    """Test connection using the REST API approach."""
    print("\nTesting connection with REST API...")
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")
    
    if not api_key:
        print("❌ PINECONE_API_KEY environment variable not set")
        return False
    
    try:
        # Try to make a request to Pinecone
        print(f"Making REST API request to environment: {environment}")
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        url = f"https://controller.{environment}.pinecone.io/databases"
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Successfully connected via REST API!")
            try:
                data = response.json()
                print(f"Response data: {json.dumps(data, indent=2)}")
                return True
            except Exception as e:
                print(f"⚠️ Could not parse JSON response: {str(e)}")
                return True  # Still count as success since we got 200
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ General error with REST API: {str(e)}")
        return False

def main():
    print("=" * 50)
    print("PINECONE CONNECTION TEST")
    print("=" * 50)
    
    print(f"Testing with environment: {os.environ.get('PINECONE_ENVIRONMENT', 'not set')}")
    
    # Test both methods
    modern_success = test_modern_pinecone_api()
    rest_success = test_rest_api()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Modern Pinecone API: {'✅ SUCCESS' if modern_success else '❌ FAILED'}")
    print(f"REST API approach:   {'✅ SUCCESS' if rest_success else '❌ FAILED'}")
    
    # Provide guidance
    if modern_success:
        print("\n✅ The modern Pinecone API is working - this is what the main application uses.")
        if not rest_success:
            print("⚠️ The REST API failed but the modern API worked - this might cause health check failures")
            print("   but the main application should still function correctly.")
    elif rest_success:
        print("\n⚠️ Only the REST API is working. The main application might have issues.")
    else:
        print("\n❌ Both connection methods failed. Please check:")
        print("   1. Your Pinecone API key")
        print("   2. Your Pinecone environment (should be format like 'us-east-1')")
        print("   3. Network connectivity to Pinecone")
    
    print("\n" + "=" * 50)
    return 0 if modern_success or rest_success else 1

if __name__ == "__main__":
    sys.exit(main())
