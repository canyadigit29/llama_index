#!/usr/bin/env python3
"""
Pinecone Diagnostic Utility

This script performs advanced diagnostics on Pinecone connectivity issues,
checking network, API keys, and environment configuration. It's designed
to help troubleshoot common Pinecone setup issues.

Usage:
    python pinecone_diagnostics.py [--verbose]
"""

import os
import sys
import json
import socket
import importlib.util
import requests
import logging
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pinecone_diagnostics")

def check_environment_variables() -> Dict[str, Any]:
    """Check if all required Pinecone environment variables are set."""
    results = {}
    required_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
    optional_vars = ["PINECONE_INDEX_NAME"]
    
    # Check required variables
    for var in required_vars:
        value = os.environ.get(var)
        results[var] = {
            "status": "set" if value else "missing",
            "message": "Present" if value else "Missing - this must be set for Pinecone to work"
        }
        
        # Special case for PINECONE_ENVIRONMENT format
        if var == "PINECONE_ENVIRONMENT" and value:
            if "-" in value:
                cloud = value.split("-")[0]
                region = "-".join(value.split("-")[1:])
                
                if cloud in ["us", "eu", "asia", "gcp"]:
                    results[var]["message"] = f"Format looks valid: cloud='{cloud}', region='{region}'"
                else:
                    results[var]["message"] = f"Unusual format: '{value}' - expected formats include 'us-east-1', 'gcp-starter'"
            else:
                results[var]["message"] = f"Format may be incorrect: '{value}' - expected format includes a hyphen like 'us-east-1'"
    
    # Check optional variables
    for var in optional_vars:
        value = os.environ.get(var)
        if not value:
            default_values = {
                "PINECONE_INDEX_NAME": "developer-quickstart-py"
            }
            default = default_values.get(var, "none")
            results[var] = {
                "status": "default",
                "message": f"Using default value: '{default}'"
            }
        else:
            results[var] = {
                "status": "set",
                "message": "Present"
            }
    
    return results

