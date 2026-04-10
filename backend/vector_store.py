"""
vector_store.py - Unified vector store interface
Supports two backends:
  • FAISS  — fast in-memory / file-based index (no server needed)
  • Chroma — persistent, document-aware vector DB

Both backends expose the same API:
  store.add(chunks, embeddings)
  store.search(query_embedding, top_k) → (chunks, scores)
  store.save() / store.load()
"""

import os
import logging
import pickle
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any

import numpy as np
from config import FAISS_INDEX_DIR, CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# Abstract base class
# ════════════════════════════════════════════════════════════════

class BaseVectorStore(ABC):
    """Common interface every vector store backend must implement."""

    @abstractmethod
    def add(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        """Index *chunks* with their pre-computed *embeddings*."""

    @abstractmethod
    def search(
        self, query_embedding: np.ndarray, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        Return the top-k most similar chunks and their similarity scores.

        Returns
        -------
        (chunks, scores)
          chunks : list of chunk dicts (same structure as ingested)
          scores : float list, higher is better, range ≈ [0, 1]
        """

    @abstractmethod
    def save(self) -> None:
        """Persist the index to disk."""

    @abstractmethod
    def load(self) -> bool:
        """Load a previously saved index. Returns True if successful."""

    @property
    @abstractmethod
    def count(self) -> int:
        """Number of stored vectors."""


# ════════════════════════════════════════════════════════════════
# FAISS backend
# ════════════════════════════════════════════════════════════════

class FAISSStore(BaseVectorStore):
    """
    FAISS flat inner-product index.
    Because embeddings are L2-normalised, inner product ≡ cosine similarity.
    """

    _INDEX_FILE = "index.faiss"
    _META_FILE  = "meta.pkl"

    def __init__(self, embedding_dim: int, model_key: str = "minilm"):
        self.embedding_dim = embedding_dim
        self.model_key = model_key
        self._index = None      # faiss.IndexFlatIP
        self._chunks: List[Dict[str, Any]] = []
        self._save_dir = os.path.join(FAISS_INDEX_DIR, model_key)

    # ── internal helpers ──────────────────────────────────────

    def _build_index(self) -> None:
        import faiss
        self._index = faiss.IndexFlatIP(self.embedding_dim)

    # ── public API ────────────────────────────────────────────

    def add(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        if self._index is None:
            self._build_index()

        self._index.add(embeddings)
        self._chunks.extend(chunks)
        logger.info("[FAISS] Added %d vectors. Total: %d.", len(chunks), self._index.ntotal)

    def search(
        self, query_embedding: np.ndarray, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        if self._index is None or self._index.ntotal == 0:
            return [], []

        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query_embedding, k)

        # Flatten from shape (1, k) → (k,)
        scores = scores[0].tolist()
        indices = indices[0].tolist()

        result_chunks = []
        result_scores = []
        for idx, score in zip(indices, scores):
            if idx == -1:       # FAISS sentinel for "not enough results"
                continue
            result_chunks.append(self._chunks[idx])
            result_scores.append(float(score))

        return result_chunks, result_scores

    def save(self) -> None:
        import faiss
        os.makedirs(self._save_dir, exist_ok=True)
        faiss.write_index(
            self._index, os.path.join(self._save_dir, self._INDEX_FILE)
        )
        with open(os.path.join(self._save_dir, self._META_FILE), "wb") as f:
            pickle.dump(self._chunks, f)
        logger.info("[FAISS] Index saved to '%s'.", self._save_dir)

    def load(self) -> bool:
        import faiss
        idx_path  = os.path.join(self._save_dir, self._INDEX_FILE)
        meta_path = os.path.join(self._save_dir, self._META_FILE)
        if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
            return False
        self._index = faiss.read_index(idx_path)
        with open(meta_path, "rb") as f:
            self._chunks = pickle.load(f)
        logger.info("[FAISS] Loaded index with %d vectors.", self._index.ntotal)
        return True

    @property
    def count(self) -> int:
        return self._index.ntotal if self._index else 0


# ════════════════════════════════════════════════════════════════
# Chroma backend
# ════════════════════════════════════════════════════════════════

class ChromaStore(BaseVectorStore):
    """
    ChromaDB persistent vector store.
    Uses a cosine-distance metric; scores are converted to similarities.
    """

    def __init__(self, model_key: str = "minilm"):
        self.model_key = model_key
        self._collection_name = f"rag_{model_key}"
        self._client = None
        self._collection = None
        self._chunks: Dict[str, Dict[str, Any]] = {}   # id → chunk
        self._init_client()

    # ── internal helpers ──────────────────────────────────────

    def _init_client(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
            persist_dir = os.path.join(CHROMA_PERSIST_DIR, self.model_key)
            os.makedirs(persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "[Chroma] Connected. Collection '%s' has %d items.",
                self._collection_name, self._collection.count(),
            )
        except ImportError:
            raise ImportError(
                "chromadb is required for the Chroma backend. "
                "Run:  pip install chromadb"
            )

    # ── public API ────────────────────────────────────────────

    def add(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> None:
        ids        = [f"chunk_{i}_{id(c)}" for i, c in enumerate(chunks)]
        documents  = [c["text"] for c in chunks]
        metadatas  = [
            {k: str(v) for k, v in c.items() if k != "text"}
            for c in chunks
        ]
        self._collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
        )
        # keep a local copy for reconstruction
        for cid, chunk in zip(ids, chunks):
            self._chunks[cid] = chunk
        logger.info("[Chroma] Added %d vectors. Total: %d.", len(chunks), self.count)

    def search(
        self, query_embedding: np.ndarray, top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        if self.count == 0:
            return [], []

        k = min(top_k, self.count)
        results = self._collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        chunks: List[Dict[str, Any]] = []
        scores: List[float] = []

        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Chroma returns cosine distance ∈ [0, 2]; convert to similarity ∈ [0, 1]
            similarity = max(0.0, 1.0 - dist)
            chunk = {"text": doc}
            chunk.update(meta)
            chunks.append(chunk)
            scores.append(similarity)

        return chunks, scores

    def save(self) -> None:
        # Chroma PersistentClient auto-saves; nothing extra needed.
        logger.info("[Chroma] Data is automatically persisted.")

    def load(self) -> bool:
        # Client is initialised in __init__; data is already loaded.
        return self.count > 0

    @property
    def count(self) -> int:
        try:
            return self._collection.count()
        except Exception:
            return 0


# ════════════════════════════════════════════════════════════════
# Factory function
# ════════════════════════════════════════════════════════════════

def get_vector_store(
    backend: str = "faiss",
    embedding_dim: int = 384,
    model_key: str = "minilm",
) -> BaseVectorStore:
    """
    Return the requested vector store backend.

    Parameters
    ----------
    backend       : "faiss" or "chroma"
    embedding_dim : Dimensionality of the embedding vectors (FAISS only).
    model_key     : Embedding model key used to namespace the index files.
    """
    backend = backend.lower()
    if backend == "faiss":
        return FAISSStore(embedding_dim=embedding_dim, model_key=model_key)
    elif backend == "chroma":
        return ChromaStore(model_key=model_key)
    else:
        raise ValueError(
            f"Unknown vector store backend: '{backend}'. "
            f"Choose 'faiss' or 'chroma'."
        )
