"""
Generic PDF Loader — fallback for non-legal documents.

EXTRACTED FROM: notebook/pdf_loader.ipynb (PDF loading code)

WHAT IT DOES:
  Loads all PDF files from a directory and returns them as LangChain Document
  objects. This is used for PDFs that don't follow the Indian legal act
  structure (e.g., general reference documents).

WHEN TO USE:
  - LegalActParser: For structured legal acts (Section 1, Section 2, ...)
  - PDFLoader: For everything else (reports, manuals, general docs)
"""

from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from loguru import logger


class PDFLoader:
    """Load PDF files from a directory with metadata enrichment.

    Usage:
        loader = PDFLoader()
        docs = loader.load_directory("data/pdfs/")
    """

    def load_directory(self, directory: str) -> List[Document]:
        """
        Process all PDF files in a directory recursively.

        Args:
            directory: Path to directory containing PDF files.

        Returns:
            List of Document objects, one per page of each PDF.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        pdf_files = list(dir_path.rglob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        all_documents = []
        for pdf_path in pdf_files:
            docs = self.load_single(str(pdf_path))
            all_documents.extend(docs)

        logger.success(f"Loaded {len(all_documents)} pages from {len(pdf_files)} PDFs")
        return all_documents

    def load_single(self, file_path: str) -> List[Document]:
        """
        Load a single PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of Document objects (one per page).
        """
        try:
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()

            # Enrich metadata with source file info
            source_file = Path(file_path).name
            for doc in documents:
                doc.metadata["source_file"] = source_file
                doc.metadata["file_type"] = "pdf"
                doc.metadata["category"] = "general"
                doc.metadata["act_name"] = source_file.replace(".pdf", "").replace("_", " ")

            logger.info(f"Loaded {len(documents)} pages from {source_file}")
            return documents
        except Exception as e:
            logger.error(f"Failed to load PDF '{file_path}': {e}")
            return []
