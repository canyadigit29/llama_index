#!/usr/bin/env python3
"""
Environment Variable Quick Check

This script performs a quick check of required environment variables
and logs warnings for any missing variables. It's designed to be run
at application startup to provide immediate feedback about the environment.

Usage:
    python env_quickcheck.py
"""

import os
import logging
import sys
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("env_quickcheck")

# Define the environment variables to check
CRITICAL_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY", 
    "PINECONE_API_KEY",
    "PINECONE_ENVIRONMENT",
    "OPENAI_API_KEY"
]

IMPORTANT_VARS = [
    "SUPABASE_JWT_SECRET",
    "LLAMAINDEX_API_KEY",
    "PORT"
]

OPTIONAL_VARS = [
    "PINECONE_INDEX_NAME",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSIONS",
    "FRONTEND_URL",
    "ENVIRONMENT",
    "DEBUG"
]

# Define default values for some variables
DEFAULT_VALUES = {
    "PORT": "8000",
    "PINECONE_INDEX_NAME": "developer-quickstart-py",
    "EMBEDDING_MODEL": "text-embedding-3-large",
    "EMBEDDING_DIMENSIONS": "3072",
    "ENVIRONMENT": "production",
}

def check_env_vars() -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Check environment variables and return lists of missing variables
    
    Returns:
        Tuple containing:
        - List of missing critical variables
        - List of missing important variables
        - List of missing optional variables
        - List of warnings about variable values
    """
    missing_critical = []
    missing_important = []
    missing_optional = []
    warnings = []
    
    # Check critical variables
    for var in CRITICAL_VARS:
        if not os.environ.get(var):
            missing_critical.append(var)
    
    # Check important variables
    for var in IMPORTANT_VARS:
        if not os.environ.get(var):
            missing_important.append(var)
    
    # Check optional variables
    for var in OPTIONAL_VARS:
        if not os.environ.get(var) and var not in DEFAULT_VALUES:
            missing_optional.append(var)
    
    # Special check for PORT on Railway
    if os.environ.get("RAILWAY_SERVICE_ID") and os.environ.get("PORT") != "8000":
        warnings.append(f"PORT is set to '{os.environ.get('PORT')}' but should be '8000' for Railway")
    
    # Special check for Pinecone environment format
    pinecone_env = os.environ.get("PINECONE_ENVIRONMENT")
    if pinecone_env:
        known_regions = ["us-east-1", "us-west-2", "gcp-starter", "asia-southeast1"]
        if pinecone_env not in known_regions and "-" not in pinecone_env:
            warnings.append(f"PINECONE_ENVIRONMENT value '{pinecone_env}' may be incorrect. Expected format like 'us-east-1'.")
    
    return missing_critical, missing_important, missing_optional, warnings

def main() -> int:
    """
    Main function to run the quick check
    
    Returns:
        Exit code (0 for success, 1 for critical vars missing)
    """
    logger.info("==========================================")
    logger.info("ENVIRONMENT VARIABLE QUICK CHECK")
    logger.info("==========================================")
    
    missing_critical, missing_important, missing_optional, warnings = check_env_vars()
    
    # Print summary
    logger.info(f"Critical variables checked: {len(CRITICAL_VARS)}")
    logger.info(f"Important variables checked: {len(IMPORTANT_VARS)}")
    logger.info(f"Optional variables checked: {len(OPTIONAL_VARS)}")
    
    # Log results
    if not missing_critical and not missing_important and not warnings:
        logger.info("✅ All critical and important environment variables are set")
    
    if missing_critical:
        logger.error("❌ CRITICAL VARIABLES MISSING:")
        for var in missing_critical:
            logger.error(f"  - {var} is not set - Application may not function correctly!")
    
    if missing_important:
        logger.warning("⚠️ IMPORTANT VARIABLES MISSING:")
        for var in missing_important:
            logger.warning(f"  - {var} is not set - Some features may be limited")
    
    if missing_optional:
        logger.info("ℹ️ OPTIONAL VARIABLES MISSING (using defaults):")
        for var in missing_optional:
            default = DEFAULT_VALUES.get(var, "none")
            logger.info(f"  - {var} is not set - Using default: {default}")
    
    if warnings:
        logger.warning("⚠️ WARNINGS:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("==========================================")
    
    # Return appropriate exit code
    return 1 if missing_critical else 0

if __name__ == "__main__":
    sys.exit(main())
