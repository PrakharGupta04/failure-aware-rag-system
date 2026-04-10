"""
retriever.py - Retrieval module
Given a user query, encodes it and fetches the top-k most
relevant chunks from the chosen vector store.

Also orchestrates the full build (ingest → chunk → embed → index)
so that main.py only needs to call one function.
"""

import logging
from typing import List, Dict, Any, Tuple

import numpy as np

from config import (
    DEFAULT_TOP_K,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_VECTOR_STORE,
    DEFAULT_CHUNK_SIZE,
)
from ingestion import load_documents
from chunking import chunk_documents
from embedding import embed_texts, embed_query, get_embedding_dim
from vector_store import get_vector_store, BaseVectorStore

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Build the index (one-time setup)
# ──────────────────────────────────────────────────────────────

def build_index(
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    vector_store_backend: str = DEFAULT_VECTOR_STORE,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    force_rebuild: bool = False,
) -> Tuple[BaseVectorStore, List[Dict[str, Any]]]:
    """
    Full pipeline: load → chunk → embed → index.

    If a saved index already exists for this config, it is loaded
    instead of being rebuilt (unless *force_rebuild* is True).

    Parameters
    ----------
    embedding_model      : Key from config.EMBEDDING_MODELS.
    vector_store_backend : "faiss" or "chroma".
    chunk_size           : Words per chunk (200 or 500).
    force_rebuild        : Skip loading a cached index.

    Returns
    -------
    (store, all_chunks)
      store      : Populated BaseVectorStore instance.
      all_chunks : The flat list of chunk dicts that were indexed.
    """
    dim   = get_embedding_dim(embedding_model)
    store = get_vector_store(vector_store_backend, embedding_dim=dim,
                             model_key=embedding_model)

    # ── Try loading existing index ───────────────────────────
    if not force_rebuild and store.load():
        logger.info(
            "Loaded existing index: backend=%s, model=%s, chunks=%d.",
            vector_store_backend, embedding_model, store.count,
        )
        # We don't have the chunks list in memory after a reload,
        # so rebuild it for metadata purposes (no re-embedding needed).
        documents  = load_documents()
        all_chunks = chunk_documents(documents, chunk_size=chunk_size)
        return store, all_chunks

    # ── Fresh build ──────────────────────────────────────────
    logger.info("Building fresh index (backend=%s, model=%s, chunk_size=%d) …",
                vector_store_backend, embedding_model, chunk_size)

    documents  = load_documents()
    all_chunks = chunk_documents(documents, chunk_size=chunk_size)

    texts      = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts, model_key=embedding_model, show_progress=True)

    store.add(all_chunks, embeddings)
    store.save()

    logger.info("Index built and saved. Total vectors: %d.", store.count)
    return store, all_chunks


# ──────────────────────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    store: BaseVectorStore,
    top_k: int = DEFAULT_TOP_K,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Encode *query* and retrieve the top-k chunks from *store*.

    Parameters
    ----------
    query           : The user's question string.
    store           : A populated BaseVectorStore.
    top_k           : Number of results to return.
    embedding_model : Must match the model used at index time.

    Returns
    -------
    (chunks, scores)
      chunks : List of chunk dicts, ordered by descending similarity.
      scores : Corresponding float similarity scores (0-1 range).
    """
    query_emb = embed_query(query, model_key=embedding_model)
    chunks, scores = store.search(query_emb, top_k=top_k)

    logger.info(
        "Retrieved %d chunks for query '%s…'. Top score: %.4f.",
        len(chunks),
        query[:60],
        scores[0] if scores else 0.0,
    )
    return chunks, scores


# ──────────────────────────────────────────────────────────────
# Convenience: format sources for the API response
# ──────────────────────────────────────────────────────────────

def format_sources(chunks: List[Dict[str, Any]], scores: List[float]) -> List[Dict[str, Any]]:
    """
    Zip chunks and scores into clean source dicts for the response payload.
    """
    sources = []
    for chunk, score in zip(chunks, scores):
        sources.append({
            "text":       chunk.get("text", ""),
            "preview":    chunk.get("preview", chunk.get("text", "")[:120]),
            "doc_id":     chunk.get("doc_id", -1),
            "chunk_id":   chunk.get("chunk_id", -1),
            "score":      round(score, 4),
        })
    return sources
