from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os

# Pinecone imports
import pinecone
from llama_index.vector_stores.llama_index_vector_stores_pinecone.llama_index.vector_stores.pinecone import PineconeVectorStore
from fastapi.responses import JSONResponse

app = FastAPI()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
INDEX_NAME = "developer-quickstart-py"

# Example: Load documents and build index at startup (customize as needed)
@app.on_event("startup")
def load_index():
    global index
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
    data_dir = os.environ.get("DATA_DIRECTORY", "./data")
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        documents = SimpleDirectoryReader(data_dir).load_data()
        index = VectorStoreIndex.from_documents(documents, vector_store=vector_store)
    else:
        index = VectorStoreIndex(vector_store=vector_store)
        print(f"Warning: Data directory '{data_dir}' does not exist. Index loaded with no documents.")

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest):
    if index is None:
        return {"error": "Index not loaded. No data directory found."}
    query_engine = index.as_query_engine()
    result = query_engine.query(request.question)
    return {"answer": str(result)}

@app.get("/admin/status")
def admin_status():
    status = {}
    # Check Pinecone API key and environment
    status["pinecone_api_key_set"] = bool(PINECONE_API_KEY)
    status["pinecone_environment_set"] = bool(PINECONE_ENVIRONMENT)
    # Check Pinecone index
    try:
        pinecone_indexes = pinecone.list_indexes()
        status["pinecone_index_exists"] = INDEX_NAME in pinecone_indexes
    except Exception as e:
        status["pinecone_index_exists"] = False
        status["pinecone_error"] = str(e)
    # Check in-memory index
    status["index_loaded"] = 'index' in globals() and index is not None
    # Optionally, check if index has documents (if possible)
    try:
        if status["index_loaded"]:
            # This is a best-effort check; adjust as needed for your index type
            status["index_document_count"] = getattr(index, 'docstore', None) and len(getattr(index.docstore, 'docs', {}))
        else:
            status["index_document_count"] = 0
    except Exception as e:
        status["index_document_count"] = f"Error: {e}"
    return JSONResponse(content=status)

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    data_dir = os.environ.get("DATA_DIRECTORY", "./data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    file_path = os.path.join(data_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return {"message": f"File '{file.filename}' uploaded successfully."}

@app.post("/reindex")
def reindex():
    global index
    data_dir = os.environ.get("DATA_DIRECTORY", "./data")
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        documents = SimpleDirectoryReader(data_dir).load_data()
        index = VectorStoreIndex.from_documents(documents, vector_store=index.vector_store)
        return {"message": "Reindexing completed successfully."}
    return {"error": "Data directory does not exist."}

@app.post("/delete_index")
def delete_index():
    global index
    pinecone.delete_index(INDEX_NAME)
    index = None
    return {"message": f"Index '{INDEX_NAME}' deleted successfully."}

@app.get("/list_indices")
def list_indices():
    indices = pinecone.list_indexes()
    return {"indices": indices}
