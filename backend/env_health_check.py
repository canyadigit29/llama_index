#!/usr/bin/env python3
"""
Environment Variable Health Check for LlamaIndex Backend

This script checks for the presence and validity of all required
environment variables for the LlamaIndex backend deployment on Railway.
It will log warnings for missing or potentially misconfigured variables.

Usage:
    python env_health_check.py [--verbose]

Add to your main.py or use in a pre-flight check before starting the server.
"""

import os
import sys
import re
import logging
from typing import Dict, List, Optional, Tuple, Union
import requests
from urllib.parse import urlparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ENV_HEALTH_CHECK")

# Environment variable categories and their requirements
ENV_VARS = {
    "ESSENTIAL": {
        # Supabase Configuration
        "SUPABASE_URL": {
            "required": True, 
            "validation": lambda x: bool(urlparse(x).netloc),
            "message": "Must be a valid URL"
        },
        "SUPABASE_ANON_KEY": {
            "required": True,
            "validation": lambda x: len(x) > 20,
            "message": "Should be a long API key string"
        },
        "SUPABASE_JWT_SECRET": {
            "required": True,
            "validation": lambda x: len(x) > 20,
            "message": "Should be a long secret string"
        },
        "SUPABASE_SERVICE_ROLE_KEY": {
            "required": True,
            "validation": lambda x: len(x) > 20,
            "message": "Should be a long API key string"
        },
        
        # Pinecone Configuration
        "PINECONE_API_KEY": {
            "required": True,
            "validation": lambda x: len(x) > 20,
            "message": "Should be a valid Pinecone API key"
        },        "PINECONE_ENVIRONMENT": {
            "required": True,
            "validation": lambda x: bool(x) and (x in ["us-east-1", "us-west-2", "gcp-starter", "asia-southeast1"] or "-" in x),
            "message": "Should specify a valid Pinecone environment (e.g., 'us-east-1' for AWS or 'gcp-starter' for GCP)"
        },
        "PINECONE_INDEX_NAME": {
            "required": True,
            "validation": lambda x: bool(x),
            "message": "Should specify a Pinecone index name",
            "default": "developer-quickstart-py"
        },
        
        # OpenAI Configuration
        "OPENAI_API_KEY": {
            "required": True,
            "validation": lambda x: x.startswith("sk-") and len(x) > 30,
            "message": "Should be a valid OpenAI API key starting with 'sk-'"
        },
        
        # Authentication
        "LLAMAINDEX_API_KEY": {
            "required": True,
            "validation": lambda x: len(x) > 16,
            "message": "Should be a strong, randomly-generated string"
        },
        
        # Deployment Settings
        "PORT": {
            "required": True,
            "validation": lambda x: x == "8000",
            "message": "Must be set to 8000 for Railway deployment",
            "default": "8000"
        }
    },
    
    "OPTIONAL": {
        # Frontend Integration
        "FRONTEND_URL": {
            "required": False,
            "validation": lambda x: bool(urlparse(x).netloc) if x else True,
            "message": "Should be a valid URL if provided"
        },
        
        # Embedding Configuration
        "EMBEDDING_MODEL": {
            "required": False,
            "validation": lambda x: bool(x),
            "message": "Should specify an OpenAI embedding model",
            "default": "text-embedding-3-large"
        },
        "EMBEDDING_DIMENSIONS": {
            "required": False,
            "validation": lambda x: x.isdigit() and int(x) > 0,
            "message": "Should be a positive integer",
            "default": "3072"
        },
        
        # Storage Configuration
        "STORAGE_BUCKET_NAME": {
            "required": False,
            "validation": lambda x: bool(x),
            "message": "Should specify a Supabase storage bucket name",
            "default": "files"
        },
        
        # Environment Settings
        "ENVIRONMENT": {
            "required": False,
            "validation": lambda x: x in ["development", "production", "staging"],
            "message": "Should be 'development', 'production', or 'staging'",
            "default": "production"
        },
        "DEBUG": {
            "required": False,
            "validation": lambda x: x.lower() in ["true", "false", "1", "0", "yes", "no"],
            "message": "Should be a boolean value",
            "default": "false"
        }
    }
}

