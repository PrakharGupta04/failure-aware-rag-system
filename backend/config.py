"""
config.py - Central configuration for the Failure-Aware RAG System
All tunable parameters live here. Change these to experiment with the system.
"""

# ──────────────────────────────────────────────
# EMBEDDING MODELS
# Two models are supported. Switch via API or UI.
# ──────────────────────────────────────────────
EMBEDDING_MODELS = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "bge": "BAAI/bge-small-en",
}

# Default embedding model key (minilm or bge)
DEFAULT_EMBEDDING_MODEL = "minilm"

# ──────────────────────────────────────────────
# VECTOR STORES
# Supported: "faiss" or "chroma"
# ──────────────────────────────────────────────
VECTOR_STORES = ["faiss", "chroma"]
DEFAULT_VECTOR_STORE = "faiss"

# Where to persist Chroma data
CHROMA_PERSIST_DIR = "./data/chroma_db"

# Where to save FAISS index files
FAISS_INDEX_DIR = "./data/faiss_index"

# ──────────────────────────────────────────────
# CHUNKING
# Supported sizes (in tokens/words): 200, 500
# ──────────────────────────────────────────────
CHUNK_SIZES = [200, 500]
DEFAULT_CHUNK_SIZE = 200
CHUNK_OVERLAP = 50  # words of overlap between consecutive chunks

# ──────────────────────────────────────────────
# RETRIEVAL
# ──────────────────────────────────────────────
DEFAULT_TOP_K = 5  # how many chunks to retrieve

# ──────────────────────────────────────────────
# FAILURE DETECTION THRESHOLDS
# If max similarity < threshold → reject query
# ──────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.40  # below this → reject

# Confidence bands based on similarity score
CONFIDENCE_BANDS = {
    "High":   (0.70, 1.01),
    "Medium": (0.50, 0.70),
    "Low":    (0.40, 0.50),
}

# ──────────────────────────────────────────────
# LLM CONFIGURATION
# ──────────────────────────────────────────────

# Local model via Ollama (must be running: `ollama serve`)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "tinyllama"          # or "llama3"

# Optional: OpenAI-compatible API
OPENAI_API_KEY = ""               # set your key here or via env var
OPENAI_MODEL = "gpt-3.5-turbo"

# Which LLM to use by default: "ollama" or "openai"
DEFAULT_LLM = "ollama"

# Max tokens for the generated answer
LLM_MAX_TOKENS = 512

# ──────────────────────────────────────────────
# DATASET
# ──────────────────────────────────────────────
# "squad"     → loads SQuAD v1 passages (Hugging Face datasets)
# "wikipedia" → uses a small bundled Wikipedia sample
DATASET_SOURCE = "squad"          # change to "wikipedia" if needed
SQUAD_SPLIT = "train"
SQUAD_MAX_DOCS = 500              # limit for faster ingestion in demo

# ──────────────────────────────────────────────
# LOGGING / EVALUATION
# ──────────────────────────────────────────────
LOG_FILE = "./logs/eval_log.jsonl"
