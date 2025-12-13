from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import re

# LangChain Core
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import  InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# LangChain Community
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# LangChain Ollama
from langchain_ollama import ChatOllama

import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMemory:
    """Simple conversation memory storage"""
    
    def __init__(self): 
        self.sessions: Dict[str, InMemoryChatMessageHistory] = {}
    
    def get_session(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.sessions:
            self.sessions[session_id] = InMemoryChatMessageHistory()
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].clear()


class LangChainAgent:
    """
    LangChain-powered AI agent with conversation memory and context tracking
    """
    
    def __init__(
        self, 
        collection_name: str = "table_rf_docs",
        model_name: str = "llama3:latest",
        enable_tracing: bool = True
    ):
        self.collection_name = collection_name
        self.model_name = model_name
        self.enable_tracing = enable_tracing
        
        logger.info("🔧 Initializing LangChain Agent...")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_data")
        
        # Initialize vector store
        self.vectorstore = Chroma(
            client=self.chroma_client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
        
        # Initialize LLM (using ChatOllama for conversation support)
        self.llm = ChatOllama(
            model=model_name,
            temperature=0.7
        )
        
        # Initialize memory
        self.memory = ConversationMemory()
        
        # Store session metadata
        self.sessions = {}
        
        logger.info("✅ LangChain Agent initialized")
        logger.info(f"📊 Documents: {self.vectorstore._collection.count()}")

    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create memory for this session
        self.memory.get_session(session_id)
        
        # Store session metadata
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "interaction_count": 0,
            "trace_log": []
        }
        
        logger.info(f"📝 Session created: {session_id}")
        return session_id

    def _reformulate_question(
        self, 
        question: str, 
        chat_history: List[BaseMessage]
    ) -> str:
        """
        Reformulate follow-up questions to be standalone using chat history
        """
        if not chat_history:
            return question
        
        # Only reformulate if there's previous context
        if len(chat_history) < 2:
            return question
        
        # Build context from recent messages
        recent_messages = chat_history[-4:]  # Last 2 exchanges
        context = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        reformulate_prompt = f"""Given the conversation history below, reformulate the follow-up question to be a standalone question that includes all necessary context.

Conversation History:
{context}

Follow-up Question: {question}

Standalone Question (keep it concise and clear):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=reformulate_prompt)])
            reformulated = response.content.strip()
            
            # If reformulation failed or is too similar, use original
            if not reformulated or reformulated == question:
                return question
            
            logger.info(f"🔄 Reformulated: '{question}' → '{reformulated}'")
            return reformulated
            
        except Exception as e:
            logger.warning(f"Failed to reformulate question: {e}")
            return question

    def _retrieve_documents(
        self, 
        query: str, 
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Retrieve relevant documents from vector store"""
        
        logger.info(f"🔍 Searching for: {query[:100]}...")
        
        # Build search kwargs
        search_kwargs = {"k": top_k}
        if filter_metadata:
            search_kwargs["filter"] = filter_metadata
        
        # Search
        docs = self.vectorstore.similarity_search(query, **search_kwargs)
        
        # Format results
        results = []
        for i, doc in enumerate(docs):
            results.append({
                "rank": i + 1,
                "document": doc.page_content,
                "metadata": doc.metadata,
                "filename": doc.metadata.get("filename", "Unknown"),
                "relevance_note": f"Source {i+1}"
            })
        
        logger.info(f"📚 Retrieved {len(results)} documents")
        return results

    def ask(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ask a question with full conversation context
        """
        # Create session if needed
        if session_id is None or session_id not in self.sessions:
            session_id = self.create_session()
        
        session = self.sessions[session_id]
        chat_history = self.memory.get_session(session_id)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 Query: {query}")
        logger.info(f"📝 Session: {session_id}")
        logger.info(f"💬 Interaction: {session['interaction_count'] + 1}")
        logger.info(f"{'='*70}")
        
        start_time = datetime.now()
        
        try:
            # Step 1: Reformulate question with context
            reformulated_question = self._reformulate_question(
                query, 
                chat_history.messages
            )
            
            # Step 2: Retrieve relevant documents
            sources = self._retrieve_documents(
                reformulated_question, 
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # Step 3: Build context from documents
            doc_context = "\n\n".join([
                f"[Source {s['rank']}: {s['filename']}]\n{s['document']}"
                for s in sources
            ])
            
            # Step 4: Build prompt with chat history
            messages = [
                SystemMessage(content="""You are an expert assistant with access to documentation. 
Answer questions based on the provided context and conversation history.
Always cite the source documents you used.
If you don't know the answer, say so clearly.""")
            ]
            
            # Add chat history
            messages.extend(chat_history.messages)
            
            # Add current query with context
            current_query = f"""Context from documentation:
{doc_context}

Question: {query}

Please provide a detailed answer based on the context above."""
            
            messages.append(HumanMessage(content=current_query))
            
            # Step 5: Get answer from LLM
            logger.info(f"🤖 Generating answer...")
            response = self.llm.invoke(messages)
            answer = response.content
            
            # Step 6: Save to memory
            chat_history.add_user_message(query)
            chat_history.add_ai_message(answer)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Build trace info
            trace_info = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "original_question": query,
                "reformulated_question": reformulated_question,
                "documents_retrieved": len(sources),
                "processing_time_seconds": duration,
                "interaction_number": session["interaction_count"] + 1
            }
            
            # Update session
            session["interaction_count"] += 1
            session["trace_log"].append(trace_info)
            
            logger.info(f"✅ Answer generated in {duration:.2f}s")
            
            # Build response
            return {
                "answer": answer,
                "sources": sources,
                "trace": trace_info,
                "session_id": session_id,
                "reformulated_question": reformulated_question,
                "memory_summary": self._get_memory_summary(session_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise

    def fix_code(
        self,
        code: str,
        error_message: str,
        language: str = "python",
        session_id: Optional[str] = None
    ) -> Dict:
        """Fix code errors with context from documentation"""
        
        if session_id is None or session_id not in self.sessions:
            session_id = self.create_session()
        
        logger.info(f"🔧 Fixing {language} code error...")
        
        # Search for relevant documentation
        search_query = f"{language} {error_message} error fix"
        sources = self._retrieve_documents(search_query, top_k=3)
        
        doc_context = "\n\n".join([
            f"[{s['filename']}]\n{s['document']}"
            for s in sources
        ])
        
        # Build fixing prompt
        fix_prompt = f"""You are an expert {language} debugger.

BUGGY CODE:
```{language}
{code}
```

ERROR MESSAGE:
{error_message}

RELEVANT DOCUMENTATION:
{doc_context}

Please provide:
1. FIXED CODE in a ```{language} code block
2. EXPLANATION of what was wrong
3. BEST PRACTICES to avoid this error

Be specific and clear."""
        
        # Get fix
        response = self.llm.invoke([HumanMessage(content=fix_prompt)])
        full_response = response.content
        
        # Extract code block
        fixed_code = self._extract_code_block(full_response, language)
        
        # Save to memory
        chat_history = self.memory.get_session(session_id)
        chat_history.add_user_message(f"Fix this {language} error: {error_message[:100]}")
        chat_history.add_ai_message(full_response[:200] + "...")
        
        # Update session
        self.sessions[session_id]["interaction_count"] += 1
        
        return {
            "fixed_code": fixed_code,
            "full_explanation": full_response,
            "sources": [
                {"filename": s["filename"], "content": s["document"][:200] + "..."}
                for s in sources
            ],
            "session_id": session_id,
            "language": language
        }

    def _extract_code_block(self, text: str, language: str) -> str:
        """Extract code block from markdown"""
        pattern = rf"```{language}(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        pattern = r"```(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return ""

    def get_conversation_history(self, session_id: str, format_type: str = "list") -> Any:
        """Get conversation history in different formats"""
        if session_id not in self.sessions:
            return None
        
        chat_history = self.memory.get_session(session_id)
        messages = chat_history.messages
        
        if format_type == "messages":
            return messages
        
        elif format_type == "text":
            text_history = []
            for msg in messages:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                text_history.append(f"{role}: {msg.content}")
            return "\n\n".join(text_history)
        
        else:  # list format
            history = []
            for msg in messages:
                history.append({
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                    "type": type(msg).__name__
                })
            return history

    def _get_memory_summary(self, session_id: str) -> Dict:
        """Get summary of conversation memory"""
        if session_id not in self.sessions:
            return {}
        
        chat_history = self.memory.get_session(session_id)
        messages = chat_history.messages
        
        return {
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if isinstance(m, HumanMessage)]),
            "ai_messages": len([m for m in messages if isinstance(m, AIMessage)]),
            "memory_type": "buffer"
        }

    def get_session_trace(self, session_id: str) -> Dict:
        """Get full trace log for a session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "total_interactions": session["interaction_count"],
            "user_id": session.get("user_id"),
            "trace_log": session["trace_log"],
            "memory_summary": self._get_memory_summary(session_id)
        }

    def clear_session(self, session_id: str):
        """Clear a conversation session"""
        if session_id in self.sessions:
            self.memory.clear_session(session_id)
            self.sessions[session_id]["interaction_count"] = 0
            self.sessions[session_id]["trace_log"] = []
            logger.info(f"🗑️ Session {session_id} cleared")

    def export_conversation(self, session_id: str, format: str = "json") -> str:
        """Export conversation in various formats"""
        if session_id not in self.sessions:
            return "Session not found"
        
        history = self.get_conversation_history(session_id, format_type="list")
        session = self.sessions[session_id]
        
        if format == "markdown":
            md = f"# Conversation Log: {session_id}\n\n"
            md += f"**Created:** {session['created_at']}\n"
            md += f"**Interactions:** {session['interaction_count']}\n\n"
            md += "---\n\n"
            
            for i, msg in enumerate(history, 1):
                role = "👤 User" if msg["role"] == "user" else "🤖 Assistant"
                md += f"### {role} (Message {i})\n\n"
                md += f"{msg['content']}\n\n"
                md += "---\n\n"
            
            return md
        
        elif format == "text":
            return self.get_conversation_history(session_id, format_type="text")
        
        else:  # json
            import json
            return json.dumps({
                "session_id": session_id,
                "created_at": session["created_at"],
                "interactions": history,
                "trace": session["trace_log"]
            }, indent=2)


# Example usage
if __name__ == "__main__":
    agent = LangChainAgent(
        model_name="llama3:latest",
        enable_tracing=True
    )
    
    # Create session
    session_id = agent.create_session(user_id="demo_user")
    print(f"\n✅ Session: {session_id}\n")
    
    # Question 1
    print("="*70)
    print("QUESTION 1")
    print("="*70)
    result1 = agent.ask("What is TableRF?", session_id=session_id)
    print(f"\n💬 Answer:\n{result1['answer'][:300]}...\n")
    print(f"🔄 Reformulated: {result1['reformulated_question']}")
    
    # Question 2 (with context)
    print("\n" + "="*70)
    print("QUESTION 2 (uses context from Q1)")
    print("="*70)
    result2 = agent.ask("What are its main components?", session_id=session_id)
    print(f"\n💬 Answer:\n{result2['answer'][:300]}...\n")
    print(f"🔄 Reformulated: {result2['reformulated_question']}")
    
    # Question 3
    print("\n" + "="*70)
    print("QUESTION 3 (deeper context)")
    print("="*70)
    result3 = agent.ask("How does the first one work?", session_id=session_id)
    print(f"\n💬 Answer:\n{result3['answer'][:300]}...\n")
    
    # Trace
    trace = agent.get_session_trace(session_id)
    print("\n" + "="*70)
    print("SESSION TRACE")
    print("="*70)
    print(f"Interactions: {trace['total_interactions']}")
    print(f"Memory: {trace['memory_summary']}")