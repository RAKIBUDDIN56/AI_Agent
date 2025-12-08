# from chroma_db.doc_loader import DocLoader
# from chroma_db.collection_manager import CollectionManager
# from chroma_db.db_client import get_chroma_client
# import sys
# sys.path.append(r"C:\Users\rakib.uddin\Desktop\rakib\AI_Agent")
from config.doc_loader import DocLoader


if __name__ == "__main__":
    loader = DocLoader(docs_dir="./docs")
    loader.load_docs()
