"""
CodeGraph Backend - Repository Service
"""
from pathlib import Path
import logging
import shutil
import asyncio

try:
    from git import Repo as GitRepo
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class RepositoryService:
    """Service for managing git repositories."""
    
    def __init__(self, repos_dir: str | None = None):
        self.repos_dir = Path(repos_dir or settings.repos_dir)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
    
    async def clone(
        self,
        url: str,
        branch: str = "main",
        depth: int = 1,
    ) -> Path:
        """Clone a repository and return the local path."""
        
        if not GIT_AVAILABLE:
            raise RuntimeError("GitPython not installed")
        
        # Generate a unique directory name from URL
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        local_path = self.repos_dir / f"{repo_name}_{unique_id}"
        
        logger.info(f"Cloning {url} to {local_path}")
        
        # Clone in a thread pool to not block async
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: GitRepo.clone_from(
                url,
                local_path,
                branch=branch,
                depth=depth,
                single_branch=True,
            )
        )
        
        logger.info(f"Successfully cloned {repo_name}")
        return local_path
    
    async def delete(self, local_path: Path):
        """Delete a cloned repository."""
        if local_path.exists():
            shutil.rmtree(local_path)
            logger.info(f"Deleted repository at {local_path}")
    
    def get_file_list(self, local_path: Path, extensions: list[str] | None = None) -> list[Path]:
        """Get list of files in repository, optionally filtered by extension."""
        files = []
        
        for item in local_path.rglob("*"):
            if item.is_file():
                # Skip hidden files and common non-code directories
                parts = item.relative_to(local_path).parts
                if any(p.startswith(".") or p in ["node_modules", "__pycache__", "venv"] for p in parts):
                    continue
                
                if extensions:
                    if item.suffix.lower() in extensions:
                        files.append(item)
                else:
                    files.append(item)
        
        return files
    
    def read_file(self, file_path: Path) -> str | None:
        """Read file contents safely."""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get information about a file."""
        content = self.read_file(file_path)
        return {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": file_path.stat().st_size if file_path.exists() else 0,
            "lines": len(content.split("\n")) if content else 0,
        }
