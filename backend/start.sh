#!/bin/bash

# Set default port if not provided
# Railway seems to be forwarding requests to port 8000
export PORT=${PORT:-8000}

# Print debugging info
echo "Starting server on port: $PORT"
echo "Railway forwarding configuration expects port 8000"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
