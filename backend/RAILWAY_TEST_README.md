# Railway Test App

This is a minimal FastAPI application for testing Railway deployment. It doesn't rely on any external dependencies like Supabase, Pinecone, or OpenAI, making it perfect for troubleshooting Railway connectivity issues.

## Features

- Minimal dependencies (only requires FastAPI and uvicorn)
- Health check endpoint
- Environment variable status check
- Debug endpoint for request information

## How to Use

1. Deploy this to Railway to verify that basic Python services can run
2. Check the endpoints to confirm connectivity
3. Use the environment check to verify that your variables are set correctly

## Endpoints

- `/` - Root endpoint with basic status
- `/health` - Health check endpoint
- `/env` - Environment variable status (safe info only)
- `/debug` - Request debug information

## Deployment

Update your Railway `requirements.txt` to include just the minimal dependencies:

```
fastapi==0.110.0
uvicorn==0.27.1
```

Set the start command to:

```
uvicorn railway_test_app:app --host 0.0.0.0 --port $PORT
```

## Troubleshooting Steps

If this minimal app works but your main app doesn't:

1. Compare environment variables
2. Check logs for dependency errors
3. Add dependencies back one by one until you find the problem

If this app also fails, there may be an issue with your Railway configuration or networking.
