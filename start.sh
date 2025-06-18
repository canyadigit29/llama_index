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

# Print listening ports for diagnostics
echo "Currently listening ports:"
netstat -tuln 2>/dev/null || echo "netstat not available"

# Start the application on port 8000 explicitly
echo "Starting application on port 8000..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
