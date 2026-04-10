/**
 * api.js — Thin wrapper around the FastAPI backend.
 * All fetch logic lives here so components stay clean.
 */

const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/** Generic fetch helper with error handling */
async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** POST /api/query — run a RAG query */
export async function queryRAG({
  query,
  embeddingModel,
  vectorStore,
  topK,
  threshold,
  llmBackend,
}) {
  return request('/api/query', {
    method: 'POST',
    body: JSON.stringify({
      query,
      embedding_model: embeddingModel || undefined,
      vector_store:    vectorStore    || undefined,
      top_k:           topK           || undefined,
      threshold:       threshold      !== undefined ? threshold : undefined,
      llm_backend:     llmBackend     || undefined,
    }),
  });
}

/** POST /api/build-index — rebuild the vector index */
export async function buildIndex({ embeddingModel, vectorStore, chunkSize, forceRebuild }) {
  return request('/api/build-index', {
    method: 'POST',
    body: JSON.stringify({
      embedding_model: embeddingModel,
      vector_store:    vectorStore,
      chunk_size:      chunkSize,
      force_rebuild:   forceRebuild,
    }),
  });
}

/** GET /api/stats — evaluation statistics */
export async function fetchStats() {
  return request('/api/stats');
}

/** GET /api/config — available options + current settings */
export async function fetchConfig() {
  return request('/api/config');
}

/** GET /health — is the server up? */
export async function checkHealth() {
  return request('/health');
}
