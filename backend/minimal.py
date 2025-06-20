"""
Minimal FastAPI server for LlamaIndex backend
Used as a fallback if the full server fails to start
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Print diagnostic information
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

app = FastAPI(title="LlamaIndex Minimal API")

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
    return {
        "status": "ok",
        "service": "LlamaIndex Minimal Backend",
        "message": "Server is running in minimal mode",
        "environment": {
            "python_version": sys.version,
            "path": sys.path
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/debug")
async def debug():
    """Return diagnostic info for debugging purposes."""
    # Collect environment variables (redact sensitive ones)
    env_vars = {}
    for key, val in os.environ.items():
        if any(sensitive in key.lower() for sensitive in ["key", "token", "password", "secret"]):
            env_vars[key] = f"{val[:4]}...{val[-4:]}" if len(val) > 8 else "***"
        else:
            env_vars[key] = val
    
    # Collect system info
    sys_info = {
        "python_version": sys.version,
        "python_path": sys.path,
        "cwd": os.getcwd(),
        "listdir": os.listdir(".")
    }
    
    # Try importing critical modules
    imports = {}
    for module in ["fastapi", "pinecone", "llama_index"]:
        try:
            imported = __import__(module)
            imports[module] = getattr(imported, "__version__", "unknown")
        except ImportError as e:
            imports[module] = f"ERROR: {str(e)}"
    
    return {
        "status": "minimal_mode",
        "environment": env_vars,
        "system": sys_info,
        "imports": imports
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
