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
    documents = SimpleDirectoryReader(data_dir).load_data()
    index = VectorStoreIndex.from_documents(documents)

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest):
    query_engine = index.as_query_engine()
    result = query_engine.query(request.question)
    return {"answer": str(result)}
