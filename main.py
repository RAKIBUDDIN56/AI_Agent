# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from pydantic import BaseModel, Field
# from typing import List
# from rag import FileWiseRAG
# from config.doc_loader import DocLoader
# import logging
# from contextlib import asynccontextmanager


# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# rag_system = None  # global

# # Lifespan handler
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global rag_system
#     try:
#         logger.info("Initializing RAG system on startup...")
#         rag_system = FileWiseRAG(
#             collection_name="table_rf_docs",
#             model_name="llama3:latest"
#         )
#         logger.info("RAG system initialized successfully")
#     except Exception as e:
#         logger.error(f"Failed to initialize RAG system: {e}")
#         raise

#     yield  # app runs here

#     logger.info("Shutting down application...")

# # FastAPI initialization with lifespan
# app = FastAPI(
#     title="RapidFire RAG API",
#     description="Retrieval-Augmented Generation API for RapidFire",
#     version="1.0.0",
#     lifespan=lifespan  
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, restrict this
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Models
# class QueryRequest(BaseModel):
#     query: str = Field(..., min_length=1)
#     top_k: int = Field(default=5, ge=1, le=20)

# class Source(BaseModel):
#     filename: str
#     score: float
#     preview: str

# class QueryResponse(BaseModel):
#     answer: str
#     sources: List[Source]
#     query: str
#     documents_searched: int

# class HealthResponse(BaseModel):
#     status: str
#     collection_name: str
#     document_count: int
#     model_name: str

# class LoadDocsRequest(BaseModel):
#     docs_dir: str = Field(default="./docs")

# class LoadDocsResponse(BaseModel):
#     success: bool
#     documents_loaded: int
#     message: str


# # Health check
# @app.get("/", response_model=HealthResponse)
# async def health_check():
#     if rag_system is None:
#         raise HTTPException(status_code=503, detail="RAG not initialized")

#     try:
#         doc_count = rag_system.collection.get_count()
#         return HealthResponse(
#             status="healthy",
#             collection_name="table_rf_docs",
#             document_count=doc_count,
#             model_name=rag_system.model_name
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Health failed: {e}")

# # Query endpoint
# @app.post("/query", response_model=QueryResponse)
# async def query_documents(request: QueryRequest):
#     if rag_system is None:
#         raise HTTPException(status_code=503, detail="RAG not initialized")

#     try:
#         logger.info(f"🔍 Processing query: {request.query}")

#         answer, sources = rag_system.ask(request.query, top_k=request.top_k)

#         formatted_sources = [
#             Source(
#                 filename=s['filename'],
#                 score=s['score'],
#                 preview=s['document'][:200] + "..." if len(s['document']) > 200 else s['document']
#             )
#             for s in sources
#         ]

#         return QueryResponse(
#             answer=answer,
#             sources=formatted_sources,
#             query=request.query,
#             documents_searched=len(sources)
#         )
#     except Exception as e:
#         logger.error(f"❌ Query failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Load docs
# @app.post("/load-docs", response_model=LoadDocsResponse)
# async def load_documents(request: LoadDocsRequest):
#     try:
#         logger.info(f"📂 Loading docs from: {request.docs_dir}")

#         loader = DocLoader(docs_dir=request.docs_dir)
#         count = loader.load_docs()

#         global rag_system
#         rag_system = FileWiseRAG(
#             collection_name="table_rf_docs",
#             model_name="llama3:latest"
#         )

#         return LoadDocsResponse(
#             success=True,
#             documents_loaded=count,
#             message=f"Loaded {count} documents"
#         )
#     except Exception as e:
#         logger.error(f"❌ Load failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Stats endpoint
# @app.get("/stats")
# async def get_stats():
#     if rag_system is None:
#         raise HTTPException(status_code=503, detail="RAG not initialized")

#     try:
#         doc_count = rag_system.collection.get_count()
#         return {
#             "total_documents": doc_count,
#             "collection_name": "table_rf_docs",
#             "embedding_model": "all-MiniLM-L6-v2",
#             "llm_model": rag_system.model_name
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# # Serve static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# @app.get("/app")
# async def serve_frontend():
#     return FileResponse("static/index.html")


# # Uvicorn entry
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from langchain_agent import LangChainAgent
from config.doc_loader import DocLoader
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RapidFire AI Agent with LangChain",
    description="Advanced RAG system with conversation memory, tracing, and code fixing",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = None

# ============================================================================
# Pydantic Models
# ============================================================================

class SessionCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="Optional user identifier")

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    message: str

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User's question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    filter_metadata: Optional[Dict] = Field(None, description="Metadata filters for retrieval")

class Source(BaseModel):
    rank: int
    filename: str
    document: str
    metadata: Dict
    relevance_note: str

class TraceInfo(BaseModel):
    session_id: str
    timestamp: str
    original_question: str
    reformulated_question: str
    documents_retrieved: int
    processing_time_seconds: float
    interaction_number: int

class MemorySummary(BaseModel):
    total_messages: int
    user_messages: int
    ai_messages: int
    memory_type: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    trace: TraceInfo
    session_id: str
    reformulated_question: str
    memory_summary: MemorySummary

class CodeFixRequest(BaseModel):
    code: str = Field(..., description="The buggy code")
    error_message: str = Field(..., description="Error message")
    language: str = Field(default="python", description="Programming language")
    session_id: Optional[str] = Field(None, description="Session ID for context")

class CodeFixResponse(BaseModel):
    fixed_code: str
    full_explanation: str
    sources: List[Dict]
    session_id: str
    language: str