def check_env_vars() -> Tuple[bool, Dict[str, Dict[str, Union[bool, str]]]]:
    """
    Check all environment variables for presence and validity.
    
    Returns:
        Tuple containing:
        - Boolean indicating if all required variables are present and valid
        - Dictionary with detailed status of each variable
    """
    all_valid = True
    results = {}
    
    # Check all variables across categories
    for category, variables in ENV_VARS.items():
        for var_name, config in variables.items():
            var_value = os.environ.get(var_name)
            required = config.get("required", False)
            validation = config.get("validation", lambda x: True)
            message = config.get("message", "")
            default = config.get("default", None)
            
            # Check if variable exists
            if var_value is None:
                if required:
                    all_valid = False
                    status = "MISSING_REQUIRED"
                else:
                    status = "MISSING_OPTIONAL"
                    if default:
                        var_value = default
                        status = f"USING_DEFAULT: {default}"
            else:
                # Validate variable value
                try:
                    is_valid = validation(var_value)
                    if is_valid:
                        status = "VALID"
                    else:
                        status = f"INVALID: {message}"
                        if required:
                            all_valid = False
                except Exception as e:
                    status = f"VALIDATION_ERROR: {str(e)}"
                    if required:
                        all_valid = False
            
            # Store result
            results[var_name] = {
                "status": status,
                "required": required,
                "category": category,
                # Don't include actual value for security reasons
                "value_set": var_value is not None
            }
    
    return all_valid, results

def check_supabase_connectivity() -> Dict[str, Union[bool, str]]:
    """Check if Supabase connection details are valid by making a test request."""
    result = {"success": False, "message": "Not attempted"}
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        result["message"] = "Missing Supabase URL or key"
        return result
    
    try:
        # Try to make a simple request to Supabase
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result["success"] = True
            result["message"] = "Successfully connected to Supabase"
        else:
            result["message"] = f"Supabase returned status code: {response.status_code}"
    except Exception as e:
        result["message"] = f"Error connecting to Supabase: {str(e)}"
    
    return result

def check_pinecone_connectivity() -> Dict[str, Union[bool, str]]:
    """Check if Pinecone connection details are valid by making a test request."""
    result = {"success": False, "message": "Not attempted"}
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    
    if not api_key or not environment:
        result["message"] = "Missing Pinecone API key or environment"
        return result
    
    # Validate environment format
    known_regions = ["us-east-1", "us-west-2", "gcp-starter", "asia-southeast1"]
    if environment not in known_regions and "-" not in environment:
        result["message"] = f"Pinecone environment format seems invalid: '{environment}'. Expected formats include 'us-east-1', 'us-west-2', 'gcp-starter'."
        return result
    
    try:
        # First try to use the new Pinecone client API (same as in main.py)
        try:
            # Dynamically import to avoid dependency issues
            import importlib
            pinecone_spec = importlib.util.find_spec("pinecone")
            
            if pinecone_spec:
                pinecone = importlib.import_module("pinecone")
                
                # Check if the new API is available
                if hasattr(pinecone, "Pinecone"):
                    pc = pinecone.Pinecone(api_key=api_key)
                    
                    # Try to list indexes
                    try:
                        indices = pc.list_indexes().names()
                        result["success"] = True
                        result["message"] = f"Successfully connected to Pinecone environment '{environment}' using modern API"
                        
                        # Check if the specified index exists
                        index_found = index_name in indices
                        if not index_found:
                            result["message"] += f", but index '{index_name}' was not found"
                            # Don't mark as failure if index doesn't exist
                            # The app will create it if needed
                        
                        return result
                    except Exception as e:
                        # Fall back to the legacy approach if this fails
                        pass
        except ImportError:
            # Module not available, will fall back to the REST API approach
            pass
                    
        # Fall back to the REST API approach
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"https://controller.{environment}.pinecone.io/databases",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result["success"] = True
            result["message"] = f"Successfully connected to Pinecone environment '{environment}' using REST API"
            
            # Check for the index
            try:
                indices = response.json()
                index_found = any(index.get("name") == index_name for index in indices)
                if not index_found:
                    result["message"] += f", but index '{index_name}' was not found"
                    # Don't mark as failure if index doesn't exist
            except Exception:
                result["message"] += ", but couldn't verify index existence"
        else:
            result["message"] = f"Pinecone returned status code: {response.status_code} for environment '{environment}'"
    except requests.exceptions.ConnectionError:
        result["message"] = f"Connection error - Unable to connect to Pinecone using environment: '{environment}'. Please verify this is the correct region format (e.g., 'us-east-1')."
    except Exception as e:
        result["message"] = f"Error connecting to Pinecone: {str(e)}"
    
    return result

def check_openai_connectivity() -> Dict[str, Union[bool, str]]:
    """Check if OpenAI API key is valid by making a test request."""
    result = {"success": False, "message": "Not attempted"}
    
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        result["message"] = "Missing OpenAI API key"
        return result
    
    try:
        # Try to make a simple request to OpenAI
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result["success"] = True
            result["message"] = "Successfully connected to OpenAI API"
            
            # Check for embedding model
            embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")
            try:
                models = response.json().get("data", [])
                model_found = any(model.get("id") == embedding_model for model in models)
                if not model_found:
                    result["message"] += f", but model '{embedding_model}' was not found or not accessible"
            except Exception:
                result["message"] += ", but couldn't verify model existence"
        else:
            result["message"] = f"OpenAI API returned status code: {response.status_code}"
    except Exception as e:
        result["message"] = f"Error connecting to OpenAI API: {str(e)}"
    
    return result

