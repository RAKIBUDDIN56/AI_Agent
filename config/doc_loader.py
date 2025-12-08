import os
import uuid
from sentence_transformers import SentenceTransformer
from .collection_manager import CollectionManager

class DocLoader:
    def __init__(self, docs_dir="./docs"):
        self.docs_dir = docs_dir
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = CollectionManager("table_rf_docs")
        
        print(f"Looking for docs in: {os.path.abspath(self.docs_dir)}")

    def load_docs(self):
        """Recursively load all .md files under docs directory"""

        if not os.path.exists(self.docs_dir):
            print(f"Directory not found: {self.docs_dir}")
            return 0
        
        initial_count = self.collection.get_count()
        print(f"Initial document count: {initial_count}")

        files_added = 0
        self.collection.clear_collection()

        # Walk all folders under docs/
        for root, _, files in os.walk(self.docs_dir):

            # find .md files
            md_files = [f for f in files if f.endswith(".md")]

            for filename in md_files:
                file_path = os.path.join(root, filename)

                # generate metadata friendly relative folder
                relative_path = os.path.relpath(file_path, self.docs_dir)

                print(f"\nProcessing: {relative_path}")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                    
                    if not text:
                        print(f"Skipping empty file: {filename}")
                        continue

                    # Generate embedding
                    embedding = self.embedder.encode(text).tolist()

                    # Add to vector store
                    self.collection.add_doc(
                        doc_id=str(uuid.uuid4()),
                        text=text,
                        metadata={
                            "filename": filename,
                            "path": relative_path
                        },
                        embedding=embedding
                    )

                    files_added += 1

                except Exception as e:
                    print(f"Error processing {relative_path}: {e}")
                    continue

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
    loader = DocLoader(docs_dir="./docs")
    count = loader.load_docs()

    if count > 0:
        print("\nTesting query...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        query_emb = embedder.encode("TableRF component").tolist()

        results = loader.collection.query_docs(query_emb, top_k=3)
        print(f"\nQuery returned {len(results)} results:")

        for r in results:
            print(f"   - {r['metadata']['path']} (score: {r['score']:.4f})")
