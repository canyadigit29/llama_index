# LlamaIndex Backend API

This is a FastAPI backend for LlamaIndex that provides document ingestion, indexing, and querying functionality with Supabase for document storage and authentication, and Pinecone for vector embeddings storage.

## Architecture

This backend uses a dual-storage architecture:
- **Supabase**: Stores raw document content, metadata, and handles user authentication
- **Pinecone**: Stores vector embeddings for semantic search and retrieval

## Features

- Document uploading and indexing with metadata
- Natural language querying against indexed documents
- Authentication with Supabase
- Vector search with Pinecone
- Admin endpoints for monitoring and management

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

- `PINECONE_API_KEY` - Your Pinecone API key
- `PINECONE_ENVIRONMENT` - Pinecone environment (e.g., "us-east-1-gcp")
- `PINECONE_INDEX_NAME` - Name of your Pinecone index
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous API key
- `SUPABASE_SERVICE_KEY` - Your Supabase service key (for admin operations)
- `OPENAI_API_KEY` - OpenAI API key for embeddings (if using OpenAI)
- `DATA_DIRECTORY` - Directory for temporary document storage (default: "./data")

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn main:app --reload
```

3. Open API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## Deployment on Railway

### Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2Fyour-username%2Fllama-index&envs=PINECONE_API_KEY%2CPINECONE_ENVIRONMENT%2COPENAI_API_KEY)

### Manual Deployment

1. Push your code to GitHub
2. Create a new project in Railway
3. Connect your GitHub repository
4. Add the required environment variables in Railway
5. Deploy the application

## API Endpoints

- `POST /query` - Query your indexed documents
- `POST /upload` - Upload a document for indexing
- `POST /reindex` - Re-index all documents
- `GET /admin/status` - Check system status
- `POST /delete_index` - Delete the Pinecone index
