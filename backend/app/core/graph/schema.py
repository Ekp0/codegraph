"""
CodeGraph Backend - Graph Schema Definitions
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Types of nodes in the code graph."""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    PARAMETER = "parameter"


class EdgeType(str, Enum):
    """Types of relationships between nodes."""
    CONTAINS = "contains"      # Module/class contains function/class
    CALLS = "calls"            # Function calls another function
    IMPORTS = "imports"        # Module imports another module
    INHERITS = "inherits"      # Class inherits from another class
    REFERENCES = "references"  # Code references a variable/function
    DEFINES = "defines"        # Scope defines a variable
    RETURNS = "returns"        # Function returns a type
    PARAMETER_OF = "parameter_of"  # Parameter belongs to function


@dataclass
class GraphNodeData:
    """Data stored in a graph node."""
    id: str
    type: NodeType
    name: str
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str | None = None
    docstring: str | None = None
    source_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, NodeType) else self.type,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "signature": self.signature,
            "docstring": self.docstring,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdgeData:
    """Data stored in a graph edge."""
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value if isinstance(self.type, EdgeType) else self.type,
            "weight": self.weight,
            "metadata": self.metadata,
        }


# Node ID generation utilities
def make_node_id(file_path: str, qualified_name: str) -> str:
    """Generate a unique node ID."""
    import hashlib
    content = f"{file_path}::{qualified_name}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def make_module_id(file_path: str) -> str:
    """Generate a module node ID from file path."""
    import hashlib
    return hashlib.sha256(file_path.encode()).hexdigest()[:16]
