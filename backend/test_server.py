"""
Simple test script to verify Railway deployment and port configuration
This should be used for diagnostic purposes only
"""

from fastapi import FastAPI
import os
import socket
import uvicorn

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
    port_info = {}
    
    # Check if port 8000 is actually being used
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    port_info["port_8000"] = "in use" if result == 0 else "free"
    sock.close()
    
    # Get environment variables
    env_vars = {
        "PORT": os.environ.get("PORT", "not set"),
        "RAILWAY_SERVICE_ID": os.environ.get("RAILWAY_SERVICE_ID", "not set"),
        "RAILWAY_PUBLIC_DOMAIN": os.environ.get("RAILWAY_PUBLIC_DOMAIN", "not set"),
    }
    
    # Return health check response
    return {
        "status": "healthy",
        "port_info": port_info,
        "environment": env_vars,
        "service_address": f"Running on 0.0.0.0:8000"
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
