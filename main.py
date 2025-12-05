from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from rag import FileWiseRAG
from chroma_db.doc_loader import DocLoader
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RapidFire RAG API",
    description="Retrieval-Augmented Generation API for RapidFire",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = None

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")

class Source(BaseModel):
    filename: str
    score: float
    preview: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    query: str
    documents_searched: int

class HealthResponse(BaseModel):
    status: str
    collection_name: str
    document_count: int
    model_name: str

class LoadDocsRequest(BaseModel):
    docs_dir: str = Field(default="./docs/tablerf", description="Directory containing documents")

class LoadDocsResponse(BaseModel):
    success: bool
    documents_loaded: int
    message: str


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    try:
        logger.info("Initializing RAG system...")
        rag_system = FileWiseRAG(
            collection_name="table_rf_docs",
            model_name="llama3:latest"
        )
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise


# Health check endpoint
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Check if the API is running and RAG system is ready"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        doc_count = rag_system.collection.get_count()
        return HealthResponse(
            status="healthy",
            collection_name="table_rf_docs",
            document_count=doc_count,
            model_name=rag_system.model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the RAG system with a question
    
    - **query**: Your question about TableRF
    - **top_k**: Number of relevant documents to retrieve (default: 5)
    """
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Get answer from RAG system
        answer, sources = rag_system.ask(request.query, top_k=request.top_k)
        
        # Format sources for response
        formatted_sources = [
            Source(
                filename=s['filename'],
                score=s['score'],
                preview=s['document'][:200] + "..." if len(s['document']) > 200 else s['document']
            )
            for s in sources
        ]
        
        return QueryResponse(
            answer=answer,
            sources=formatted_sources,
            query=request.query,
            documents_searched=len(sources)
        )
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


# Load documents endpoint
@app.post("/load-docs", response_model=LoadDocsResponse)
async def load_documents(request: LoadDocsRequest):
    """
    Load documents from a directory into the vector database
    
    - **docs_dir**: Path to directory containing .md files (default: ./docs/tablerf)
    """
    try:
        logger.info(f"Loading documents from: {request.docs_dir}")
        
        loader = DocLoader(docs_dir=request.docs_dir)
        count = loader.load_docs()
        
        # Reinitialize RAG system to pick up new documents
        global rag_system
        rag_system = FileWiseRAG(
            collection_name="table_rf_docs",
            model_name="llama3:latest"
        )
        
        return LoadDocsResponse(
            success=True,
            documents_loaded=count,
            message=f"Successfully loaded {count} documents"
        )
    
    except Exception as e:
        logger.error(f"Document loading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load documents: {str(e)}")


# Get collection stats
@app.get("/stats")
async def get_stats():
    """Get statistics about the document collection"""
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        doc_count = rag_system.collection.get_count()
        return {
            "total_documents": doc_count,
            "collection_name": "table_rf_docs",
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": rag_system.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/app")
async def serve_frontend():
    """Serve the frontend HTML"""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# 