def check_railway_specific() -> Dict[str, Union[bool, str]]:
    """Check Railway-specific environment variables."""
    railway_vars = {
        "RAILWAY_SERVICE_ID": os.environ.get("RAILWAY_SERVICE_ID"),
        "RAILWAY_ENVIRONMENT_NAME": os.environ.get("RAILWAY_ENVIRONMENT_NAME"),
        "RAILWAY_SERVICE_NAME": os.environ.get("RAILWAY_SERVICE_NAME")
    }
    
    is_railway = any(railway_vars.values())
    message = "Running on Railway" if is_railway else "Not running on Railway"
    
    return {
        "is_railway": is_railway,
        "message": message,
        "variables": railway_vars
    }

def check_port_binding() -> Dict[str, Union[bool, str]]:
    """Check if PORT is correctly set to 8000 for Railway."""
    port = os.environ.get("PORT", "8000")
    result = {
        "success": port == "8000",
        "port": port,
        "message": f"PORT is set to {port}"
    }
    
    if port != "8000":
        result["message"] = f"WARNING: PORT is set to {port}, but Railway expects 8000"
    
    return result

def run_health_check(verbose: bool = False) -> Dict:
    """
    Run all health checks and return a comprehensive status report.
    
    Args:
        verbose: Whether to include detailed information in the report
        
    Returns:
        Dictionary containing check results
    """
    # Check environment variables
    env_valid, env_results = check_env_vars()
    
    # Run connectivity checks only if essential variables are set
    connectivity_checks = {}
    if env_valid or verbose:
        connectivity_checks = {
            "supabase": check_supabase_connectivity(),
            "pinecone": check_pinecone_connectivity(),
            "openai": check_openai_connectivity()
        }
    
    # Check Railway-specific configuration
    railway_status = check_railway_specific()
    port_status = check_port_binding()
    
    # Build detailed report
    report = {
        "status": "healthy" if env_valid and all(
            check["success"] for check in connectivity_checks.values()
        ) else "unhealthy",
        "environment_variables": {
            "valid": env_valid,
            "details": env_results if verbose else {
                k: v for k, v in env_results.items() 
                if v["status"] != "VALID" or verbose
            }
        },
        "connectivity": connectivity_checks,
        "railway": railway_status,
        "port": port_status,
        "timestamp": logging.Formatter().converter()
    }
    
    return report

def log_health_check_results(report: Dict) -> None:
    """Log health check results with appropriate severity levels."""
    status = report["status"]
    
    if status == "healthy":
        logger.info("✅ HEALTH CHECK PASSED: All required environment variables are properly configured")
    else:
        logger.error("❌ HEALTH CHECK FAILED: There are issues with the environment configuration")
    
    # Log environment variable issues
    env_vars = report["environment_variables"]
    if not env_vars["valid"]:
        for var_name, details in env_vars["details"].items():
            if details["status"] != "VALID":
                if details["required"]:
                    logger.error(f"❌ {var_name}: {details['status']}")
                else:
                    logger.warning(f"⚠️ {var_name}: {details['status']}")
    
    # Log connectivity issues
    for service, result in report["connectivity"].items():
        if result["success"]:
            logger.info(f"✅ {service.upper()}: {result['message']}")
        else:
            logger.error(f"❌ {service.upper()}: {result['message']}")
    
    # Log Railway-specific information
    railway = report["railway"]
    if railway["is_railway"]:
        logger.info(f"🚂 {railway['message']}")
    else:
        logger.info(f"💻 {railway['message']}")
    
    # Log port status
    port = report["port"]
    if port["success"]:
        logger.info(f"✅ PORT: {port['message']}")
    else:
        logger.error(f"❌ PORT: {port['message']}")

def main() -> int:
    """Main function that runs health checks and logs results."""
    verbose = "--verbose" in sys.argv
    
    logger.info("==========================================")
    logger.info("STARTING ENVIRONMENT VARIABLE HEALTH CHECK")
    logger.info("==========================================")
    
    try:
        report = run_health_check(verbose)
        log_health_check_results(report)
        
        # Print JSON report if requested
        if "--json" in sys.argv:
            print(json.dumps(report, indent=2, default=str))
        
        logger.info("==========================================")
        logger.info(f"HEALTH CHECK COMPLETE: Status = {report['status'].upper()}")
        logger.info("==========================================")
        
        # Return 0 even if unhealthy to allow the application to continue
        # This prevents the build from failing due to health check issues
        if "--strict" in sys.argv:
            return 0 if report["status"] == "healthy" else 1
        else:
            # In non-strict mode, always return 0 to allow startup to continue
            return 0
    except Exception as e:
        logger.error(f"Error running health check: {str(e)}")
        logger.error("Continuing anyway to avoid blocking application startup")
        return 0  # Allow the application to start even if the health check fails

if __name__ == "__main__":
    sys.exit(main())
