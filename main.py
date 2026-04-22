from fastapi import FastAPI
from dotenv import load_dotenv
import os
from supabase import create_client, Client

app = FastAPI()

# Load environment variables from .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.get("/")
def root():
    response = (
        supabase.table("users")
        .select("*")
        .execute()
    )
    return {"message": response}