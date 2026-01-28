"""
CodeGraph Backend - SQLAlchemy Database Models
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a unique ID."""
    return str(uuid.uuid4())


class Repository(Base):
    """Repository metadata and status."""
    __tablename__ = "repositories"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    url = Column(String(500), nullable=False)
    name = Column(String(200), nullable=False)
    branch = Column(String(100), default="main")
    local_path = Column(String(500))
    
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    
    file_count = Column(Integer, default=0)
    node_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)
    
    # Relationships
    queries = relationship("Query", back_populates="repository")
    
    def __repr__(self):
        return f"<Repository {self.name} ({self.status})>"


class Query(Base):
    """Query history and results."""
    __tablename__ = "queries"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    
    question = Column(Text, nullable=False)
    answer = Column(Text)
    citations = Column(JSON, default=list)
    reasoning_steps = Column(JSON, default=list)
    
    provider = Column(String(50))
    model = Column(String(100))
    confidence = Column(Integer, default=0)  # 0-100
    tokens_used = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="queries")
    
    def __repr__(self):
        return f"<Query {self.id[:8]}...>"


class CodeNode(Base):
    """Cached code node information."""
    __tablename__ = "code_nodes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    
    node_type = Column(String(20), nullable=False)  # module, class, function, etc.
    name = Column(String(200), nullable=False)
    qualified_name = Column(String(500))
    
    file_path = Column(String(500), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    
    signature = Column(Text)
    docstring = Column(Text)
    source_code = Column(Text)
    
    node_metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<CodeNode {self.node_type}:{self.name}>"
