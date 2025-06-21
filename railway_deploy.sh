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

# Run import test first to validate environment
echo "Testing critical imports..."
cd /app && python test_imports.py || echo "⚠️ Some imports failed - see warnings above"

# Run Pinecone configuration validation
echo "Validating Pinecone configuration for Railway..."
if [ -f "/app/backend/railway_pinecone_test.py" ]; then
  python /app/backend/railway_pinecone_test.py
  PINECONE_TEST_RESULT=$?
  if [ $PINECONE_TEST_RESULT -ne 0 ]; then
    echo "⚠️ Pinecone test failed with exit code $PINECONE_TEST_RESULT - check logs for details"
  else
    echo "✅ Pinecone connection test passed"
  fi
else
  echo "Pinecone test script not found, falling back to legacy setup..."
  cd /app/backend && python railway_pinecone_setup.py || echo "Pinecone validation completed with warnings"
fi

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

# Enhanced debugging
echo "---------------------------------------------"
echo "PYTHON ENVIRONMENT DETAILS"
echo "---------------------------------------------"
python --version
echo "Python executable: $(which python)"
echo "Python path:"
python -c "import sys; print('\n'.join(sys.path))"
echo "Installed packages (selected):"
pip list | grep -E 'pinecone|llama|fastapi|uvicorn'
echo "---------------------------------------------"

# Add app root and current directory to Python path
export PYTHONPATH=${PYTHONPATH}:/app:$(pwd)

echo "Running application with port 8000 and PYTHONPATH=$PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Listing files in current directory:"
ls -la

# Check if vector_store_config.py is in the current directory
if [ -f "vector_store_config.py" ]; then
  echo "Found vector_store_config.py in current directory"
else
  echo "vector_store_config.py NOT found in current directory"
fi

# Check if directory structure is as expected
if [ -d "/app/backend" ]; then
  echo "Directory structure has backend/ subfolder - using /app/backend"
  cd /app/backend
else
  echo "Using flat structure - backend files are in /app root"
  cd /app
fi

# Run import troubleshooter to help diagnose any issues
if [ -f "railway_troubleshoot.py" ]; then
  echo "Running import path troubleshooter"
  python railway_troubleshoot.py
else
  echo "Import troubleshooter not found - skipping"
fi

# Run the validation script for Pinecone if it exists
if [ -f "railway_pinecone_setup.py" ]; then
  echo "Running Pinecone validation script"
  python railway_pinecone_setup.py
else
  echo "Pinecone validation script not found - skipping"
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000
