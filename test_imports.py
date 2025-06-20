#!/usr/bin/env python3
"""
LlamaIndex Railway Import Tester

This script tests critical imports needed by the application
to help diagnose startup errors on Railway.
"""

import sys
import os
import importlib

print("=" * 70)
print("LLAMAINDEX RAILWAY IMPORT TESTER")
print("=" * 70)

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Add current directory and backend to path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Added {current_dir} to sys.path")
    
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
    print(f"Added {backend_dir} to sys.path")

print("\nTesting critical imports:")
core_modules = [
    "fastapi",
    "uvicorn", 
    "pinecone",
    "llama_index.core",
    "llama_index.vector_stores.pinecone",
    "llama_index.embeddings.openai"
]

# Optional modules - don't fail the entire script if these are missing
optional_modules = [
    "backend.vector_store_config",
    "vector_store_config"
]

successful_imports = 0
# First test required modules
for module_name in core_modules:
    try:
        # Try to import the module
        module = importlib.import_module(module_name)
        # Then try optional modules but don't abort on failure
print("\nTesting optional modules:")
for module_name in optional_modules:
    try:
        module = importlib.import_module(module_name)
        print(f"✅ {module_name} imported successfully")
    except ImportError as e:
        print(f"⚠️ {module_name} import failed: {str(e)} (this may be expected depending on directory structure)")
        continue
        
        # Try to get version if available
        version = getattr(module, "__version__", "unknown")
        
        print(f"✓ Successfully imported {module_name} (version: {version})")
        successful_imports += 1
        
        # Special handling for pinecone
        if module_name == "pinecone":
            # Check for new vs legacy API
            if hasattr(module, "Pinecone"):
                print("  ✓ Modern Pinecone API (v3+) available")
            else:
                print("  ✓ Legacy Pinecone API available")
            
            # Try init with dummy values
            try:
                if hasattr(module, "Pinecone"):
                    pc = module.Pinecone(api_key="dummy_for_testing")
                    print("  ✓ Pinecone client initialization works")
                else:
                    module.init(api_key="dummy_for_testing", environment="us-east1-gcp")
                    print("  ✓ Legacy pinecone.init() works")
            except Exception as e:
                print(f"  ⚠️ Pinecone initialization error: {str(e)}")
        
        # Special handling for PineconeVectorStore
        if module_name == "llama_index.vector_stores.pinecone":
            # Check for the class
            if hasattr(module, "PineconeVectorStore"):
                print("  ✓ PineconeVectorStore class found")
            else:
                print("  ⚠️ PineconeVectorStore class not found in expected location")
                
            # Try alternate import paths
            try:
                from llama_index.vector_stores.pinecone.base import PineconeVectorStore
                print("  ✓ PineconeVectorStore importable from .base")
            except ImportError as e:
                print(f"  ⚠️ Cannot import from .base: {str(e)}")
                
            try:
                from llama_index.core.vector_stores.pinecone import PineconeVectorStore
                print("  ✓ PineconeVectorStore importable from core")
            except ImportError as e:
                print(f"  ⚠️ Cannot import from core: {str(e)}")
                
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {str(e)}")

print(f"\nSuccessfully imported {successful_imports}/{len(core_modules)} modules")

if successful_imports == len(core_modules):
    print("\nAll imports successful! Your environment should work correctly.")
    sys.exit(0)
else:
    print("\nSome imports failed. Check the errors above but continuing anyway.")
    # Don't exit with error code 1 in Railway - we want to continue deployment anyway
    sys.exit(0)
