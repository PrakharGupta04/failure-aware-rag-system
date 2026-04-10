"""
main.py - FastAPI entry point for the Failure-Aware RAG System

Endpoints:
  POST /api/query          — main QA endpoint
  POST /api/build-index    — (re-)build the vector index
  GET  /api/stats          — evaluation statistics
  GET  /api/config         — current configuration options
  GET  /health             — health check
"""

import logging
import os
import sys

# ── make sure sibling modules are importable ─────────────────
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from config import (
    EMBEDDING_MODELS,
    VECTOR_STORES,
    CHUNK_SIZES,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_VECTOR_STORE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_TOP_K,
    DEFAULT_LLM,
    SIMILARITY_THRESHOLD,
)
from retriever import build_index, retrieve, format_sources
from evaluator import (
    should_reject,
    build_rejection,
    build_success,
    log_query,
    get_stats,
)
from llm import generate_answer

# ──────────────────────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# ──────────────────────────────────────────────────────────────
# Application state — shared across requests
# ──────────────────────────────────────────────────────────────
app_state: Dict[str, Any] = {
    "store":           None,   # active BaseVectorStore
    "all_chunks":      [],     # flat list of all indexed chunks
    "embedding_model": DEFAULT_EMBEDDING_MODEL,
    "vector_store":    DEFAULT_VECTOR_STORE,
    "chunk_size":      DEFAULT_CHUNK_SIZE,
    "threshold":       SIMILARITY_THRESHOLD,
    "top_k":           DEFAULT_TOP_K,
    "llm_backend":     DEFAULT_LLM,
    "index_ready":     False,
}


# ──────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Failure-Aware RAG System",
    description=(
        "A RAG-based QA system that intelligently detects "
        "retrieval failures and rejects low-confidence queries."
    ),
    version="1.0.0",
)

# Allow the React dev server (port 3000) and production builds
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Startup: build index automatically on first launch
# ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("Server starting — building initial index …")
    try:
        store, chunks = build_index(
            embedding_model=app_state["embedding_model"],
            vector_store_backend=app_state["vector_store"],
            chunk_size=app_state["chunk_size"],
        )
        app_state["store"]       = store
        app_state["all_chunks"]  = chunks
        app_state["index_ready"] = True
        logger.info("Index ready (%d vectors).", store.count)
    except Exception as e:
        logger.error("Index build failed on startup: %s", e)
        app_state["index_ready"] = False


# ════════════════════════════════════════════════════════════════
# Request / Response models (Pydantic)
# ════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The user's question")
    embedding_model: Optional[str] = Field(
        None, description="Override: 'minilm' or 'bge'"
    )
    vector_store: Optional[str] = Field(
        None, description="Override: 'faiss' or 'chroma'"
    )
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Rejection threshold")
    llm_backend: Optional[str] = Field(None, description="'ollama' or 'openai'")


class BuildIndexRequest(BaseModel):
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    vector_store:    str = DEFAULT_VECTOR_STORE
    chunk_size:      int = DEFAULT_CHUNK_SIZE
    force_rebuild:   bool = False


# ════════════════════════════════════════════════════════════════
# Endpoints
# ════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Simple health probe."""
    return {
        "status":      "ok",
        "index_ready": app_state["index_ready"],
        "num_vectors": app_state["store"].count if app_state["store"] else 0,
    }


@app.get("/api/config")
async def get_config():
    """Return the available configuration options and current defaults."""
    return {
        "available_embedding_models": list(EMBEDDING_MODELS.keys()),
        "available_vector_stores":    VECTOR_STORES,
        "available_chunk_sizes":      CHUNK_SIZES,
        "current": {
            "embedding_model": app_state["embedding_model"],
            "vector_store":    app_state["vector_store"],
            "chunk_size":      app_state["chunk_size"],
            "threshold":       app_state["threshold"],
            "top_k":           app_state["top_k"],
            "llm_backend":     app_state["llm_backend"],
        },
    }


