#!/usr/bin/env python3
"""
LlamaIndex Documents Table Diagnostic

This script checks the llama_index_documents table in Supabase and
compares it with the documents stored in Pinecone to ensure consistency.
"""

import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Get Pinecone credentials
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}=== {text} ==={Colors.RESET}")
    
def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
def print_warning(text):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.RESET}")
    
def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def validate_env_vars():
    """Validate required environment variables are present."""
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_ANON_KEY": SUPABASE_ANON_KEY,
        "PINECONE_API_KEY": PINECONE_API_KEY,
        "PINECONE_ENVIRONMENT": PINECONE_ENVIRONMENT,
        "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME
    }
    
    missing = [var for var, val in required_vars.items() if not val]
    
    if missing:
        print_error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    
    return True

def check_supabase_documents():
    """Check documents in the llama_index_documents table."""
    try:
        from supabase import create_client
        
        print_header("Checking Supabase Connection")
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print_success("Connected to Supabase")
        
        # Check if table exists
        print_header("Checking llama_index_documents Table")
        try:
            response = supabase.table("llama_index_documents").select("count", count="exact").limit(1).execute()
            count = response.count
            print_success(f"Table exists with {count} records")
            
            # Get sample documents
            response = supabase.table("llama_index_documents").select("*").limit(5).execute()
            docs = response.data
            
            if not docs:
                print_warning("No documents found in the table")
                return []
            
            print(f"Sample documents ({len(docs)}):")
            for i, doc in enumerate(docs):
                print(f"\nDocument {i+1}:")
                print(f"  - ID: {doc.get('id')}")
                print(f"  - File ID: {doc.get('supabase_file_id')}")
                print(f"  - Processed: {doc.get('processed')}")
                print(f"  - Chunks: {doc.get('chunk_count', 'N/A')}")
                print(f"  - Embedding Model: {doc.get('embedding_model', 'N/A')}")
                print(f"  - Vector Store: {doc.get('vector_store', 'N/A')}")
                
                # Check if file exists
                file_id = doc.get('supabase_file_id')
                if file_id:
                    file_response = supabase.table("files").select("*").eq("id", file_id).execute()
                    if file_response.data:
                        print(f"  - Associated File: {file_response.data[0].get('name')} (found)")
                    else:
                        print_warning(f"  - Associated File: Not found (orphaned document)")
            
            return docs
            
        except Exception as e:
            if "relation \"llama_index_documents\" does not exist" in str(e):
                print_error("Table does not exist")
                print("Run the migration script to create the table")
            else:
                print_error(f"Error checking table: {str(e)}")
            return []
            
    except Exception as e:
        print_error(f"Failed to connect to Supabase: {str(e)}")
        return []

def check_pinecone_documents():
    """Check documents in Pinecone."""
    try:
        import pinecone
        
        print_header("Checking Pinecone Connection")
        # Initialize Pinecone
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        print_success("Connected to Pinecone")
        
        # Check if index exists
        print_header("Checking Pinecone Index")
        indexes = pinecone.list_indexes()
        
        if PINECONE_INDEX_NAME not in indexes:
            print_error(f"Index '{PINECONE_INDEX_NAME}' not found")
            print(f"Available indexes: {indexes}")
            return False
        
        print_success(f"Index '{PINECONE_INDEX_NAME}' exists")
        
        # Connect to index
        index = pinecone.Index(PINECONE_INDEX_NAME)
        
        # Get index stats
        stats = index.describe_index_stats()
        vector_count = stats.get('total_vector_count', 0)
        dimension = stats.get('dimension', 'unknown')
        
        print(f"Vector count: {vector_count}")
        print(f"Vector dimension: {dimension}")
        if dimension == 3072:
            print_success("Vector dimension matches text-embedding-3-large (3072)")
        elif dimension == 1536:
            print_warning("Vector dimension matches older text-embedding-ada-002 (1536)")
        else:
            print(f"Vector dimension: {dimension}")
        
        # Query for some sample vectors to check metadata
        print_header("Checking Vector Metadata")
        if vector_count > 0:
            try:
                # Query index to get sample vector metadata
                query_response = index.query(
                    vector=[0.0] * int(dimension),  # Dummy vector
                    top_k=5,
                    include_metadata=True
                )
                
                if query_response and hasattr(query_response, 'matches') and query_response.matches:
                    print_success(f"Retrieved {len(query_response.matches)} sample vectors")
                    
                    for i, match in enumerate(query_response.matches):
                        print(f"\nVector {i+1}:")
                        if hasattr(match, 'metadata') and match.metadata:
                            print(f"  - Metadata: {match.metadata}")
                            
                            # Check for supabase_file_id in metadata
                            if 'supabase_file_id' in match.metadata:
                                print_success(f"  - Has 'supabase_file_id' link: {match.metadata['supabase_file_id']}")
                            else:
                                print_warning("  - No 'supabase_file_id' link")
                        else:
                            print_warning("  - No metadata")
                else:
                    print_warning("No vectors returned in query")
            except Exception as e:
                print_error(f"Error querying vectors: {str(e)}")
        else:
            print_warning("No vectors found in index")
        
        return True
    except Exception as e:
        print_error(f"Failed to connect to Pinecone: {str(e)}")
        return False

def compare_documents(supabase_docs):
    """Compare documents in Supabase and Pinecone."""
    if not supabase_docs:
        print_warning("No Supabase documents to compare")
        return
        
    try:
        import pinecone
        
        print_header("Comparing Documents")
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        index = pinecone.Index(PINECONE_INDEX_NAME)
        
        for doc in supabase_docs:
            file_id = doc.get('supabase_file_id')
            if not file_id:
                print_warning(f"Document {doc.get('id')} has no file ID")
                continue
                
            # Check if vectors exist in Pinecone
            try:
                fetch_response = index.fetch(ids=[file_id])
                vectors_found = len(fetch_response.get('vectors', {})) > 0
                
                if vectors_found:
                    print_success(f"Document {file_id} exists in both Supabase and Pinecone")
                else:
                    print_error(f"Document {file_id} exists in Supabase but NOT in Pinecone")
                    
            except Exception as e:
                print_error(f"Error checking document {file_id} in Pinecone: {str(e)}")
    except Exception as e:
        print_error(f"Error during comparison: {str(e)}")

def main():
    """Main function to run diagnostics."""
    print_header("LLAMA INDEX DOCUMENTS TABLE DIAGNOSTIC")
    print(f"Time: {datetime.now().isoformat()}")
    
    if not validate_env_vars():
        sys.exit(1)
    
    supabase_docs = check_supabase_documents()
    pinecone_ok = check_pinecone_documents()
    
    if supabase_docs and pinecone_ok:
        compare_documents(supabase_docs)
    
    print_header("DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    main()
