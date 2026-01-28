"""
CodeGraph Backend - ChromaDB Vector Store
"""
from pathlib import Path
from typing import Any
import logging

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-based vector store for code embeddings."""
    
    def __init__(self, persist_dir: str | None = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self._client = None
        self._collections: dict[str, Any] = {}
    
    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            if not CHROMADB_AVAILABLE:
                raise RuntimeError("ChromaDB not installed")
            
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client
    
    def get_collection(self, repo_id: str):
        """Get or create a collection for a repository."""
        if repo_id not in self._collections:
            self._collections[repo_id] = self.client.get_or_create_collection(
                name=f"repo_{repo_id[:32]}",  # ChromaDB limits collection names
                metadata={"repository_id": repo_id}
            )
        return self._collections[repo_id]
    
    def add_documents(
        self,
        repo_id: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        ids: list[str],
    ):
        """Add documents with embeddings to the collection."""
        collection = self.get_collection(repo_id)
        
        # ChromaDB has batch size limits
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            collection.add(
                documents=documents[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end],
            )
    
    def query(
        self,
        repo_id: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict | None = None,
    ) -> dict:
        """Query the collection with an embedding."""
        collection = self.get_collection(repo_id)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        return results
    
    def search_text(
        self,
        repo_id: str,
        query_text: str,
        n_results: int = 10,
    ) -> dict:
        """Search using text query (requires embedding function in collection)."""
        collection = self.get_collection(repo_id)
        
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        return results
    
    def delete_collection(self, repo_id: str):
        """Delete a repository's collection."""
        collection_name = f"repo_{repo_id[:32]}"
        try:
            self.client.delete_collection(collection_name)
            if repo_id in self._collections:
                del self._collections[repo_id]
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
    
    def get_count(self, repo_id: str) -> int:
        """Get the number of documents in a collection."""
        collection = self.get_collection(repo_id)
        return collection.count()


# Singleton instance
_vectorstore: VectorStore | None = None


def get_vectorstore() -> VectorStore:
    """Get the global vector store instance."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStore()
    return _vectorstore
