#!/usr/bin/env python3
"""
Environment Variable Template Generator

This script generates a template .env file with all required
environment variables for the LlamaIndex backend. It can also
check an existing .env file for completeness.

Usage:
    python env_template.py [--check] [--output=.env.template]

Options:
    --check          Check existing .env file instead of creating a template
    --output=FILE    Specify output file (default: .env.template)
"""

import os
import sys
import re
from typing import Dict, List, Set

# Define variable categories
REQUIRED_VARS = [
    # Supabase Configuration
    {"name": "SUPABASE_URL", "description": "URL of your Supabase instance", "example": "https://your-project.supabase.co"},
    {"name": "SUPABASE_ANON_KEY", "description": "Supabase anonymous/public API key", "example": "eyJhbGc..."},
    {"name": "SUPABASE_JWT_SECRET", "description": "Supabase JWT secret for token verification", "example": "your-jwt-secret"},
    {"name": "SUPABASE_SERVICE_ROLE_KEY", "description": "Supabase service role key for admin operations", "example": "eyJhbGc..."},
    
    # Pinecone Configuration
    {"name": "PINECONE_API_KEY", "description": "API key for Pinecone vector database", "example": "12345-abcde-..."},
    {"name": "PINECONE_ENVIRONMENT", "description": "Pinecone environment (e.g., us-east-1 for AWS)", "example": "us-east-1"},
    {"name": "PINECONE_INDEX_NAME", "description": "Name of your Pinecone index", "example": "developer-quickstart-py"},
    
    # OpenAI Configuration
    {"name": "OPENAI_API_KEY", "description": "OpenAI API key", "example": "sk-..."},
    
    # Authentication
    {"name": "LLAMAINDEX_API_KEY", "description": "API key for accessing the LlamaIndex backend", "example": "a-strong-random-string"},
]

OPTIONAL_VARS = [
    # Deployment Settings
    {"name": "PORT", "description": "Port to run the API on (must be 8000 for Railway)", "example": "8000", "default": "8000"},
    
    # Frontend Integration
    {"name": "FRONTEND_URL", "description": "URL of the frontend for CORS", "example": "https://your-frontend.com", "default": ""},
    
    # Embedding Configuration
    {"name": "EMBEDDING_MODEL", "description": "OpenAI embedding model to use", "example": "text-embedding-3-large", "default": "text-embedding-3-large"},
    {"name": "EMBEDDING_DIMENSIONS", "description": "Dimensions for the embedding model", "example": "3072", "default": "3072"},
    
    # Environment Settings
    {"name": "ENVIRONMENT", "description": "Environment (development, production, staging)", "example": "development", "default": "production"},
    {"name": "DEBUG", "description": "Enable debug mode", "example": "true", "default": "false"},
]

def generate_template() -> str:
    """Generate a template .env file with all required and optional variables."""
    lines = [
        "# LlamaIndex Backend Environment Configuration",
        "# Generated template for required environment variables",
        "# Fill in the values and rename to .env for local development",
        "",
        "# ======== REQUIRED VARIABLES ========",
        "",
    ]
    
    # Add required variables
    for var in REQUIRED_VARS:
        lines.append(f"# {var['description']}")
        lines.append(f"{var['name']}={var['example']}")
        lines.append("")
    
    # Add optional variables
    lines.append("# ======== OPTIONAL VARIABLES ========")
    lines.append("")
    
    for var in OPTIONAL_VARS:
        default = var.get('default', '')
        lines.append(f"# {var['description']}")
        lines.append(f"# Default: {default}" if default else "# No default value")
        lines.append(f"{var['name']}={var['example']}")
        lines.append("")
    
    # Add Railway-specific variables
    lines.append("# ======== RAILWAY-SPECIFIC VARIABLES ========")
    lines.append("# These are automatically set by Railway and don't need to be configured locally")
    lines.append("# RAILWAY_SERVICE_ID=...")
    lines.append("# RAILWAY_ENVIRONMENT_NAME=...")
    lines.append("# RAILWAY_SERVICE_NAME=...")
    
    return "\n".join(lines)

def check_env_file(filename: str = ".env") -> bool:
    """
    Check if an existing .env file has all required variables.
    
    Returns:
        bool: True if all required variables are present, False otherwise
    """
    # Check if .env file exists
    if not os.path.exists(filename):
        print(f"Error: {filename} file not found.")
        return False
    
    # Read .env file
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extract variables from .env
    env_vars = set()
    for line in content.split('\n'):
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Extract variable name (before = sign)
        match = re.match(r'^([A-Za-z0-9_]+)=', line)
        if match:
            env_vars.add(match.group(1))
    
    # Check for missing required variables
    missing_required = []
    for var in REQUIRED_VARS:
        if var['name'] not in env_vars:
            missing_required.append(var)
    
    # Check for missing optional variables
    missing_optional = []
    for var in OPTIONAL_VARS:
        if var['name'] not in env_vars:
            missing_optional.append(var)
    
    # Print results
    if not missing_required and not missing_optional:
        print(f"✅ {filename} file contains all required and optional variables.")
        return True
    
    if not missing_required:
        print(f"✅ {filename} file contains all required variables.")
    else:
        print(f"❌ {filename} file is missing {len(missing_required)} required variables:")
        for var in missing_required:
            print(f"  - {var['name']} ({var['description']})")
    
    if missing_optional:
        print(f"ℹ️ {filename} file is missing {len(missing_optional)} optional variables:")
        for var in missing_optional:
            default = var.get('default', 'None')
            print(f"  - {var['name']} ({var['description']}, default: {default})")
    
    return len(missing_required) == 0

def main():
    """Main function to generate template or check existing .env file."""
    # Parse command-line arguments
    check_mode = "--check" in sys.argv
    output_file = ".env.template"
    
    for arg in sys.argv:
        if arg.startswith("--output="):
            output_file = arg.split("=")[1]
    
    if check_mode:
        # Check existing .env file
        env_file = output_file if output_file != ".env.template" else ".env"
        result = check_env_file(env_file)
        return 0 if result else 1
    else:
        # Generate template
        template = generate_template()
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(template)
        
        print(f"Template .env file generated at: {output_file}")
        print(f"Edit this file with your actual values and rename to .env for local development.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