def check_network_connectivity(environment: str) -> Dict[str, Any]:
    """Check basic network connectivity to Pinecone endpoints."""
    result = {
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    # Formulate endpoints to test
    endpoints = [
        f"controller.{environment}.pinecone.io",
        f"index-1.{environment}.pinecone.io",  # Example index endpoint pattern
    ]
    
    # Test connectivity to each endpoint
    port = 443  # HTTPS port
    connectivity_results = {}
    
    for endpoint in endpoints:
        try:
            # Try TCP socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            
            logger.info(f"Testing TCP connection to {endpoint}:{port}...")
            conn_result = sock.connect_ex((endpoint, port))
            if conn_result == 0:
                status = "success"
                message = f"Successfully connected to {endpoint}:{port}"
            else:
                status = "failed"
                message = f"Failed to connect to {endpoint}:{port} with error code {conn_result}"
            
            sock.close()
        except socket.gaierror:
            status = "failed"
            message = f"DNS resolution failed for {endpoint}"
        except socket.timeout:
            status = "failed"
            message = f"Connection timeout for {endpoint}:{port}"
        except Exception as e:
            status = "failed"
            message = f"Error connecting to {endpoint}:{port}: {str(e)}"
            
        connectivity_results[endpoint] = {
            "status": status,
            "message": message
        }
    
    # Determine overall status
    if all(result["status"] == "success" for result in connectivity_results.values()):
        result["status"] = "success"
        result["message"] = "Network connectivity to Pinecone endpoints successful"
    elif any(result["status"] == "success" for result in connectivity_results.values()):
        result["status"] = "partial"
        result["message"] = "Partial connectivity to Pinecone endpoints"
    else:
        result["status"] = "failed"
        result["message"] = "Failed to connect to any Pinecone endpoints"
    
    result["details"] = connectivity_results
    return result

def test_modern_pinecone_api() -> Dict[str, Any]:
    """Test connection using the modern Pinecone API."""
    result = {
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    index_name = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")
    
    if not api_key:
        result["status"] = "failed"
        result["message"] = "PINECONE_API_KEY not set"
        return result
        
    if not environment:
        result["status"] = "failed"
        result["message"] = "PINECONE_ENVIRONMENT not set"
        return result
    
    try:
        # Check if module exists
        pinecone_spec = importlib.util.find_spec("pinecone")
        
        if not pinecone_spec:
            result["status"] = "failed"
            result["message"] = "Pinecone module not installed"
            return result
        
        # Import the module
        pinecone = importlib.import_module("pinecone")
        
        # Check for modern API
        if not hasattr(pinecone, "Pinecone"):
            result["status"] = "failed"
            result["message"] = "Modern Pinecone API not available - module too old"
            result["details"]["module_version"] = getattr(pinecone, "__version__", "unknown")
            return result
        
        # Initialize client
        result["details"]["client_init"] = "Attempting to initialize Pinecone client"
        pc = pinecone.Pinecone(api_key=api_key)
        result["details"]["client_init"] = "Successfully initialized Pinecone client"
        
        # Try listing indexes
        result["details"]["list_indexes"] = "Attempting to list indexes"
        try:
            indexes = pc.list_indexes().names()
            result["details"]["list_indexes"] = f"Successfully listed indexes: {indexes}"
            result["details"]["indexes"] = indexes
            
            # Check if specific index exists
            if index_name in indexes:
                result["details"]["index_found"] = True
            else:
                result["details"]["index_found"] = False
                result["details"]["index_name"] = index_name
            
            result["status"] = "success"
            result["message"] = "Successfully connected to Pinecone using modern API"
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"Error listing indexes: {str(e)}"
            result["details"]["list_indexes_error"] = str(e)
    except Exception as e:
        result["status"] = "failed"
        result["message"] = f"Error with modern Pinecone API: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result

def test_rest_api() -> Dict[str, Any]:
    """Test connection using direct REST API calls."""
    result = {
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    
    if not api_key:
        result["status"] = "failed"
        result["message"] = "PINECONE_API_KEY not set"
        return result
        
    if not environment:
        result["status"] = "failed"
        result["message"] = "PINECONE_ENVIRONMENT not set"
        return result
    
    try:
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
        # Test endpoint URL
        url = f"https://controller.{environment}.pinecone.io/databases"
        result["details"]["request_url"] = url
        
        # Make request
        response = requests.get(url, headers=headers, timeout=5)
        result["details"]["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["status"] = "success"
            result["message"] = "Successfully connected to Pinecone via REST API"
            
            try:
                data = response.json()
                result["details"]["response_data"] = data
            except Exception as e:
                result["details"]["json_parsing_error"] = str(e)
        else:
            result["status"] = "failed"
            result["message"] = f"Failed with status code: {response.status_code}"
            result["details"]["response_text"] = response.text
    except requests.exceptions.ConnectionError as e:
        result["status"] = "failed"
        result["message"] = f"Connection error: {str(e)}"
        result["details"]["error"] = str(e)
    except Exception as e:
        result["status"] = "failed"
        result["message"] = f"Error with REST API: {str(e)}"
        result["details"]["error"] = str(e)
    
    return result

def run_diagnostics() -> Dict[str, Any]:
    """Run all diagnostic checks and return comprehensive report."""
    # Get environment info
    environment = os.environ.get("PINECONE_ENVIRONMENT", "")
    
    diagnostics = {
        "environment": environment,
        "timestamp": logging.Formatter().converter(),
        "environment_variables": check_environment_variables()
    }
    
    # Only run connectivity tests if environment is set
    if environment:
        diagnostics["network"] = check_network_connectivity(environment)
        diagnostics["modern_api"] = test_modern_pinecone_api()
        diagnostics["rest_api"] = test_rest_api()
        
        # Determine overall status
        modern_api_success = diagnostics["modern_api"]["status"] == "success"
        rest_api_success = diagnostics["rest_api"]["status"] == "success"
        network_success = diagnostics["network"]["status"] in ["success", "partial"]
        
        if modern_api_success:
            diagnostics["status"] = "healthy"
            diagnostics["message"] = "Pinecone connection is working correctly with modern API"
        elif rest_api_success:
            diagnostics["status"] = "partial"
            diagnostics["message"] = "Pinecone REST API works but modern API failed"
        elif network_success:
            diagnostics["status"] = "network_only"
            diagnostics["message"] = "Network connectivity exists but API authentication failed"
        else:
            diagnostics["status"] = "unhealthy"
            diagnostics["message"] = "All Pinecone connectivity checks failed"
    else:
        diagnostics["status"] = "missing_config"
        diagnostics["message"] = "Missing Pinecone environment configuration"
    
    return diagnostics

def log_diagnostics(report: Dict[str, Any]) -> None:
    """Log diagnostic results with appropriate severity levels."""
    status = report.get("status", "unknown")
    
    logger.info("==========================================")
    logger.info("PINECONE CONNECTIVITY DIAGNOSTIC RESULTS")
    logger.info("==========================================")
    
    logger.info(f"Status: {status.upper()}")
    logger.info(f"Message: {report.get('message', 'No message')}")
    logger.info(f"Environment: {report.get('environment', 'Not set')}")
    
    # Log environment variables status
    env_vars = report.get("environment_variables", {})
    for var, details in env_vars.items():
        if details["status"] == "missing":
            logger.error(f"❌ {var}: {details['message']}")
        else:
            logger.info(f"✓ {var}: {details['message']}")
    
    # Log network connectivity
    if "network" in report:
        network = report["network"]
        if network["status"] == "success":
            logger.info(f"✓ Network: {network['message']}")
        elif network["status"] == "partial":
            logger.warning(f"⚠️ Network: {network['message']}")
        else:
            logger.error(f"❌ Network: {network['message']}")
    
    # Log API test results
    if "modern_api" in report:
        modern_api = report["modern_api"]
        if modern_api["status"] == "success":
            logger.info(f"✓ Modern API: {modern_api['message']}")
        else:
            logger.error(f"❌ Modern API: {modern_api['message']}")
    
    if "rest_api" in report:
        rest_api = report["rest_api"]
        if rest_api["status"] == "success":
            logger.info(f"✓ REST API: {rest_api['message']}")
        else:
            logger.warning(f"⚠️ REST API: {rest_api['message']}")
    
    logger.info("==========================================")
    
    # Provide recommendations
    logger.info("RECOMMENDATIONS:")
    if status == "healthy":
        logger.info("✓ Pinecone is configured correctly and accessible!")
    elif status == "partial":
        logger.info("⚠️ The application may work but health checks might fail.")
        logger.info("   Consider updating the pinecone-client library.")
    elif status == "network_only":
        logger.info("❌ Check your Pinecone API key - network connectivity works but API calls are failing.")
    elif status == "missing_config":
        logger.info("❌ Set the PINECONE_ENVIRONMENT and PINECONE_API_KEY environment variables.")
    else:
        logger.info("❌ Check:")
        logger.info("   1. Your network connectivity to Pinecone")
        logger.info("   2. Your Pinecone API key")
        logger.info("   3. Your Pinecone environment format (should be like 'us-east-1')")
    
    logger.info("==========================================")

def main() -> int:
    """Main function that runs all diagnostic checks."""
    verbose = "--verbose" in sys.argv
    json_output = "--json" in sys.argv
    
    diagnostics = run_diagnostics()
    
    if not json_output:
        log_diagnostics(diagnostics)
    else:
        print(json.dumps(diagnostics, indent=2, default=str))
    
    # Return appropriate exit code
    return 0 if diagnostics["status"] in ["healthy", "partial"] else 1

if __name__ == "__main__":
    sys.exit(main())
