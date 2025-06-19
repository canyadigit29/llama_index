#!/bin/bash

# =========== PORT CONFIGURATION FIX ===========
# This script ensures the application always runs on port 8000
# regardless of any environment variable settings

# Print diagnostic information
echo "===== RAILWAY DEPLOYMENT START SCRIPT ====="
echo "Current environment:"
echo "- PORT: $PORT (will be overridden)"
echo "- PWD: $(pwd)"
echo "- Files in current directory: $(ls -la)"

# Force port to 8000 to match Railway routing
export PORT=8000
echo "PORT forced to: $PORT"

# Run environment checks
echo -e "\n===== ENVIRONMENT CHECKS ====="

# Quick check first (always available)
echo "Running quick environment check..."
python backend/env_quickcheck.py
QUICKCHECK_EXIT=$?

# More comprehensive pre-flight check if available
echo "Running comprehensive pre-flight check..."
if [ -f "backend/preflight_check.py" ]; then
    python backend/preflight_check.py
    PREFLIGHT_EXIT=$?
    if [ $PREFLIGHT_EXIT -ne 0 ]; then
        echo "WARNING: Pre-flight check detected issues, but continuing anyway..."
        echo "Check logs for details on environment variable problems."
    fi
else
    echo "Pre-flight check script not found, skipping..."
fi

# Run Pinecone-specific diagnostics if available
if [ -f "backend/pinecone_diagnostics.py" ]; then
    echo -e "\n===== PINECONE CONNECTIVITY DIAGNOSTICS ====="
    echo "Running Pinecone diagnostic checks..."
    python backend/pinecone_diagnostics.py
    # Diagnostics are informational only, no exit code check
    echo "Pinecone diagnostics complete."
fi

# Warn about critical issues from quick check
if [ $QUICKCHECK_EXIT -ne 0 ]; then
    echo "⚠️ CRITICAL ENVIRONMENT ISSUES DETECTED - Application may not function correctly!"
    echo "  See logs above for details on missing environment variables."
fi

# Print listening ports for diagnostics
echo -e "\n===== PORT DIAGNOSTICS ====="
echo "Currently listening ports:"
netstat -tuln 2>/dev/null || echo "netstat not available"

# Start the application on port 8000 explicitly
echo -e "\n===== STARTING APPLICATION ====="
echo "Starting application on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
