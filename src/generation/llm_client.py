"""
Legal LLM Client — wraps Groq LLM for structured legal Q&A.

EXTRACTED FROM: notebook/pdf_loader.ipynb (lines 1762–1942)
  - rag_simple() function
  - rag_advanced() function
  - AdvancedRAGPipeline class

WHAT IT DOES:
  1. detect_category() — Asks the LLM to classify a question into a legal
     category (consumer, property, rti, etc.). This is used BEFORE retrieval
     to narrow down which documents to search.

  2. generate_legal_answer() — Takes the user's question + retrieved context
     chunks and asks the LLM to produce a structured legal answer with
     sections, action steps, and citations.

WHY GROQ:
  Groq provides extremely fast LLM inference (sub-second for most queries).
  The langchain-groq wrapper lets us call it with a simple .invoke() method.
  We use llama-3.1-8b-instant — a compact but capable model that's free-tier
  eligible on Groq.
"""

from typing import Any, Dict, List

from langchain_groq import ChatGroq
from loguru import logger

from src.config import settings
from src.generation.prompts import CATEGORY_DETECTION_PROMPT, LEGAL_QA_PROMPT


class LegalLLMClient:
    """Manages LLM interactions for legal Q&A.

    Usage:
        client = LegalLLMClient()
        category = client.detect_category("Can I get a refund?")
        # → "consumer"

        result = client.generate_legal_answer(
            query="Can I get a refund?",
            context="Section 42 states...",
            sources=[{"act_name": "Consumer Protection", ...}]
        )
        # → {"answer": "## 📋 Short Answer\n...", "sources": [...], "category": "consumer"}
    """

    def __init__(self):
        """Initialize the Groq LLM client with settings from config."""
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        logger.info(f"LLM client initialized: model={settings.LLM_MODEL}")

    def detect_category(self, query: str) -> str:
        """
        Auto-detect the legal category of a question.

        This runs BEFORE retrieval so we can filter the search to relevant acts.
        For example, "Can I get a refund?" → "consumer", which means we only
        search Consumer Protection Act chunks instead of all acts.

        Args:
            query: The user's legal question.

        Returns:
            Category string: "consumer", "property", "rti", "traffic",
            "criminal", or "general".
        """
        try:
            prompt = CATEGORY_DETECTION_PROMPT.format(query=query)
            response = self.llm.invoke(prompt)
            category = response.content.strip().lower()

            # Validate against known categories
            valid = {"consumer", "property", "rti", "traffic", "criminal", "general"}
            if category not in valid:
                logger.warning(
                    f"LLM returned unknown category '{category}', "
                    f"falling back to 'general'"
                )
                return "general"

            logger.info(f"Detected category: {category}")
            return category
        except Exception as e:
            logger.error(f"Category detection failed: {e}")
            return "general"

    def generate_legal_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate a structured legal response.

        Args:
            query: The user's legal question.
            context: Concatenated text from retrieved document chunks.
            sources: List of source metadata dicts from the retriever.

        Returns:
            Dict with:
              - 'answer': Markdown-formatted legal answer
              - 'sources': The sources list (passed through for the API)
              - 'category': Detected legal category
        """
        try:
            prompt = LEGAL_QA_PROMPT.format(context=context, query=query)
            response = self.llm.invoke(prompt)

            return {
                "answer": response.content,
                "sources": sources,
                "category": self.detect_category(query),
            }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "answer": (
                    "I'm sorry, I encountered an error while generating a response. "
                    "Please try again or rephrase your question."
                ),
                "sources": sources,
                "category": "general",
            }