class ConversationHistory(BaseModel):
    session_id: str
    history: List[Dict[str, Any]]
    total_messages: int

class SessionTrace(BaseModel):
    session_id: str
    created_at: str
    total_interactions: int
    user_id: Optional[str]
    trace_log: List[Dict]
    memory_summary: MemorySummary

class ExportRequest(BaseModel):
    session_id: str
    format: str = Field(default="json", description="Export format: json, markdown, or text")

class HealthResponse(BaseModel):
    status: str
    agent_status: str
    documents_count: int
    active_sessions: int
    tracing_enabled: bool

# ============================================================================
# Startup
# ============================================================================

@app.on_event("startup")
async def startup_event():
    global agent
    try:
        logger.info("🚀 Initializing LangChain Agent...")
        
        agent = LangChainAgent(
            collection_name="table_rf_docs",
            model_name="llama3:latest",
            enable_tracing=True,
            # memory_type="buffer"
        )
        
        logger.info("✅ LangChain Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise

# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Check system health and status"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        return HealthResponse(
            status="healthy",
            agent_status="ready",
            documents_count=agent.vectorstore._collection.count(),
            active_sessions=len(agent.sessions),
            tracing_enabled=agent.enable_tracing
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        total_interactions = sum(
            session["interaction_count"]
            for session in agent.sessions.values()
        )
        
        return {
            "total_documents": agent.vectorstore._collection.count(),
            "active_sessions": len(agent.sessions),
            "total_interactions": total_interactions,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": agent.model_name,
            "tracing_enabled": agent.enable_tracing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# ============================================================================
# Session Management Endpoints
# ============================================================================

@app.post("/session/create", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new conversation session with memory"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        session_id = agent.create_session(user_id=request.user_id)
        session = agent.sessions[session_id]
        
        return SessionResponse(
            session_id=session_id,
            created_at=session["created_at"],
            message="Session created successfully with conversation memory"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/session/{session_id}/history", response_model=ConversationHistory)
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    history = agent.get_conversation_history(session_id, format_type="list")
    
    if history is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ConversationHistory(
        session_id=session_id,
        history=history,
        total_messages=len(history)
    )

@app.get("/session/{session_id}/trace", response_model=SessionTrace)
async def get_session_trace(session_id: str):
    """Get full trace log for a session"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    trace = agent.get_session_trace(session_id)
    
    if "error" in trace:
        raise HTTPException(status_code=404, detail=trace["error"])
    
    return SessionTrace(**trace)

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        agent.clear_session(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@app.post("/session/export")
async def export_conversation(request: ExportRequest):
    """Export conversation in various formats"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        export_data = agent.export_conversation(request.session_id, format=request.format)
        
        if export_data == "Session not found":
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Return appropriate response based on format
        if request.format == "markdown":
            return {"content": export_data, "format": "markdown"}
        elif request.format == "text":
            return {"content": export_data, "format": "text"}
        else:  # json
            return {"content": json.loads(export_data), "format": "json"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# ============================================================================
# Query Endpoints
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def query_with_context(request: QueryRequest):
    """
    Query the agent with full conversation context and tracing
    
    - **query**: Your question
    - **session_id**: Optional session ID (creates new if not provided)
    - **top_k**: Number of relevant documents to retrieve
    - **filter_metadata**: Optional metadata filters for document retrieval
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info(f"📥 Received query: {request.query[:100]}...")
        
        # Get answer with full context
        result = agent.ask(
            query=request.query,
            session_id=request.session_id,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata
        )
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

# ============================================================================
# Code Fixing Endpoints
# ============================================================================

@app.post("/fix-code", response_model=CodeFixResponse)
async def fix_code_error(request: CodeFixRequest):
    """
    Fix code errors using AI agent with documentation context
    
    - **code**: The buggy code
    - **error_message**: The error message
    - **language**: Programming language (default: python)
    - **session_id**: Optional session ID for conversation context
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        logger.info(f"🔧 Fixing {request.language} code error...")
        
        result = agent.fix_code(
            code=request.code,
            error_message=request.error_message,
            language=request.language,
            session_id=request.session_id
        )
        
        return CodeFixResponse(**result)
    
    except Exception as e:
        logger.error(f"Code fixing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Code fixing failed: {str(e)}")

# ============================================================================
# Document Management
# ============================================================================

@app.post("/load-docs")
async def load_documents(docs_dir: str = "./docs/tablerf"):
    """Load documents from directory into the knowledge base"""
    try:
        logger.info(f"📚 Loading documents from: {docs_dir}")
        
        loader = DocLoader(docs_dir=docs_dir)
        count = loader.load_docs()
        
        return {
            "success": True,
            "documents_loaded": count,
            "message": f"Successfully loaded {count} documents into knowledge base"
        }
    
    except Exception as e:
        logger.error(f"Document loading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load documents: {str(e)}")

# ============================================================================
# Serve Frontend
# ============================================================================

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
async def serve_frontend():
    """Serve the frontend application"""
    return FileResponse("static/index.html")

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/sessions/list")
async def list_sessions():
    """List all active sessions"""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    sessions_info = []
    for session_id, session in agent.sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "created_at": session["created_at"],
            "interaction_count": session["interaction_count"],
            "user_id": session.get("user_id"),
            "memory_messages": len(session["memory"].chat_memory.messages)
        })
    
    return {
        "total_sessions": len(sessions_info),
        "sessions": sessions_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")