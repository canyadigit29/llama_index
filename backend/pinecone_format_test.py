#!/usr/bin/env python3
"""
Pinecone Environment Format Test

This script tests various Pinecone environment format strings against
the validation logic to ensure that our validators correctly identify
valid and invalid formats.
"""

import os
import sys

# Import the validation function from env_health_check.py
sys.path.insert(0, os.path.dirname(__file__))
from env_health_check import check_pinecone_connectivity

def test_pinecone_environment_formats():
    """Test different Pinecone environment format strings."""
    formats_to_test = [
        "us-east-1",       # Valid AWS region
        "us-west-2",       # Valid AWS region
        "gcp-starter",     # Valid GCP starter
        "asia-southeast1", # Valid Asia region
        "uswest1",         # Invalid - missing hyphen
        "us-west1-gcp",    # Old format - should give warning but pass validation
        "",                # Invalid - empty
    ]
    
    print("Testing Pinecone environment format validation...")
    print("=" * 50)
    
    for env_format in formats_to_test:
        # Set the environment variable
        os.environ["PINECONE_ENVIRONMENT"] = env_format
        os.environ["PINECONE_API_KEY"] = "dummy_key_for_testing"
        
        # Check the validation
        result = check_pinecone_connectivity()
        
        # Print the result
        print(f"\nTesting: '{env_format}'")
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_pinecone_environment_formats()
