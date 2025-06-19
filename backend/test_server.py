"""
Simple test script to verify Railway deployment and port configuration
This should be used for diagnostic purposes only
"""

from fastapi import FastAPI
import os
import socket
import uvicorn
import datetime

app = FastAPI()

@app.get("/")
async def root():
    """Root endpoint that returns basic information."""
    return {
        "message": "LlamaIndex API is running",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint required by Railway."""
    # This MUST return a 200 status code for Railway to consider the deployment healthy
    # Simplify to ensure it always returns successfully
    return {
        "status": "healthy",
        "message": "LlamaIndex API test server is healthy",
        "timestamp": str(datetime.datetime.utcnow())
    }

@app.get("/debug")
async def debug():
    """Debug endpoint with more detailed information."""
    import sys
    import platform
    
    # Get all network interfaces
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    return {
        "system": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "hostname": hostname,
            "local_ip": local_ip,
        },
        "environment": dict(os.environ),
    }

# This will only be used when running the script directly, not with uvicorn
if __name__ == "__main__":
    # Force port to 8000
    port = 8000
    print(f"Starting test server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
