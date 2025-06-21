"""
Vector Store Configuration Module

This module handles the initialization and configuration of vector stores,
specifically Pinecone, following LlamaIndex best practices.
"""

import os
from typing import Optional, List, Dict, Any
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding


class VectorStoreManager:
    """Manages vector store initialization and configuration."""
    
    def __init__(self):
        self.vector_store = None
        self.index = None
        self.embed_model = None
        
        # Environment variables
        self.pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        self.pinecone_environment = os.environ.get("PINECONE_ENVIRONMENT")
        self.pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")
        self.embedding_dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "3072"))
        
        print(f"Vector Store Config: Using Pinecone index '{self.pinecone_index_name}' in environment '{self.pinecone_environment}'")
        if not self.pinecone_api_key:
            print("WARNING: PINECONE_API_KEY environment variable is not set!")
        
    def initialize_embeddings(self) -> OpenAIEmbedding:
        """Initialize OpenAI embeddings."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
            
        self.embed_model = OpenAIEmbedding(
            api_key=self.openai_api_key,
            model=self.embedding_model,
            dimensions=self.embedding_dimensions
        )
        
        # Set global settings
        Settings.embed_model = self.embed_model
        print(f"✅ Initialized OpenAI embeddings: {self.embedding_model} ({self.embedding_dimensions}D)")
        return self.embed_model
    
    def initialize_pinecone_vector_store(self) -> PineconeVectorStore:
        """Initialize Pinecone vector store using the proper from_params method."""
        try:
            if not self.pinecone_api_key:
                raise ValueError("PINECONE_API_KEY is required")
                
            if not self.pinecone_environment:
                raise ValueError("PINECONE_ENVIRONMENT is required")

            # Try modern Pinecone API first
            try:
                # Try importing the modern Pinecone client
                import pinecone
                has_modern_api = hasattr(pinecone, "Pinecone")
                
                if has_modern_api:
                    # Modern API approach
                    pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
                    
                    # Check if index exists
                    try:
                        if self.pinecone_index_name not in pc.list_indexes().names():
                            print(f"WARNING: Pinecone index '{self.pinecone_index_name}' not found.")
                            raise ValueError(f"Index '{self.pinecone_index_name}' not found")
                    except Exception as list_err:
                        print(f"Warning: Could not list indexes: {list_err}. Continuing anyway.")
                    
                    # Get the index
                    pinecone_index = pc.Index(self.pinecone_index_name)
                    
                    # Create vector store
                    self.vector_store = PineconeVectorStore(pinecone_index)
                    print(f"✅ Connected to Pinecone index '{self.pinecone_index_name}' using modern API")
                    print(f"DEBUG: Vector store type: {type(self.vector_store).__name__}")
                    print(f"DEBUG: Pinecone index object type: {type(pinecone_index).__name__}")
                    
                    # Verify vector store has the pinecone_index property
                    if hasattr(self.vector_store, '_pinecone_index'):
                        print(f"DEBUG: _pinecone_index is properly set in vector store")
                        try:
                            # Test stats retrieval to ensure connectivity
                            stats = pinecone_index.describe_index_stats()
                            print(f"DEBUG: Successfully retrieved Pinecone stats: {stats}")
                        except Exception as stats_err:
                            print(f"WARNING: Could not retrieve Pinecone stats: {stats_err}")
                else:
                    # Legacy API approach 
                    pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
                    
                    # Check if index exists
                    try:
                        if self.pinecone_index_name not in pinecone.list_indexes():
                            print(f"WARNING: Pinecone index '{self.pinecone_index_name}' not found.")
                            raise ValueError(f"Index '{self.pinecone_index_name}' not found")
                    except Exception as list_err:
                        print(f"Warning: Could not list indexes: {list_err}. Continuing anyway.")
                    
                    # Get the index
                    pinecone_index = pinecone.Index(self.pinecone_index_name)
                    
                    # Create vector store
                    self.vector_store = PineconeVectorStore(pinecone_index)
                    print(f"✅ Connected to Pinecone index '{self.pinecone_index_name}' using legacy API")
                    print(f"DEBUG: Vector store type: {type(self.vector_store).__name__}")
                    print(f"DEBUG: Pinecone index object type: {type(pinecone_index).__name__}")
                    
                    # Verify vector store has the pinecone_index property
                    if hasattr(self.vector_store, '_pinecone_index'):
                        print(f"DEBUG: _pinecone_index is properly set in vector store")
                        try:
                            # Test stats retrieval to ensure connectivity
                            stats = pinecone_index.describe_index_stats()
                            print(f"DEBUG: Successfully retrieved Pinecone stats: {stats}")
                        except Exception as stats_err:
                            print(f"WARNING: Could not retrieve Pinecone stats: {stats_err}")
            except ImportError as e:
                print(f"Error importing Pinecone: {e}. Make sure pinecone-client is installed.")
                raise
            except Exception as e:
                print(f"Error initializing Pinecone: {e}")
                print(f"DEBUG: Exception type: {type(e).__name__}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                raise
                
            # If we got here, we have successfully initialized the vector store
            if not self.vector_store:
                raise ValueError("Vector store initialization failed but no exception was raised")
                
            # One final check before returning
            print(f"DEBUG: Final vector store type: {type(self.vector_store).__name__}")
            return self.vector_store
                
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone vector store: {e}")
            print(f"DEBUG: Exception type: {type(e).__name__}")
            # Check if Pinecone API key and environment are set
            print(f"DEBUG: PINECONE_API_KEY set: {bool(self.pinecone_api_key)}")
            print(f"DEBUG: PINECONE_ENVIRONMENT set: {bool(self.pinecone_environment)}")
            print(f"DEBUG: PINECONE_INDEX_NAME: {self.pinecone_index_name}")
            # Check if pinecone module is available
            try:
                import pinecone
                print(f"DEBUG: Pinecone module available, version: {getattr(pinecone, '__version__', 'unknown')}")
                print(f"DEBUG: Has modern API: {hasattr(pinecone, 'Pinecone')}")
            except ImportError:
                print("DEBUG: Pinecone module not available (ImportError)")
            raise
    
    def initialize_vector_index(self) -> VectorStoreIndex:
        """Initialize vector index with the vector store."""
        try:
            if not self.vector_store:
                # If vector_store is not initialized, do it now
                self.initialize_pinecone_vector_store()
                
            if not self.embed_model:
                # If embed_model is not initialized, do it now
                self.initialize_embeddings()
                
            # Initialize empty index with the vector store and embed model
            try:
                # Try with empty nodes list
                self.index = VectorStoreIndex(
                    nodes=[], 
                    vector_store=self.vector_store, 
                    embed_model=self.embed_model
                )
            except ValueError:
                # Create a simple document as placeholder if needed
                placeholder_doc = Document(text="Placeholder document for initializing index.", id_="placeholder")
                self.index = VectorStoreIndex.from_documents(
                    [placeholder_doc], 
                    vector_store=self.vector_store,
                    embed_model=self.embed_model
                )
                print("Initialized index with a placeholder document")
                
            print("✅ Successfully initialized VectorStoreIndex")
            print(f"DEBUG: Vector index type: {type(self.index).__name__}")
            print(f"DEBUG: Vector index using vector store type: {type(self.index.vector_store).__name__}")
            return self.index
            
        except Exception as e:
            print(f"❌ Failed to initialize vector index: {e}")
            raise
    
    def list_indexes(self) -> List[str]:
        """List available Pinecone indexes."""
        try:
            import pinecone
            has_modern_api = hasattr(pinecone, "Pinecone")
            
            if has_modern_api:
                # Modern API approach
                pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
                return pc.list_indexes().names()
            else:
                # Legacy API approach 
                pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
                return pinecone.list_indexes()
        except Exception as e:
            print(f"Error listing Pinecone indexes: {e}")
            return [self.pinecone_index_name]  # Return just the configured index name as fallback
            
    def delete_index(self) -> bool:
        """Delete the Pinecone index."""
        try:
            import pinecone
            has_modern_api = hasattr(pinecone, "Pinecone")
            
            if has_modern_api:
                # Modern API approach
                pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
                if self.pinecone_index_name in pc.list_indexes().names():
                    pc.delete_index(self.pinecone_index_name)
                    print(f"✅ Deleted Pinecone index '{self.pinecone_index_name}' using modern API")
                    return True
            else:
                # Legacy API approach 
                pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
                if self.pinecone_index_name in pinecone.list_indexes():
                    pinecone.delete_index(self.pinecone_index_name)
                    print(f"✅ Deleted Pinecone index '{self.pinecone_index_name}' using legacy API")
                    return True
                    
            print(f"Index '{self.pinecone_index_name}' not found, nothing to delete")
            return False
        except Exception as e:
            print(f"Error deleting Pinecone index: {e}")
            return False
            
    def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> bool:
        """Delete documents from Pinecone by metadata filter."""
        try:
            if not self.vector_store:
                # If vector_store is not initialized, do it now
                self.initialize_pinecone_vector_store()
                
            # Check if we can access the pinecone_index directly
            if hasattr(self.vector_store, '_pinecone_index'):
                pinecone_index = self.vector_store._pinecone_index
                pinecone_index.delete(filter=metadata_filter)
                print(f"✅ Deleted vectors with metadata filter {metadata_filter}")
                return True
            else:
                print("Cannot access Pinecone index directly from vector store")
                return False
        except Exception as e:
            print(f"Error deleting by metadata: {e}")
            return False

    def get_index_stats(self) -> dict:
        """Get statistics about the current index."""
        if not self.vector_store:
            return {"error": "Vector store not initialized"}
        
        try:
            # Access the underlying Pinecone index
            if hasattr(self.vector_store, '_pinecone_index'):
                pinecone_index = self.vector_store._pinecone_index
                stats = pinecone_index.describe_index_stats()
                return {
                    "success": True,
                    "stats": stats,
                    "index_name": self.pinecone_index_name
                }
            else:
                return {
                    "error": "Vector store does not have _pinecone_index attribute",
                    "vector_store_type": type(self.vector_store).__name__
                }
        except Exception as e:
            return {"error": f"Failed to get index stats: {str(e)}"}

    def initialize_all(self) -> tuple[VectorStoreIndex, PineconeVectorStore, OpenAIEmbedding]:
        """Initialize all components in the correct order."""
        print("🚀 Initializing vector store components...")
        
        # Initialize embeddings first
        embed_model = self.initialize_embeddings()
        
        # Initialize vector store
        vector_store = self.initialize_pinecone_vector_store()
        
        # Initialize vector index
        index = self.initialize_vector_index()
        
        print("✅ All vector store components initialized successfully!")
        
        return index, vector_store, embed_model

# Global instance
vector_store_manager = VectorStoreManager()


def get_vector_store_manager() -> VectorStoreManager:
    """Get the global vector store manager instance."""
    return vector_store_manager


def initialize_vector_store() -> tuple[VectorStoreIndex, PineconeVectorStore, OpenAIEmbedding]:
    """Convenience function to initialize the vector store."""
    return vector_store_manager.initialize_all()


def create_index():
    """Alternative convenience function to initialize the vector store and return the index."""
    vector_store_manager.initialize_all()
    return vector_store_manager.index
