#!/usr/bin/env python3
"""
Railway Import Path Troubleshooter

This script helps diagnose import path issues in Railway deployment.
"""

import os
import sys
import importlib

print("=" * 70)
print("RAILWAY IMPORT PATH TROUBLESHOOTER")
print("=" * 70)

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

# Print sys.path
print("\nPython import paths (sys.path):")
for idx, path in enumerate(sys.path):
    print(f"  {idx}. {path}")
    if os.path.exists(path):
        files = os.listdir(path)[:5]  # Show first 5 files
        if files:
            print(f"     Contents (first 5): {', '.join(files)}" + ("..." if len(os.listdir(path)) > 5 else ""))
    else:
        print("     [Directory does not exist]")

# Check for specific files
files_to_check = [
    "main.py",
    "vector_store_config.py",
    "railway_deploy.sh",
    "start.sh"
]

print("\nChecking for key files:")
current_dir = os.getcwd()
for file in files_to_check:
    current_path = os.path.join(current_dir, file)
    parent_path = os.path.join(current_dir, "..", file)
    backend_path = os.path.join(current_dir, "backend", file)
    
    if os.path.exists(current_path):
        print(f"  ✅ {file} found in current directory")
    elif os.path.exists(parent_path):
        print(f"  ✅ {file} found in parent directory")
    elif os.path.exists(backend_path):
        print(f"  ✅ {file} found in backend/ subdirectory")
    else:
        print(f"  ❌ {file} not found")

# Try to import key modules
modules_to_check = [
    "vector_store_config",
    "backend.vector_store_config",
    "fastapi",
    "uvicorn",
    "pinecone"
]

print("\nTrying to import key modules:")
for module_name in modules_to_check:
    try:
        module = importlib.import_module(module_name)
        print(f"  ✅ Successfully imported {module_name}")
        if module_name in ["vector_store_config", "backend.vector_store_config"]:
            if hasattr(module, "VectorStoreManager"):
                print(f"     Found VectorStoreManager class in {module_name}")
            else:
                print(f"     VectorStoreManager class NOT found in {module_name}")
    except ImportError as e:
        print(f"  ❌ Failed to import {module_name}: {str(e)}")

# Print environment variables
print("\nRelevant environment variables:")
env_vars = [
    "PINECONE_API_KEY",
    "PINECONE_ENVIRONMENT",
    "PINECONE_INDEX_NAME",
    "OPENAI_API_KEY",
    "PORT",
    "PYTHONPATH"
]

for var in env_vars:
    value = os.environ.get(var)
    if var.endswith("API_KEY") and value:
        print(f"  {var}: [Set but not shown for security]")
    else:
        print(f"  {var}: {value or 'Not set'}")

print("\nDeployment structure summary:")
if os.path.exists(os.path.join(current_dir, "main.py")):
    print("  Files appear to be in the app's root directory.")
elif os.path.exists(os.path.join(current_dir, "backend", "main.py")):
    print("  Files appear to be in a subdirectory structure with the backend/ folder.")
else:
    print("  Could not determine directory structure.")

print("\nIf you're having import issues, try:")
print("  1. Make sure vector_store_config.py is copied to the same directory as main.py")
print("  2. Ensure PYTHONPATH includes the directories containing your modules")
print("  3. Check that file permissions allow reading the modules")
print("  4. Update import statements to use absolute or relative imports correctly")

print("\nTroubleshooter complete.")
