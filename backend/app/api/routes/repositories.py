"""
CodeGraph Backend - Repository Management Routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryList,
    RepositoryStatus,
)
from app.services.repository import RepositoryService
from app.services.indexing import IndexingService
import uuid
from datetime import datetime

router = APIRouter()

# In-memory store for demo (will be replaced with database)
_repositories: dict[str, dict] = {}


@router.post("", response_model=RepositoryResponse)
async def create_repository(
    repo: RepositoryCreate,
    background_tasks: BackgroundTasks
):
    """Clone and index a new repository."""
    repo_id = str(uuid.uuid4())
    
    # Extract repo name from URL
    url_str = str(repo.url)
    name = url_str.rstrip("/").split("/")[-1].replace(".git", "")
    
    repo_data = {
        "id": repo_id,
        "url": url_str,
        "name": name,
        "branch": repo.branch,
        "status": RepositoryStatus.PENDING,
        "file_count": None,
        "node_count": None,
        "created_at": datetime.utcnow(),
        "indexed_at": None,
        "error_message": None,
    }
    
    _repositories[repo_id] = repo_data
    
    # Start background indexing task
    background_tasks.add_task(
        _process_repository,
        repo_id,
        url_str,
        repo.branch
    )
    
    return RepositoryResponse(**repo_data)


@router.get("", response_model=RepositoryList)
async def list_repositories():
    """List all repositories."""
    repos = [RepositoryResponse(**r) for r in _repositories.values()]
    return RepositoryList(repositories=repos, total=len(repos))


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str):
    """Get repository details."""
    if repo_id not in _repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryResponse(**_repositories[repo_id])


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str):
    """Delete a repository and its index."""
    if repo_id not in _repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # TODO: Clean up files and index
    del _repositories[repo_id]
    return {"status": "deleted", "id": repo_id}


async def _process_repository(repo_id: str, url: str, branch: str):
    """Background task to clone and index repository."""
    try:
        # Update status to cloning
        _repositories[repo_id]["status"] = RepositoryStatus.CLONING
        
        # Clone repository
        repo_service = RepositoryService()
        local_path = await repo_service.clone(url, branch)
        
        # Update status to indexing
        _repositories[repo_id]["status"] = RepositoryStatus.INDEXING
        
        # Index the repository
        indexing_service = IndexingService()
        stats = await indexing_service.index_repository(repo_id, local_path)
        
        # Update with results
        _repositories[repo_id].update({
            "status": RepositoryStatus.READY,
            "file_count": stats.get("file_count", 0),
            "node_count": stats.get("node_count", 0),
            "indexed_at": datetime.utcnow(),
        })
        
    except Exception as e:
        _repositories[repo_id].update({
            "status": RepositoryStatus.ERROR,
            "error_message": str(e),
        })
