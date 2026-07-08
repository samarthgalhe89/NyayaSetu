"""
Embedding Manager — converts text into numerical vectors.

EXTRACTED FROM: notebook/pdf_loader.ipynb (lines 822–868)

WHAT IT DOES:
  Takes a string like "Can I get a refund for a defective phone?" and turns it
  into a list of 384 numbers (a "vector"). Two sentences with similar meanings
  will produce vectors that are close together in 384-dimensional space.

WHY THIS MATTERS:
  This is the foundation of semantic search. When a user asks a question, we
  convert it to a vector, then find document chunks whose vectors are closest
  to the query vector. This lets us match "refund for defective product" with
  "product liability" even though they share no words.

TECHNOLOGY:
  SentenceTransformer('all-MiniLM-L6-v2') — a compact model that runs locally
  on CPU. No API calls needed for embedding generation.
"""

from typing import List

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from src.config import settings


class EmbeddingManager:
    """Manages document embedding generation using SentenceTransformer.

    Usage:
        em = EmbeddingManager()
        vectors = em.generate_embeddings(["Hello world", "How are you?"])
        # vectors.shape → (2, 384)
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the embedding manager.

        Args:
            model_name: HuggingFace model name. If None, uses the value
                        from settings.EMBEDDING_MODEL (default: 'all-MiniLM-L6-v2')
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model: SentenceTransformer | None = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the SentenceTransformer model into memory."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            logger.success(f"Embedding model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            numpy array of shape (len(texts), embedding_dim).
            For all-MiniLM-L6-v2, embedding_dim = 384.
        """
        if not self.model:
            raise ValueError("Embedding model not loaded. Call _load_model() first.")

        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(texts, show_progress_bar=len(texts) > 10)
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings

    def generate_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string.

        This is a convenience method used during retrieval — we only need
        to embed one query at a time.

        Args:
            text: Single text string to embed.

        Returns:
            1-D numpy array of shape (embedding_dim,).
        """
        return self.generate_embeddings([text])[0]
