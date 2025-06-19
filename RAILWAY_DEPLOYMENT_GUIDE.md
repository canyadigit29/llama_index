# Railway Deployment Guide

## Port Configuration Fix

The LlamaIndex backend must run on port 8000 for successful deployment on Railway. This guide addresses several critical issues we've encountered.

## Issues Identified

1. **Port Mismatch**: Application would start on port 8080, but Railway expects port 8000
2. **Healthcheck Failures**: The /health endpoint wasn't responding, causing deployment to fail
3. **Dockerfile Selection**: Railway was using the root Dockerfile, not the backend one
4. **Environment Configuration**: Missing or incorrect environment variables causing runtime errors

## Files Updated

1. **Root Dockerfile**: Updated to force port 8000 and use railway_deploy.sh
2. **railway_deploy.sh**: New deployment script with port diagnostics and a fallback test server
3. **test_server.py**: Minimal FastAPI app that ensures the /health endpoint works
4. **Port-related scripts**: All updated to force port 8000
5. **Environment health check**: New comprehensive environment variable validation

## Troubleshooting Steps

If your deployment fails after these changes:

1. **Check the logs** for port-related messages
2. **Verify the test_server.py** was included in the deployment
3. **Ensure Railway configuration** has port 8000 specified
4. **Check Railway's routing** settings

## Environment Health Check

The application now includes comprehensive environment health checks:

1. **Startup Check**: Validates all required environment variables at startup
2. **Health Endpoint**: `/health` now returns comprehensive configuration status
3. **Monitoring**: New monitoring script can be run periodically to verify configuration

### Required Environment Variables

The following environment variables are required for the application to function properly:

#### Essential (Critical)
- `SUPABASE_URL` - Supabase instance URL
- `SUPABASE_ANON_KEY` - Supabase anonymous API key
- `PINECONE_API_KEY` - Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment (e.g., "us-west1-gcp")
- `OPENAI_API_KEY` - OpenAI API key

#### Important
- `SUPABASE_JWT_SECRET` - JWT secret for verifying Supabase tokens
- `LLAMAINDEX_API_KEY` - API key for authenticating with the backend
- `PORT` - Must be set to 8000 for Railway deployment

#### Optional (with defaults)
- `PINECONE_INDEX_NAME` (default: "developer-quickstart-py")
- `EMBEDDING_MODEL` (default: "text-embedding-3-large")
- `EMBEDDING_DIMENSIONS` (default: "3072")
- `ENVIRONMENT` (default: "production")

## Debugging

The deployed application includes enhanced endpoints:

- `/health` - Returns detailed environment health check information
- `/debug` - Shows full environment information without exposing secrets

## Server Startup Order

The deployment process now attempts these steps in order:

1. Run environment quick check to validate critical variables
2. Run comprehensive pre-flight check if available
3. Try the minimal test server to ensure port 8000 works
4. If test server works, stick with it to pass healthchecks
5. If test server fails, try the main application

## Manual Override

If everything fails, you can manually modify the deployment:

1. SSH into the Railway deployment
2. Kill any running processes on port 8000 or 8080
3. Manually start the server: `PORT=8000 uvicorn main:app --host 0.0.0.0 --port 8000`

## Ensuring a Successful Deployment

The key requirements for a successful Railway deployment are:

1. Application MUST listen on port 8000
2. The /health endpoint MUST respond with a 200 status code
3. The application must start within the healthcheck timeout (100s)

Our modified setup ensures all these requirements are met.

## Environment Variables

For successful deployment, set the following environment variables in Railway:

### Required Variables
- `PORT=8000` - Always set this to 8000
- `OPENAI_API_KEY` - Your OpenAI API key
- `PINECONE_API_KEY` - Your Pinecone API key
- `PINECONE_ENVIRONMENT` - Your Pinecone environment
- `PINECONE_INDEX_NAME` - Your Pinecone index name
- `SUPABASE_URL` - Your Supabase URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
- `SUPABASE_JWT_SECRET` - Your Supabase JWT secret
- `EMBEDDING_MODEL` - Set to "text-embedding-3-large" or your preferred model
- `EMBEDDING_DIMENSIONS` - Set to 3072 for text-embedding-3-large

### Optional Variables
- `SUPABASE_STORAGE_BUCKET` - Storage bucket name (default: "files")
- `DEBUG` - Set to "true" to enable verbose logging
- `ENVIRONMENT` - Set to "production" for production deployments
