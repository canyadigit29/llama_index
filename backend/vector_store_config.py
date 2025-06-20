"""
Vector Store Configuration Module

This module handles the initialization and configuration of vector stores,
specifically Pinecone, following LlamaIndex best practices.
"""

import os
from typing import Optional
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
        self.pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "maxgpt")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")
        self.embedding_dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "3072"))
        
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
        if not self.pinecone_api_key or not self.pinecone_environment:
            raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT are required")
        
        try:
            # Use the official PineconeVectorStore.from_params method
            self.vector_store = PineconeVectorStore.from_params(
                api_key=self.pinecone_api_key,
                index_name=self.pinecone_index_name,
                environment=self.pinecone_environment,
                # namespace can be added here if needed
            )
            
            print(f"✅ Initialized Pinecone vector store: {self.pinecone_index_name}")
            return self.vector_store
            
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone vector store: {str(e)}")
            raise
    
    def initialize_vector_index(self) -> VectorStoreIndex:
        """Initialize the vector index with the configured vector store and embeddings."""
        if not self.vector_store:
            raise ValueError("Vector store must be initialized first")
        
        if not self.embed_model:
            raise ValueError("Embeddings must be initialized first")
        
        try:
            # Initialize empty index
            self.index = VectorStoreIndex(
                nodes=[],
                vector_store=self.vector_store,
                embed_model=self.embed_model
            )
            
            print(f"✅ Initialized vector index")
            return self.index
            
        except ValueError as e:
            if "One of nodes, objects, or index_struct must be provided" in str(e):
                # Create with a placeholder document if needed
                print("Creating index with placeholder document...")
                placeholder_doc = Document(
                    text="Placeholder document for initializing index structure.",
                    id_="placeholder"
                )
                self.index = VectorStoreIndex.from_documents(
                    [placeholder_doc],
                    vector_store=self.vector_store,
                    embed_model=self.embed_model
                )
                print("✅ Initialized vector index with placeholder document")
                return self.index
            else:
                raise
        except Exception as e:
            print(f"❌ Failed to initialize vector index: {str(e)}")
            raise
    
    def get_index_stats(self) -> dict:
        """Get statistics about the current index."""
        if not self.vector_store:
            return {"error": "Vector store not initialized"}
        
        try:
            # Access the underlying Pinecone index
            pinecone_index = self.vector_store._pinecone_index
            stats = pinecone_index.describe_index_stats()
            return {
                "success": True,
                "stats": stats,
                "index_name": self.pinecone_index_name
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
