#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-8000}

# Print debugging info
echo "Starting server on port: $PORT"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port $PORT
