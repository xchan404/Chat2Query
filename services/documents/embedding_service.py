"""Embedding service — loads bge-m3 once as a singleton, batch-embeds chunks.

The model is ~2GB so it MUST be loaded once at startup, not per-request.
"""

import logging
import threading
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Module-level singleton lock and model reference
_model_lock = threading.Lock()
_model_instance = None
_model_name: str | None = None


def _get_model(model_name: str = "BAAI/bge-m3"):
    """Load the sentence-transformer model exactly once (thread-safe singleton)."""
    global _model_instance, _model_name

    if _model_instance is not None and _model_name == model_name:
        return _model_instance

    with _model_lock:
        # Double-check inside lock
        if _model_instance is not None and _model_name == model_name:
            return _model_instance

        logger.info(f"Loading embedding model '{model_name}' (this is a one-time operation)...")
        from sentence_transformers import SentenceTransformer
        _model_instance = SentenceTransformer(model_name, trust_remote_code=True)
        _model_name = model_name
        logger.info(f"Embedding model '{model_name}' loaded successfully")
        return _model_instance


def embed_texts(
    texts: list[str],
    model_name: str = "BAAI/bge-m3",
    batch_size: int = 32,
) -> list[list[float]]:
    """Embed a batch of texts using the singleton model.

    Returns a list of 1024-dimensional vectors (bge-m3 output dimension).
    """
    if not texts:
        return []

    model = _get_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,  # Cosine similarity friendly
    )

    # Convert to plain Python lists for database storage
    return [emb.tolist() for emb in embeddings]


def embed_single(text: str, model_name: str = "BAAI/bge-m3") -> list[float]:
    """Embed a single text string. Convenience wrapper."""
    result = embed_texts([text], model_name=model_name)
    return result[0] if result else []
