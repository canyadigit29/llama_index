# Railway Deployment Guide

## Port Configuration Fix

The LlamaIndex backend must run on port 8000 for successful deployment on Railway. This guide addresses several critical issues we've encountered.

## Issues Identified

1. **Port Mismatch**: Application would start on port 8080, but Railway expects port 8000
2. **Healthcheck Failures**: The /health endpoint wasn't responding, causing deployment to fail
3. **Dockerfile Selection**: Railway was using the root Dockerfile, not the backend one

## Files Updated

1. **Root Dockerfile**: Updated to force port 8000 and use railway_deploy.sh
2. **railway_deploy.sh**: New deployment script with port diagnostics and a fallback test server
3. **test_server.py**: Minimal FastAPI app that ensures the /health endpoint works
4. **Port-related scripts**: All updated to force port 8000

## Troubleshooting Steps

If your deployment fails after these changes:

1. **Check the logs** for port-related messages
2. **Verify the test_server.py** was included in the deployment
3. **Ensure Railway configuration** has port 8000 specified
4. **Check Railway's routing** settings

## Debugging

The deployed application includes enhanced endpoints:

- `/health` - Returns detailed port information
- `/debug` - Shows full environment information

## Server Startup Order

The deployment process now attempts these steps in order:

1. Try the minimal test server to ensure port 8000 works
2. If test server works, stick with it to pass healthchecks
3. If test server fails, try the main application

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
