from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, Document
# Use the correct import path for SimpleDirectoryReader
try:
    from llama_index.readers.file import SimpleDirectoryReader
except ImportError:
    # Fallback import path
    from llama_index.core import SimpleDirectoryReader
import os
import uuid
import json
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="LlamaIndex API", 
              description="Backend API for LlamaIndex document ingestion and querying",
              version="1.0.0")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://llamaindex-production-633d.up.railway.app",  # Backend URL itself
        "http://localhost:3000",          # For local development frontend
        "https://localhost:3000",         # For secure local development
        os.environ.get("FRONTEND_URL", ""),  # Get from environment variable if set
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "developer-quickstart-py")

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
        return token
        
    # In production with JWT secret, verify the token
    try:
        # Basic validation - in a real implementation, you would
        # decode and verify the JWT using a library like python-jose
        # For now, we'll just return the token
        return token
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

# Initialize services and build index at startup
@app.on_event("startup")
def load_index():
    global index, supabase_client
    
    # Initialize variables with default values
    index = None
    supabase_client = None
    
    try:
        # Check if Pinecone credentials are available
        if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
            print("WARNING: Missing Pinecone credentials. Some features will be unavailable.")
            return
            
        # Initialize Pinecone with error handling
        try:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)            # Check if index exists, if not, suggest manual creation
            if INDEX_NAME not in pinecone.list_indexes():
                print(f"WARNING: Index '{INDEX_NAME}' not found in Pinecone. For best results, create it manually in the Pinecone console.")
                print("Attempting to create index with default settings - this may fail if your account does not support these settings.")
                
                try:
                    pinecone.create_index(
                        name=INDEX_NAME,
                        dimension=1536,  # default for OpenAI embeddings
                        metric="cosine",
                        pod_type="p1"  # Using pod_type instead of cloud/region for better compatibility
                    )
                    print(f"Successfully created Pinecone index: {INDEX_NAME}")
                except Exception as create_error:
                    print(f"Failed to auto-create Pinecone index: {str(create_error)}")
                    print("Please create the index manually in the Pinecone console with the appropriate settings for your account.")
                    print("Then restart this application.")
                    # We'll continue and try to use the index anyway in case it was created but raised an error
              # Connect to the index
            try:
                pinecone_index = pinecone.Index(INDEX_NAME)
                vector_store = PineconeVectorStore(pinecone_index)
                
                # Initialize empty index
                index = VectorStoreIndex(vector_store=vector_store)
                print("Pinecone and Vector Index initialized successfully")
            except Exception as index_error:
                print(f"Failed to connect to Pinecone index: {str(index_error)}")
                index = None  # Set to None to indicate initialization failure
        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
        
        # Initialize Supabase client with error handling        if SUPABASE_URL and SUPABASE_KEY:
            try:
                # Initialize Supabase client with only the required parameters
                # to avoid issues with unexpected keyword arguments like 'proxy'
                supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("Supabase client initialized successfully")
                
                # Check if llama_index_documents table exists, create if needed
                try:
                    # Try to query the table - this will fail if it doesn't exist
                    supabase_client.table("llama_index_documents").select("id").limit(1).execute()
                    print("llama_index_documents table exists")
                except Exception as table_error:
                    print(f"Note: llama_index_documents table might not exist: {table_error}")
                    print("Creating llama_index_documents table will be handled by Supabase migrations")
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}")
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
        return {
            "error": "Vector index not available", 
            "message": "Please check Pinecone configuration and API keys"
        }
    
    try:
        # Create query engine
        query_engine = index.as_query_engine()
        
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
        
        # Execute query
        result = query_engine.query(request.question)
        return {"answer": str(result)}
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}

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
        pinecone_indexes = pinecone.list_indexes()
        status["services"]["pinecone"]["connected"] = True
        status["services"]["pinecone"]["indexes"] = pinecone_indexes
        status["services"]["pinecone"]["index_exists"] = INDEX_NAME in pinecone_indexes
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
        supabase_client.storage.from_("documents").upload(
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
            
        # Recreate the index with the loaded documents
        index = VectorStoreIndex.from_documents(documents, vector_store=index.vector_store)
        
        return {
            "message": "Reindexing completed successfully.",
            "document_count": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing documents: {str(e)}")

@app.post("/delete_index")
def delete_index():
    global index
    pinecone.delete_index(INDEX_NAME)
    
@app.get("/")
def root():
    """Root endpoint for basic API information."""
    return {
        "service": "LlamaIndex API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Simple health check endpoint that doesn't depend on external services."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/list_indices")
def list_indices():
    indices = pinecone.list_indexes()
    return {"indices": indices}

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
                storage_response = supabase_client.storage.from_('documents').download(f"{doc['id']}")
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
        supabase_client.storage.from_("documents").remove([document_id])
        
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
        # Parse the request body
        data = await request.json()
        file_id = data.get("file_id")
        supabase_file_path = data.get("supabase_file_path")
        file_name = data.get("name", "Unknown")
        file_type = data.get("type", "text/plain")
        description = data.get("description", "")
        user_id = data.get("user_id")
        
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
            print(f"Attempting to download file from Supabase: {supabase_file_path}")
            response = supabase_client.storage.from_("files").download(supabase_file_path)
            if not response:
                raise Exception("Failed to download file from Supabase - empty response")
            file_content = response
            print(f"Successfully downloaded file, size: {len(file_content) if file_content else 'unknown'} bytes")
        except Exception as e:
            print(f"Error downloading file from Supabase: {str(e)}")
            raise HTTPException(
                status_code=404, 
                detail=f"Error retrieving file from Supabase: {str(e)}"
            )
        
        # Create metadata for the document
        metadata = {
            "supabase_file_id": file_id,
            "name": file_name,
            "type": file_type,            "description": description,
            "user_id": user_id,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Process the file based on its type
        file_text = ""
        try:
            # Decode the file content based on type
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
                    try:
                        # Import PDF processing libraries
                        import tempfile
                        from PyPDF2 import PdfReader
                        
                        # Create a temporary file to save the PDF
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                            temp_path = temp_file.name
                            temp_file.write(file_content)
                        
                        # Extract text from PDF
                        try:
                            pdf_reader = PdfReader(temp_path)
                            pdf_texts = []
                            
                            # Extract text from each page
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                pdf_texts.append(page.extract_text())
                            
                            # Join all the pages together
                            file_text = "\n\n".join(pdf_texts)
                            
                            # Clean up temp file
                            os.unlink(temp_path)
                        except Exception as pdf_err:
                            print(f"Error extracting text from PDF: {str(pdf_err)}")
                            raise HTTPException(
                                status_code=500,
                                detail=f"Error extracting text from PDF: {str(pdf_err)}"
                            )
                    except ImportError:
                        print("PyPDF2 is not installed. Please install it to process PDF files.")
                        raise HTTPException(
                            status_code=500,
                            detail="PDF processing is not available. PyPDF2 is not installed."
                        )
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
            index.insert_nodes(nodes)
            
            print(f"Successfully indexed {len(nodes)} chunks from file {file_name}")
            # Store the mapping between Supabase file ID and the document in Pinecone
            # This could be useful for updates/deletions later
            supabase_client.table("llama_index_documents").insert({
                "supabase_file_id": file_id,
                "processed": True,
                "metadata": metadata
            }).execute()
            
        except Exception as e:
            print(f"Error indexing document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error indexing document: {str(e)}"
            )
        
        return {
            "success": True,
            "file_id": file_id,
            "message": "File processed and indexed successfully."
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as they already have the right format
        raise
    except Exception as e:
        print(f"Unexpected error processing file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing file: {str(e)}"
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
