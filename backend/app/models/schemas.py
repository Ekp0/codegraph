"""
CodeGraph Backend - Pydantic Schemas for API
"""
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, HttpUrl


# =============================================================================
# Enums
# =============================================================================

class RepositoryStatus(str, Enum):
    """Status of repository processing."""
    PENDING = "pending"
    CLONING = "cloning"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class NodeType(str, Enum):
    """Types of nodes in the code graph."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"


class EdgeType(str, Enum):
    """Types of edges/relationships in the code graph."""
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    REFERENCES = "references"
    DEFINES = "defines"
    CONTAINS = "contains"


# =============================================================================
# Repository Schemas
# =============================================================================

class RepositoryCreate(BaseModel):
    """Request to clone and index a repository."""
    url: HttpUrl = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Branch to clone")
    
    model_config = {"json_schema_extra": {
        "example": {
            "url": "https://github.com/fastapi/fastapi",
            "branch": "main"
        }
    }}


class RepositoryResponse(BaseModel):
    """Repository information response."""
    id: str
    url: str
    name: str
    branch: str
    status: RepositoryStatus
    file_count: int | None = None
    node_count: int | None = None
    created_at: datetime
    indexed_at: datetime | None = None
    error_message: str | None = None


class RepositoryList(BaseModel):
    """List of repositories."""
    repositories: list[RepositoryResponse]
    total: int


# =============================================================================
# Query Schemas
# =============================================================================

class QueryRequest(BaseModel):
    """Request to ask a question about the code."""
    question: str = Field(..., min_length=3, description="Natural language question")
    repository_id: str = Field(..., description="Repository to query")
    provider: str | None = Field(default=None, description="LLM provider override")
    model: str | None = Field(default=None, description="Model override")
    
    model_config = {"json_schema_extra": {
        "example": {
            "question": "How does the main function work?",
            "repository_id": "repo_abc123"
        }
    }}


class Citation(BaseModel):
    """Code citation with file location."""
    file_path: str = Field(..., description="Relative file path")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    content: str = Field(..., description="Code content")
    node_type: NodeType | None = None
    node_name: str | None = None


class ReasoningStep(BaseModel):
    """A step in the multi-hop reasoning chain."""
    step_number: int
    action: str = Field(..., description="What the agent did")
    node_visited: str | None = None
    observation: str | None = None


class QueryResponse(BaseModel):
    """Response to a code question."""
    answer: str = Field(..., description="Natural language answer")
    citations: list[Citation] = Field(default_factory=list)
    reasoning_steps: list[ReasoningStep] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description="Confidence score")
    tokens_used: int | None = None
    processing_time_ms: int | None = None


# =============================================================================
# Graph Schemas
# =============================================================================

class GraphNode(BaseModel):
    """Node in the code graph."""
    id: str
    type: NodeType
    name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str | None = None
    docstring: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Edge/relationship in the code graph."""
    source: str
    target: str
    type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: dict[str, int] = Field(default_factory=dict)


class GraphQuery(BaseModel):
    """Query for graph traversal."""
    repository_id: str
    start_node: str | None = None
    node_types: list[NodeType] | None = None
    edge_types: list[EdgeType] | None = None
    max_depth: int = Field(default=3, ge=1, le=10)


# =============================================================================
# WebSocket Schemas
# =============================================================================

class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "progress", "result", "error"
    data: dict[str, Any]
