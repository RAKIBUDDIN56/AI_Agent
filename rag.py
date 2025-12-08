from sentence_transformers import SentenceTransformer
from config.collection_manager import CollectionManager
import ollama

class FileWiseRAG:
    def __init__(self, collection_name="table_rf_docs", model_name="llama3:latest"):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = CollectionManager(collection_name)
        self.model_name = model_name
        
        # Verify collection has data
        count = self.collection.collection.count()
        print(f"Collection '{collection_name}' has {count} documents")

    def ask(self, user_query, top_k=10):
        # 1. Embed query
        query_embedding = self.embedder.encode(user_query).tolist()
        print(f"Query: {user_query}")

        # 2. Retrieve top-k docs
        raw_results = self.collection.query_docs(query_embedding, top_k=top_k)
        
        print(f" Raw results type: {type(raw_results)}")
        print(f" Raw results length: {len(raw_results) if raw_results else 0}")
        
        if not raw_results or len(raw_results) == 0:
            return " No relevant documents found.", []

        # 3. Prepare file-name-wise context
        context_text = "\n\n".join(
            [f"File: {d.get('metadata', {}).get('filename', 'Unknown')}\nContent: {d.get('document', '')}" 
             for d in raw_results]
        )
        print(f"Context length: {len(context_text)} characters")

        # 4. Send to Ollama model
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert assistant."},
                {"role": "user", "content": f"Answer based on this context:\n{context_text}\n\nUser question: {user_query}"}
            ]
        )

        return response["message"]["content"], raw_results


# Example usage
if __name__ == "__main__":
    rag = FileWiseRAG(model_name="llama3:latest")
    answer, sources = rag.ask("Generate sample code for TableRF", top_k=3)

    print("\nGenerated Answer:\n", answer)
    print("\nSources:")
    for s in sources:
        print(f"{s.get('filename', 'Unknown')} - Score: {s.get('score', 'N/A')}")