import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

supabase_client = None

def get_supabase_client() -> Client:
    global supabase_client
    if supabase_client is not None:
        return supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables.")
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase_client
