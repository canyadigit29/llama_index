#!/bin/bash

# Force port to 8000 regardless of PORT environment variable
# Railway is configured to forward requests to port 8000
export PORT=8000

# Run port check script
if [ -f "check_port.sh" ]; then
  chmod +x check_port.sh
  ./check_port.sh $PORT
fi

# Print debugging info
echo "Starting server on port: $PORT"
echo "Using port 8000 to match Railway forwarding configuration"

# Start the application with explicit port 8000 to ensure it matches Railway's routing
exec uvicorn main:app --host 0.0.0.0 --port 8000
