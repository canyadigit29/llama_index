from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import json

class RequestLoggerMiddleware:
    """
    Middleware for logging all requests to the API.
    This will help diagnose if requests are actually reaching the backend.
    """
    async def __call__(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = f"req_{int(time.time() * 1000)}"
        
        # Log request details
        print(f"======= INCOMING REQUEST {request_id} =======")
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")
        print(f"Client: {request.client}")
        print(f"Headers: {dict(request.headers)}")
        
        # Try to log body if it's a POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Clone the request to avoid consuming the body
                body_bytes = await request.body()
                
                # Try to parse as JSON for prettier logging
                try:
                    body = json.loads(body_bytes)
                    if isinstance(body, dict) and "api_key" in body:
                        # Redact sensitive info
                        body["api_key"] = "[REDACTED]"
                    print(f"Body: {json.dumps(body, indent=2)}")
                except:
                    # If not JSON, truncate to avoid huge logs
                    body_str = body_bytes.decode('utf-8', errors='replace')
                    if len(body_str) > 1000:
                        print(f"Body: {body_str[:1000]}... [truncated]")
                    else:
                        print(f"Body: {body_str}")
            except Exception as e:
                print(f"Could not log request body: {e}")
        
        start_time = time.time()
        try:
            # Process the request
            response = await call_next(request)
            
            # Log the response
            duration = time.time() - start_time
            print(f"======= RESPONSE {request_id} =======")
            print(f"Status: {response.status_code}")
            print(f"Duration: {duration:.4f}s")
            
            return response
        except Exception as e:
            # Log any exceptions
            duration = time.time() - start_time
            print(f"======= ERROR {request_id} =======")
            print(f"Error: {str(e)}")
            print(f"Duration: {duration:.4f}s")
            raise

def add_request_logger(app: FastAPI):
    """
    Add the request logger middleware to a FastAPI app.
    """
    app.middleware("http")(RequestLoggerMiddleware())
