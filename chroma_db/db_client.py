# db_client.py
import chromadb
from chromadb.config import Settings

def get_chroma_client():
    # Use the updated Settings format
    client = chromadb.Client(
        Settings(
            persist_directory="./chroma_db"  # only persist_directory is needed
        )
    )
    return client
