#!/bin/bash

# =====================================
# RAILWAY DEPLOYMENT SCRIPT
# =====================================
# This script ensures the application always runs on port 8000
# and provides a fallback to a minimal test server if the main app fails

echo "==============================================="
echo "RAILWAY DEPLOYMENT SCRIPT - PORT DIAGNOSTICS"
echo "==============================================="

# Make all scripts executable (with error handling)
echo "Making scripts executable..."
chmod +x /app/*.py || echo "Warning: Could not make all Python files executable"
chmod +x /app/*.sh || echo "Warning: Could not make all shell scripts executable"

# Force port to 8000 regardless of environment
export PORT=8000

# Run port availability check
echo "Running port availability check..."
python port_config.py 2>/dev/null || echo "Port config script not found, continuing..."

# Print diagnostic information
echo "Current environment:"
echo "- PORT: $PORT"
echo "- PWD: $(pwd)"
echo "- Directory contents: $(ls -la)"

# Check if port 8000 is already in use
echo "---------------------------------------------"
echo "CHECKING PORT AVAILABILITY"
echo "---------------------------------------------"
if command -v nc &> /dev/null; then
  if nc -z localhost 8000 &> /dev/null; then
    echo "CRITICAL ERROR: Port 8000 is already in use by another process!"
    echo "This will prevent Railway from routing traffic correctly"
    echo "Attempting to identify the process using port 8000:"
    if command -v lsof &> /dev/null; then
      lsof -i :8000
    elif command -v fuser &> /dev/null; then
      fuser 8000/tcp
    else
      echo "Cannot identify process. Try manually stopping services on port 8000"
    fi
    # Do not exit - Railway will retry, and we want to provide diagnostics in logs
  else
    echo "✓ Port 8000 is available"
  fi
else
  echo "Cannot check port availability (nc command not found)"
fi

# Port diagnostics
echo "---------------------------------------------"
echo "PORT DIAGNOSTICS"
echo "---------------------------------------------"
if command -v netstat &> /dev/null; then
  echo "Currently listening ports:"
  netstat -tuln | grep LISTEN
else
  echo "netstat not available"
fi

# Health check functionality removed
echo "---------------------------------------------"
echo "HEALTH CHECK DISABLED"
echo "---------------------------------------------"
echo "Health checks have been disabled per user request"
# Test server functionality removed

# Check Pinecone connectivity if diagnostics are available
if [ -f "pinecone_diagnostics.py" ]; then
  echo "---------------------------------------------"
  echo "RUNNING PINECONE DIAGNOSTICS"
  echo "---------------------------------------------"
  python pinecone_diagnostics.py || echo "Pinecone diagnostics completed with warnings"
fi

# Start the main application
echo "---------------------------------------------"
echo "STARTING MAIN APPLICATION"
echo "---------------------------------------------"
echo "Starting main application on port 8000..."

# Health check server functionality removed
echo "Health check servers have been disabled per user request"

# Skip environment health check since health checks are disabled
echo "Health checks disabled, skipping env_health_check.py"

# Explicitly use port 8000 for the main application
echo "Starting main application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
