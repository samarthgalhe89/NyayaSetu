"""
API Routes — defines the URL endpoints your frontend calls.

WHAT IS A ROUTE:
  A route maps a URL + HTTP method to a Python function. For example:
    POST /api/query  →  query_legal() function

  FastAPI's @router.post() decorator tells the framework:
    "When someone sends a POST request to /api/query, run this function
    and return its result as JSON."

ENDPOINTS:
  POST /api/query      → Main Q&A: send a question, get a legal answer
  GET  /api/categories → List available legal categories
  GET  /api/health     → Check if the server is running
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

# pyrefly: ignore [missing-import]
from api.schemas import HealthResponse, QueryRequest, QueryResponse, SourceInfo
# pyrefly: ignore [missing-import]
from src.config import settings
# pyrefly: ignore [missing-import]
from src.embeddings.manager import EmbeddingManager
# pyrefly: ignore [missing-import]
from src.generation.llm_client import LegalLLMClient
# pyrefly: ignore [missing-import]
from src.retrieval.retriever import LegalRetriever
# pyrefly: ignore [missing-import]
from src.vectorstore.store import VectorStore

# ── Initialize pipeline components (created once, reused for every request) ──
# These are module-level singletons — FastAPI creates them when the server
# starts and reuses them across all requests.
logger.info("Initializing RAG pipeline components...")
embedding_manager = EmbeddingManager()
vector_store = VectorStore()
retriever = LegalRetriever(vector_store, embedding_manager)
llm_client = LegalLLMClient()
logger.success("RAG pipeline ready.")

# ── Create the router ────────────────────────────────────────────────────
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_legal(request: QueryRequest):
    """
    Main endpoint — ask a legal question, get a structured answer.

    Flow:
      1. Detect category (or use the one provided)
      2. Retrieve relevant document chunks (with category filter)
      3. Generate structured legal answer with LLM
      4. Return answer + sources + confidence

    The 'async' keyword lets FastAPI handle multiple requests concurrently.
    Even though our LLM call is blocking, FastAPI runs it in a thread pool
    so the server doesn't freeze for other users.
    """
    try:
        # Step 1: Detect or use provided category
        category = request.category
        if not category:
            category = llm_client.detect_category(request.question)

        # Step 2: Retrieve relevant chunks with metadata filtering
        results = retriever.retrieve(
            query=request.question,
            category=category if category != "general" else None,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        # Step 3: Build context from retrieved chunks
        if not results:
            return QueryResponse(
                question=request.question,
                category=category,
                answer=(
                    "I could not find specific legal provisions for your question "
                    "in my current database. Please consult a lawyer or visit "
                    "[indiacode.nic.in](https://www.indiacode.nic.in) for more information."
                ),
                sources=[],
                confidence=0.0,
            )

        context = "\n\n".join([doc["content"] for doc in results])

        # Build source info for the response
        sources = [
            SourceInfo(
                act_name=doc["metadata"].get("act_name", "Unknown Act"),
                section_number=doc["metadata"].get("section_number", ""),
                section_title=doc["metadata"].get("section_title", ""),
                page=doc["metadata"].get("page", 0),
                similarity_score=doc["similarity_score"],
                preview=doc["content"][:200] + "..."
                if len(doc["content"]) > 200
                else doc["content"],
            )
            for doc in results
        ]

        # Step 4: Generate answer with LLM
        llm_result = llm_client.generate_legal_answer(
            query=request.question,
            context=context,
            sources=[s.model_dump() for s in sources],
        )

        confidence = max(doc["similarity_score"] for doc in results)

        return QueryResponse(
            question=request.question,
            category=llm_result.get("category", category),
            answer=llm_result["answer"],
            sources=sources,
            confidence=confidence,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your question: {str(e)}",
        )


@router.get("/categories")
async def list_categories():
    """
    List available legal categories.

    The frontend uses this to render the category filter pills.
    """
    return {
        "categories": [
            {"id": "all", "label": "All", "icon": "📚"},
            {"id": "consumer", "label": "Consumer Rights", "icon": "🛒"},
            {"id": "property", "label": "Property & Rent", "icon": "🏠"},
            {"id": "rti", "label": "RTI", "icon": "📋"},
            {"id": "traffic", "label": "Traffic", "icon": "🚗"},
            {"id": "criminal", "label": "Criminal", "icon": "⚖️"},
        ]
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check — is the server running and is the pipeline ready?"""
    return HealthResponse(
        status="healthy",
        documents_count=vector_store.count(),
        model=settings.LLM_MODEL,
    )