@app.post("/api/build-index")
async def api_build_index(req: BuildIndexRequest):
    """
    (Re-)build the vector index with the specified configuration.
    This may take 30–120 seconds on first run (downloading embeddings).
    """
    if req.embedding_model not in EMBEDDING_MODELS:
        raise HTTPException(400, f"Unknown embedding_model: '{req.embedding_model}'")
    if req.vector_store not in VECTOR_STORES:
        raise HTTPException(400, f"Unknown vector_store: '{req.vector_store}'")
    if req.chunk_size not in CHUNK_SIZES:
        raise HTTPException(400, f"chunk_size must be one of {CHUNK_SIZES}")

    logger.info(
        "Rebuilding index: model=%s, store=%s, chunk_size=%d, force=%s",
        req.embedding_model, req.vector_store, req.chunk_size, req.force_rebuild,
    )

    try:
        store, chunks = build_index(
            embedding_model=req.embedding_model,
            vector_store_backend=req.vector_store,
            chunk_size=req.chunk_size,
            force_rebuild=req.force_rebuild,
        )
    except Exception as e:
        logger.exception("Index build error")
        raise HTTPException(500, f"Index build failed: {e}")

    # Update shared state
    app_state["store"]           = store
    app_state["all_chunks"]      = chunks
    app_state["embedding_model"] = req.embedding_model
    app_state["vector_store"]    = req.vector_store
    app_state["chunk_size"]      = req.chunk_size
    app_state["index_ready"]     = True

    return {
        "status":        "ok",
        "num_vectors":   store.count,
        "embedding_model": req.embedding_model,
        "vector_store":  req.vector_store,
        "chunk_size":    req.chunk_size,
    }


@app.post("/api/query")
async def api_query(req: QueryRequest):
    """
    Main QA endpoint.

    Flow:
      1. Validate index is ready.
      2. Retrieve top-k chunks.
      3. Failure detection → reject or proceed.
      4. If proceeding → LLM generation.
      5. Return structured response.
    """
    if not app_state["index_ready"] or app_state["store"] is None:
        raise HTTPException(
            503,
            "Index not ready. Call POST /api/build-index first or wait for startup.",
        )

    # ── Resolve per-request overrides ────────────────────────
    emb_model   = req.embedding_model or app_state["embedding_model"]
    vs_backend  = req.vector_store    or app_state["vector_store"]
    top_k       = req.top_k           or app_state["top_k"]
    threshold   = req.threshold       if req.threshold is not None else app_state["threshold"]
    llm_backend = req.llm_backend     or app_state["llm_backend"]

    # If the user changed embedding model or vector store, we need a different store.
    # For simplicity, we only use the in-memory store unless it matches.
    # A production system would maintain a store-per-config cache.
    store = app_state["store"]

    # ── Retrieve ──────────────────────────────────────────────
    try:
        chunks, scores = retrieve(
            query=req.query,
            store=store,
            top_k=top_k,
            embedding_model=emb_model,
        )
    except Exception as e:
        logger.exception("Retrieval error")
        raise HTTPException(500, f"Retrieval failed: {e}")

    # ── Failure detection ────────────────────────────────────
    if should_reject(scores, threshold=threshold):
        log_query(req.query, "rejected", scores)
        return build_rejection(req.query, scores, threshold=threshold)

    # ── Format sources ────────────────────────────────────────
    sources = format_sources(chunks, scores)

    # ── LLM generation ───────────────────────────────────────
    try:
        answer = generate_answer(
            query=req.query,
            context_chunks=chunks,
            llm_backend=llm_backend,
        )
    except Exception as e:
        logger.exception("LLM generation error")
        answer = f"[Generation failed: {e}]"

    # ── Build and log response ────────────────────────────────
    response = build_success(req.query, answer, scores, sources)
    log_query(req.query, "answered", scores, answer)
    return response


@app.get("/api/stats")
async def api_stats():
    """Return evaluation statistics collected since server start."""
    return get_stats()


# ──────────────────────────────────────────────────────────────
# Run directly with:  python main.py
# (Production: uvicorn main:app --host 0.0.0.0 --port 8000)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
