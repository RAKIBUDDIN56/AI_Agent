# chroma_db/__init__.py

# Expose main functions for easy import
# from .db_client import get_client
# from .collection_manager import get_or_create_collection
# from .doc_loader import insert_docs
from .db_client import get_chroma_client
from .collection_manager import CollectionManager
from .doc_loader import DocLoader
# from ..index_docs import index_documents
# from ..index_docs import index_documents_from_directory



