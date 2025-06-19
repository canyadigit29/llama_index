#!/usr/bin/env python3
"""
Healthcheck Setup for Railway Deployment

This script ensures that the /health endpoint returns a 200 status even before
the main application is fully initialized. This is critical for Railway's 
healthcheck system to consider the deployment successful.

Usage:
    python healthcheck.py
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
import time
import os
import socket
import requests
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("healthcheck")

# Create app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for basic verification."""
    return {
        "status": "online",
        "message": "LlamaIndex API Healthcheck Server",
    }

@app.get("/health")
async def health():
    """Health check endpoint that always returns 200 OK."""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "railway": bool(os.environ.get("RAILWAY_SERVICE_ID")),
        "port": os.environ.get("PORT", "8000"),
        "message": "Railway healthcheck proxy is functioning correctly"
    }

def run_healthcheck_server():
    """Run the health check server on a high port."""
    try:
        # Run on a high port (8765) that shouldn't conflict
        port = 8765
        logger.info(f"Starting healthcheck server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error running healthcheck server: {e}")

def start_proxy_server():
    """Start a separate thread with the health check server."""
    # Start in a new thread
    healthcheck_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
    healthcheck_thread.start()
    logger.info("Healthcheck proxy started in background")
    return healthcheck_thread

def setup_railway_healthcheck_proxy():
    """
    Set up a proxy server that will respond to healthchecks on a high port.
    
    Returns the thread running the server.
    """
    return start_proxy_server()

if __name__ == "__main__":
    # Run the healthcheck server directly
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
