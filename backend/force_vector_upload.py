"""
Force Vector Upload Utility for Railway

This script directly tests vector upload to Pinecone, bypassing the normal flow
to identify issues with the vector insertion process.
"""

import os
import sys
import time
import traceback

print("=" * 80)
print("FORCE VECTOR UPLOAD TEST")
print("=" * 80)

# Set up sys path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to sys.path")
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Added {current_dir} to sys.path")

# Check key environment variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

print("Environment variables:")
print(f"PINECONE_API_KEY: {'SET' if PINECONE_API_KEY else 'NOT SET'}")
print(f"PINECONE_ENVIRONMENT: {PINECONE_ENVIRONMENT or 'NOT SET'}")
print(f"PINECONE_INDEX_NAME: {PINECONE_INDEX_NAME}")
print(f"OPENAI_API_KEY: {'SET' if OPENAI_API_KEY else 'NOT SET'}")

if not PINECONE_API_KEY:
    print("❌ PINECONE_API_KEY is not set!")
    sys.exit(1)
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY is not set!")
    sys.exit(1)

# Try importing necessary modules
try:
    # Import the vector store manager first
    print("\nImporting vector_store_manager...")
    try:
        try:
            from vector_store_config import VectorStoreManager, vector_store_manager
            print("✓ Successfully imported from root vector_store_config")
        except ImportError:
            from backend.vector_store_config import VectorStoreManager, vector_store_manager
            print("✓ Successfully imported from backend.vector_store_config")
    except ImportError as e:
        print(f"❌ Failed to import VectorStoreManager: {e}")
        sys.exit(1)

    # Import LlamaIndex Document and embedding model
    print("\nImporting LlamaIndex components...")
    try:
        from llama_index.core import Document, Settings
        print("✓ Document imported from llama_index.core")
    except ImportError:
        try:
            from llama_index import Document, Settings
            print("✓ Document imported from llama_index")
        except ImportError as e:
            print(f"❌ Failed to import Document: {e}")
            sys.exit(1)

    # Import OpenAI embedding
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
        print("✓ OpenAIEmbedding imported from llama_index.embeddings.openai")
    except ImportError:
        try:
            from llama_index.core.embeddings import OpenAIEmbedding
            print("✓ OpenAIEmbedding imported from llama_index.core.embeddings")
        except ImportError as e:
            print(f"❌ Failed to import OpenAIEmbedding: {e}")
            sys.exit(1)

    # Initialize pinecone directly to confirm connection
    print("\nTesting direct Pinecone connection...")
    try:
        import pinecone
        print(f"Pinecone version: {getattr(pinecone, '__version__', 'unknown')}")
        has_modern_api = hasattr(pinecone, "Pinecone")
        print(f"Has modern API: {has_modern_api}")

        if has_modern_api:
            print("Using modern Pinecone API...")
            pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
            indexes = pc.list_indexes().names()
            print(f"Available indexes: {indexes}")
            
            if PINECONE_INDEX_NAME not in indexes:
                print(f"⚠️ Index '{PINECONE_INDEX_NAME}' not found in Pinecone!")
                print(f"Available indexes: {indexes}")
                sys.exit(1)
            
            pinecone_index = pc.Index(PINECONE_INDEX_NAME)
            print("✓ Successfully connected to Pinecone index")
            
            # Get index stats
            stats_before = pinecone_index.describe_index_stats()
            print(f"Index stats before test: {stats_before}")
            vector_count_before = stats_before.get('total_vector_count', 0)
            print(f"Vector count before test: {vector_count_before}")
        else:
            print("Using legacy Pinecone API...")
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            indexes = pinecone.list_indexes()
            print(f"Available indexes: {indexes}")
            
            if PINECONE_INDEX_NAME not in indexes:
                print(f"⚠️ Index '{PINECONE_INDEX_NAME}' not found in Pinecone!")
                print(f"Available indexes: {indexes}")
                sys.exit(1)
            
            pinecone_index = pinecone.Index(PINECONE_INDEX_NAME)
            print("✓ Successfully connected to Pinecone index")
            
            # Get index stats
            stats_before = pinecone_index.describe_index_stats()
            print(f"Index stats before test: {stats_before}")
            vector_count_before = stats_before.get('total_vector_count', 0)
            print(f"Vector count before test: {vector_count_before}")
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone directly: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Initialize the vector store manager
    print("\nInitializing VectorStoreManager components...")
    try:
        # Initialize embeddings
        print("Initializing OpenAI embeddings...")
        embed_model = vector_store_manager.initialize_embeddings()
        print(f"✓ Embeddings initialized: {type(embed_model).__name__}")
        
        # Initialize vector store
        print("Initializing Pinecone vector store...")
        vector_store = vector_store_manager.initialize_pinecone_vector_store()
        print(f"✓ Vector store initialized: {type(vector_store).__name__}")
        
        # Initialize index
        print("Initializing vector index...")
        index = vector_store_manager.initialize_vector_index()
        print(f"✓ Vector index initialized: {type(index).__name__}")
    except Exception as e:
        print(f"❌ Failed to initialize vector store components: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Create a test document with unique ID for tracking
    print("\nCreating test document...")
    test_doc_id = f"test-doc-{int(time.time())}"
    test_document = Document(
        text="This is a test document for Pinecone vector insertion. If you see this document in your index, the vector insertion is working properly.",
        metadata={
            "source": "force_vector_upload.py",
            "id": test_doc_id,
            "test": True
        }
    )
    print(f"✓ Created test document with ID: {test_doc_id}")

    # Generate embedding directly for the test document
    print("\nGenerating embedding for test document...")
    try:
        embedding = embed_model.get_text_embedding(test_document.text)
        print(f"✓ Generated embedding with {len(embedding)} dimensions")
        
        # Print first few values of the embedding for debugging
        print(f"Embedding preview: {embedding[:5]}...")
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Insert into Pinecone directly to bypass any potential issues with LlamaIndex
    print("\nInserting directly into Pinecone...")
    try:
        if has_modern_api:
            # Modern Pinecone API direct insert
            pinecone_index.upsert(
                vectors=[{
                    "id": test_doc_id,
                    "values": embedding,
                    "metadata": test_document.metadata
                }],
                namespace=""
            )
        else:
            # Legacy Pinecone API direct insert
            pinecone_index.upsert([
                (test_doc_id, embedding, test_document.metadata)
            ], namespace="")
        print("✓ Direct Pinecone upsert completed")
        
        # Wait a moment for the update to propagate
        print("Waiting 3 seconds for update to propagate...")
        time.sleep(3)
        
        # Check if the vector was inserted by getting updated stats
        stats_after_direct = pinecone_index.describe_index_stats()
        vector_count_after_direct = stats_after_direct.get('total_vector_count', 0)
        print(f"Vector count after direct insert: {vector_count_after_direct}")
        
        if vector_count_after_direct > vector_count_before:
            print(f"✅ DIRECT INSERT SUCCESSFUL: Vector count increased from {vector_count_before} to {vector_count_after_direct}")
        else:
            print(f"❌ DIRECT INSERT FAILED: Vector count remained at {vector_count_after_direct}")
    except Exception as e:
        print(f"❌ Failed to insert directly into Pinecone: {e}")
        traceback.print_exc()

    # Also test inserting through LlamaIndex API
    print("\nInserting through LlamaIndex API...")
    try:
        # Create a node from the document with the embedding attached
        from llama_index.core.node import TextNode
        node = TextNode(
            text=test_document.text,
            metadata=test_document.metadata,
            id_=f"{test_doc_id}-llamaindex"
        )
        
        # Explicitly generate and set the embedding
        node_embedding = embed_model.get_text_embedding(node.text)
        node.embedding = node_embedding
        print(f"✓ Created node with {len(node_embedding)} dimension embedding")
        
        # Insert the node into the index
        print("Inserting node into index...")
        index.insert_nodes([node])
        print("✓ LlamaIndex insert_nodes completed")
        
        # Wait a moment for the update to propagate
        print("Waiting 3 seconds for update to propagate...")
        time.sleep(3)
        
        # Check if the vector was inserted
        stats_after_llamaindex = pinecone_index.describe_index_stats()
        vector_count_after_llamaindex = stats_after_llamaindex.get('total_vector_count', 0)
        print(f"Vector count after LlamaIndex insert: {vector_count_after_llamaindex}")
        
        if vector_count_after_llamaindex > vector_count_after_direct:
            print(f"✅ LLAMAINDEX INSERT SUCCESSFUL: Vector count increased from {vector_count_after_direct} to {vector_count_after_llamaindex}")
        else:
            print(f"❌ LLAMAINDEX INSERT FAILED: Vector count remained at {vector_count_after_llamaindex}")
    except Exception as e:
        print(f"❌ Failed to insert through LlamaIndex API: {e}")
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Initial vector count: {vector_count_before}")
    print(f"Final vector count: {vector_count_after_llamaindex}")
    print(f"Change: {vector_count_after_llamaindex - vector_count_before}")
    
    if vector_count_after_llamaindex > vector_count_before:
        print("\n✅ TEST PASSED: Successfully inserted vectors into Pinecone!")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED: No vectors were inserted into Pinecone!")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    traceback.print_exc()
    sys.exit(1)
