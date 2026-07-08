"""
Ingestion Script — one-shot script to ingest legal act PDFs into the vector store.

USAGE:
    python scripts/ingest_legal_docs.py

WHAT THIS DOES:
    1. Reads PDF files from data/legal_acts/
    2. Parses them with LegalActParser (section-aware)
    3. Chunks them with LegalChunker (section-boundary-aware)
    4. Generates embeddings with EmbeddingManager
    5. Stores everything in ChromaDB via VectorStore (with deduplication)

WHY A SEPARATE SCRIPT:
    Ingestion is a one-time (or rare) operation. You run it once to populate
    the database, then start the API server. You don't want ingestion logic
    mixed into your web server code.

NOTE:
    To add new legal acts, put the PDF in data/legal_acts/ and add an entry
    to the LEGAL_ACTS list below with the correct name, year, and category.
"""

import sys
from pathlib import Path

# Add project root to Python path so imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# pyrefly: ignore [missing-import]
from src.config import settings
# pyrefly: ignore [missing-import]
from src.embeddings.manager import EmbeddingManager
# pyrefly: ignore [missing-import]
from src.ingestion.legal_parser import LegalActParser
# pyrefly: ignore [missing-import]
from src.ingestion.pdf_loader import PDFLoader
# pyrefly: ignore [missing-import]
from src.processing.chunker import LegalChunker
# pyrefly: ignore [missing-import]
from src.vectorstore.store import VectorStore


# ── Registry of legal acts to ingest ─────────────────────────────────────
# Add new acts here as you obtain their PDFs.
# Each entry maps a filename pattern to its metadata.
LEGAL_ACTS = [
    {
        "filename": "Consumer Protection Act",
        "act_name": "Consumer Protection Act",
        "act_year": "2019",
        "category": "consumer",
    },
    {
        "filename": "It_Act_2000",
        "act_name": "Information Technology Act",
        "act_year": "2000",
        "category": "rti",
    },
    {
        "filename": "Digital Personal Data Protection Act",
        "act_name": "Digital Personal Data Protection Act",
        "act_year": "2023",
        "category": "property",  # Just assigning to property for the demo
    },
    {
        "filename": "constitution_of_india",
        "act_name": "Constitution of India",
        "act_year": "1950",
        "category": "general",
    },
]


def find_pdf_for_act(acts_dir: Path, filename_pattern: str) -> Path | None:
    """Find a PDF file matching the given pattern in the acts directory."""
    for pdf_file in acts_dir.glob("*.pdf"):
        if filename_pattern.lower() in pdf_file.stem.lower():
            return pdf_file
    return None


def ingest_all():
    """Main ingestion pipeline."""
    acts_dir = Path(settings.LEGAL_ACTS_DIR)
    acts_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Looking for legal act PDFs in: {acts_dir.absolute()}")

    # Initialize pipeline components
    embedding_manager = EmbeddingManager()
    vector_store = VectorStore()
    chunker = LegalChunker()
    pdf_loader = PDFLoader()  # Fallback for unrecognized PDFs

    total_added = 0
    total_files = 0

    # Process registered legal acts
    for act_info in LEGAL_ACTS:
        pdf_path = find_pdf_for_act(acts_dir, act_info["filename"])
        if not pdf_path:
            logger.warning(
                f"PDF not found for: {act_info['act_name']} "
                f"(looking for '*{act_info['filename']}*.pdf' in {acts_dir})"
            )
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {act_info['act_name']}, {act_info['act_year']}")
        logger.info(f"File: {pdf_path.name}")
        logger.info(f"{'='*60}")

        # Parse with legal-aware parser
        parser = LegalActParser(
            act_name=act_info["act_name"],
            act_year=act_info["act_year"],
            act_category=act_info["category"],
        )
        documents = parser.load_and_parse(str(pdf_path))

        if not documents:
            logger.warning(f"No content extracted from {pdf_path.name}")
            continue

        # Chunk the documents
        chunks = chunker.chunk_documents(documents)

        # Generate embeddings
        texts = [chunk.page_content for chunk in chunks]
        embeddings = embedding_manager.generate_embeddings(texts)

        # Store in vector database
        added = vector_store.add_documents(chunks, embeddings)
        total_added += added
        total_files += 1

    # Also process any unregistered PDFs with the generic loader
    all_pdfs = set(acts_dir.glob("*.pdf"))
    registered_pdfs = set()
    for act_info in LEGAL_ACTS:
        pdf = find_pdf_for_act(acts_dir, act_info["filename"])
        if pdf:
            registered_pdfs.add(pdf)

    unregistered = all_pdfs - registered_pdfs
    for pdf_path in unregistered:
        logger.info(f"\nProcessing unregistered PDF: {pdf_path.name}")
        documents = pdf_loader.load_single(str(pdf_path))
        if documents:
            chunks = chunker.chunk_documents(documents)
            texts = [c.page_content for c in chunks]
            embeddings = embedding_manager.generate_embeddings(texts)
            added = vector_store.add_documents(chunks, embeddings)
            total_added += added
            total_files += 1

    logger.success(f"\n{'='*60}")
    logger.success(f"INGESTION COMPLETE")
    logger.success(f"Files processed: {total_files}")
    logger.success(f"New documents added: {total_added}")
    logger.success(f"Total in vector store: {vector_store.count()}")
    logger.success(f"{'='*60}")


if __name__ == "__main__":
    ingest_all()
