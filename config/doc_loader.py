import os
import uuid
from sentence_transformers import SentenceTransformer
from .collection_manager import CollectionManager

class DocLoader:
    def __init__(self, docs_dir="./docs/tablerf"):
        self.docs_dir = docs_dir
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = CollectionManager("table_rf_docs")
        
        print(f"Looking for docs in: {os.path.abspath(self.docs_dir)}")

    def load_docs(self):
        """Load all .md files from docs directory"""
        
        # Check if directory exists
        if not os.path.exists(self.docs_dir):
            print(f"Directory not found: {self.docs_dir}")
            return 0
        
        # Get initial count
        initial_count = self.collection.get_count()
        print(f"Initial document count: {initial_count}")
        
        files_added = 0
        md_files = [f for f in os.listdir(self.docs_dir) if f.endswith(".md")]
        
        if not md_files:
            print(f"No .md files found in {self.docs_dir}")
            return 0
        
        print(f"Found {len(md_files)} .md files")
        
        for filename in md_files:
            file_path = os.path.join(self.docs_dir, filename)
            print(f"\nProcessing: {filename}")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                
                if not text:
                    print(f"Skipping empty file: {filename}")
                    continue

                # Generate embedding
                embedding = self.embedder.encode(text).tolist()
                print(f"   Embedding dimension: {len(embedding)}")
                print(f"   Text length: {len(text)} chars")
                print(f"   Preview: {text[:100]}...")

                # Add to collection
                self.collection.add_doc(
                    doc_id=str(uuid.uuid4()),
                    text=text,
                    metadata={"filename": filename},
                    embedding=embedding
                )
                
                files_added += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue

        # Verify final count
        final_count = self.collection.get_count()
        print(f"\n{'='*50}")
        print(f"Successfully added {files_added} documents")
        print(f"Initial count: {initial_count}")
        print(f"Final count: {final_count}")
        print(f"Expected count: {initial_count + files_added}")
        print(f"{'='*50}\n")
        
        return files_added


# Test script
if __name__ == "__main__":
    loader = DocLoader()
    count = loader.load_docs()
    
    if count > 0:
        print("\nTesting query...")
        from sentence_transformers import SentenceTransformer
        
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        query_emb = embedder.encode("TableRF component").tolist()
        
        results = loader.collection.query_docs(query_emb, top_k=3)
        print(f"\nQuery returned {len(results)} results:")
        for r in results:
            print(f"   - {r['filename']} (score: {r['score']:.4f})")