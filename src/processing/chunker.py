"""
Legal-Aware Document Chunker — splits documents respecting section boundaries.

WHAT IT DOES:
  Takes the parsed sections from LegalActParser and ensures each one fits
  within the embedding model's optimal window size (CHUNK_SIZE, default 800).

  Strategy:
    1. If a section fits within CHUNK_SIZE → keep it as a single chunk ✅
    2. If a section is too long → split it with RecursiveCharacterTextSplitter
       BUT prepend the section title to every sub-chunk so context is never lost

WHY NOT JUST USE RecursiveCharacterTextSplitter DIRECTLY:
  The default splitter from your notebook splits blindly by character count.
  This means a legal section can get cut in half mid-sentence:

    ❌ "Section 42. Product Liability— ... manufacturing defec"  ← CUT
    ❌ "t; or the product is defective in design..."

  Our chunker keeps the section intact when possible, and when it must split,
  it prepends "Section 42. Product Liability —" to every sub-chunk so the
  embedding model always has context about WHICH section the text belongs to.
"""

from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from src.config import settings


class LegalChunker:
    """Chunk legal documents respecting section boundaries.

    Usage:
        chunker = LegalChunker()
        chunks = chunker.chunk_documents(parsed_sections)
    """

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum characters per chunk. Default from config.
            chunk_overlap: Overlap between chunks. Default from config.
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        # Fallback splitter for sections that exceed chunk_size
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk documents with legal section awareness.

        For each document:
          - If it fits in chunk_size → keep as-is (one chunk = one section)
          - If too long → split with RecursiveCharacterTextSplitter but prepend
            section header to each sub-chunk for context continuity

        Args:
            documents: List of Document objects (from LegalActParser).

        Returns:
            List of Document objects, each ≤ chunk_size characters.
        """
        chunks = []
        kept_intact = 0
        split_count = 0

        for doc in documents:
            content_length = len(doc.page_content)

            if content_length <= self.chunk_size:
                # Section fits — keep it as a single chunk
                chunks.append(doc)
                kept_intact += 1
            else:
                # Section too long — split with context header
                sub_chunks = self._split_with_header(doc)
                chunks.extend(sub_chunks)
                split_count += 1

        logger.info(
            f"Chunked {len(documents)} documents → {len(chunks)} chunks "
            f"({kept_intact} intact, {split_count} split)"
        )
        return chunks

    def _split_with_header(self, doc: Document) -> List[Document]:
        """
        Split a long section, prepending the section header to each sub-chunk.

        This ensures that even after splitting, each chunk knows which section
        and act it belongs to — critical for the embedding model to capture
        the correct semantic meaning.
        """
        # Build a context header from metadata
        metadata = doc.metadata
        header_parts = []
        if metadata.get("act_name"):
            header_parts.append(metadata["act_name"])
        if metadata.get("section_number"):
            title = metadata.get("section_title", "")
            header_parts.append(f"Section {metadata['section_number']}. {title}")

        header = " — ".join(header_parts)
        header_prefix = f"[{header}]\n\n" if header else ""

        # Split the content
        sub_docs = self.fallback_splitter.create_documents(
            texts=[doc.page_content],
            metadatas=[doc.metadata],
        )

        # Prepend header to each sub-chunk and add chunk index
        result = []
        for i, sub_doc in enumerate(sub_docs):
            sub_doc.page_content = header_prefix + sub_doc.page_content
            sub_doc.metadata = dict(doc.metadata)  # Copy metadata
            sub_doc.metadata["chunk_index"] = i
            sub_doc.metadata["total_chunks"] = len(sub_docs)
            result.append(sub_doc)

        return result
