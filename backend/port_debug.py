#!/usr/bin/env python3
"""
Port Binding Debug Script

This script tests binding to various ports to verify which ones are available
and properly routed in the Railway environment.
"""

import socket
import os
import time
import sys

def check_port(port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(1)
        print(f"✅ Successfully bound to port {port}")
        sock.close()
        return True
    except Exception as e:
        print(f"❌ Failed to bind to port {port}: {e}")
        return False

def main():
    print("=== PORT BINDING TEST ===")
    print(f"Running as PID: {os.getpid()}")
    print(f"Current environment PORT: {os.environ.get('PORT', 'Not set')}")
    
    ports_to_check = [8000, 8080]
    successful_ports = []
    
    print("\nTesting standard ports...")
    for port in ports_to_check:
        if check_port(port):
            successful_ports.append(port)
    
    print("\nStarting test server on successful port...")
    if successful_ports:
        test_port = successful_ports[0]
        print(f"Starting a test HTTP server on port {test_port}")
        
        try:
            import http.server
            import socketserver
            
            class TestHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Test server running on port {test_port}".encode())
                    print(f"Handled request to {self.path}")
            
            with socketserver.TCPServer(("0.0.0.0", test_port), TestHandler) as httpd:
                print(f"Server running on port {test_port}. Press Ctrl+C to stop.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
        except Exception as e:
            print(f"Error running test server: {e}")
    else:
        print("No ports available for testing. Please check your environment.")

if __name__ == "__main__":
    main()
