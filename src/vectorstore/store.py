"""
Vector Store — persistent storage and retrieval of document embeddings.

EXTRACTED FROM: notebook/pdf_loader.ipynb (lines 904–997)

WHAT IT DOES:
  Stores document text + embedding vectors + metadata in ChromaDB (a vector
  database). When you search, ChromaDB finds the documents whose vectors
  are most similar to your query vector — this is called "similarity search."

WHY CHROMADB:
  - Persists to disk (survives restarts)
  - Supports metadata filtering (e.g., "only search consumer protection docs")
  - Lightweight — no separate server needed, runs in-process
  - Free and open-source

KEY IMPROVEMENT OVER NOTEBOOK:
  The notebook had a duplication problem: running the ingestion cell multiple
  times added the same documents again. Our VectorStore now uses content hashing
  to detect and skip duplicates.
"""

import hashlib
import os
import uuid
from typing import Any, List

import chromadb
import numpy as np
from langchain_core.documents import Document
from loguru import logger

# pyrefly: ignore [missing-import]
from src.config import settings


class VectorStore:
    """Manages document embeddings in a ChromaDB vector store.

    Usage:
        vs = VectorStore()
        vs.add_documents(documents, embeddings)
        results = vs.collection.query(query_embeddings=[...], n_results=5)
    """

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | None = None,
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the ChromaDB collection.
                             Defaults to settings.COLLECTION_NAME.
            persist_directory: Directory to persist the database.
                               Defaults to settings.VECTOR_STORE_DIR.
        """
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.persist_directory = persist_directory or str(settings.VECTOR_STORE_DIR)
        self.client: chromadb.PersistentClient | None = None
        self.collection: chromadb.Collection | None = None
        self._initialize_store()

    def _initialize_store(self) -> None:
        """Initialize ChromaDB client and get or create the collection."""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # get_or_create_collection: if it exists, opens it; if not, creates it
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "NyayaSetu legal document embeddings"},
            )

            doc_count = self.collection.count()
            logger.info(
                f"Vector store initialized. Collection: '{self.collection_name}', "
                f"Documents: {doc_count}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    @staticmethod
    def _content_hash(text: str) -> str:
        """Generate a short hash of text content for deduplication."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

    def add_documents(
        self,
        documents: List[Document],
        embeddings: np.ndarray,
    ) -> int:
        """
        Add documents and their embeddings to the vector store.

        Uses content hashing to skip documents that already exist,
        solving the notebook's duplicate ingestion problem.

        Args:
            documents: List of LangChain Document objects.
            embeddings: Corresponding embeddings array, shape (N, dim).

        Returns:
            Number of NEW documents actually added (skipping duplicates).
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(documents)} documents but {len(embeddings)} embeddings"
            )

        logger.info(f"Adding {len(documents)} documents to vector store...")

        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []
        skipped = 0

        # Fetch existing hashes to detect duplicates
        existing_data = self.collection.get(include=["documents"])
        existing_hashes = set()
        if existing_data["documents"]:
            for doc_text in existing_data["documents"]:
                existing_hashes.add(self._content_hash(doc_text))

        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            # Check for duplicate content
            content_hash = self._content_hash(doc.page_content)
            if content_hash in existing_hashes:
                skipped += 1
                continue

            # Generate a unique ID for this document
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)

            # Build metadata (ChromaDB requires flat key-value pairs)
            metadata = dict(doc.metadata)
            metadata["doc_index"] = i
            metadata["content_length"] = len(doc.page_content)
            metadata["content_hash"] = content_hash
            metadatas.append(metadata)

            documents_text.append(doc.page_content)
            embeddings_list.append(embedding.tolist())

            # Track this hash so we don't add duplicates within the same batch
            existing_hashes.add(content_hash)

        if not ids:
            logger.warning(f"All {skipped} documents were duplicates — nothing added.")
            return 0

        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents_text,
            )
            added = len(ids)
            logger.success(
                f"Added {added} new documents (skipped {skipped} duplicates). "
                f"Total in collection: {self.collection.count()}"
            )
            return added
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count() if self.collection else 0
