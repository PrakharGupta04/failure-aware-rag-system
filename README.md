# Failure-Aware RAG System

A production-grade Retrieval-Augmented Generation (RAG) system that **intelligently detects retrieval failures** and rejects queries when insufficient information is available — instead of hallucinating an answer.

---

## Architecture Overview

```
User Query
    │
    ▼
[FastAPI Backend]
    │
    ├─ Ingestion   ← SQuAD / Wikipedia dataset
    ├─ Chunking    ← 200 or 500 word windows
    ├─ Embedding   ← MiniLM-L6 or BGE-small
    ├─ Vector Store← FAISS or ChromaDB
    │
    ├─ Retrieval   ← top-k chunks + similarity scores
    │
    ├─ Evaluator   ← FAILURE DETECTION
    │      ├─ score < threshold → REJECT (return warning)
    │      └─ score ≥ threshold → PASS → LLM
    │
    └─ LLM         ← Ollama (local) or OpenAI
           │
           ▼
    Structured JSON Response
    {status, answer, confidence, sources, rejection}
```

---

## Project Structure

```
rag_system/
├── backend/
│   ├── config.py        ← ALL tunable parameters
│   ├── ingestion.py     ← Dataset loading (SQuAD / Wikipedia)
│   ├── chunking.py      ← Word-based overlapping chunker
│   ├── embedding.py     ← SentenceTransformer model manager
│   ├── vector_store.py  ← FAISS + Chroma backends
│   ├── retriever.py     ← Build index + retrieve chunks
│   ├── evaluator.py     ← Failure detection + confidence + logging
│   ├── llm.py           ← Ollama + OpenAI generation
│   ├── main.py          ← FastAPI app (entry point)
│   └── requirements.txt
│
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── App.jsx              ← Root component
│   │   ├── api.js               ← Backend HTTP calls
│   │   ├── index.js / index.css ← Entry point + global styles
│   │   └── components/
│   │       ├── ConfidenceBadge.jsx
│   │       ├── SourcesPanel.jsx
│   │       ├── LoadingAnimation.jsx
│   │       ├── SettingsPanel.jsx
│   │       ├── IndexBuilder.jsx
│   │       ├── ResultPanel.jsx
│   │       └── StatsPanel.jsx
│   └── package.json
│
├── data/          ← FAISS + Chroma index files (auto-created)
├── logs/          ← eval_log.jsonl (auto-created)
└── README.md
```

---

## Step-by-Step Setup

### Prerequisites

| Tool        | Version  | Notes                          |
|-------------|----------|--------------------------------|
| Python      | ≥ 3.10   | Use a virtual environment      |
| Node.js     | ≥ 18     | For the React frontend         |
| npm         | ≥ 9      | Comes with Node                |
| Ollama      | latest   | Optional — for local LLM       |

---

### Step 1 — Clone / Extract the project

```bash
# If you downloaded a zip, extract it.
# The backend and frontend folders should be at the root.
cd rag_system
```

---

### Step 2 — Backend setup

```bash
cd backend

# Create a virtual environment
python -m venv .venv

# Activate it
# macOS / Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Note on PyTorch**: `requirements.txt` installs CPU PyTorch by default.
> For GPU support replace `torch>=2.0.0` with `torch>=2.0.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118`.

---

### Step 3 — (Optional) Set up Ollama for local LLM

```bash
# Install Ollama from https://ollama.com
# Then pull a model:
ollama pull mistral      # recommended (~4 GB)
# OR
ollama pull llama3       # larger (~8 GB)

# Start the server (leave this running in a separate terminal):
ollama serve
```

If you prefer OpenAI, open `backend/config.py` and set:
```python
OPENAI_API_KEY = "sk-..."
DEFAULT_LLM    = "openai"
```

---

### Step 4 — Configure the system (optional)

Edit `backend/config.py` to adjust:

```python
DATASET_SOURCE       = "squad"    # "squad" or "wikipedia"
SQUAD_MAX_DOCS       = 500        # increase for better coverage
SIMILARITY_THRESHOLD = 0.40       # lower → more permissive, higher → stricter
DEFAULT_CHUNK_SIZE   = 200        # 200 or 500 words
DEFAULT_EMBEDDING_MODEL = "minilm" # "minilm" or "bge"
DEFAULT_VECTOR_STORE = "faiss"    # "faiss" or "chroma"
DEFAULT_LLM          = "ollama"   # "ollama" or "openai"
```

---

### Step 5 — Start the backend

```bash
# From the backend/ directory (with venv active):
python main.py

