# Railway External Service Connection Debugging Guide

## Potential Issues with External Services

If your backend is experiencing connection issues on Railway, it could be related to:

### 1. Pinecone Connection Issues

**Symptoms:**
- 502 errors when trying to process documents or perform queries
- Error messages about Pinecone in the logs
- Application crashes during startup when initializing Pinecone

**Debugging Steps:**
1. Check Railway logs for specific Pinecone error messages
2. Verify your Pinecone API key is correctly set in Railway environment variables
3. Confirm your Pinecone environment (e.g., "gcp-starter") is correctly set
4. Verify your index dimensions (3072) match what's configured in the code
5. Check if your Pinecone index exists and is properly set up
6. Try accessing Pinecone directly from another tool to verify API access

**Quick Fix:**
- Update the Railway environment variables:
  - PINECONE_API_KEY
  - PINECONE_ENVIRONMENT
  - PINECONE_INDEX_NAME

### 2. Supabase Connection Issues

**Symptoms:**
- 502 errors when trying to upload or access files
- Application crashes during startup when initializing Supabase
- Error messages about Supabase in the logs

**Debugging Steps:**
1. Check Railway logs for specific Supabase error messages
2. Verify your Supabase URL and API keys are correctly set
3. Confirm your Supabase database tables exist and have correct permissions
4. Test Supabase connection directly to isolate the issue

**Quick Fix:**
- Update the Railway environment variables:
  - SUPABASE_URL
  - SUPABASE_ANON_KEY
  - SUPABASE_SERVICE_ROLE_KEY

### 3. OpenAI API Issues

**Symptoms:**
- 502 errors when trying to generate embeddings
- Error messages about OpenAI in the logs
- Application crashes when trying to process documents

**Debugging Steps:**
1. Check Railway logs for specific OpenAI error messages
2. Verify your OpenAI API key is correctly set
3. Check if your OpenAI account has sufficient quota
4. Confirm you're using a supported OpenAI embedding model

**Quick Fix:**
- Update the Railway environment variable:
  - OPENAI_API_KEY

## Testing External Services Independently

To isolate if the issue is with external services:

1. **Use the Railway shell** to test connections directly:
   ```bash
   curl https://api.openai.com/v1/engines -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. **Check the health endpoint** to see service status:
   ```
   https://your-railway-app.up.railway.app/health
   ```

3. **Monitor the logs** for specific service connection errors

## Correcting Environment Variables

If you determine an environment variable is incorrect:
1. Go to the Railway dashboard
2. Select your project
3. Click on the "Variables" tab
4. Update the variable with the correct value
5. Railway will automatically redeploy your application

Remember to check the logs after updating environment variables to ensure the application starts correctly and can connect to all external services.
