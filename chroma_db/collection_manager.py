from .db_client import get_chroma_client

class CollectionManager:
    def __init__(self, name="table_rf_docs"):
        self.client = get_chroma_client()
        # Create or get collection
        self.collection = self.client.get_or_create_collection(name=name)
        print(f"Collection '{name}' initialized with {self.collection.count()} documents")

    def add_doc(self, doc_id: str, text: str, metadata: dict, embedding):
        """Add a single document to the collection"""
        try:
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            print(f"Added doc: {metadata.get('filename', doc_id)}")
        except Exception as e:
            print(f"Error adding document {doc_id}: {e}")
            raise

    def query_docs(self, query_embedding, top_k=5):
        """Query top_k similar documents"""
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        docs = []
        if result["documents"] and result["documents"][0]:
            for doc, meta, score in zip(
                result["documents"][0], 
                result["metadatas"][0], 
                result["distances"][0]
            ):
                docs.append({
                    "document": doc, 
                    "metadata": meta,
                    "filename": meta.get("filename", "Unknown"), 
                    "score": score
                })
        return docs
    
    def get_count(self):
        """Get total document count"""
        return self.collection.count()