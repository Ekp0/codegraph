"""
CodeGraph Backend - NetworkX Graph Builder
"""
from pathlib import Path
from typing import Any
import logging
import networkx as nx

from app.core.parsing.tree_sitter import get_parser, ParsedNode
from app.core.graph.schema import (
    NodeType,
    EdgeType,
    GraphNodeData,
    GraphEdgeData,
    make_node_id,
    make_module_id,
)
from app.models.schemas import GraphData, GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds and manages code graphs using NetworkX."""
    
    def __init__(self):
        self._graphs: dict[str, nx.DiGraph] = {}
    
    def build_graph(self, repo_id: str, repo_path: Path) -> nx.DiGraph:
        """Build a complete code graph from a repository."""
        logger.info(f"Building graph for repository: {repo_id}")
        
        graph = nx.DiGraph()
        parser = get_parser()
        
        # Parse all files
        nodes_by_file: dict[str, list[ParsedNode]] = {}
        
        for parsed_node in parser.parse_directory(repo_path):
            file_path = parsed_node.file_path
            if file_path not in nodes_by_file:
                nodes_by_file[file_path] = []
            nodes_by_file[file_path].append(parsed_node)
        
        # Create module nodes and code nodes
        for file_path, nodes in nodes_by_file.items():
            # Create module node
            rel_path = self._get_relative_path(file_path, repo_path)
            module_id = make_module_id(rel_path)
            
            graph.add_node(
                module_id,
                data=GraphNodeData(
                    id=module_id,
                    type=NodeType.MODULE,
                    name=Path(file_path).stem,
                    qualified_name=rel_path,
                    file_path=rel_path,
                    start_line=1,
                    end_line=self._count_lines(file_path),
                ).to_dict()
            )
            
            # Create nodes for code elements
            for parsed in nodes:
                node_id = make_node_id(rel_path, parsed.qualified_name)
                node_type = self._map_node_type(parsed.node_type)
                
                graph.add_node(
                    node_id,
                    data=GraphNodeData(
                        id=node_id,
                        type=node_type,
                        name=parsed.name,
                        qualified_name=parsed.qualified_name,
                        file_path=rel_path,
                        start_line=parsed.start_line,
                        end_line=parsed.end_line,
                        signature=parsed.signature,
                        docstring=parsed.docstring,
                        source_code=parsed.source_code,
                    ).to_dict()
                )
                
                # Add CONTAINS edge from module
                graph.add_edge(
                    module_id,
                    node_id,
                    data=GraphEdgeData(
                        source=module_id,
                        target=node_id,
                        type=EdgeType.CONTAINS,
                    ).to_dict()
                )
                
                # Add CONTAINS edge from parent class if applicable
                if parsed.parent_name:
                    parent_id = make_node_id(rel_path, parsed.parent_name)
                    if parent_id in graph:
                        graph.add_edge(
                            parent_id,
                            node_id,
                            data=GraphEdgeData(
                                source=parent_id,
                                target=node_id,
                                type=EdgeType.CONTAINS,
                            ).to_dict()
                        )
        
        # Analyze call relationships
        self._analyze_calls(graph, repo_path)
        
        # Analyze imports
        self._analyze_imports(graph)
        
        # Store the graph
        self._graphs[repo_id] = graph
        
        logger.info(f"Built graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        return graph
    
    def get_graph(self, repo_id: str) -> nx.DiGraph | None:
        """Get an existing graph by repository ID."""
        return self._graphs.get(repo_id)
    
    async def load_graph(self, repo_id: str) -> GraphData:
        """Load graph and convert to API response format."""
        graph = self._graphs.get(repo_id)
        if not graph:
            raise ValueError(f"Graph not found: {repo_id}")
        
        return self._convert_to_response(graph)
    
    def _convert_to_response(self, graph: nx.DiGraph) -> GraphData:
        """Convert NetworkX graph to API response format."""
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            nodes.append(GraphNode(
                id=node_id,
                type=data.get("type", "unknown"),
                name=data.get("name", ""),
                file_path=data.get("file_path", ""),
                start_line=data.get("start_line", 0),
                end_line=data.get("end_line", 0),
                signature=data.get("signature"),
                docstring=data.get("docstring"),
                metadata=data.get("metadata", {}),
            ))
        
        edges = []
        for source, target, attrs in graph.edges(data=True):
            data = attrs.get("data", {})
            edges.append(GraphEdge(
                source=source,
                target=target,
                type=data.get("type", "references"),
                metadata=data.get("metadata", {}),
            ))
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            stats={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "module_count": sum(1 for n in nodes if n.type == "module"),
                "function_count": sum(1 for n in nodes if n.type in ["function", "method"]),
                "class_count": sum(1 for n in nodes if n.type == "class"),
            }
        )
    
    def _map_node_type(self, parsed_type: str) -> NodeType:
        """Map parsed node type to graph NodeType."""
        mapping = {
            "function": NodeType.FUNCTION,
            "class": NodeType.CLASS,
            "method": NodeType.METHOD,
            "import": NodeType.IMPORT,
            "variable": NodeType.VARIABLE,
        }
        return mapping.get(parsed_type, NodeType.FUNCTION)
    
    def _get_relative_path(self, file_path: str, repo_path: Path) -> str:
        """Get relative path from repository root."""
        try:
            return str(Path(file_path).relative_to(repo_path))
        except ValueError:
            return file_path
    
    def _count_lines(self, file_path: str) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def _analyze_calls(self, graph: nx.DiGraph, repo_path: Path):
        """Analyze function call relationships."""
        # Get all function/method nodes
        function_nodes = {}
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            if data.get("type") in [NodeType.FUNCTION.value, NodeType.METHOD.value, "function", "method"]:
                function_nodes[data.get("name")] = node_id
        
        # Look for calls in source code
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            source = data.get("source_code", "")
            if not source:
                continue
            
            # Simple pattern matching for function calls
            import re
            call_pattern = r'(\w+)\s*\('
            for match in re.finditer(call_pattern, source):
                called_name = match.group(1)
                if called_name in function_nodes and called_name != data.get("name"):
                    target_id = function_nodes[called_name]
                    if not graph.has_edge(node_id, target_id):
                        graph.add_edge(
                            node_id,
                            target_id,
                            data=GraphEdgeData(
                                source=node_id,
                                target=target_id,
                                type=EdgeType.CALLS,
                            ).to_dict()
                        )
    
    def _analyze_imports(self, graph: nx.DiGraph):
        """Analyze import relationships between modules."""
        module_nodes = {}
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            if data.get("type") == NodeType.MODULE.value or data.get("type") == "module":
                module_nodes[data.get("name")] = node_id
        
        # Look for import nodes and create edges
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            if data.get("type") == NodeType.IMPORT.value or data.get("type") == "import":
                # Parse import statement to find target module
                signature = data.get("signature", "")
                # Simple extraction - could be improved
                import re
                for match in re.finditer(r'(?:from|import)\s+(\w+)', signature):
                    imported_name = match.group(1)
                    if imported_name in module_nodes:
                        source_module = self._find_parent_module(graph, node_id)
                        if source_module:
                            graph.add_edge(
                                source_module,
                                module_nodes[imported_name],
                                data=GraphEdgeData(
                                    source=source_module,
                                    target=module_nodes[imported_name],
                                    type=EdgeType.IMPORTS,
                                ).to_dict()
                            )
    
    def _find_parent_module(self, graph: nx.DiGraph, node_id: str) -> str | None:
        """Find the module that contains a node."""
        for predecessor in graph.predecessors(node_id):
            data = graph.nodes[predecessor].get("data", {})
            if data.get("type") == NodeType.MODULE.value or data.get("type") == "module":
                return predecessor
        return None


# Singleton instance
_builder: GraphBuilder | None = None


def get_graph_builder() -> GraphBuilder:
    """Get the global graph builder instance."""
    global _builder
    if _builder is None:
        _builder = GraphBuilder()
    return _builder
