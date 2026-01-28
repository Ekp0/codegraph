"""
CodeGraph Backend - Celery Worker for Background Tasks
"""
from celery import Celery
from pathlib import Path
import logging

from app.config import settings
from app.services.repository import RepositoryService
from app.services.indexing import IndexingService

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "codegraph",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, name="tasks.clone_repository")
def clone_repository(self, repo_id: str, url: str, branch: str = "main"):
    """Clone a git repository in the background."""
    logger.info(f"[Task {self.request.id}] Cloning repository: {url}")
    
    try:
        # Update task state
        self.update_state(state="CLONING", meta={"progress": 10})
        
        # Clone the repository
        repo_service = RepositoryService()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        local_path = loop.run_until_complete(
            repo_service.clone(url, branch)
        )
        
        logger.info(f"[Task {self.request.id}] Cloned to {local_path}")
        
        return {
            "repo_id": repo_id,
            "local_path": str(local_path),
            "status": "cloned",
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Clone failed: {e}")
        raise


@celery_app.task(bind=True, name="tasks.index_repository")
def index_repository(self, repo_id: str, local_path: str):
    """Index a cloned repository in the background."""
    logger.info(f"[Task {self.request.id}] Indexing repository: {repo_id}")
    
    try:
        self.update_state(state="INDEXING", meta={"progress": 30})
        
        # Index the repository
        indexing_service = IndexingService()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        stats = loop.run_until_complete(
            indexing_service.index_repository(repo_id, Path(local_path))
        )
        
        self.update_state(state="COMPLETED", meta={"progress": 100})
        
        logger.info(f"[Task {self.request.id}] Indexed {repo_id}: {stats}")
        
        return {
            "repo_id": repo_id,
            "status": "ready",
            **stats,
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Indexing failed: {e}")
        raise


@celery_app.task(bind=True, name="tasks.process_repository")
def process_repository(self, repo_id: str, url: str, branch: str = "main"):
    """Full pipeline: clone and index a repository."""
    logger.info(f"[Task {self.request.id}] Processing repository: {url}")
    
    try:
        # Step 1: Clone
        self.update_state(state="CLONING", meta={"progress": 10})
        
        repo_service = RepositoryService()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        local_path = loop.run_until_complete(
            repo_service.clone(url, branch)
        )
        
        # Step 2: Index
        self.update_state(state="INDEXING", meta={"progress": 50})
        
        indexing_service = IndexingService()
        stats = loop.run_until_complete(
            indexing_service.index_repository(repo_id, local_path)
        )
        
        self.update_state(state="COMPLETED", meta={"progress": 100})
        
        return {
            "repo_id": repo_id,
            "local_path": str(local_path),
            "status": "ready",
            **stats,
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Processing failed: {e}")
        raise


@celery_app.task(name="tasks.delete_repository")
def delete_repository(repo_id: str, local_path: str):
    """Delete a repository and its data."""
    logger.info(f"Deleting repository: {repo_id}")
    
    try:
        repo_service = RepositoryService()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            repo_service.delete(Path(local_path))
        )
        
        # TODO: Also delete from vector store and database
        
        return {"repo_id": repo_id, "status": "deleted"}
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise
