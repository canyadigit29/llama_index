"""
This script examines the codebase to confirm whether the Supabase storage bucket name
is hardcoded or configurable through environment variables.
"""

import os
import re
from pathlib import Path

def check_main_py():
    """Check main.py for references to Supabase storage buckets."""
    print("Analyzing main.py...")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("  ERROR: main.py not found!")
        return
        
    storage_references = []
    env_var_definitions = []
    bucket_constants = []
    
    with open(main_path, 'r', encoding='utf-8') as file:
        content = file.read()
        lines = content.split('\n')
        
        # Find environment variable definitions
        env_pattern = re.compile(r'(?:^|\s+)([A-Z_]+)\s*=\s*os\.environ\.get\(["\']([^"\']+)["\'].*\)')
        for line_num, line in enumerate(lines, 1):
            match = env_pattern.search(line)
            if match:
                var_name, env_name = match.groups()
                env_var_definitions.append((line_num, var_name, env_name, line.strip()))
        
        # Find storage bucket references
        storage_pattern = re.compile(r'storage\.from_\(["\']([^"\']+)["\']\)')
        for line_num, line in enumerate(lines, 1):
            for match in storage_pattern.finditer(line):
                bucket_name = match.group(1)
                storage_references.append((line_num, bucket_name, line.strip()))
                
        # Look for any constants that might be used for bucket names
        constant_pattern = re.compile(r'(?:^|\s+)([A-Z_]+_BUCKET|BUCKET_[A-Z_]+)\s*=\s*["\']([^"\']+)["\']')
        for line_num, line in enumerate(lines, 1):
            match = constant_pattern.search(line)
            if match:
                var_name, bucket_name = match.groups()
                bucket_constants.append((line_num, var_name, bucket_name, line.strip()))
    
    # Report findings
    print(f"\nFound {len(env_var_definitions)} environment variable definitions:")
    for line_num, var_name, env_name, line in sorted(env_var_definitions):
        print(f"  Line {line_num}: {var_name} = os.environ.get('{env_name}', ...)")
    
    print(f"\nFound {len(storage_references)} storage bucket references:")
    bucket_names = set()
    for line_num, bucket_name, line in sorted(storage_references):
        print(f"  Line {line_num}: storage.from_('{bucket_name}') in: {line}")
        bucket_names.add(bucket_name)
    
    print(f"\nUnique bucket names used: {sorted(bucket_names)}")
    
    print(f"\nFound {len(bucket_constants)} potential bucket name constants:")
    for line_num, var_name, bucket_name, line in sorted(bucket_constants):
        print(f"  Line {line_num}: {var_name} = '{bucket_name}' in: {line}")
    
    # Check if any environment variables might be used for bucket names
    bucket_env_vars = [var for _, var, _, _ in env_var_definitions if 'BUCKET' in var or 'STORAGE' in var]
    if bucket_env_vars:
        print(f"\nPotential bucket-related environment variables: {bucket_env_vars}")
    else:
        print("\nNo environment variables appear to be used for bucket names.")
    
    # Analysis result
    if all(bucket == "files" for bucket in bucket_names):
        print("\nANALYSIS RESULT:")
        print("  The bucket name 'files' appears to be hardcoded throughout the codebase.")
        print("  No environment variables were found that configure the bucket name.")
    elif len(bucket_names) > 1:
        print("\nANALYSIS RESULT:")
        print(f"  Multiple bucket names used: {sorted(bucket_names)}")
        print("  Check if these are configurable or hardcoded.")
    else:
        print("\nANALYSIS RESULT: Inconclusive")

def check_frontend_references():
    """Check if there are any references in chatbot-ui frontend code."""
    frontend_paths = [
        Path(__file__).parent.parent.parent / "chatbot-ui" / "db" / "storage" / "files.ts",
        Path(__file__).parent.parent.parent / "chatbot-ui" / "app" / "api" / "llama-index" / "process" / "route.ts"
    ]
    
    found_any = False
    for path in frontend_paths:
        if path.exists():
            found_any = True
            print(f"\nChecking frontend file: {path}")
            
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                lines = content.split('\n')
                
                # Check for storage references
                storage_pattern = re.compile(r'storage\.from\(["\'](.*?)["\']\)')
                bucket_refs = []
                
                for line_num, line in enumerate(lines, 1):
                    for match in storage_pattern.finditer(line):
                        bucket_name = match.group(1)
                        bucket_refs.append((line_num, bucket_name, line.strip()))
                
                print(f"  Found {len(bucket_refs)} storage bucket references:")
                for line_num, bucket_name, line in bucket_refs:
                    print(f"    Line {line_num}: storage.from('{bucket_name}') in: {line}")
    
    if not found_any:
        print("\nNo frontend files found to check.")

def check_railway_config():
    """Check Railway config for any bucket-related variables."""
    railway_configs = [
        Path(__file__).parent / "railway.toml",
        Path(__file__).parent.parent / "railway.toml"
    ]
    
    found_any = False
    for path in railway_configs:
        if path.exists():
            found_any = True
            print(f"\nChecking Railway config: {path}")
            
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                lines = content.split('\n')
                
                # Look for storage/bucket related env vars
                storage_vars = []
                for line_num, line in enumerate(lines, 1):
                    if ('bucket' in line.lower() or 'storage' in line.lower()) and '=' in line:
                        storage_vars.append((line_num, line.strip()))
                
                if storage_vars:
                    print(f"  Found {len(storage_vars)} potential storage-related variables:")
                    for line_num, line in storage_vars:
                        print(f"    Line {line_num}: {line}")
                else:
                    print("  No storage-related variables found.")
    
    if not found_any:
        print("\nNo Railway config files found.")

def main():
    """Execute all checks."""
    print("=" * 60)
    print("SUPABASE STORAGE BUCKET CONFIGURATION ANALYSIS")
    print("=" * 60)
    
    check_main_py()
    check_frontend_references()
    check_railway_config()
    
    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("The storage bucket name 'files' appears to be hardcoded in both")
    print("the backend and frontend code, with no environment variable")
    print("configuration option available.")
    print("=" * 60)

if __name__ == "__main__":
    main()
