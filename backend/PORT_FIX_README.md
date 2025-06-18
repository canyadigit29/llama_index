# Port Configuration Fix

## Problem Identified
The application was running on port 8080 while Railway's routing expects it to run on port 8000. This port mismatch was causing 500/502 errors when the frontend tried to communicate with the backend.

## Changes Made

1. **start.sh**: Updated to force PORT=8000 regardless of environment variables
2. **Procfile**: Updated to explicitly use port 8000
3. **railway.Dockerfile**: 
   - Added docker_entrypoint.sh script to ensure port 8000 is used
   - Explicitly set ENV PORT=8000
4. **docker_entrypoint.sh**: Added new script for debugging and forcing port 8000
5. **check_port.sh**: Added port diagnostic script

## Deployment Instructions

1. Commit these changes to your repository
2. Redeploy on Railway
3. Watch the logs to confirm the server starts on port 8000
4. Test the frontend integration to ensure it can successfully process files

## Verification

After deploying, you should see logs indicating:
```
Starting server on port: 8000
Using port 8000 to match Railway forwarding configuration
```

And the uvicorn server should start with:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## If Problems Persist

If you continue to see "Application failed to respond" errors:
1. Check the Railway logs for any port-related issues
2. Run the PORT diagnostic scripts to see if something is overriding our settings
3. Verify Railway's service configuration to ensure it's routing to port 8000
