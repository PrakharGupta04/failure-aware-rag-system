"""
chunking.py - Text chunking module
Splits a list of documents into smaller, overlapping chunks.

Two chunk sizes are supported (configurable in config.py):
  • 200 tokens/words  — fine-grained retrieval
  • 500 tokens/words  — broader context retrieval

We use a simple word-based splitter so there are no tokenizer
dependencies at ingestion time.
"""

import logging
from typing import List, Dict, Any
from config import CHUNK_OVERLAP

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Data structure for a chunk
# ──────────────────────────────────────────────────────────────

def make_chunk(text: str, doc_id: int, chunk_id: int, chunk_size: int) -> Dict[str, Any]:
    """Return a standardised chunk dict."""
    return {
        "text": text,
        "doc_id": doc_id,       # index of the source document
        "chunk_id": chunk_id,   # sequential chunk index within the doc
        "chunk_size": chunk_size,
        # A short preview useful for displaying in the UI
        "preview": text[:120] + ("…" if len(text) > 120 else ""),
    }


# ──────────────────────────────────────────────────────────────
# Core splitter
# ──────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 200) -> List[str]:
    """
    Split *text* into overlapping word windows.

    Parameters
    ----------
    text       : The raw document string.
    chunk_size : Number of words per chunk.

    Returns
    -------
    List of chunk strings.
    """
    words = text.split()
    if not words:
        return []

    overlap = min(CHUNK_OVERLAP, chunk_size // 4)   # cap overlap at 25 %
    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        # Move window forward; subtract overlap so consecutive chunks share context
        start += chunk_size - overlap

    return chunks


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def chunk_documents(documents: List[str], chunk_size: int = 200) -> List[Dict[str, Any]]:
    """
    Chunk all documents and return a flat list of chunk dicts.

    Parameters
    ----------
    documents  : List of raw document strings from ingestion.
    chunk_size : Target words per chunk (200 or 500 recommended).

    Returns
    -------
    List of chunk dicts, each containing 'text', 'doc_id', 'chunk_id', etc.
    """
    if chunk_size not in (200, 500):
        logger.warning(
            "chunk_size=%d is non-standard. Supported values: 200, 500.", chunk_size
        )

    all_chunks: List[Dict[str, Any]] = []

    for doc_id, doc_text in enumerate(documents):
        raw_chunks = chunk_text(doc_text, chunk_size=chunk_size)
        for chunk_id, chunk_str in enumerate(raw_chunks):
            chunk = make_chunk(
                text=chunk_str,
                doc_id=doc_id,
                chunk_id=chunk_id,
                chunk_size=chunk_size,
            )
            all_chunks.append(chunk)

    logger.info(
        "Chunked %d documents → %d chunks  (size=%d, overlap=%d).",
        len(documents), len(all_chunks), chunk_size, CHUNK_OVERLAP,
    )
    return all_chunks
