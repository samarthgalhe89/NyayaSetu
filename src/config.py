"""
Centralized configuration for NyayaSetu using pydantic-settings.

HOW IT WORKS:
  1. When you do `from src.config import settings`, Pydantic reads your .env file
  2. It fills in GROQ_API_KEY from the .env, and uses defaults for everything else
  3. If GROQ_API_KEY is missing, the app crashes IMMEDIATELY with a clear error
     — no silent failures, no confusing "None" errors deep in the pipeline

WHY THIS MATTERS:
  Instead of hardcoding "all-MiniLM-L6-v2" in 5 different files, we define it
  ONCE here. Change it here → changes everywhere. Same for the Groq model,
  chunk sizes, API port, etc.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    All configurable values for the NyayaSetu application.

    Values are loaded in this priority order:
      1. Environment variables (highest priority)
      2. Values from .env file
      3. Defaults defined below (lowest priority)
    """

    # ── API Keys ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str  # REQUIRED — no default, app won't start without it

    # ── LLM Settings ─────────────────────────────────────────────────────
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.1  # Low temp = more deterministic legal answers
    LLM_MAX_TOKENS: int = 1024

    # ── Embedding Settings ───────────────────────────────────────────────
    # all-MiniLM-L6-v2 produces 384-dim vectors, good balance of speed & quality
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Chunking Settings ────────────────────────────────────────────────
    CHUNK_SIZE: int = 800  # Max chars per chunk
    CHUNK_OVERLAP: int = 200  # Overlap between chunks for context continuity

    # ── Paths ────────────────────────────────────────────────────────────
    DATA_DIR: Path = Path("data")
    LEGAL_ACTS_DIR: Path = Path("data/legal_acts")
    VECTOR_STORE_DIR: Path = Path("data/vector_store")

    # ── Vector Store ─────────────────────────────────────────────────────
    COLLECTION_NAME: str = "legal_documents"

    # ── API Server Settings ──────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ── Singleton instance ───────────────────────────────────────────────────
# Import this everywhere: `from src.config import settings`
settings = Settings()
