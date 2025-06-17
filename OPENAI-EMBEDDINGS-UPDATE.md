# OpenAI Embeddings Update

This update addresses the error related to the OpenAI embeddings in the LlamaIndex backend:

## Error
```
Failed to connect to Pinecone index: `llama-index-embeddings-openai` package not found, please run `pip install llama-index-embeddings-openai`
```

## Changes Made

1. Added the missing dependency to requirements.txt:
   ```
   llama-index-embeddings-openai>=0.1.5
   ```

2. Updated the imports to handle different versions of the embedding module:
   ```python
   try:
       from llama_index.embeddings.openai import OpenAIEmbedding
   except ImportError:
       try:
           from llama_index.core.embeddings import OpenAIEmbedding
       except ImportError:
           from llama_index.embeddings import OpenAIEmbedding
   ```

3. Explicitly configured the OpenAI embeddings when initializing the index:
   - Added OPENAI_API_KEY to the environment variables
   - Created an OpenAIEmbedding instance with the API key
   - Updated the global Settings with the embedding model
   - Passed the embedding model explicitly when creating VectorStoreIndex

These changes ensure that the LlamaIndex backend will properly use OpenAI embeddings for indexing and searching documents.

## Deployment

To deploy these changes to Railway:

1. Commit these changes to your Git repository
2. Push to the branch that Railway is deploying from
3. Railway should automatically detect the changes and redeploy

Once deployed, the OpenAI embeddings error should be resolved.
