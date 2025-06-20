from fastapi import FastAPI, Request
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import os

app = FastAPI()

# Example: Load documents and build index at startup (customize as needed)
@app.on_event("startup")
def load_index():
    global index
    data_dir = os.environ.get("DATA_DIRECTORY", "./data")
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        documents = SimpleDirectoryReader(data_dir).load_data()
        index = VectorStoreIndex.from_documents(documents)
    else:
        index = None
        print(f"Warning: Data directory '{data_dir}' does not exist. Index not loaded.")

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest):
    if index is None:
        return {"error": "Index not loaded. No data directory found."}
    query_engine = index.as_query_engine()
    result = query_engine.query(request.question)
    return {"answer": str(result)}
