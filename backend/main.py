from fastapi import FastAPI, Request
from pydantic import BaseModel
import os

app = FastAPI()

# Startup event no longer loads local documents
@app.on_event("startup")
def startup_event():
    print("Startup: No local document loading. Expecting Supabase or remote storage integration.")

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query(request: QueryRequest):
    # Replace this with Supabase or remote storage query logic
    return {"error": "Local index loading is disabled. Please implement Supabase or remote storage integration for querying."}
