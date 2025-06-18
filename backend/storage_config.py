"""
Supabase Storage Configuration Module

This module provides a centralized configuration for Supabase storage
with environment variable support for custom bucket names.
"""

import os
from typing import Dict, Any, Optional
import json

# Default bucket name - will be used if no environment variable is set
DEFAULT_BUCKET = "files"

# Get bucket name from environment variable or use default
STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", DEFAULT_BUCKET)

def get_bucket_name() -> str:
    """
    Get the configured bucket name for file storage.
    
    Returns:
        str: The bucket name to use for file storage
    """
    return STORAGE_BUCKET

def get_file_path(user_id: str, file_id: str) -> str:
    """
    Generate the standardized file path to use in storage.
    
    Args:
        user_id: The user's unique identifier
        file_id: The file's unique identifier
        
    Returns:
        str: The standardized file path for storage
    """
    return f"{user_id}/{file_id}"

def get_file_paths_to_try(file_id: str, user_id: Optional[str] = None, original_path: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a dictionary of file paths to try in order of preference.
    
    Args:
        file_id: The file's unique identifier
        user_id: Optional user identifier
        original_path: Optional original path if different from standard format
        
    Returns:
        Dict[str, str]: Dictionary of path_type -> path mappings to try in order
    """
    paths = {}
    
    # Start with the original path if provided
    if original_path:
        paths["original"] = original_path
    
    # Try user_id/file_id format
    if user_id:
        paths["user_id_file_id"] = f"{user_id}/{file_id}"
    
    # Try just the file_id as a fallback
    paths["file_id_only"] = file_id
    
    return paths

def log_storage_operations(operation: str, bucket: str, path: str, success: bool, error: Optional[Exception] = None) -> Dict[str, Any]:
    """
    Log storage operations for debugging purposes
    
    Args:
        operation: The operation being performed (e.g., "download", "upload")
        bucket: The bucket name
        path: The file path
        success: Whether the operation was successful
        error: The exception if the operation failed
        
    Returns:
        Dict[str, Any]: Dictionary containing operation details for logging
    """
    result = {
        "operation": operation,
        "bucket": bucket,
        "path": path,
        "success": success,
        "timestamp": str(import_datetime().now())
    }
    
    if error:
        result["error"] = str(error)
        result["error_type"] = type(error).__name__
    
    # Print to console for debugging
    if success:
        print(f"[STORAGE] {operation} successful: bucket='{bucket}', path='{path}'")
    else:
        print(f"[STORAGE] {operation} failed: bucket='{bucket}', path='{path}', error='{str(error)}'")
    
    return result

# Helper function to avoid circular imports
def import_datetime():
    from datetime import datetime
    return datetime
