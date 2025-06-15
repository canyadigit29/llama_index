from fastapi import FastAPI, Request
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os

# Pinecone imports
import pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore

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
