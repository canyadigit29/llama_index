#!/usr/bin/env python3
"""
Environment Variable Pre-flight Check for LlamaIndex Backend

This script performs a pre-flight check of all environment variables
before starting the main application. It can be called from start.sh
or other deployment scripts to verify environment health before starting
the application.

Usage:
    python preflight_check.py [--strict]

With --strict flag, the script will exit with error code 1 if any
required environment variable is missing or invalid.
"""

import sys
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PREFLIGHT_CHECK")

# Import the health check functions
try:
    from env_health_check import run_health_check, log_health_check_results
except ImportError:
    print("Failed to import env_health_check.py. Make sure it's in the same directory.")
    sys.exit(1)

def print_header():
    """Print a visually distinct header for the pre-flight check."""
    print("\n" + "=" * 80)
    print(f" PRE-FLIGHT CHECK FOR LLAMAINDEX BACKEND - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

def print_footer(success):
    """Print a visually distinct footer for the pre-flight check."""
    print("\n" + "=" * 80)
    if success:
        print(" ✅ PRE-FLIGHT CHECK PASSED - The environment is correctly configured.")
    else:
        print(" ❌ PRE-FLIGHT CHECK FAILED - Issues detected with environment configuration.")
    print("=" * 80 + "\n")

def main():
    """Run pre-flight check and return exit code."""
    print_header()
    
    strict_mode = "--strict" in sys.argv
    if strict_mode:
        logger.info("Running in STRICT mode - will exit with error if any issues are detected.")
    else:
        logger.info("Running in WARN mode - will issue warnings but won't prevent startup.")
    
    # Run health check with verbose output
    health_report = run_health_check(verbose=True)
    log_health_check_results(health_report)
    
    is_healthy = health_report["status"] == "healthy"
    print_footer(is_healthy)
    
    if strict_mode and not is_healthy:
        logger.error("Exiting with error code 1 due to environment issues in strict mode.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
