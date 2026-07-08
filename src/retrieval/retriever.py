"""
Legal Retriever — finds relevant document chunks for a user's question.

EXTRACTED FROM: notebook/pdf_loader.ipynb (lines 1524–1599)

WHAT IT DOES:
  Given a question like "Can I get a refund for a defective product?", this
  module:
    1. Converts the question into a vector (using EmbeddingManager)
    2. Optionally narrows the search to a specific legal category (e.g., "consumer")
    3. Searches ChromaDB for the closest matching document chunks
    4. Deduplicates results (the notebook returned the same chunk 3 times!)
    5. Returns structured results with metadata and similarity scores

KEY IMPROVEMENT — METADATA FILTERING:
  The notebook searched ALL documents for every query. This module can filter
  by 'category' or 'act_name' metadata, so a consumer rights question only
  searches consumer protection chunks — faster and more accurate.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

# pyrefly: ignore [missing-import]
from src.embeddings.manager import EmbeddingManager
# pyrefly: ignore [missing-import]
from src.vectorstore.store import VectorStore


class LegalRetriever:
    """Retrieve relevant legal sections with smart filtering.

    Usage:
        retriever = LegalRetriever(vector_store, embedding_manager)
        results = retriever.retrieve("Can I get a refund?", category="consumer")
    """

    def __init__(self, vector_store: VectorStore, embedding_manager: EmbeddingManager):
        """
        Initialize the retriever.

        Args:
            vector_store: VectorStore instance containing document embeddings.
            embedding_manager: EmbeddingManager for generating query embeddings.
        """
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        act_name: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant legal sections for a query.

        Flow:
          1. Generate query embedding
          2. Apply metadata filters (category, act_name) if provided
          3. Search ChromaDB with filters
          4. Deduplicate results (same content appearing multiple times)
          5. Filter by minimum similarity score
          6. Return structured results sorted by relevance

        Args:
            query: The user's legal question.
            category: Filter to a specific legal category
                      (e.g., "consumer", "property", "rti").
            act_name: Filter to a specific act name.
            top_k: Maximum number of results to return.
            min_score: Minimum similarity score threshold (0.0 to 1.0).

        Returns:
            List of dicts, each containing:
              - 'id': Document ID in ChromaDB
              - 'content': The actual text of the chunk
              - 'metadata': Rich metadata (act_name, section_number, etc.)
              - 'similarity_score': How relevant this chunk is (higher = better)
              - 'rank': Position in the results (1 = most relevant)
        """
        logger.info(f"Retrieving documents for: '{query[:80]}...'")

        # Step 1: Convert the question to a vector
        query_embedding = self.embedding_manager.generate_single(query)

        # Step 2: Build metadata filter
        # ChromaDB's 'where' clause lets us search ONLY within matching docs
        where_filter = self._build_filter(category, act_name)

        # Step 3: Search ChromaDB
        try:
            results = self.vector_store.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k * 2,  # Fetch extra to account for dedup filtering
                where=where_filter if where_filter else None,
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        # Step 4: Process and deduplicate results
        retrieved_docs = []
        seen_hashes = set()

        if results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            ids = results["ids"][0]

            for doc_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances
            ):
                # ChromaDB returns cosine DISTANCE; convert to similarity SCORE
                # Distance 0 = identical → score 1.0
                # Distance 2 = opposite → score -1.0 (but we treat as 0)
                similarity_score = 1 - distance

                # Skip low-confidence results
                if similarity_score < min_score:
                    continue

                # Deduplicate: skip if we've seen this exact content before
                content_hash = metadata.get("content_hash", "")
                if content_hash and content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)

                retrieved_docs.append(
                    {
                        "id": doc_id,
                        "content": document,
                        "metadata": metadata,
                        "similarity_score": round(similarity_score, 4),
                    }
                )

        # Step 5: Sort by score (highest first) and limit to top_k
        retrieved_docs.sort(key=lambda x: x["similarity_score"], reverse=True)
        retrieved_docs = retrieved_docs[:top_k]

        # Add rank numbers
        for i, doc in enumerate(retrieved_docs):
            doc["rank"] = i + 1

        logger.info(
            f"Retrieved {len(retrieved_docs)} documents "
            f"(category={category or 'all'})"
        )
        return retrieved_docs

    @staticmethod
    def _build_filter(
        category: Optional[str], act_name: Optional[str]
    ) -> Optional[Dict]:
        """
        Build a ChromaDB metadata filter.

        ChromaDB uses a 'where' clause for metadata filtering:
          {"category": "consumer"}           → only consumer docs
          {"act_name": "Consumer Protection"} → only that specific act

        If both are provided, we combine them with $and.
        """
        conditions = []
        if category and category.lower() not in ["all", "general"]:
            # If a specific category is requested, allow that category OR 'general'
            conditions.append({"$or": [{"category": category.lower()}, {"category": "general"}]})
        elif category and category.lower() == "general":
            conditions.append({"category": "general"})

        if act_name:
            conditions.append({"act_name": act_name})

        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
