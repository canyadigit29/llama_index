#!/usr/bin/env python3
"""
Import Error Diagnostic Tool

This script attempts to import your FastAPI application from various paths
to identify exactly where the import error is occurring.
"""

import sys
import traceback
import importlib.util
import os

def try_import(module_path, description):
    """Try importing a module and report any errors."""
    print(f"\nAttempting to import {description}: {module_path}")
    try:
        if "." in module_path:
            # For dotted path imports
            module = importlib.import_module(module_path)
            print(f"✅ Successfully imported {module_path}")
            return True
        else:
            # For file path imports
            if not os.path.exists(module_path):
                print(f"❌ File not found: {module_path}")
                return False
                
            module_name = os.path.basename(module_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ Successfully imported {module_path}")
            return True
    except Exception as e:
        print(f"❌ Error importing {module_path}: {type(e).__name__}: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return False

# Print diagnostic information
print("=" * 60)
print("IMPORT ERROR DIAGNOSTIC TOOL")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

# Try importing the main module in different ways
modules_to_try = [
    ("backend.main", "backend.main as module"),
    ("main", "main directly as module"),
    ("/app/backend/main.py", "main.py from absolute path"),
    ("./main.py", "main.py from current directory"),
    ("./backend/main.py", "main.py from backend subdirectory"),
]

for module_path, description in modules_to_try:
    try_import(module_path, description)

# Try importing potential problematic dependencies
dependencies = [
    "fastapi",
    "llama_index",
    "llama_index.core",
    "pinecone",
    "uvicorn",
    "openai",
    "vector_store_config",
]

print("\n" + "=" * 60)
print("CHECKING DEPENDENCIES")
print("=" * 60)

for dep in dependencies:
    try_import(dep, f"dependency {dep}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
