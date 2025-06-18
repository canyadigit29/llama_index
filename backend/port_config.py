#!/usr/bin/env python3
"""
Port Configuration Module

This module ensures consistent port configuration across the application.
It centralizes all port-related logic and provides diagnostic functions.
"""

import os
import socket
import sys

# Default port for Railway deployment
DEFAULT_PORT = 8000

def get_configured_port():
    """
    Get the port that should be used by the application.
    This function ensures we always use port 8000 for Railway.
    """
    # Force port 8000 for Railway deployments
    if os.environ.get("RAILWAY_SERVICE_ID"):
        print(f"[PORT CONFIG] Railway environment detected. Forcing port to {DEFAULT_PORT}")
        return DEFAULT_PORT
    
    # Otherwise use environment variable or default
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    print(f"[PORT CONFIG] Using port {port}")
    
    return port

def check_port_availability(port=DEFAULT_PORT):
    """
    Check if the specified port is available.
    Returns True if port is available, False if it's in use.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    available = False
    try:
        # Try to bind to the port
        sock.bind(('0.0.0.0', port))
        available = True
    except socket.error:
        pass
    finally:
        sock.close()
    
    status = "available" if available else "in use"
    print(f"[PORT CONFIG] Port {port} is {status}")
    return available

def ensure_port_available(port=DEFAULT_PORT, exit_on_error=True):
    """
    Ensure the specified port is available,
    exit application if not available and exit_on_error is True.
    """
    if not check_port_availability(port):
        print(f"[PORT CONFIG] ERROR: Port {port} is already in use!")
        print(f"[PORT CONFIG] This will prevent the application from starting correctly.")
        
        # Additional diagnostics
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                for conn in proc.connections():
                    if conn.laddr.port == port:
                        print(f"[PORT CONFIG] Process using port {port}: PID={proc.pid}, Name={proc.name()}")
        except ImportError:
            print("[PORT CONFIG] Install psutil for more detailed port usage information")
        
        if exit_on_error:
            print("[PORT CONFIG] Exiting due to port conflict")
            sys.exit(1)
        return False
    return True

# If run directly, run diagnostic checks
if __name__ == "__main__":
    print("==== PORT CONFIGURATION DIAGNOSTIC ====")
    configured_port = get_configured_port()
    ensure_port_available(configured_port, exit_on_error=False)
