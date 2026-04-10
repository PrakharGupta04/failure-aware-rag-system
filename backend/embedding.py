"""
embedding.py - Embedding model management
Loads sentence-transformer models (all-MiniLM-L6-v2 or bge-small-en)
and encodes text into dense vectors.

Models are cached after first load so hot-swapping is fast.
"""

import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODELS, DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# In-process model cache: model_key → SentenceTransformer instance
_MODEL_CACHE: Dict[str, SentenceTransformer] = {}


# ──────────────────────────────────────────────────────────────
# Model loading
# ──────────────────────────────────────────────────────────────

def get_model(model_key: str = DEFAULT_EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Return a (possibly cached) SentenceTransformer for *model_key*.

    Parameters
    ----------
    model_key : One of the keys in config.EMBEDDING_MODELS
                ("minilm" or "bge").

    Returns
    -------
    A loaded SentenceTransformer instance.
    """
    if model_key not in EMBEDDING_MODELS:
        raise ValueError(
            f"Unknown embedding model key: '{model_key}'. "
            f"Valid keys: {list(EMBEDDING_MODELS.keys())}"
        )

    if model_key not in _MODEL_CACHE:
        model_name = EMBEDDING_MODELS[model_key]
        logger.info("Loading embedding model '%s' (%s) …", model_key, model_name)
        _MODEL_CACHE[model_key] = SentenceTransformer(model_name)
        logger.info("Model '%s' loaded and cached.", model_key)

    return _MODEL_CACHE[model_key]


# ──────────────────────────────────────────────────────────────
# Encoding helpers
# ──────────────────────────────────────────────────────────────

def embed_texts(
    texts: List[str],
    model_key: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = 64,
    show_progress: bool = False,
) -> np.ndarray:
    """
    Encode a list of strings into an embedding matrix.

    Parameters
    ----------
    texts        : Strings to encode.
    model_key    : Which embedding model to use.
    batch_size   : Encoding batch size (tune for GPU/CPU RAM).
    show_progress: Show tqdm bar during encoding.

    Returns
    -------
    np.ndarray of shape (len(texts), embedding_dim), dtype float32.
    """
    model = get_model(model_key)
    logger.info("Encoding %d texts with model '%s' …", len(texts), model_key)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True,   # cosine similarity works well with L2-normalised vecs
    )

    logger.info("Encoding complete. Shape: %s", embeddings.shape)
    return embeddings.astype(np.float32)


def embed_query(
    query: str,
    model_key: str = DEFAULT_EMBEDDING_MODEL,
) -> np.ndarray:
    """
    Encode a single query string.

    Returns
    -------
    np.ndarray of shape (1, embedding_dim), dtype float32.
    """
    return embed_texts([query], model_key=model_key)


def get_embedding_dim(model_key: str = DEFAULT_EMBEDDING_MODEL) -> int:
    """Return the embedding dimension for the given model."""
    model = get_model(model_key)
    # Encode a dummy string to get the dimension
    dummy = model.encode(["hello"], convert_to_numpy=True)
    return dummy.shape[1]
