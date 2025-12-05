import chromadb

def get_chroma_client():
    """
    Returns a persistent ChromaDB client
    """
    # NEW API - Use PersistentClient
    client = chromadb.PersistentClient(path="./chroma_db_data")
    return client