#!/usr/bin/env python3
"""
Supabase Service Account Authentication Fix

This script provides a function to create a valid Supabase session
for accessing files in storage without requiring user authentication.
"""

import os
from typing import Optional, Dict
from supabase import create_client, Client

def get_service_authenticated_supabase() -> Optional[Client]:
    """
    Create a Supabase client with service account authentication.
    
    This bypasses normal user authentication and allows direct file access
    regardless of RLS policies, enabling the backend to download any file.
    
    Returns:
        Optional[Client]: An authenticated Supabase client or None on failure
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not service_role_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        return None
    
    try:
        # Create a client with the service role key instead of the anon key
        # This gives admin access that bypasses RLS policies
        print("Creating Supabase client with service role key")
        service_client = create_client(supabase_url, service_role_key)
        print("✓ Successfully created service-role authenticated Supabase client")
        return service_client
    except Exception as e:
        print(f"✗ Failed to create service-authenticated Supabase client: {str(e)}")
        return None

def download_file_with_service_role(bucket_name: str, file_path: str) -> Optional[bytes]:
    """
    Download a file from Supabase storage using service role authentication,
    bypassing RLS policies.
    
    Args:
        bucket_name: The name of the storage bucket (e.g., "files")
        file_path: The path of the file in the bucket
        
    Returns:
        Optional[bytes]: The file content as bytes, or None on failure
    """
    service_client = get_service_authenticated_supabase()
    if not service_client:
        return None
        
    try:
        print(f"Attempting to download {file_path} from {bucket_name} with service role")
        response = service_client.storage.from_(bucket_name).download(file_path)
        print(f"✓ Successfully downloaded file with service role: {file_path}")
        return response
    except Exception as e:
        print(f"✗ Failed to download with service role: {str(e)}")
        return None

# Example usage in main.py:
"""
from supabase_service_auth import download_file_with_service_role

# In your process endpoint:
try:
    # First try normal auth download
    response = supabase_client.storage.from_("files").download(file_path)
except Exception:
    # Fall back to service role auth
    response = download_file_with_service_role("files", file_path)
    if not response:
        raise HTTPException(status_code=404, detail="File not found")
"""
