#!/usr/bin/env python3
"""
Simple test script to validate vector store configuration
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing vector store configuration import...")
    import vector_store_config
    print("✅ vector_store_config imported successfully")
    
    print("Testing vector store manager...")
    manager = vector_store_config.get_vector_store_manager()
    print(f"✅ Vector store manager created: {manager}")
    
    print("Testing environment variables...")
    config = vector_store_config.VectorStoreManager()
    print(f"PINECONE_API_KEY: {'✅ Set' if config.pinecone_api_key else '❌ Missing'}")
    print(f"PINECONE_ENVIRONMENT: {'✅ Set' if config.pinecone_environment else '❌ Missing'}")
    print(f"OPENAI_API_KEY: {'✅ Set' if config.openai_api_key else '❌ Missing'}")
    print(f"Index name: {config.pinecone_index_name}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
