from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from middleware import add_request_logger
from llama_index.core import VectorStoreIndex, Document, Settings
# Use the correct import path for SimpleDirectoryReader
try:
    from llama_index.readers.file import SimpleDirectoryReader
except ImportError:
    # Fallback import path
    from llama_index.core import SimpleDirectoryReader
# Import embeddings
try:
    from llama_index.embeddings.openai import OpenAIEmbedding
except ImportError:
    try:
        from llama_index.core.embeddings import OpenAIEmbedding
    except ImportError:
        from llama_index.embeddings import OpenAIEmbedding

import os
import uuid
import json
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# Define storage bucket name from environment variables with fallback to "files"
STORAGE_BUCKET_NAME = os.environ.get("STORAGE_BUCKET_NAME", "files")
print(f"Using storage bucket name: {STORAGE_BUCKET_NAME}")

# Import for vector store
import pinecone
# Flexible import path for PineconeVectorStore
try:
    from llama_index.vector_stores.pinecone import PineconeVectorStore
except ImportError:
    try:
        # Alternative import path
        from llama_index.vector_stores.pinecone.base import PineconeVectorStore
    except ImportError:
        # Another possible path
        from llama_index.indices.vector_store.providers.pinecone import PineconeVectorStore
from fastapi.responses import JSONResponse

# Supabase imports
from supabase import create_client, Client

# JWT handling
import base64
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    print("WARNING: PyJWT not installed. JWT verification will not work. Install with pip install pyjwt")

# Import environment health check
try:
    from env_health_check import run_health_check, log_health_check_results, check_env_vars
    ENV_HEALTH_CHECK_AVAILABLE = True
    # Run environment health check at startup
    print("Running environment health check at startup...")
    health_report = run_health_check(verbose=True)
    log_health_check_results(health_report)
    if health_report["status"] == "unhealthy":
        print("⚠️ WARNING: Environment health check found issues that may affect application functionality")
        # Log specific issues for Railway logs
        for service_name, service_status in health_report.get("connectivity", {}).items():
            if not service_status.get("success", True):
                print(f"❌ Service connectivity issue: {service_name} - {service_status.get('message', 'Unknown error')}")
        
        # Log environment variable issues
        env_vars = health_report.get("environment_variables", {}).get("details", {})
        for var_name, details in env_vars.items():
            if details.get("status", "VALID") != "VALID" and details.get("required", False):
                print(f"❌ Required variable issue: {var_name} - {details.get('status', 'Unknown status')}")
except ImportError:
    ENV_HEALTH_CHECK_AVAILABLE = False
    print("WARNING: env_health_check.py not available. Health checks will be limited.")

app = FastAPI(title="LlamaIndex API", 
              description="Backend API for LlamaIndex document ingestion and querying",
              version="1.0.0")

# Add request logging middleware to track ALL incoming requests
add_request_logger(app)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,    allow_origins=[
        "https://llamaindex-production-633d.up.railway.app",  # Backend URL itself
        "http://localhost:3000",          # For local development frontend
        "https://localhost:3000",         # For secure local development
        "https://chatbot-ui-loyat-one.vercel.app",  # Your Vercel frontend
        "*",                             # Allow all origins temporarily for debugging
        os.environ.get("FRONTEND_URL", ""),  # Get from environment variable if set
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "maxgpt")
INDEX_NAME = PINECONE_INDEX_NAME  # For backward compatibility
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# OpenAI embedding configuration
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "3072"))

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Authentication
security = HTTPBearer(auto_error=False)

