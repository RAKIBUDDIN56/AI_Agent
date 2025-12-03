# doc_loader.py
import os
import uuid
from sentence_transformers import SentenceTransformer
from .collection_manager import CollectionManager

class DocLoader:
    def __init__(self, docs_dir="./docs/tablerf"):
        self.docs_dir = docs_dir
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.collection = CollectionManager("table_rf_docs")

    def load_docs(self):
        for filename in os.listdir(self.docs_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.docs_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

                embedding = self.embedder.encode(text).tolist()

                self.collection.add_doc(
                    doc_id=str(uuid.uuid4()),
                    text=text,
                    metadata={"filename": filename},
                    embedding=embedding
                )

        print("✅ All docs stored in Chroma successfully.")
