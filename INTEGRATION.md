# LlamaIndex + Chatbot-UI + Supabase Integration

This documentation provides a comprehensive guide for the integration between LlamaIndex (backend), Chatbot-UI (frontend), and Supabase (database and storage).

## Architecture Overview

![Architecture Diagram](https://www.plantuml.com/plantuml/png/TP71JiCm38RlUGgVTvGLkN75gAcq8NkWAw5aTI1eHR9-zsmplxrDoCJ7Ed_xzqspsADI3UZyfLRH0CKbGie38ymbLhPs7OvcMTrhRp0R1zHrEmwhMFQzuQG9U5qaVJykEggSOAi9EqH4sC8KNc7T5oAzAdHH4593xLFf1MjsMs719xSbOQsM9JkZsTsllB9ry0JWjix0iisS7acFcdMlkoJ7OFOss2Kzhl1EmNUDvazeNtIxzxFFXSs55P4YBlN2Rij_tW-doqWTaopFsoeXT4Xqx5i_WBsNvMWErifxytpy0G00)

The integration involves three main components:

1. **LlamaIndex Backend** (Python/FastAPI):
   - Handles document processing, embedding, indexing, and search
   - Connects to OpenAI (for embeddings), Pinecone (for vector storage)
   - Uses Supabase for authentication and file storage

2. **Chatbot-UI Frontend** (Next.js):
   - User interface for document upload and chat interactions
   - Manages file uploads to Supabase storage
   - Handles authentication via Supabase

3. **Supabase**:
   - Database for metadata storage
   - Storage for document files
   - Authentication for both frontend and backend

## Integration Workflow

1. User authenticates through Chatbot-UI (via Supabase auth)
2. User uploads files through Chatbot-UI, which:
   - Creates file metadata record in Supabase database
   - Uploads file to Supabase storage with path: `{user_id}/{file_id}`
   - Passes file information to backend for processing
3. LlamaIndex backend processes the file:
   - Downloads file from Supabase storage
   - Chunks the document and creates embeddings
   - Indexes the content in Pinecone
   - Updates metadata in Supabase
4. User can then search/chat using the processed documents

## Key Integration Points

### File Path Structure

Files are stored in Supabase using the following path structure:
```
{user_id}/{file_id}
```

The backend includes fallback mechanisms to try multiple paths:
1. First: Use provided path if specified
2. Second: Try `{user_id}/{file_id}` format  
3. Last: Try just `{file_id}` as a fallback

### Authentication Flow

1. Frontend authenticates users via Supabase Auth
2. JWT tokens are passed to backend API calls
3. Backend verifies JWTs using Supabase JWT secret
4. Service role fallback is used for file access when user auth fails

## Environment Variables

### Backend (LlamaIndex)

Required:
- `PORT=8000` (Critical for Railway deployment)
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_ENVIRONMENT`
- `PINECONE_INDEX_NAME`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `EMBEDDING_MODEL="text-embedding-3-large"`
- `EMBEDDING_DIMENSIONS=3072`

Optional:
- `SUPABASE_STORAGE_BUCKET`
- `DEBUG`
- `ENVIRONMENT`

### Frontend (Chatbot-UI)

Required:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_LLAMA_INDEX_API_KEY`
- `NEXT_PUBLIC_LLAMA_INDEX_URL`

## Deployment

### Railway Deployment

For Railway deployment, ensure:
1. The application runs on port 8000
2. The `/health` endpoint responds with a 200 status code
3. The application starts within the healthcheck timeout (100s)

See [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) for detailed instructions.

## Troubleshooting

### Diagnostic Tools

The following diagnostic tools are available:

- `e2e_test.py`: End-to-end integration test of the full workflow
- `check_file_paths.py`: Verifies file paths in Supabase storage
- `env_debug.py`: Checks environment variable configuration
- `auth_test.py`: Tests Supabase authentication
- `service_role_test.py`: Tests service role authentication
- `railway_health_check.py`: Tests Railway connectivity
- `port_debug.py`: Checks port binding and conflicts
- `test_railway_connectivity.py`: Tests Railway endpoint accessibility
- `test_server.py`: Minimal server for Railway healthchecks
- `check_storage_bucket_config.py`: Confirms storage bucket hardcoding

### Common Issues

1. **Port Conflicts**: Ensure port 8000 is available for Railway deployment.
2. **Storage Path Mismatches**: Check if file paths in frontend match expected paths in backend.
3. **JWT Verification Failures**: Verify the `SUPABASE_JWT_SECRET` is correctly set.

## Testing

To run the end-to-end test:

```bash
python backend/e2e_test.py
```

This test will:
1. Create a test document
2. Upload it to Supabase storage
3. Trigger processing in the backend
4. Verify search functionality
5. Clean up test data

## Next Steps

1. Deploy with modified scripts forcing port 8000
2. Enable verbose logging to troubleshoot Railway deployment
3. Test end-to-end flow starting with small test files
4. If healthchecks continue to fail, try deploying the minimal test_server.py first

---

Last Updated: June 18, 2025