# Authentication utility - improved with Supabase JWT verification
async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Verify JWT token from Supabase.
    
    In development mode, this will pass through any token.
    In production, it will verify the token if SUPABASE_JWT_SECRET is set.
    """
    # Return None if no credentials provided
    if not credentials:
        return None
        
    token = credentials.credentials
    
    # Get JWT secret from environment
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
    
    # In development mode or if no JWT secret, just return the token
    if not jwt_secret or os.environ.get("ENVIRONMENT") == "development":
        print("Development mode or no JWT secret - skipping token verification")
        return token
        
    # In production with JWT secret, verify the token
    if JWT_AVAILABLE:
        try:
            # Supabase JWT verification
            # The secret is base64 encoded, need to decode it first
            jwt_secret_bytes = base64.b64decode(jwt_secret)
            
            # Decode and verify JWT
            decoded = jwt.decode(
                token,
                jwt_secret_bytes,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # Return the token if verification succeeds
            print("JWT verification successful")
            return token
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    else:
        print("WARNING: JWT library not available, token verification skipped")
        return token

# Initialize services and build index at startup
@app.on_event("startup")
def load_index():
    global index, supabase_client
    
    # Initialize variables with default values
    index = None
    supabase_client = None
    
    # First set up basic functionality without external dependencies
    print("Starting application initialization...")
    
    # Initialize external services with more robust error handling
    try:
        # Check if Pinecone credentials are available
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            print("WARNING: Missing Pinecone credentials. Some features will be unavailable.")
            # Continue initialization - don't return early
              # Initialize Pinecone with error handling
        try:
            # Use the new Pinecone client initialization
            try:
                # Try the new Pinecone client approach
                from pinecone import Pinecone, ServerlessSpec
                
                # Create Pinecone client
                pc = Pinecone(api_key=PINECONE_API_KEY)
                print("Initialized Pinecone client using new API")
                  # Check if index exists
                existing_indexes = pc.list_indexes().names()
                print(f"DEBUG: Available Pinecone indexes: {existing_indexes}")
                print(f"DEBUG: Looking for index: {INDEX_NAME}")
                if INDEX_NAME not in existing_indexes:
                    print(f"WARNING: Index '{INDEX_NAME}' not found in Pinecone. For best results, create it manually in the Pinecone console.")
                    print("Attempting to create index with default settings - this may fail if your account does not support these settings.")
                      try:
                        # Try to create the index with serverless spec
                        pc.create_index(
                            name=INDEX_NAME,
                            dimension=3072,  # For text-embedding-3-large model
                            metric="cosine",
                            spec=ServerlessSpec(
                                cloud=PINECONE_ENVIRONMENT.split("-")[0],  # Extract cloud provider from environment
                                region=PINECONE_ENVIRONMENT.split("-", 1)[1] if "-" in PINECONE_ENVIRONMENT else "us-west-2"
                            )
                        )
                        print(f"Successfully created Pinecone index: {INDEX_NAME} with serverless spec")
                    except Exception as spec_error:
                        print(f"Serverless creation failed, trying standard creation: {spec_error}")
                        # Try again without serverless spec (for older Pinecone accounts)                        try:
                            pc.create_index(
                                name=INDEX_NAME,
                                dimension=3072,  # For text-embedding-3-large model
                                metric="cosine"
                            )
                            print(f"Successfully created Pinecone index: {INDEX_NAME}")
                        except Exception as std_error:
                            print(f"Failed to auto-create Pinecone index: {str(std_error)}")
                            print("Please create the index manually in the Pinecone console with the appropriate settings for your account.")
                  # Connect to the index
                try:
                    # Use the new API to get the index
                    print(f"DEBUG: Connecting to Pinecone index: {INDEX_NAME}")
                    pinecone_index = pc.Index(INDEX_NAME)
                    print(f"DEBUG: Successfully connected to Pinecone index")
                    print(f"DEBUG: Index stats: {pinecone_index.describe_index_stats()}")
                    vector_store = PineconeVectorStore(pinecone_index)# Configure the embeddings explicitly
                    embed_model = OpenAIEmbedding(
                        api_key=OPENAI_API_KEY,
                        model="text-embedding-3-large",  # Large model with 3072 dimensions
                        dimensions=3072
                    )
                      # Update the global settings
                    Settings.embed_model = embed_model
                    
                    # Initialize empty index with the embed model explicitly set
                    # For a new/empty index, we need to create a minimal structure
                    try:
                        # Try to create with empty nodes list to initialize structure
                        index = VectorStoreIndex(nodes=[], vector_store=vector_store, embed_model=embed_model)
                        print("Pinecone and Vector Index initialized successfully with OpenAI embeddings")
                    except Exception as struct_error:
                        print(f"Note: Could not initialize with empty nodes: {struct_error}")
                        # Create a simple document as placeholder if needed
                        placeholder_doc = Document(text="Placeholder document for initializing index.", id_="placeholder")
                        index = VectorStoreIndex.from_documents([placeholder_doc], vector_store=vector_store, embed_model=embed_model)
                        print("Initialized index with a placeholder document")
                    except ValueError as e:
                        if "One of nodes, objects, or index_struct must be provided" in str(e):
                            # Create an empty document to initialize the index structure
                            print("Creating an empty index with a blank document to initialize structure")
                            empty_doc = Document(text="This is a placeholder document to initialize the index structure.")
                            index = VectorStoreIndex.from_documents(
                                [empty_doc], 
                                vector_store=vector_store,
                                embed_model=embed_model
                            )
                            print("Created new index structure with an empty document")
                        else:
                            raise
                except Exception as index_error:
                    print(f"Failed to connect to Pinecone index: {str(index_error)}")
                    index = None  # Set to None to indicate initialization failure
                    
            except (ImportError, AttributeError) as version_error:
                # Fall back to legacy approach if needed
                print(f"Using legacy Pinecone initialization: {version_error}")
                
                # Legacy initialization method (for older versions)
                pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
                
                if INDEX_NAME not in pinecone.list_indexes():
                    print(f"WARNING: Index '{INDEX_NAME}' not found in Pinecone. Attempting to create it...")
                    pinecone.create_index(
                        name=INDEX_NAME,
                        dimension=3072,  # For text-embedding-3-large model
                        metric="cosine",
                        pod_type="p1"  # Using pod_type instead of cloud/region for better compatibility
                    )
                    
                # Connect to the index
                pinecone_index = pinecone.Index(INDEX_NAME)
                vector_store = PineconeVectorStore(pinecone_index)                # Configure the embeddings explicitly
                embed_model = OpenAIEmbedding(
                    api_key=OPENAI_API_KEY,
                    model="text-embedding-3-large",  # Large model with 3072 dimensions
                    dimensions=3072
                )
                  # Update the global settings
                Settings.embed_model = embed_model
                
                # Initialize empty index with the embed model explicitly set
                # For a new/empty index, we need to create a minimal structure
                try:
                    # Try to create with empty nodes list to initialize structure
                    index = VectorStoreIndex(nodes=[], vector_store=vector_store, embed_model=embed_model)
                    print("Pinecone and Vector Index initialized successfully with OpenAI embeddings (legacy method)")
                except Exception as struct_error:
                    print(f"Note: Could not initialize with empty nodes: {struct_error}")
                    # Create a simple document as placeholder if needed
                    placeholder_doc = Document(text="Placeholder document for initializing index.", id_="placeholder")
                    index = VectorStoreIndex.from_documents([placeholder_doc], vector_store=vector_store, embed_model=embed_model)
                    print("Initialized index with a placeholder document (legacy method)")
                except ValueError as e:
                    if "One of nodes, objects, or index_struct must be provided" in str(e):
                        # Create an empty document to initialize the index structure
                        print("Creating an empty index with a blank document to initialize structure")
                        empty_doc = Document(text="This is a placeholder document to initialize the index structure.")
                        index = VectorStoreIndex.from_documents(
                            [empty_doc], 
                            vector_store=vector_store,
                            embed_model=embed_model
                        )
                        print("Created new index structure with an empty document (legacy method)")
                    else:
                        raise
                
        except Exception as index_error:
            print(f"Failed to connect to Pinecone index: {str(index_error)}")
            index = None  # Set to None to indicate initialization failure
        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
          # Initialize Supabase client with error handling
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                # Initialize Supabase client with only the required parameters
                # to avoid issues with unexpected keyword arguments like 'proxy'
                try:
                    # First attempt: Basic initialization with just URL and key
                    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                except TypeError as type_error:
                    if "got an unexpected keyword argument" in str(type_error):
                        print(f"Adjusting Supabase client initialization due to: {type_error}")
                        # Different versions of the library may expect different parameters
                        # Try to import the specific version and adjust accordingly
                        import sys
                        print(f"Supabase library version: {sys.modules.get('supabase', None)}")
                        
                        # Handle potential version differences
                        import inspect
                        client_params = inspect.signature(create_client).parameters
                        if len(client_params) == 2:  # Just URL and key
                            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                        else:
                            # Fallback to basic minimum parameters
                            supabase_client = create_client(
                                supabase_url=SUPABASE_URL,
                                supabase_key=SUPABASE_KEY
                            )
                    else:
                        raise                print("Supabase client initialized successfully")
                
                # Try to make a simple API call to verify connectivity
                try:
                    health_check = supabase_client.table("llama_index_documents").select("count", count="exact").limit(1).execute()
                    print(f"Supabase connectivity verified with simple query")
                except Exception as health_error:
                    print(f"Supabase connectivity check failed: {health_error}")
                    if "Authentication failed" in str(health_error) or "JWT" in str(health_error):
                        print("AUTHENTICATION ERROR: Likely issue with Supabase key or permissions")
                        print("Verify SUPABASE_ANON_KEY is correct and RLS policies are properly configured")
                    elif "not found" in str(health_error).lower():
                        print("TABLE ERROR: Required table not found in database")
                        print("Make sure all migration scripts have been run")
                    else:
                        print(f"Unexpected Supabase error: {str(health_error)}")
                
                # Check storage bucket access
                try:
                    storage_buckets = supabase_client.storage.list_buckets()
                    print(f"Successfully accessed storage buckets: {[b['name'] for b in storage_buckets]}")
                except Exception as storage_error:
                    print(f"Failed to access storage buckets: {storage_error}")
                    if "permission" in str(storage_error).lower() or "access" in str(storage_error).lower():
                        print("STORAGE ERROR: Likely permissions issue with storage buckets")
                        print("Verify RLS policies for storage are correctly set up")                # Check if llama_index_documents table exists
                try:
                    # Try to query the table - this will fail if it doesn't exist
                    supabase_client.table("llama_index_documents").select("id").limit(1).execute()
                    print("'llama_index_documents' table exists")
                except Exception as table_error:
                    print(f"'llama_index_documents' table check failed: {table_error}")
                    if "not found" in str(table_error).lower():
                        print("WARNING: 'llama_index_documents' table not found.")
                        print("Please apply the migration from: supabase/migrations/20250618000000_add_llama_index_documents.sql")
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}")
                # Check for common errors and provide helpful messages
                if "connection" in str(e).lower() or "network" in str(e).lower():
                    print("NETWORK ERROR: Could not connect to Supabase")
                    print("Check that the SUPABASE_URL is correct and the service is accessible from your deployment environment")
                elif "unauthorized" in str(e).lower() or "authentication" in str(e).lower():
                    print("AUTHENTICATION ERROR: Supabase rejected the provided credentials")
                    print("Verify that SUPABASE_ANON_KEY is correct")
                supabase_client = None
        else:
            print("WARNING: Missing Supabase credentials. Document storage features will be unavailable.")
            
    except Exception as e:
        print(f"Error during startup: {e}")
        # The app will still start, but with limited functionality

# Models for API requests/responses
class QueryRequest(BaseModel):
    question: str
    user_id: Optional[str] = None

class DocumentMetadata(BaseModel):
    name: str
    type: str
    size: int
    user_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class DocumentResponse(BaseModel):
    id: str
    name: str
    created_at: str
    metadata: dict

@app.post("/query")
async def query(request: QueryRequest, token: str = Depends(verify_token)):
    # Check if index is available
    if index is None:
        print("Query attempted but vector index is not available")
        return {
            "error": "Vector index not available", 
            "message": "Please check Pinecone configuration and API keys",
            "status": "service_unavailable"
        }
    
    try:
        # Create query engine with error handling
        try:
            query_engine = index.as_query_engine()
        except Exception as qe_error:
            print(f"Failed to create query engine: {str(qe_error)}")
            return {
                "error": "Failed to initialize query engine",
                "message": "Internal server error with query engine creation",
                "status": "internal_error"
            }
        
        # Log the query to Supabase (optional, non-blocking)
        if supabase_client and request.user_id:
            try:
                supabase_client.table("queries").insert({
                    "user_id": request.user_id,
                    "question": request.question,
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()
            except Exception as e:
                # Just log the error but continue with the query
                print(f"Error logging query: {e}")
        
        # Execute query with timeout and error handling
        try:
            # Execute query
            result = query_engine.query(request.question)
            print(f"Query successful: '{request.question}' -> response length: {len(str(result))}")
            return {"answer": str(result)}
        except Exception as query_error:
            print(f"Query execution failed: {str(query_error)}")
            return {
                "error": f"Query execution failed",
                "message": f"Error: {str(query_error)}",
                "status": "query_error"
            }
    except Exception as e:
        print(f"Unexpected query error: {str(e)}")
        return {
            "error": "Unexpected error",
            "message": f"Details: {str(e)}",
            "status": "error"
        }

@app.get("/admin/status")
async def admin_status(token: str = Depends(verify_token)):
    status = {
        "services": {
            "pinecone": {},
            "supabase": {},
        },
        "index": {},
        "system": {
            "api_version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
      # Check Pinecone status
    status["services"]["pinecone"]["api_key_set"] = bool(PINECONE_API_KEY)
    status["services"]["pinecone"]["environment_set"] = bool(PINECONE_ENVIRONMENT)
    
    try:
        # Try new Pinecone client approach first
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=PINECONE_API_KEY)
            pinecone_indexes = pc.list_indexes().names()
            status["services"]["pinecone"]["connected"] = True
            status["services"]["pinecone"]["indexes"] = pinecone_indexes
            status["services"]["pinecone"]["index_exists"] = INDEX_NAME in pinecone_indexes
            status["services"]["pinecone"]["client_version"] = "new"
        except (ImportError, AttributeError):
            # Fall back to legacy approach
            pinecone_indexes = pinecone.list_indexes()
            status["services"]["pinecone"]["connected"] = True
            status["services"]["pinecone"]["indexes"] = pinecone_indexes
            status["services"]["pinecone"]["index_exists"] = INDEX_NAME in pinecone_indexes
            status["services"]["pinecone"]["client_version"] = "legacy"
    except Exception as e:
        status["services"]["pinecone"]["connected"] = False
        status["services"]["pinecone"]["error"] = str(e)
    
    # Check Supabase status
    status["services"]["supabase"]["url_set"] = bool(SUPABASE_URL)
    status["services"]["supabase"]["key_set"] = bool(SUPABASE_KEY)
    
    try:
        if supabase_client:
            # Simple connection test - fetch user count
            response = supabase_client.table("documents").select("count", count="exact").execute()
            doc_count = response.count if hasattr(response, 'count') else 0
            
            status["services"]["supabase"]["connected"] = True
            status["services"]["supabase"]["document_count"] = doc_count
        else:
            status["services"]["supabase"]["connected"] = False
    except Exception as e:
        status["services"]["supabase"]["connected"] = False
        status["services"]["supabase"]["error"] = str(e)
    
    # Check in-memory index
    status["index"]["loaded"] = 'index' in globals() and index is not None
    
    # Optionally, check if index has documents
    try:
        if status["index"]["loaded"]:
            # This is a best-effort check
            status["index"]["document_count"] = getattr(index, 'docstore', None) and len(getattr(index.docstore, 'docs', {}))
        else:
            status["index"]["document_count"] = 0
    except Exception as e:
        status["index"]["error"] = str(e)
    
    return JSONResponse(content=status)

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    metadata: Optional[str] = None,
    token: str = Depends(verify_token)
):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Parse metadata if provided
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except:
                meta_dict = {"description": metadata}
        
        # Add basic file metadata
        meta_dict.update({
            "name": file.filename,
            "type": file.content_type,
            "size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        })
        
        # Upload file content to Supabase Storage
        storage_path = f"{doc_id}"
        supabase_client.storage.from_("files").upload(
            path=storage_path,
            file=file_content,
            file_options={"content_type": file.content_type}
        )
        
        # Insert metadata record in the documents table
        supabase_client.table("documents").insert({
            "id": doc_id,
            "name": file.filename,
            "metadata": meta_dict
        }).execute()
        
        # Create LlamaIndex document and add to the index
        doc = Document(
            text=file_content.decode('utf-8') if isinstance(file_content, bytes) else str(file_content),
            metadata=meta_dict
        )
        
        # Update the vector index
        global index
        if index:
            index.insert(doc)
        
        return {
            "id": doc_id,
            "name": file.filename,
            "message": "File uploaded and indexed successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/reindex")
async def reindex(user_id: Optional[str] = None, token: str = Depends(verify_token)):
    global index
    
    try:
        # Load documents from Supabase
        documents = await load_documents_from_supabase(user_id)
        
        if not documents:
            return {"message": "No documents found to index."}
              # Configure the embeddings explicitly
        embed_model = OpenAIEmbedding(
            api_key=OPENAI_API_KEY,
            model="text-embedding-3-large",  # Large model with 3072 dimensions
            dimensions=3072
        )
        
        # Update the global settings
        Settings.embed_model = embed_model
        
        # Recreate the index with the loaded documents and explicit embeddings
        index = VectorStoreIndex.from_documents(
            documents, 
            vector_store=index.vector_store,
            embed_model=embed_model
        )
        
        return {
            "message": "Reindexing completed successfully.",
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing documents: {str(e)}")

@app.post("/delete_index")
def delete_index():
    global index
    try:
        # Try new Pinecone client approach first
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=PINECONE_API_KEY)
            pc.delete_index(INDEX_NAME)
            print(f"Deleted Pinecone index: {INDEX_NAME} using new API")
        except (ImportError, AttributeError):
            # Fall back to legacy approach
            pinecone.delete_index(INDEX_NAME)
            print(f"Deleted Pinecone index: {INDEX_NAME} using legacy API")
    except Exception as e:
        print(f"Error deleting index: {e}")
    
@app.get("/")
def root():
    """Root endpoint for basic API information."""
    # This is the most fundamental endpoint and should never fail
    try:
        # Get service status with external dependencies
        services = {
            "pinecone": {
                "initialized": index is not None,
                "api_key_set": bool(PINECONE_API_KEY),
                "environment_set": bool(PINECONE_ENVIRONMENT),
                "index_name": PINECONE_INDEX_NAME,
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimensions": EMBEDDING_DIMENSIONS
            },
            "supabase": {
                "initialized": supabase_client is not None,
                "url_set": bool(SUPABASE_URL),
                "key_set": bool(SUPABASE_KEY),
                "jwt_secret_set": bool(os.environ.get("SUPABASE_JWT_SECRET")),
                "jwt_library_available": JWT_AVAILABLE
            },
            "openai": {
                "api_key_set": bool(OPENAI_API_KEY)
            },
            "auth": {
                "api_key_auth": bool(os.environ.get("BACKEND_API_KEY")),
                "environment": os.environ.get("ENVIRONMENT", "production")
            }
        }
        
        # Add build and deployment info
        deployment_info = {
            "port": os.environ.get("PORT", 8000),
            "host": "0.0.0.0",
            "railway_service_id": os.environ.get("RAILWAY_SERVICE_ID", "Not deployed on Railway"),
            "deployed": bool(os.environ.get("RAILWAY_SERVICE_ID")),
        }
        
        return {
            "service": "LlamaIndex API",
            "status": "running",
            "version": "1.0.2",
            "docs": "/docs",
            "services": services,
            "deployment": deployment_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Absolute fallback that should never fail
        return {
            "service": "LlamaIndex API",
            "status": "running with errors",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health")
def health_check():
    """Simple health check endpoint that always returns 200 OK."""
    # Always return 200 OK for Railway deployments    return {"status": "ok", "message": "Service is running"}

@app.get("/list_indices")
def list_indices():
    try:
        # Try new Pinecone client approach first
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=PINECONE_API_KEY)
            indices = pc.list_indexes().names()
            return {"indices": indices}
        except (ImportError, AttributeError):
            # Fall back to legacy approach
            indices = pinecone.list_indexes()
            return {"indices": indices}
    except Exception as e:
        return {"error": f"Failed to list indices: {str(e)}"}

# Authentication utility
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token for API access
    
    Checks if the provided token matches the expected API key.
    Falls back to JWT verification if API_KEY is not set.
    """
    # Return None if no credentials provided
    if not credentials:
        return None
        
    token = credentials.credentials
    
    # Check if an API key is set for simple auth
    api_key = os.environ.get("API_KEY")
    if api_key and token == api_key:
        return token
    
    # If no API key is set, allow in dev mode
    if os.environ.get("ENVIRONMENT") == "development":
        return token
        
    # In production without matching key, reject
    if api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # No API key set, accept any token (not recommended for production)
    print("WARNING: No API_KEY set, authentication is disabled")
    return token

