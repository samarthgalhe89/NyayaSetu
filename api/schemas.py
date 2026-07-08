"""
API Schemas — defines the shape of every API request and response.

WHAT ARE PYDANTIC MODELS:
  Pydantic models are Python classes that define what fields a JSON object
  must have, and what types those fields must be. FastAPI uses them to:
    1. VALIDATE incoming requests (reject bad data with clear error messages)
    2. SERIALIZE outgoing responses (convert Python objects to JSON)
    3. DOCUMENT the API (auto-generates OpenAPI/Swagger docs)

WHY THIS MATTERS:
  Without schemas, you'd have to manually check every incoming request:
    "Did the user send a 'question' field? Is it a string? Is 'top_k' a number?"
  Pydantic does all of this automatically. If someone sends {"question": 123},
  they get a clear error: "question must be a string."
"""

from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Schema for the /api/query endpoint request body.

    Example JSON:
      {"question": "Can I get a refund for a defective product?", "category": "consumer"}
    """

    question: str = Field(
        ...,  # '...' means REQUIRED — request will be rejected without it
        description="The user's legal question in plain language",
        min_length=3,
        max_length=2000,
    )
    category: Optional[str] = Field(
        default=None,
        description="Legal category filter. If omitted, auto-detected by LLM. "
        "Options: consumer, property, rti, traffic, criminal, general",
    )
    top_k: int = Field(
        default=5,
        ge=1,  # Must be >= 1
        le=20,  # Must be <= 20
        description="Number of document chunks to retrieve",
    )
    min_score: float = Field(
        default=0.1,
        description="Minimum similarity score for retrieving chunks (0.0 to 1.0)",
    )


class SourceInfo(BaseModel):
    """Metadata about a single source citation."""

    act_name: str = ""
    section_number: str = ""
    section_title: str = ""
    page: int = 0
    similarity_score: float = 0.0
    preview: str = ""  # First ~200 chars of the source text


class QueryResponse(BaseModel):
    """
    Schema for the /api/query endpoint response.

    The frontend parses this JSON to render:
      - The answer as styled Markdown
      - Source citations as clickable badges
      - Confidence indicator
    """

    question: str
    category: str
    answer: str  # Markdown-formatted legal answer
    sources: list[SourceInfo]
    confidence: float = Field(
        description="Highest similarity score among retrieved chunks (0.0–1.0)"
    )


class HealthResponse(BaseModel):
    """Schema for the /api/health endpoint response."""

    status: str
    documents_count: int
    model: str
