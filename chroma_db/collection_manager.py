# collection_manager.py
from .db_client import get_chroma_client

class CollectionManager:
    def __init__(self, name="table_rf_docs"):
        client = get_chroma_client()
        # Use the updated method for latest ChromaDB
        self.collection = client.get_or_create_collection(
            name=name
        )

    def add_doc(self, doc_id: str, text: str, metadata: dict, embedding):
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],  # per-document metadata
            embeddings=[embedding]
        )

    def query_docs(self, query_text_embedding, top_k=5):
        results = self.collection.query(
            query_embeddings=[query_text_embedding],
            n_results=top_k
        )
        docs = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]

        # Return results file-name wise
        return [
            {
                "filename": meta.get("filename", "unknown"),
                "document": doc,
                "score": dist
            }
            for doc, meta, dist in zip(docs, metadatas, distances)
        ]
