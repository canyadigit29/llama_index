# Troubleshooting Railway Deployment

This guide addresses common issues when deploying to Railway and how to fix them.

## 502 Bad Gateway / Connection Refused

If you see a 502 error or "connection refused" error:

1. **Check port configuration**:
   - Make sure your app is listening on port 8080
   - Railway.toml, Dockerfile, and start.sh should all use the same port
   - Current configuration uses port 8080 consistently across all files

2. **Check logs in Railway dashboard**:
   - Look for any startup errors
   - Ensure the application is starting properly
   - Check that it's binding to the correct port

3. **Verify environment variables**:
   - Make sure all required environment variables are set
   - Check that OpenAI, Pinecone, and Supabase credentials are correct

4. **Check health endpoint**:
   - Try accessing the `/health` endpoint directly
   - This endpoint is lighter weight than the main API endpoints
   - It can help identify if the issue is with a specific API or with the entire service

## LlamaIndex / Pinecone Issues

If the application starts but has issues with indexing:

1. **Check Pinecone configuration**:
   - Verify PINECONE_API_KEY, PINECONE_ENVIRONMENT, and PINECONE_INDEX_NAME
   - Ensure your Pinecone index has 3072 dimensions to match the OpenAI embeddings model
   - Make sure the index exists in your Pinecone dashboard

2. **Check OpenAI configuration**:
   - Ensure OPENAI_API_KEY is set correctly
   - Check that your OpenAI account has sufficient quota

3. **Check for initialization errors**:
   - The application will try to initialize with a placeholder document if needed
   - Review logs for any issues during index initialization

## Deployment Updates

After making changes:

1. Commit the changes to your Git repository
2. Push to the branch connected to Railway
3. Railway will automatically deploy the changes
4. Check the logs to verify successful deployment
5. Test the endpoints to verify functionality
