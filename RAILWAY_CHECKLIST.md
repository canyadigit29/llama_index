# Railway Deployment Checklist

This document provides a step-by-step checklist for deploying the LlamaIndex backend to Railway.

## Pre-Deployment Checks

Before initiating deployment to Railway, complete the following checks:

- [ ] All environment variables are defined in Railway project
- [ ] Code changes committed to repository
- [ ] Local tests pass with `python backend/e2e_test.py`
- [ ] Port configuration verified (must use 8000)
- [ ] Health check endpoint (`/health`) is working locally

## Environment Variable Configuration

Ensure the following environment variables are configured in Railway:

### Required Variables

- [ ] `PORT=8000` (critical - must be exactly 8000)
- [ ] `OPENAI_API_KEY` (valid API key)
- [ ] `PINECONE_API_KEY` (valid API key) 
- [ ] `PINECONE_ENVIRONMENT` (e.g., "gcp-starter")
- [ ] `PINECONE_INDEX_NAME` (valid index name)
- [ ] `SUPABASE_URL` (valid URL)
- [ ] `SUPABASE_ANON_KEY` (valid key)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` (valid key)
- [ ] `SUPABASE_JWT_SECRET` (valid secret)
- [ ] `EMBEDDING_MODEL="text-embedding-3-large"`
- [ ] `EMBEDDING_DIMENSIONS=3072`

### Optional Variables

- [ ] `DEBUG=true` (for verbose logging during initial deployment)
- [ ] `ENVIRONMENT=production`
- [ ] `SUPABASE_STORAGE_BUCKET=files` (if you've changed the bucket name)

## Deployment Steps

1. **Initial Deployment**

- [ ] Push code to the GitHub repository linked to Railway
- [ ] Watch the build logs for any errors
- [ ] If deployment fails, check "Failed Deployment Troubleshooting" section

2. **Verify Basic Functionality**

- [ ] Visit the deployed URL to verify the application is running
- [ ] Test `/health` endpoint
- [ ] Test `/debug` endpoint for environment information

3. **Integration Testing**

- [ ] Run remote e2e test: `LLAMAINDEX_URL=<your-railway-url> python backend/e2e_test.py`
- [ ] Test file upload via the frontend
- [ ] Test search functionality

## Failed Deployment Troubleshooting

If deployment fails, follow these steps in order:

1. **Check Deployment Logs**

- [ ] Look for any error messages in Railway logs
- [ ] Verify that port 8000 is being used
- [ ] Check for environment variable issues

2. **Try Minimal Test Server**

- [ ] Update Railway build command to use the test server:
```
cd backend && python test_server.py
```
- [ ] Deploy and check if the test server works
- [ ] If test server works but main app doesn't, likely an application issue

3. **Port Conflict Resolution**

- [ ] SSH into Railway deployment
- [ ] Check for processes using port 8000: `lsof -i :8000`
- [ ] Kill any conflicting processes: `kill -9 <PID>`
- [ ] Manually start the server: `PORT=8000 uvicorn main:app --host 0.0.0.0 --port 8000`

4. **Manual Deployment Verification**

- [ ] Set up a test environment with identical variables
- [ ] Run `python backend/railway_health_check_simplified.py`
- [ ] Check response data for clues about any misconfigurations

## Common Issues and Solutions

### Health Check Failures

**Problem**: Railway deployment healthchecks fail despite application starting.

**Potential Fixes**:
- Check that the app is listening on port 8000 explicitly
- Ensure the `/health` endpoint returns a 200 status code
- Try the minimal test server to isolate the issue

### Supabase Connection Issues

**Problem**: Application starts but can't connect to Supabase.

**Potential Fixes**:
- Verify all Supabase-related environment variables
- Check if IP restrictions are enabled in Supabase
- Try the service role authentication as a fallback

### Memory/Resource Issues

**Problem**: Application crashes or becomes unresponsive.

**Potential Fixes**:
- Upgrade the Railway service plan for more resources
- Optimize memory usage in the application
- Set up monitoring to identify resource bottlenecks

## Post-Deployment Steps

After successful deployment:

1. **Monitoring Setup**
- [ ] Configure Railway alerts for failed deployments
- [ ] Set up uptime monitoring

2. **Performance Optimization**
- [ ] Disable DEBUG mode once stable
- [ ] Monitor and adjust resource allocation as needed

3. **Documentation**
- [ ] Update deployment documentation with any new findings
- [ ] Document any custom configuration required

---

Last Updated: June 18, 2025
