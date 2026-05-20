"""
Embedding utilities for semantic search.
"""

import numpy as np


class EmbeddingService:
    """Manages embeddings for semantic search."""

    def __init__(self, embeddings: np.ndarray, model_name: str = "all-MiniLM-L6-v2"):
        self.embeddings = embeddings
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_query(self, text: str) -> np.ndarray:
        """Encode a text query into an embedding vector."""
        model = self._get_model()
        return model.encode([text])[0]
