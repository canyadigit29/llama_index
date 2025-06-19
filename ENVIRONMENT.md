# Environment Variable Configuration

This document describes all the environment variables used by the LlamaIndex backend service.

## Required Environment Variables

The following environment variables are required for the application to function correctly:

### Supabase Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | URL of your Supabase instance | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase anonymous/public API key | `eyJhbGc...` |
| `SUPABASE_JWT_SECRET` | JWT secret for token verification | `your-jwt-secret` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key for admin operations | `eyJhbGc...` |

### Pinecone Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `PINECONE_API_KEY` | API key for Pinecone vector database | `12345-abcde-...` |
| `PINECONE_ENVIRONMENT` | Pinecone environment | `us-west1-gcp` |
| `PINECONE_INDEX_NAME` | Name of your Pinecone index | `developer-quickstart-py` (default) |

### OpenAI Configuration
| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |

### Authentication
| Variable | Description | Example |
|----------|-------------|---------|
| `LLAMAINDEX_API_KEY` | API key for accessing the LlamaIndex backend | `a-strong-random-string` |

## Optional Environment Variables

These variables have default values but can be customized:

### Deployment Settings
| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `PORT` | Port to run the API on | `8000` | Must be 8000 for Railway |

### Frontend Integration
| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `FRONTEND_URL` | URL of the frontend for CORS | `""` | Add your frontend URL |

### Embedding Configuration
| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `EMBEDDING_MODEL` | OpenAI embedding model to use | `text-embedding-3-large` | |
| `EMBEDDING_DIMENSIONS` | Dimensions for the embedding model | `3072` | |

### Environment Settings
| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENVIRONMENT` | Environment | `production` | `development`, `production`, `test` |
| `DEBUG` | Enable debug mode | `false` | `true` or `false` |

## Railway-specific Variables

These variables are automatically set by Railway and don't need to be configured manually:

- `RAILWAY_SERVICE_ID`
- `RAILWAY_ENVIRONMENT_NAME`
- `RAILWAY_SERVICE_NAME`

## Health Checks

The application includes comprehensive environment health checks:

1. **Quick Check**: A simple check that logs warnings for missing variables
2. **Pre-flight Check**: A more comprehensive check that validates variable values
3. **Health Endpoint**: The `/health` endpoint returns detailed environment status
4. **Monitoring**: The `railway_env_monitor.py` script can be run periodically to check environment health

## Environment Template

You can generate a template `.env` file with all required variables using:

```bash
python backend/env_template.py
```

This will create a `.env.template` file that you can edit and rename to `.env` for local development.

To check if your `.env` file has all required variables:

```bash
python backend/env_template.py --check
```
