"""
Pinecone Connection Test Script

This script tests the connection to Pinecone independently of LlamaIndex to verify
that your API key, environment, and index configuration are correct.
"""

import os
import time

def test_modern_pinecone_api():
    """Test the modern Pinecone API (v2+)"""
    try:
        from pinecone import Pinecone
        print("✓ Successfully imported modern Pinecone API")
        
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            print("❌ PINECONE_API_KEY environment variable is not set")
            return False
            
        index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        
        print(f"Connecting to Pinecone with API key: {api_key[:4]}...{api_key[-4:]} (masked)")
        pc = Pinecone(api_key=api_key)
        print("✓ Successfully created Pinecone client")
        
        print("Listing available indexes...")
        indexes = pc.list_indexes().names()
        print(f"Available indexes: {indexes}")
        
        if index_name not in indexes:
            print(f"❌ Index '{index_name}' not found in available indexes")
            print("Please create the index in the Pinecone console first")
            return False
            
        print(f"Connecting to index '{index_name}'...")
        index = pc.Index(index_name)
        print("✓ Successfully connected to index")
        
        print("Getting index statistics...")
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        
        print("Creating a test vector...")
        test_vector = [0.1] * 3072  # 3072 dimensions
        test_id = f"test-vector-{int(time.time())}"
        
        print(f"Upserting test vector with ID '{test_id}'...")
        try:
            index.upsert(vectors=[(test_id, test_vector, {"test": True})])
            print("✓ Successfully upserted test vector")
        except Exception as e:
            print(f"❌ Failed to upsert vector: {e}")
            if "dimension mismatch" in str(e).lower():
                print("This likely means your index was created with a different dimension than 3072.")
                print(f"Check the dimensions of your index in the Pinecone console.")
            return False
            
        print("Testing query...")
        try:
            results = index.query(vector=test_vector, top_k=1, include_metadata=True)
            print(f"Query results: {results}")
            print("✓ Successfully queried index")
        except Exception as e:
            print(f"❌ Failed to query index: {e}")
            return False
            
        print("Cleaning up test vector...")
        try:
            index.delete(ids=[test_id])
            print("✓ Successfully deleted test vector")
        except Exception as e:
            print(f"❌ Failed to delete test vector: {e}")
            
        return True
    except ImportError:
        print("❌ Failed to import modern Pinecone API")
        print("Try: pip install -U pinecone-client")
        return False
    except Exception as e:
        print(f"❌ Error testing modern Pinecone API: {e}")
        return False

def test_legacy_pinecone_api():
    """Test the legacy Pinecone API (v1)"""
    try:
        import pinecone
        
        if hasattr(pinecone, "Pinecone"):
            print("Modern Pinecone API already tested")
            return False
            
        print("✓ Successfully imported legacy Pinecone API")
        
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            print("❌ PINECONE_API_KEY environment variable is not set")
            return False
            
        environment = os.environ.get("PINECONE_ENVIRONMENT")
        if not environment:
            print("❌ PINECONE_ENVIRONMENT environment variable is not set (required for legacy API)")
            return False
            
        index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        
        print(f"Initializing Pinecone with API key: {api_key[:4]}...{api_key[-4:]} (masked)")
        print(f"Environment: {environment}")
        pinecone.init(api_key=api_key, environment=environment)
        print("✓ Successfully initialized Pinecone")
        
        print("Listing available indexes...")
        indexes = pinecone.list_indexes()
        print(f"Available indexes: {indexes}")
        
        if index_name not in indexes:
            print(f"❌ Index '{index_name}' not found in available indexes")
            print("Please create the index in the Pinecone console first")
            return False
            
        print(f"Connecting to index '{index_name}'...")
        index = pinecone.Index(index_name)
        print("✓ Successfully connected to index")
        
        print("Getting index statistics...")
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        
        print("Creating a test vector...")
        test_vector = [0.1] * 3072  # 3072 dimensions
        test_id = f"test-vector-{int(time.time())}"
        
        print(f"Upserting test vector with ID '{test_id}'...")
        try:
            index.upsert([(test_id, test_vector, {"test": True})])
            print("✓ Successfully upserted test vector")
        except Exception as e:
            print(f"❌ Failed to upsert vector: {e}")
            if "dimension mismatch" in str(e).lower():
                print("This likely means your index was created with a different dimension than 3072.")
                print(f"Check the dimensions of your index in the Pinecone console.")
            return False
            
        print("Testing query...")
        try:
            results = index.query(test_vector, top_k=1, include_metadata=True)
            print(f"Query results: {results}")
            print("✓ Successfully queried index")
        except Exception as e:
            print(f"❌ Failed to query index: {e}")
            return False
            
        print("Cleaning up test vector...")
        try:
            index.delete(ids=[test_id])
            print("✓ Successfully deleted test vector")
        except Exception as e:
            print(f"❌ Failed to delete test vector: {e}")
            
        return True
    except ImportError:
        print("❌ Failed to import legacy Pinecone API")
        print("Try: pip install -U pinecone-client==2.2.1")
        return False
    except Exception as e:
        print(f"❌ Error testing legacy Pinecone API: {e}")
        return False

def test_llama_index_integration():
    """Test the LlamaIndex integration with Pinecone"""
    try:
        print("\nTesting LlamaIndex integration with Pinecone...")
        from vector_store_config import vector_store_manager
        
        print("Initializing embeddings...")
        vector_store_manager.initialize_embeddings()
        
        print("Initializing Pinecone vector store...")
        vs = vector_store_manager.initialize_pinecone_vector_store()
        print(f"Vector store type: {type(vs).__name__}")
        
        print("Initializing vector index...")
        index = vector_store_manager.initialize_vector_index()
        print(f"Vector index type: {type(index).__name__}")
        
        print("Getting index stats...")
        stats = vector_store_manager.get_index_stats()
        print(f"Index stats: {stats}")
        
        print("✓ Successfully tested LlamaIndex integration with Pinecone")
        return True
    except ImportError as e:
        print(f"❌ Failed to import LlamaIndex: {e}")
        print("Try: pip install llama-index")
        return False
    except Exception as e:
        print(f"❌ Error testing LlamaIndex integration: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("PINECONE CONNECTION TEST")
    print("=" * 80)
    
    print("\nEnvironment variables:")
    print(f"PINECONE_API_KEY: {'SET' if os.environ.get('PINECONE_API_KEY') else 'NOT SET'}")
    print(f"PINECONE_ENVIRONMENT: {os.environ.get('PINECONE_ENVIRONMENT', 'NOT SET')}")
    print(f"PINECONE_INDEX_NAME: {os.environ.get('PINECONE_INDEX_NAME', 'developer-quickstart-py')}")
    print(f"OPENAI_API_KEY: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
    
    print("\nTesting modern Pinecone API...")
    modern_success = test_modern_pinecone_api()
    
    if not modern_success:
        print("\nTesting legacy Pinecone API...")
        legacy_success = test_legacy_pinecone_api()
    else:
        legacy_success = False
    
    if modern_success or legacy_success:
        print("\nPinecone connection successful!")
        test_llama_index_integration()
    else:
        print("\n❌ All Pinecone API tests failed.")
        print("Please check your API key and environment settings.")
    
    print("\nTest complete!")
