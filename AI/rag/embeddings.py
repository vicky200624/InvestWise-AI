"""
Embedding model utility for generating semantic vector embeddings.
Standalone module with zero Django dependencies.
"""

import logging
from typing import List, Union

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manages embedding generation using HuggingFace / SentenceTransformers or fallback models.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to load sentence_transformers model '{self.model_name}' ({e}). Fallback to basic embedding stub.")
                self._model = "STUB"

    def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embedding vector(s) for input text or list of texts.
        """
        self._load_model()
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text

        if self._model == "STUB" or self._model is None:
            # Fallback deterministic pseudo-embedding (384 dims)
            return [[0.1] * 384 for _ in texts]

        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error encoding text with {self.model_name}: {e}")
            return [[0.0] * 384 for _ in texts]
