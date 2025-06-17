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
    allow_origins=["*"],  # Update this with specific origins in production
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

# Authentication utility - in production, implement real verification with Supabase
def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Simple token verification - in a production environment, 
    this would validate the JWT with Supabase
    """
    # For development, we'll just return the token if present, or None
    return credentials.credentials if credentials else None

# Initialize services and build index at startup
@app.on_event("startup")
def load_index():
    global index, supabase_client
    
    # Initialize Pinecone
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    if INDEX_NAME not in pinecone.list_indexes():
        pinecone.create_index(
            name=INDEX_NAME,
            dimension=1536,  # default for OpenAI embeddings, adjust if needed
            metric="cosine",
            cloud="aws",
            region="us-east-1"
        )
    pinecone_index = pinecone.Index(INDEX_NAME)
    vector_store = PineconeVectorStore(pinecone_index)
    
    # Initialize Supabase client
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        supabase_client = None
    
    # Initialize empty index - we'll load documents from Supabase as needed
    index = VectorStoreIndex(vector_store=vector_store)
    
    # Note: Loading initial documents moved to a separate function that pulls from Supabase
    print("Index initialized successfully")

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
    if index is None:
        return {"error": "Index not loaded. No data directory found."}
    
    # Create query engine
    query_engine = index.as_query_engine()
    
    # Log the query to Supabase (optional)
    if supabase_client and request.user_id:
        try:
            supabase_client.table("queries").insert({
                "user_id": request.user_id,
                "question": request.question,
                "timestamp": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"Error logging query: {e}")
    
    # Execute query
    result = query_engine.query(request.question)
    return {"answer": str(result)}

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
def health_check():
    """Root endpoint for health checks and basic API information."""
    return {
        "service": "LlamaIndex API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }
    index = None
    return {"message": f"Index '{INDEX_NAME}' deleted successfully."}

@app.get("/list_indices")
def list_indices():
    indices = pinecone.list_indexes()
    return {"indices": indices}

# Authentication utility
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Supabase if authentication is required"""
    # In production, implement actual token verification with Supabase
    # This is a placeholder - integrate with Supabase auth in production
    return credentials.credentials

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
