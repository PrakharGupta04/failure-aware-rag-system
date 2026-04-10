"""
ingestion.py - Custom domain dataset for Technical Documentation Assistant
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────

def load_documents() -> List[str]:
    """
    Load domain-specific documents for RAG system.
    Returns a list of clean technical knowledge texts.
    """

    logger.info("Loading custom technical documentation dataset...")

    documents = [

        # ── Machine Learning Basics ──
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data without explicit programming.",
        "Supervised learning is a type of machine learning where models are trained using labeled data.",
        "Unsupervised learning identifies patterns in data without labeled outputs.",
        "Reinforcement learning is a technique where an agent learns by interacting with an environment and receiving rewards.",

        # ── Neural Networks ──
        "A neural network is a computational model inspired by the human brain consisting of layers of interconnected nodes.",
        "Deep learning is a subset of machine learning that uses multi-layer neural networks to model complex patterns.",
        "Overfitting occurs when a model learns noise in training data instead of the actual pattern, reducing performance on new data.",

        # ── Programming & Tools ──
        "Python is a high-level programming language widely used for machine learning and data science.",
        "NumPy is a Python library used for numerical computations and array operations.",
        "Pandas is a library used for data manipulation and analysis in Python.",
        "Scikit-learn is a machine learning library used for building models such as regression and classification.",
        "TensorFlow is an open-source deep learning framework developed by Google.",
        "PyTorch is a deep learning library widely used in research and production.",

        # ── Web & Backend ──
        "An API allows communication between different software systems.",
        "FastAPI is a modern Python web framework used to build high-performance APIs.",
        "REST APIs follow a stateless architecture for communication over HTTP.",

        # ── RAG Concepts ──
        "Retrieval-Augmented Generation combines document retrieval with language generation to improve accuracy.",
        "Vector databases store embeddings for efficient similarity-based retrieval.",
        "Embeddings are numerical representations of text used to measure semantic similarity.",
        "FAISS is a library used for efficient similarity search and clustering of dense vectors.",

    ]

    logger.info("Loaded %d domain-specific documents.", len(documents))
    return documents