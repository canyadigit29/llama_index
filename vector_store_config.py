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
        self.embed_model = None        # Environment variables
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
                try:
                    # Try importing the modern Pinecone client
                    import pinecone
                    has_modern_api = hasattr(pinecone, "Pinecone")
                    
                    if has_modern_api:
                        # Modern API approach
                        pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
                        # Check if index exists
                        if self.pinecone_index_name not in pc.list_indexes().names():
                            print(f"WARNING: Pinecone index '{self.pinecone_index_name}' not found.")
                            raise ValueError(f"Index '{self.pinecone_index_name}' not found")
                        
                        # Get the index
                        pinecone_index = pc.Index(self.pinecone_index_name)
                        
                        # Create vector store
                        self.vector_store = PineconeVectorStore(pinecone_index)
                        print(f"✅ Connected to Pinecone index '{self.pinecone_index_name}' using modern API")
                    else:
                        # Legacy API approach 
                        pinecone.init(api_key=self.pinecone_api_key, environment=self.pinecone_environment)
                        
                        # Check if index exists
                        if self.pinecone_index_name not in pinecone.list_indexes():
                            print(f"WARNING: Pinecone index '{self.pinecone_index_name}' not found.")
                            raise ValueError(f"Index '{self.pinecone_index_name}' not found")
                        
                        # Get the index
                        pinecone_index = pinecone.Index(self.pinecone_index_name)
                        
                        # Create vector store
                        self.vector_store = PineconeVectorStore(pinecone_index)
                        print(f"✅ Connected to Pinecone index '{self.pinecone_index_name}' using legacy API")
                except ImportError as e:
                    print(f"Error importing Pinecone: {e}. Make sure pinecone-client is installed.")
                    raise
                
                return self.vector_store
            except Exception as e:
                print(f"Error initializing Pinecone: {e}")
                raise
                
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone vector store: {e}")
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
            if hasattr(self.vector_store, "_pinecone_index"):
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
