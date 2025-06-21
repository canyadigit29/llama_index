"""
Pinecone Debug Patch for Railway

This file contains enhanced debugging for document processing
and Pinecone integration in Railway deployments.
"""

import logging
import os
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger('pinecone_debug')

def debug_log(message, level='info'):
    """Log a message with the appropriate level."""
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'debug':
        logger.debug(message)
    # Always print to stdout for Railway logs
    print(f"[PINECONE DEBUG] {message}")

def debug_pinecone_initialization():
    """Debug Pinecone initialization."""
    debug_log("Checking Pinecone initialization...")
    
    # Check environment variables
    debug_log(f"PINECONE_API_KEY: {'SET' if os.environ.get('PINECONE_API_KEY') else 'NOT SET'}")
    debug_log(f"PINECONE_ENVIRONMENT: {os.environ.get('PINECONE_ENVIRONMENT', 'NOT SET')}")
    debug_log(f"PINECONE_INDEX_NAME: {os.environ.get('PINECONE_INDEX_NAME', 'developer-quickstart-py')}")
    
    # Try to import Pinecone
    try:
        import pinecone
        debug_log(f"Pinecone version: {getattr(pinecone, '__version__', 'unknown')}")
        debug_log(f"Has modern API: {hasattr(pinecone, 'Pinecone')}")
        
        # Check if initialized
        if hasattr(pinecone, "Pinecone"):
            # Modern API
            pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
            indexes = pc.list_indexes().names()
            debug_log(f"Available indexes (modern API): {indexes}")
        else:
            # Legacy API
            pinecone.init(api_key=os.environ.get("PINECONE_API_KEY"), environment=os.environ.get("PINECONE_ENVIRONMENT"))
            indexes = pinecone.list_indexes()
            debug_log(f"Available indexes (legacy API): {indexes}")
        
        debug_log("Pinecone initialization check complete")
        return True
    except ImportError:
        debug_log("Failed to import pinecone. Is it installed?", level='error')
        return False
    except Exception as e:
        debug_log(f"Error checking Pinecone initialization: {e}", level='error')
        debug_log(traceback.format_exc(), level='error')
        return False

def debug_vector_store_creation(vector_store):
    """Debug vector store creation."""
    debug_log("Checking vector store...")
    
    if vector_store is None:
        debug_log("Vector store is None!", level='error')
        return False
        
    debug_log(f"Vector store type: {type(vector_store).__name__}")
    
    # Check if it's a PineconeVectorStore
    if "Pinecone" not in type(vector_store).__name__:
        debug_log("Vector store is not a PineconeVectorStore!", level='error')
        return False
        
    # Check if it has the _pinecone_index attribute
    if hasattr(vector_store, '_pinecone_index'):
        debug_log("Vector store has _pinecone_index attribute")
        
        # Try to get stats
        try:
            pinecone_index = vector_store._pinecone_index
            stats = pinecone_index.describe_index_stats()
            debug_log(f"Index stats: {stats}")
            return True
        except Exception as e:
            debug_log(f"Error getting index stats: {e}", level='error')
            return False
    else:
        debug_log("Vector store does not have _pinecone_index attribute", level='error')
        return False

def debug_document_processing(doc, nodes):
    """Debug document processing."""
    debug_log("Checking document processing...")
    
    # Check document
    debug_log(f"Document type: {type(doc).__name__}")
    debug_log(f"Document text length: {len(doc.text) if hasattr(doc, 'text') else 'N/A'}")
    debug_log(f"Document metadata: {doc.metadata if hasattr(doc, 'metadata') else 'N/A'}")
    
    # Check nodes
    debug_log(f"Number of nodes: {len(nodes)}")
    if not nodes:
        debug_log("No nodes were created!", level='error')
        return False
        
    # Check first node
    first_node = nodes[0]
    debug_log(f"First node ID: {first_node.id_ if hasattr(first_node, 'id_') else 'N/A'}")
    debug_log(f"First node text length: {len(first_node.text) if hasattr(first_node, 'text') else 'N/A'}")
    
    # Check if nodes have embeddings
    has_embeddings = all(hasattr(node, 'embedding') and node.embedding is not None for node in nodes)
    debug_log(f"All nodes have embeddings: {has_embeddings}")
    
    if not has_embeddings:
        # Count missing embeddings
        missing_count = sum(1 for node in nodes if not hasattr(node, 'embedding') or node.embedding is None)
        debug_log(f"Number of nodes missing embeddings: {missing_count}/{len(nodes)}", level='error')
        return False
        
    # Check first node embedding
    if hasattr(first_node, 'embedding') and first_node.embedding is not None:
        debug_log(f"First node embedding dimensions: {len(first_node.embedding)}")
    
    return True