# Or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

On first run the server will:
1. Download the SQuAD dataset (~35 MB) from Hugging Face
2. Download the embedding model (~90 MB)
3. Chunk, embed, and index ~500 passages
4. Save the index to `data/`

**This takes 1–5 minutes on first run. Subsequent starts load from cache in seconds.**

You can verify the backend is running:
```bash
curl http://localhost:8000/health
# → {"status":"ok","index_ready":true,"num_vectors":...}
```

---

### Step 6 — Start the frontend

Open a **new terminal**:

```bash
cd rag_system/frontend

# Install Node dependencies
npm install

# Start the dev server
npm start
```

The browser opens at **http://localhost:3000** automatically.

---

### Step 7 — Use the system

1. **Ask a question** in the text box — e.g., _"What is machine learning?"_
2. Hit **Submit** or press `Cmd+Enter`
3. View the result:
   - ✅ **Green card** = answer generated with confidence badge + sources
   - 🔴 **Red card** = query rejected with reason and similarity score

**Experiment with settings** (expand the Settings panel):
- Switch embedding model (MiniLM ↔ BGE)
- Switch vector store (FAISS ↔ Chroma)
- Adjust similarity threshold
- Change chunk size

After changing embedding model or chunk size, click **Rebuild Index** so the new settings take effect.

---

## API Reference

All endpoints are at `http://localhost:8000`.

### `POST /api/query`

```json
{
  "query": "What is artificial intelligence?",
  "embedding_model": "minilm",
  "vector_store": "faiss",
  "top_k": 5,
  "threshold": 0.40,
  "llm_backend": "ollama"
}
```

**Response (answered):**
```json
{
  "status": "answered",
  "answer": "Artificial intelligence is...",
  "confidence": "High",
  "sources": [{"text": "...", "score": 0.81, "doc_id": 3, "chunk_id": 1}],
  "rejection": null,
  "meta": {"max_similarity_score": 0.81}
}
```

**Response (rejected):**
```json
{
  "status": "rejected",
  "answer": null,
  "confidence": null,
  "sources": [],
  "rejection": {
    "message": "I couldn't find sufficiently relevant information...",
    "reason": "Max similarity (0.23) below threshold 0.40",
    "max_similarity_score": 0.23,
    "threshold": 0.40
  }
}
```

### `POST /api/build-index`

Triggers a rebuild of the vector index.

```json
{
  "embedding_model": "bge",
  "vector_store": "chroma",
  "chunk_size": 500,
  "force_rebuild": true
}
```

### `GET /api/stats`

Returns session-level evaluation statistics.

### `GET /api/config`

Returns available options and current configuration.

### `GET /health`

Health check + index status.

---

## Failure Detection Logic

The heart of the system lives in `evaluator.py`:

```
max_score = max(similarity scores for retrieved chunks)

if max_score < SIMILARITY_THRESHOLD:
    → REJECT (return warning + score + reason)
else:
    confidence = "High"   if max_score ≥ 0.70
               = "Medium" if max_score ≥ 0.50
               = "Low"    if max_score ≥ 0.40
    → PASS to LLM → generate answer
```

Every query is logged to `logs/eval_log.jsonl` for analysis.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Activate the virtual environment |
| `Cannot connect to Ollama` | Run `ollama serve` in a separate terminal |
| Index build hangs | Normal on first run — datasets + model are downloading |
| Chroma error on Windows | Try `pip install chromadb --upgrade` |
| Frontend shows "Backend Offline" | Start the backend first (`python main.py`) |
| All queries rejected | Lower `SIMILARITY_THRESHOLD` in `config.py` (try 0.25) |
| `faiss-cpu` install fails | Try `pip install faiss-cpu --no-build-isolation` |

---

## Evaluation Log

Every query is appended to `logs/eval_log.jsonl`:

```json
{"timestamp":"2024-...","query":"What is AI?","outcome":"answered","max_score":0.81,"all_scores":[0.81,0.76,...],"answer_len":312}
{"timestamp":"2024-...","query":"Capital of Mars?","outcome":"rejected","max_score":0.18,"all_scores":[0.18,0.15,...],"answer_len":0}
```

You can analyze this with pandas, jq, or any JSON tool.

---

## License

MIT — free to use and modify.
