#!/bin/bash

# Debug script to check environment variables and enforce port 8000

echo "================ PORT CONFIGURATION DEBUG ================"
echo "Original PORT environment variable: $PORT"

# Force port to 8000 to match Railway configuration
export PORT=8000
echo "Forcing PORT to: $PORT"

# Check other environment variables
echo "RAILWAY_PUBLIC_DOMAIN: $RAILWAY_PUBLIC_DOMAIN"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "RAILWAY_SERVICE_ID: $RAILWAY_SERVICE_ID"

# List all environment variables containing "PORT" or "port"
echo "All PORT-related environment variables:"
env | grep -i port

echo "Starting server using port $PORT..."
echo "================= END PORT DEBUG ================="

# Execute the original command with our fixed port
exec uvicorn main:app --host 0.0.0.0 --port 8000
