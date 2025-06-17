# Pinecone API Update

This update addresses the error related to the Pinecone client initialization in the Railway deployment:

## Error
```
Failed to initialize Pinecone: init is no longer a top-level attribute of the pinecone package.
```

## Changes Made

1. Updated the Pinecone client initialization code to use the new approach:
   - Now creates an instance of the `Pinecone` class instead of calling `pinecone.init()`
   - Added fallback to the legacy approach for backward compatibility

2. Updated all references to Pinecone methods:
   - Updated `list_indexes()` to `pc.list_indexes().names()`
   - Updated `delete_index()` to `pc.delete_index()`
   - Updated index creation with new `ServerlessSpec`

3. Updated the requirements.txt:
   - Set pinecone-client to use a version that supports the new API
   - Added explicit PyPDF2 dependency

## Deployment

To deploy these changes to Railway:

1. Commit these changes to your Git repository
2. Push to the branch that Railway is deploying from
3. Railway should automatically detect the changes and redeploy

Once deployed, the Pinecone initialization error should be resolved.
