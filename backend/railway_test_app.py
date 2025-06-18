#!/usr/bin/env python3
"""
Railway Startup Test Script

This script creates a minimal FastAPI application that should run on Railway
without any dependencies on external services. Use this to test if Railway
can successfully start a Python service.
"""

import os
import sys
import json
import time
from datetime import datetime

# Try to import FastAPI
try:
    from fastapi import FastAPI, Request, HTTPException
    import uvicorn
except ImportError:
    print("ERROR: FastAPI and/or uvicorn is not installed.")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

# Create a minimal FastAPI app
app = FastAPI(title="Railway Test App")

@app.get("/")
async def root():
    """Root endpoint returning basic info"""
    return {
        "message": "Railway test app is running!",
        "timestamp": datetime.now().isoformat(),
        "status": "ok"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "python_version": sys.version
    }

@app.get("/env")
async def env():
    """Return non-sensitive environment variables"""
    safe_vars = {
        "ENVIRONMENT": os.environ.get("ENVIRONMENT"),
        "PORT": os.environ.get("PORT"),
        "RAILWAY_ENVIRONMENT_NAME": os.environ.get("RAILWAY_ENVIRONMENT_NAME"),
        "RAILWAY_SERVICE_NAME": os.environ.get("RAILWAY_SERVICE_NAME"),
        # Add any other non-sensitive vars you want to check
    }
    
    # Check if critical vars exist (without revealing their values)
    critical_vars = [
        "SUPABASE_URL", 
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "OPENAI_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_ENVIRONMENT",
        "PINECONE_INDEX_NAME",
        "LLAMAINDEX_API_KEY"
    ]
    
    var_status = {}
    for var in critical_vars:
        var_status[var] = "SET" if os.environ.get(var) else "MISSING"
    
    return {
        "safe_variables": safe_vars,
        "critical_variables_status": var_status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug")
async def debug(request: Request):
    """Debug endpoint with request info"""
    headers = dict(request.headers)
    # Remove sensitive headers
    if "authorization" in headers:
        headers["authorization"] = "REDACTED"
        
    return {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "client_host": request.client.host if request.client else None,
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting minimal Railway test app on port {port}")
    print("Access the app at:")
    print(f"  - http://localhost:{port}/")
    print(f"  - http://localhost:{port}/health")
    print(f"  - http://localhost:{port}/env")
    print(f"  - http://localhost:{port}/debug")
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=port)