# Utility function to load documents from Supabase
async def load_documents_from_supabase(user_id: Optional[str] = None):
    """Load documents from Supabase storage and convert to LlamaIndex documents"""
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Query the 'documents' table in Supabase
        query = supabase_client.table('documents')
        if user_id:
            query = query.eq('user_id', user_id)
        
        response = query.select('*').execute()
        db_documents = response.data
        
        llama_docs = []
        for doc in db_documents:
            # Get file content from Supabase Storage
            try:
                storage_response = supabase_client.storage.from_('files').download(f"{doc['id']}")
                content = storage_response.decode('utf-8')
                
                # Create LlamaIndex Document
                metadata = {
                    'id': doc['id'],
                    'name': doc['name'],
                    'user_id': doc.get('user_id'),
                    'created_at': doc['created_at'],
                    'tags': doc.get('tags', [])
                }
                llama_docs.append(Document(text=content, metadata=metadata))
            except Exception as e:
                print(f"Error loading document {doc['id']}: {e}")
                continue
                
        return llama_docs
    except Exception as e:
        print(f"Error fetching documents from Supabase: {e}")
        return []

@app.get("/documents")
async def list_documents(user_id: Optional[str] = None, token: str = Depends(verify_token)):
    """List all documents in the Supabase storage"""
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Query documents table
        query = supabase_client.table("documents")
        if user_id:
            query = query.eq("user_id", user_id)
            
        response = query.select("*").execute()
        documents = response.data
        
        # Format response
        result = []
        for doc in documents:
            result.append({
                "id": doc["id"],
                "name": doc["name"],
                "created_at": doc.get("created_at", ""),
                "metadata": doc.get("metadata", {})
            })
            
        return {"documents": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, token: str = Depends(verify_token)):
    """Delete a document from Supabase and remove from the index"""
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    
    try:
        # Delete from Supabase Storage first
        supabase_client.storage.from_("files").remove([document_id])
        
        # Then delete metadata from documents table
        supabase_client.table("documents").delete().eq("id", document_id).execute()
        
        # Note: The document will remain in the Pinecone index until reindexing
        # For immediate removal, we would need document ID tracking in Pinecone
        
        return {"message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.post("/process")
async def process_file(request: Request, token: str = Depends(verify_token)):
    """
    Process a file that has already been uploaded to Supabase.
    This endpoint is called by the frontend after a file is uploaded.
    
    Authentication is required via API key or development mode.
    """
    print("==== /process endpoint called ====")
    print(f"Authentication token present: {bool(token)}")
    
    # Check authentication
    if not token:
        print("ERROR: Authentication token missing")
        raise HTTPException(
            status_code=401, 
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check service initialization
    print("Checking services initialization...")
    service_status = {}
    
    # Check Supabase
    if not supabase_client:
        print("ERROR: Supabase client not initialized")
        service_status["supabase"] = "not connected"
        if SUPABASE_URL and SUPABASE_KEY:
            print(f"Supabase URL and key are set, but client initialization failed")
        else:
            print(f"Supabase URL or key missing: URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}")
        raise HTTPException(
            status_code=500, 
            detail="Supabase client not initialized. Check connection and credentials."
        )
    else:
        service_status["supabase"] = "connected"
      # Check Pinecone/vector index
    if not index:
        print("ERROR: Vector index not initialized")
        service_status["pinecone"] = "not connected"
        raise HTTPException(
            status_code=500, 
            detail="Vector index not initialized. Check Pinecone connection and index configuration."
        )
    else:
        service_status["pinecone"] = "connected"
    
    print(f"Service status: {service_status}")
    
    try:
        # Parse the request body
        print("Parsing request body...")
        try:
            data = await request.json()
            print("Request body parsed successfully")
        except Exception as e:
            print(f"ERROR: Failed to parse request body: {str(e)}")
            import traceback
            print(f"TRACE: {traceback.format_exc()}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON in request body: {str(e)}"
            )
        
        # Extract and validate parameters
        file_id = data.get("file_id")
        supabase_file_path = data.get("supabase_file_path")
        file_name = data.get("name", "Unknown")
        file_type = data.get("type", "text/plain")
        description = data.get("description", "")
        user_id = data.get("user_id")
        
        print(f"Processing request for file: {file_name}")
        print(f"File ID: {file_id}")
        print(f"File path in Supabase: {supabase_file_path}")
        print(f"File type: {file_type}")
        print(f"User ID: {user_id}")
        
        if not file_id or not supabase_file_path:
            raise HTTPException(status_code=400, detail="Missing required file information")
            
        # Check file size limits (30MB max)
        max_size_bytes = 30 * 1024 * 1024  # 30MB
        file_size = data.get("size", 0)
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=413, 
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size of {max_size_bytes} bytes (30MB)"
            )        
        print(f"Processing file {file_name} (ID: {file_id}) from Supabase path: {supabase_file_path}")
          # Download the file from Supabase storage
        try:
            print(f"Attempting to download file from Supabase...")
            print(f"Bucket: 'files', Path: '{supabase_file_path}'")
            
            # Check if storage API is accessible
            try:
                buckets = supabase_client.storage.list_buckets()
                print(f"Available storage buckets: {[b['name'] for b in buckets]}")
                  # Check if 'files' bucket exists (this is the bucket used by frontend)
                if not any(b['name'] == 'files' for b in buckets):
                    print("NOTE: 'files' bucket not visible in list but already exists")
                    print("Available buckets:", [b['name'] for b in buckets])
            except Exception as bucket_error:
                print(f"Error listing storage buckets: {str(bucket_error)}")
                print("Continuing with download attempt anyway...")
                  # Get Supabase auth status
            print(f"[DEBUG] Supabase auth status check...")
            try:
                user = supabase_client.auth.get_user()
                print(f"[DEBUG] Auth successful! User ID: {user.user.id if user and user.user else 'Unknown'}")
            except Exception as auth_err:
                print(f"[DEBUG] Auth error: {str(auth_err)}")
                
            # Check JWT and headers in a safer way
            has_session = False
            try:
                has_session = hasattr(supabase_client.auth, 'session') and supabase_client.auth.session() is not None
            except Exception as session_err:
                print(f"[DEBUG] Error checking session: {str(session_err)}")
                
            print(f"[DEBUG] JWT token status: {'Present' if has_session else 'Missing'}")
            
            # Import service role helper
            from supabase_service_auth import get_service_authenticated_supabase
            
            # Create a service-role authenticated client as backup
            service_client = get_service_authenticated_supabase()
            if service_client:
                print(f"[DEBUG] Service role client created successfully as backup")
            else:
                print(f"[DEBUG] Failed to create service role client - missing SUPABASE_SERVICE_ROLE_KEY?")
                
            # Try to list files in the bucket
            print(f"[DEBUG] Listing files in the 'files' bucket...")
            try:
                # First try with regular client
                try:
                    files_in_bucket = supabase_client.storage.from_("files").list()
                    print(f"[DEBUG] Files in bucket (regular auth): {[f['name'] for f in files_in_bucket[:5]]}{'... and more' if len(files_in_bucket) > 5 else ''}")
                except Exception as list_regular_error:
                    print(f"[DEBUG] Regular auth listing failed: {str(list_regular_error)}")
                    # Fall back to service role if available
                    if service_client:
                        print(f"[DEBUG] Trying to list files with service role...")
                        files_in_bucket = service_client.storage.from_("files").list()
                        print(f"[DEBUG] Files in bucket (service auth): {[f['name'] for f in files_in_bucket[:5]]}{'... and more' if len(files_in_bucket) > 5 else ''}")
                    else:
                        print(f"[DEBUG] No fallback available for file listing")
                        files_in_bucket = []
                
                # Check if the file exists in storage
                file_exists = any(f['name'] == supabase_file_path for f in files_in_bucket)
                alt_path = f"{user_id}/{file_id}" if user_id and file_id else None
                alt_exists = any(f['name'] == alt_path for f in files_in_bucket) if alt_path else False
                
                print(f"[DEBUG] File check - Original path '{supabase_file_path}': {'Found' if file_exists else 'Not found'}")
                if alt_path:
                    print(f"[DEBUG] File check - Alternative path '{alt_path}': {'Found' if alt_exists else 'Not found'}")
            except Exception as list_error:
                print(f"[DEBUG] Error listing files in bucket: {str(list_error)}")
                print("[DEBUG] Continuing with download attempt anyway...")
                  # From the imported helper
            from supabase_service_auth import download_file_with_service_role
            
            # Attempt file download
            print(f"[DEBUG] Attempting to download with original path: '{supabase_file_path}'")
            try:
                # First try with the original path
                response = supabase_client.storage.from_("files").download(supabase_file_path)
                print(f"[DEBUG] ✓ Download successful with original path (regular auth)")
            except Exception as orig_error:
                print(f"[DEBUG] First download attempt failed: {str(orig_error)}")
                print(f"[DEBUG] Error type: {type(orig_error).__name__}")
                
                # Try service role with original path
                print(f"[DEBUG] Trying service role auth with original path")
                service_response = download_file_with_service_role("files", supabase_file_path)
                if service_response:
                    response = service_response
                    print(f"[DEBUG] ✓ Download successful with original path (service role auth)")
                else:
                    # If service role with original path fails, try alternative paths
                    if file_id and user_id:
                        alternative_path = f"{user_id}/{file_id}"
                        print(f"[DEBUG] Trying alternative path format: '{alternative_path}'")
                        
                        # Try regular auth with alternative path
                        try:
                            response = supabase_client.storage.from_("files").download(alternative_path)
                            print(f"[DEBUG] ✓ Download successful with alternative path (regular auth)")
                        except Exception as alt_error:
                            print(f"[DEBUG] Alternative path failed with regular auth: {str(alt_error)}")
                            
                            # Try service role with alternative path
                            print(f"[DEBUG] Trying service role auth with alternative path")
                            service_response = download_file_with_service_role("files", alternative_path)
                            if service_response:
                                response = service_response
                                print(f"[DEBUG] ✓ Download successful with alternative path (service role auth)")
                            else:
                                # Final attempt with just file_id
                                print(f"[DEBUG] Last attempt: trying with just file_id '{file_id}'")
                                
                                # Try regular auth with file_id only
                                try:
                                    response = supabase_client.storage.from_("files").download(file_id)
                                    print(f"[DEBUG] ✓ Download successful with file_id only (regular auth)")
                                except Exception as file_id_error:
                                    # Try service role with file_id only
                                    service_response = download_file_with_service_role("files", file_id)
                                    if service_response:
                                        response = service_response
                                        print(f"[DEBUG] ✓ Download successful with file_id only (service role auth)")
                                    else:
                                        print(f"[DEBUG] All download attempts failed. Details:")
                                        print(f"[DEBUG] - Original path error: {str(orig_error)}")
                                        print(f"[DEBUG] - Alternative path regular auth error: {str(alt_error)}")
                                        print(f"[DEBUG] - File ID only regular auth error: {str(file_id_error)}")
                                        raise Exception(f"Failed to download file with all path formats and auth methods. See logs for details.")
                    else:
                        print("[DEBUG] Cannot try alternative path: missing user_id or file_id")
                        raise orig_error
            
            if not response:
                print("ERROR: Empty response from Supabase download")
                raise Exception("Failed to download file from Supabase - empty response")
                
            file_content = response
            file_size = len(file_content) if file_content else 'unknown'
            print(f"Successfully downloaded file, size: {file_size} bytes")
            
            # Validate file content
            if file_size == 0:
                print("WARNING: Downloaded file has zero bytes")
            
        except Exception as e:
            print(f"ERROR: Failed to download file from Supabase: {str(e)}")
            
            # Check for specific errors
            error_message = str(e).lower()
            if "not found" in error_message:
                print("Likely cause: File does not exist in the specified path")
                raise HTTPException(
                    status_code=404, 
                    detail=f"File not found in Supabase storage: {supabase_file_path}"
                )
            elif "permission" in error_message or "access" in error_message or "denied" in error_message:
                print("Likely cause: Permission issues with Supabase storage")
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied accessing file in Supabase storage. Check bucket policies and RLS."
                )
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error retrieving file from Supabase: {str(e)}"
                )
          # Create metadata for the document
        metadata = {
            "supabase_file_id": file_id,
            "name": file_name,
            "type": file_type,
            "description": description,
            "user_id": user_id,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Process the file based on its type
        file_text = ""
        try:            # Decode the file content based on type
            if isinstance(file_content, bytes):
                # For text-based files, try to decode as UTF-8
                if file_type.startswith("text/") or file_type in [
                    "application/json", 
                    "application/xml",
                    "application/csv"
                ]:
                    file_text = file_content.decode('utf-8')
                # Handle PDF files
                elif file_type == "application/pdf":
                    print("="*50)
                    print("PDF PROCESSING INITIATED")
                    print(f"File name: {file_name}")
                    print(f"Content size: {len(file_content)} bytes")
                    print("="*50)
                    
                    try:
                        # Use the separate PDF processor module
                        print("Importing PDF processor module...")
                        try:
                            from pdf_processor import extract_text_with_ocr_fallback
                            print("PDF processor module imported successfully")
                        except ImportError as module_err:
                            print(f"ERROR: Could not import pdf_processor module: {str(module_err)}")
                            raise ImportError(f"Failed to import PDF processor: {str(module_err)}")
                        
                        # Process the PDF with OCR fallback
                        print("Starting PDF processing with OCR fallback...")
                        file_text, used_ocr = extract_text_with_ocr_fallback(file_content)
                        print(f"PDF processing {'with OCR' if used_ocr else 'without OCR'} successful ({len(file_text)} characters)")
                        
                        # Make sure we actually got text
                        if not file_text or len(file_text.strip()) == 0:
                            print("WARNING: PDF processing produced empty text")
                            if file_content.startswith(b'%PDF'):
                                # It is a PDF but extraction failed
                                print("File appears to be a valid PDF but all extraction methods failed")
                                # Return a placeholder message
                                file_text = f"[This PDF document could not be processed: {file_name}]"
                        
                    except ImportError as import_err:
                        print(f"ERROR: PDF library not available: {str(import_err)}")
                        import traceback
                        print(f"TRACE: {traceback.format_exc()}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"PDF processing is not available: {str(import_err)}"
                        )
                    except Exception as pdf_err:
                        print(f"ERROR: PDF processing failed: {str(pdf_err)}")
                        import traceback
                        print(f"TRACE: {traceback.format_exc()}")
                        
                        # Check if it's actually a PDF
                        if not file_content.startswith(b'%PDF'):
                            raise HTTPException(
                                status_code=400,
                                detail=f"The file does not appear to be a valid PDF."
                            )
                        
                        # The OCR should have already been attempted by extract_text_with_ocr_fallback
                        # This is a fallback in case both standard extraction and OCR failed
                        print("All PDF processing methods failed")
                        file_text = f"[This PDF could not be processed: {file_name}]"
                else:
                    # For other binary files we don't yet support
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unsupported file type: {file_type}. Current implementation supports text and PDF files only."
                    )
            else:
                file_text = str(file_content)
        except Exception as e:
            print(f"Error processing file content: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file content: {str(e)}"
            )
            
        # Create LlamaIndex document and implement chunking
        from llama_index.core.node_parser import SentenceSplitter
        
        # Create a document first
        doc = Document(text=file_text, metadata=metadata)
        
        # Create a text splitter/chunker
        splitter = SentenceSplitter(
            chunk_size=1024,  # Target chunk size (characters) 
            chunk_overlap=200,  # Overlap between chunks
            paragraph_separator="\n\n",
            secondary_chunking_regex="[^,.;。？！]+[,.;。？！]?",
            tokenizer=None  # Will use default tiktoken tokenizer
        )
        
        # Split the document into chunks (nodes)
        nodes = splitter.get_nodes_from_documents([doc])
          # Insert the document into the index
        try:
            # Ensure each node has the file ID in its metadata for later deletion
            for node in nodes:
                if not node.metadata:
                    node.metadata = {}
                node.metadata["supabase_file_id"] = file_id
              # Insert the nodes into the index
            print(f"Inserting {len(nodes)} nodes into Pinecone index...")
            print(f"Index name: {INDEX_NAME}")
            print(f"Index object: {index}")
            print(f"First node metadata: {nodes[0].metadata if nodes else 'No nodes'}")
            print(f"Embedding model: {EMBEDDING_MODEL}")
            print(f"Embedding dimensions: {EMBEDDING_DIMENSIONS}")
            try:
                index.insert_nodes(nodes)
                print(f"✓ Successfully indexed {len(nodes)} chunks from file {file_name}")
                print(f"✓ Pinecone index should now have {len(nodes)} new vectors")
            except Exception as pinecone_error:
                print(f"ERROR: Failed to insert nodes into Pinecone: {str(pinecone_error)}")
                print(f"ERROR: Exception type: {type(pinecone_error).__name__}")
                import traceback
                print(f"ERROR: Full traceback:")
                print(traceback.format_exc())
                # Check for common Pinecone errors
                error_message = str(pinecone_error).lower()
                if "dimension" in error_message:
                    print("Likely cause: Embedding dimension mismatch")
                    print(f"Expected dimensions: {EMBEDDING_DIMENSIONS}")
                    print(f"Make sure your Pinecone index is configured correctly")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Embedding dimension mismatch. Check that your Pinecone index has {EMBEDDING_DIMENSIONS} dimensions."
                    )
                elif "rate limit" in error_message or "too many requests" in error_message:
                    print("Rate limit exceeded on Pinecone API")
                    raise HTTPException(
                        status_code=429,
                        detail="Pinecone rate limit exceeded. Please try again later."
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error indexing to Pinecone: {str(pinecone_error)}"
                    )# Store record in Supabase
            print("Recording indexed document in Supabase...")
            try:
                # Create a flexible record with required fields
                record_data = {
                    "supabase_file_id": file_id,
                    "processed": True,
                    "metadata": metadata
                }
                
                # Add optional fields that may not exist in all deployments
                # The try-except in this block will catch any schema errors
                try:
                    record_data["chunk_count"] = len(nodes)
                except Exception:
                    print("Note: chunk_count field could not be added")
                
                # Only add embedding model if defined
                if EMBEDDING_MODEL:
                    try:
                        record_data["embedding_model"] = EMBEDDING_MODEL
                    except Exception:
                        print("Note: embedding_model field could not be added")
                  # Add vector store info
                try:
                    record_data["vector_store"] = "pinecone"
                except Exception:
                    print("Note: vector_store field could not be added")
                
                print(f"Inserting document record with fields: {', '.join(record_data.keys())}")
                
                # Try with regular client first
                try:
                    response = supabase_client.table("llama_index_documents").insert(record_data).execute()
                    print("✓ Successfully recorded document in Supabase")
                except Exception as reg_client_error:
                    print(f"Regular client record insert failed: {str(reg_client_error)}")
                    
                    # Try with service role client if regular client fails
                    print("Trying with service role client...")
                    from supabase_service_auth import get_service_authenticated_supabase
                    service_client = get_service_authenticated_supabase()
                    
                    if service_client:
                        try:
                            response = service_client.table("llama_index_documents").insert(record_data).execute()
                            print("✓ Successfully recorded document in Supabase using service role client")
                        except Exception as service_error:
                            print(f"Service role client record insert also failed: {str(service_error)}")
                            raise service_error
                    else:
                        print("Could not create service role client")
                        raise reg_client_error
            except Exception as supabase_error:
                print(f"ERROR: Failed to record document in Supabase: {str(supabase_error)}")
                print("WARNING: Document was indexed in Pinecone but record in Supabase failed")
                # We don't want to fail the whole operation if just the record keeping failed
                # The document is already searchable in Pinecone
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            print(f"ERROR: Failed during indexing process: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error indexing document: {str(e)}"
            )
        
        print("==== Processing completed successfully ====")
        return {
            "success": True,
            "file_id": file_id,
            "chunks_processed": len(nodes),
            "message": "File processed and indexed successfully."        }
        
    except HTTPException as http_ex:
        # Log the error before re-raising
        print("=" * 50)
        print(f"HTTP Exception in /process: {http_ex.status_code} - {http_ex.detail}")
        print("=" * 50)
        raise
    except Exception as e:
        print("=" * 50)
        print(f"CRITICAL ERROR: Unexpected error in /process: {str(e)}")
        import traceback
        trace = traceback.format_exc()
        print(trace)
        print("=" * 50)
        
        # Try to categorize the error for more helpful messages
        error_msg = str(e).lower()
        detail = f"Unexpected error processing file: {str(e)}"
        
        if "pinecone" in error_msg:
            detail = f"Error connecting to Pinecone vector database: {str(e)}"
        elif "supabase" in error_msg:
            detail = f"Error connecting to Supabase database: {str(e)}"
        elif "openai" in error_msg or "embedding" in error_msg:
            detail = f"Error generating embeddings with OpenAI: {str(e)}"
        elif "pdf" in error_msg:
            detail = f"Error processing PDF file: {str(e)}"
        elif "memory" in error_msg or "out of memory" in error_msg:
            detail = "File processing failed: Out of memory. The file may be too large."
        
        raise HTTPException(
            status_code=500,
            detail=detail
        )

