from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
from rag import FileWiseRAG
from config.doc_loader import DocLoader
import logging
from contextlib import asynccontextmanager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rag_system = None  # global

# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_system
    try:
        logger.info("Initializing RAG system on startup...")
        rag_system = FileWiseRAG(
            collection_name="table_rf_docs",
            model_name="llama3:latest"
        )
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise

    yield  # app runs here

    logger.info("Shutting down application...")

# FastAPI initialization with lifespan
app = FastAPI(
    title="RapidFire RAG API",
    description="Retrieval-Augmented Generation API for RapidFire",
    version="1.0.0",
    lifespan=lifespan  
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)

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
    docs_dir: str = Field(default="./docs/tablerf")

class LoadDocsResponse(BaseModel):
    success: bool
    documents_loaded: int
    message: str


# Health check
@app.get("/", response_model=HealthResponse)
async def health_check():
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG not initialized")

    try:
        doc_count = rag_system.collection.get_count()
        return HealthResponse(
            status="healthy",
            collection_name="table_rf_docs",
            document_count=doc_count,
            model_name=rag_system.model_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health failed: {e}")

# Query endpoint
@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG not initialized")

    try:
        logger.info(f"🔍 Processing query: {request.query}")

        answer, sources = rag_system.ask(request.query, top_k=request.top_k)

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
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Load docs
@app.post("/load-docs", response_model=LoadDocsResponse)
async def load_documents(request: LoadDocsRequest):
    try:
        logger.info(f"📂 Loading docs from: {request.docs_dir}")

        loader = DocLoader(docs_dir=request.docs_dir)
        count = loader.load_docs()

        global rag_system
        rag_system = FileWiseRAG(
            collection_name="table_rf_docs",
            model_name="llama3:latest"
        )

        return LoadDocsResponse(
            success=True,
            documents_loaded=count,
            message=f"Loaded {count} documents"
        )
    except Exception as e:
        logger.error(f"❌ Load failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Stats endpoint
@app.get("/stats")
async def get_stats():
    if rag_system is None:
        raise HTTPException(status_code=503, detail="RAG not initialized")

    try:
        doc_count = rag_system.collection.get_count()
        return {
            "total_documents": doc_count,
            "collection_name": "table_rf_docs",
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": rag_system.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
async def serve_frontend():
    return FileResponse("static/index.html")


# Uvicorn entry
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
