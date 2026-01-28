"""
CodeGraph Backend - Sentence Transformer Encoder
"""
from typing import Any
import logging

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingEncoder:
    """Encode text into embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model
        self._model = None
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise RuntimeError("sentence-transformers not installed")
            
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    def encode(
        self,
        texts: str | list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """Encode text(s) into embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        
        # Convert to list of lists for JSON serialization
        return embeddings.tolist()
    
    def encode_code(
        self,
        code: str,
        context: str | None = None,
    ) -> list[float]:
        """Encode code with optional context."""
        # Combine code with context if provided
        if context:
            text = f"{context}\n\n{code}"
        else:
            text = code
        
        embeddings = self.encode(text)
        return embeddings[0]
    
    def encode_query(self, query: str) -> list[float]:
        """Encode a natural language query."""
        # Could add query-specific formatting here
        embeddings = self.encode(query)
        return embeddings[0]
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_encoder: EmbeddingEncoder | None = None


def get_encoder() -> EmbeddingEncoder:
    """Get the global encoder instance."""
    global _encoder
    if _encoder is None:
        _encoder = EmbeddingEncoder()
    return _encoder