@app.delete("/delete/{file_id}")
async def delete_file(file_id: str, token: str = Depends(verify_token)):
    """
    Delete a file from the LlamaIndex backend.
    This endpoint is called by the frontend when a file is deleted.
    
    Authentication is required via API key or development mode.
    """
    if not token:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    if not index:
        raise HTTPException(status_code=500, detail="Vector index not initialized")
    
    try:
        print(f"Attempting to delete file with ID: {file_id} from LlamaIndex")
        
        # First, check if this file is tracked in our llama_index_documents table
        try:
            response = supabase_client.table("llama_index_documents").select("*").eq("supabase_file_id", file_id).execute()
            if response.data and len(response.data) > 0:
                llama_doc = response.data[0]
                
                # Delete the metadata from our tracking table
                supabase_client.table("llama_index_documents").delete().eq("supabase_file_id", file_id).execute()
                print(f"Deleted tracking record for file {file_id} from llama_index_documents table")
                  # Now delete the document from the vector store
                # The exact deletion method depends on the vector store implementation
                try:
                    if PINECONE_API_KEY and PINECONE_ENVIRONMENT and index:
                        # Try to delete using the vector store directly first
                        try:
                            # For newer versions of LlamaIndex, we can delete by metadata filter through the index
                            index.delete(
                                filter_dict={"metadata": {"supabase_file_id": file_id}}
                            )
                            print(f"Deleted document vectors for file {file_id} from Pinecone via LlamaIndex")
                        except (AttributeError, NotImplementedError, Exception) as idx_err:
                            print(f"Could not delete through LlamaIndex: {str(idx_err)}") 
                            # Fall back to direct Pinecone deletion
                            try:
                                # For Pinecone, we can delete by metadata filter
                                pinecone_index = pinecone.Index(INDEX_NAME)
                                pinecone_index.delete(
                                    filter={"supabase_file_id": file_id}
                                )
                                print(f"Deleted document vectors for file {file_id} directly from Pinecone")
                            except Exception as pinecone_err:
                                print(f"Error deleting directly from Pinecone: {str(pinecone_err)}")
                                raise pinecone_err
                except Exception as e:
                    print(f"Error deleting vectors from vector store: {str(e)}")
                    # Continue with the function even if vector deletion fails
                    # This ensures we at least clean up our tracking table
                    pass
                
                return {"message": f"File {file_id} deleted successfully from LlamaIndex"}
            else:
                # File was not found in our tracking table
                print(f"File {file_id} was not found in llama_index_documents table")
                return {"message": f"File {file_id} was not tracked by LlamaIndex. No deletion needed."}
                
        except Exception as e:
            print(f"Error checking llama_index_documents table: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error checking if file exists in LlamaIndex: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error deleting file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error deleting file: {str(e)}"
        )

