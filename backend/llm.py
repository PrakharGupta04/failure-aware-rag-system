
import logging
import os
from typing import List, Dict, Any

import requests

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    DEFAULT_LLM,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Prompt builder  (shared by both backends)
# ──────────────────────────────────────────────────────────────

def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Build a RAG prompt that grounds the model in retrieved context.

    The prompt explicitly instructs the model to:
      • Use only the provided context.
      • Say "I don't know" if the context is insufficient.
    """
    # Join chunk texts separated by a clear delimiter
    context_text = "\n\n---\n\n".join(
        [c.get("text", "") for c in context_chunks]
    )

    prompt = (
        "You are a knowledgeable assistant. Answer the question below using ONLY "
        "the provided context. If the context does not contain enough information "
        "to answer confidently, say: 'I don't have enough information to answer this.'\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"QUESTION: {query}\n\n"
        "ANSWER:"
    )
    return prompt


# ════════════════════════════════════════════════════════════════
# Ollama backend (local)
# ════════════════════════════════════════════════════════════════

def _generate_ollama(prompt: str) -> str:
    """
    Call a locally running Ollama server.
    Start Ollama with:  ollama serve
    Pull a model with:  ollama pull mistral
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": LLM_MAX_TOKENS,
            "temperature": 0.2,   # low temperature → more factual
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except requests.exceptions.ConnectionError:
        error_msg = (
            f"Could not connect to Ollama at {OLLAMA_BASE_URL}. "
            "Is the server running? Try: `ollama serve`"
        )
        logger.error(error_msg)
        return f"[LLM ERROR] {error_msg}"
    except requests.exceptions.RequestException as e:
        logger.error("Ollama request failed: %s", e)
        return f"[LLM ERROR] Ollama request failed: {e}"


# ════════════════════════════════════════════════════════════════
# OpenAI backend (cloud)
# ════════════════════════════════════════════════════════════════

def _generate_openai(prompt: str) -> str:
    """
    Call the OpenAI Chat Completions API.
    Requires OPENAI_API_KEY in config.py or the OPENAI_API_KEY env var.
    """
    api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "[LLM ERROR] No OpenAI API key provided. Set OPENAI_API_KEY in config.py."

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role":    "system",
                    "content": (
                        "You are a factual assistant. Answer strictly from the "
                        "provided context. If the context is insufficient, say so."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=LLM_MAX_TOKENS,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        return "[LLM ERROR] openai package not installed. Run: pip install openai"
    except Exception as e:
        logger.error("OpenAI request failed: %s", e)
        return f"[LLM ERROR] OpenAI request failed: {e}"


# ════════════════════════════════════════════════════════════════
# Public entry point
# ════════════════════════════════════════════════════════════════

def generate_answer(
    query: str,
    context_chunks: List[Dict[str, Any]],
    llm_backend: str = DEFAULT_LLM,
) -> str:
    """
    Generate an answer from the LLM, grounded in *context_chunks*.

    Parameters
    ----------
    query          : The user's question.
    context_chunks : Retrieved chunks passed as context.
    llm_backend    : "ollama" or "openai".

    Returns
    -------
    str  — The generated answer text (may begin with "[LLM ERROR] …" on failure).
    """
    prompt = build_prompt(query, context_chunks)
    logger.info("Generating answer via '%s' …", llm_backend)

    if llm_backend == "ollama":
        return _generate_ollama(prompt)
    elif llm_backend == "openai":
        return _generate_openai(prompt)
    else:
        raise ValueError(
            f"Unknown llm_backend: '{llm_backend}'. Choose 'ollama' or 'openai'."
        )