def debug_index_insertion(index, nodes):
    """Debug index insertion."""
    debug_log("Checking index insertion...")
    
    # Check index
    debug_log(f"Index type: {type(index).__name__}")
    debug_log(f"Index vector store type: {type(index.vector_store).__name__ if hasattr(index, 'vector_store') else 'N/A'}")
    
    # Get stats before insertion
    try:
        if hasattr(index.vector_store, '_pinecone_index'):
            pinecone_index = index.vector_store._pinecone_index
            stats_before = pinecone_index.describe_index_stats()
            debug_log(f"Index stats before insertion: {stats_before}")
            vector_count_before = stats_before.get('namespaces', {}).get('', {}).get('vector_count', 0)
            debug_log(f"Vector count before insertion: {vector_count_before}")
            
            # Return vector count for comparison after insertion
            return vector_count_before
    except Exception as e:
        debug_log(f"Error getting index stats before insertion: {e}", level='error')
    
    return None

def debug_index_insertion_result(index, nodes, vector_count_before):
    """Debug index insertion result."""
    debug_log("Checking index insertion result...")
    
    if vector_count_before is None:
        debug_log("No vector count before insertion", level='warning')
        return
        
    # Get stats after insertion
    try:
        if hasattr(index.vector_store, '_pinecone_index'):
            pinecone_index = index.vector_store._pinecone_index
            stats_after = pinecone_index.describe_index_stats()
            debug_log(f"Index stats after insertion: {stats_after}")
            vector_count_after = stats_after.get('namespaces', {}).get('', {}).get('vector_count', 0)
            debug_log(f"Vector count after insertion: {vector_count_after}")
            
            # Compare vector counts
            diff = vector_count_after - vector_count_before
            debug_log(f"Vector count change: {vector_count_before} → {vector_count_after} (Δ {diff})")
            
            if diff != len(nodes):
                debug_log(f"Expected to add {len(nodes)} vectors but count changed by {diff}", level='warning')
            else:
                debug_log(f"Successfully added {diff} vectors")
    except Exception as e:
        debug_log(f"Error getting index stats after insertion: {e}", level='error')

def debug_embedding_model():
    """Debug embedding model."""
    debug_log("Checking embedding model...")
    
    try:
        from llama_index.core import Settings
        
        if hasattr(Settings, 'embed_model') and Settings.embed_model:
            debug_log(f"Embed model type: {type(Settings.embed_model).__name__}")
            
            # Check if it's an OpenAI embedding model
            if "OpenAI" in type(Settings.embed_model).__name__:
                debug_log("Using OpenAI embedding model")
                
                # Check model name and dimensions
                if hasattr(Settings.embed_model, 'model'):
                    debug_log(f"Model name: {Settings.embed_model.model}")
                if hasattr(Settings.embed_model, 'dimension'):
                    debug_log(f"Model dimensions: {Settings.embed_model.dimension}")
                    
                # Try to generate an embedding
                try:
                    test_embedding = Settings.embed_model.get_text_embedding("This is a test")
                    debug_log(f"Test embedding dimensions: {len(test_embedding)}")
                    return True
                except Exception as e:
                    debug_log(f"Error generating test embedding: {e}", level='error')
                    return False
            else:
                debug_log(f"Using non-OpenAI embedding model: {type(Settings.embed_model).__name__}")
                return True
        else:
            debug_log("No embed_model set in Settings", level='error')
            
            # Try to get from VectorStoreManager
            try:
                from vector_store_config import vector_store_manager
                if hasattr(vector_store_manager, 'embed_model') and vector_store_manager.embed_model:
                    debug_log(f"Embed model found in vector_store_manager: {type(vector_store_manager.embed_model).__name__}")
                    return True
                else:
                    debug_log("No embed_model in vector_store_manager", level='error')
            except ImportError:
                debug_log("Could not import vector_store_manager", level='error')
            except Exception as e:
                debug_log(f"Error checking vector_store_manager: {e}", level='error')
            
            return False
    except ImportError:
        debug_log("Failed to import Settings from llama_index.core", level='error')
        return False
    except Exception as e:
        debug_log(f"Error checking embedding model: {e}", level='error')
        return False

def inject_debug():
    """Inject debugging code into main.py."""
    debug_log("Injecting debugging code into main.py")
    debug_log("Debug patch ready for use")
