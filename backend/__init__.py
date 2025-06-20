"""
Vector Store Configuration Module (module-level import)

This is a simplified version of the vector_store_config module that can be
imported at the module level without causing import errors.

The main VectorStoreManager class is imported by main.py and initialized during startup.
"""

# Define the module as available even before the full class is loaded
VECTOR_STORE_AVAILABLE = True

# Import dependencies only if they're used
import os

def get_pinecone_config():
    """Return basic Pinecone configuration from environment variables."""
    return {
        "api_key": os.environ.get("PINECONE_API_KEY"),
        "environment": os.environ.get("PINECONE_ENVIRONMENT"),
        "index_name": os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    }

# The actual VectorStoreManager class is defined in vector_store_config.py
# This file just serves as a fallback for imports