@app.get("/debug/supabase")
async def debug_supabase(
    request: Request, 
    file_id: Optional[str] = None,
    file_path: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Debug endpoint to test Supabase connectivity and file operations.
    
    This endpoint will:
    1. Check Supabase authentication status
    2. List files in the storage bucket
    3. Try to download a specific file if file_id is provided
    """
    global supabase_client
    
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "supabase_client_exists": supabase_client is not None,
        "auth_header_present": auth_header is not None,
        "token_present": token is not None,
        "environment_variables": {
            "SUPABASE_URL": os.environ.get("SUPABASE_URL", "Not set"),
            "SUPABASE_ANON_KEY": "Present" if os.environ.get("SUPABASE_ANON_KEY") else "Not set",
            "SUPABASE_JWT_SECRET": "Present" if os.environ.get("SUPABASE_JWT_SECRET") else "Not set",
            "LLAMAINDEX_API_KEY": "Present" if os.environ.get("LLAMAINDEX_API_KEY") else "Not set"
        },
        "file_operations": {}
    }
    
    if not supabase_client:
        try:
            # Re-initialize Supabase client
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_ANON_KEY")
            if supabase_url and supabase_key:
                supabase_client = create_client(supabase_url, supabase_key)
                results["supabase_client_init"] = "Success"
            else:
                results["supabase_client_init"] = "Failed - missing credentials"
        except Exception as e:
            results["supabase_client_init"] = f"Error: {str(e)}"
    
    # Authenticate with the provided token if available
    if token and supabase_client:
        try:
            supabase_client.auth.set_session(token)
            results["auth_set_session"] = "Token set"
            
            # Try to get user info
            try:
                user = supabase_client.auth.get_user()
                results["auth_status"] = "Authenticated"
                results["user_id"] = user.user.id if user and user.user else "Unknown"
            except Exception as auth_err:
                results["auth_status"] = f"Error: {str(auth_err)}"
        except Exception as e:
            results["auth_set_session"] = f"Error: {str(e)}"
    
    # List files in the bucket
    if supabase_client:
        try:
            files_in_bucket = supabase_client.storage.from_("files").list()
            results["storage_list"] = {
                "status": "Success",
                "count": len(files_in_bucket),
                "examples": [f["name"] for f in files_in_bucket[:5]] if files_in_bucket else []
            }
            
            # Check if the specified file exists
            if file_path:
                results["file_operations"]["path_check"] = {
                    "file_path": file_path,
                    "exists": any(f["name"] == file_path for f in files_in_bucket)
                }
                
            # Check alternate path format
            if user_id and file_id:
                alt_path = f"{user_id}/{file_id}"
                results["file_operations"]["alt_path_check"] = {
                    "alt_path": alt_path,
                    "exists": any(f["name"] == alt_path for f in files_in_bucket)
                }
        except Exception as list_err:
            results["storage_list"] = {
                "status": f"Error: {str(list_err)}",
                "error_type": type(list_err).__name__
            }
    
    # Try to download a specific file if requested
    if file_id and supabase_client:
        # Try various path formats
        paths_to_try = []
        
        # Start with the provided path if given
        if file_path:
            paths_to_try.append(("provided_path", file_path))
        
        # Try user_id/file_id format
        if user_id:
            paths_to_try.append(("user_id_file_id", f"{user_id}/{file_id}"))
        
        # Try just the file_id
        paths_to_try.append(("file_id_only", file_id))
        
        results["file_operations"]["download_attempts"] = {}
        
        for path_type, path in paths_to_try:
            try:
                response = supabase_client.storage.from_("files").download(path)
                results["file_operations"]["download_attempts"][path_type] = {
                    "path": path,
                    "status": "Success",
                    "size": len(response) if response else 0
                }
                # Only try until we succeed
                break
            except Exception as e:
                results["file_operations"]["download_attempts"][path_type] = {
                    "path": path,
                    "status": f"Error: {str(e)}",
                    "error_type": type(e).__name__
                }
    
    return results
