"""
CodeGraph Backend - Graph Traversal Algorithms
"""
from dataclasses import dataclass, field
from typing import Generator, Any
import networkx as nx
from collections import deque

from app.core.graph.schema import NodeType, EdgeType


@dataclass
class TraversalStep:
    """A step in graph traversal."""
    node_id: str
    node_data: dict
    depth: int
    path: list[str]
    edge_type: str | None = None


@dataclass  
class TraversalResult:
    """Result of a graph traversal query."""
    steps: list[TraversalStep]
    nodes_visited: int
    max_depth_reached: int
    paths_found: list[list[str]]


class GraphTraversal:
    """Multi-hop graph traversal algorithms for code navigation."""
    
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
    
    def bfs(
        self,
        start_node: str,
        max_depth: int = 3,
        edge_types: list[EdgeType] | None = None,
        node_types: list[NodeType] | None = None,
    ) -> Generator[TraversalStep, None, None]:
        """Breadth-first traversal from a starting node."""
        if start_node not in self.graph:
            return
        
        visited = {start_node}
        queue = deque([(start_node, 0, [start_node], None)])
        
        while queue:
            current, depth, path, edge_type = queue.popleft()
            node_data = self.graph.nodes[current].get("data", {})
            
            # Filter by node type
            if node_types:
                node_type = node_data.get("type")
                if node_type not in [t.value for t in node_types]:
                    continue
            
            yield TraversalStep(
                node_id=current,
                node_data=node_data,
                depth=depth,
                path=path,
                edge_type=edge_type,
            )
            
            if depth >= max_depth:
                continue
            
            # Get neighbors
            for neighbor in self.graph.successors(current):
                if neighbor not in visited:
                    edge_data = self.graph.edges[current, neighbor].get("data", {})
                    curr_edge_type = edge_data.get("type")
                    
                    # Filter by edge type
                    if edge_types and curr_edge_type not in [t.value for t in edge_types]:
                        continue
                    
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1, path + [neighbor], curr_edge_type))
    
    def dfs(
        self,
        start_node: str,
        max_depth: int = 10,
        edge_types: list[EdgeType] | None = None,
    ) -> Generator[TraversalStep, None, None]:
        """Depth-first traversal from a starting node."""
        if start_node not in self.graph:
            return
        
        visited = set()
        stack = [(start_node, 0, [start_node], None)]
        
        while stack:
            current, depth, path, edge_type = stack.pop()
            
            if current in visited:
                continue
            visited.add(current)
            
            node_data = self.graph.nodes[current].get("data", {})
            
            yield TraversalStep(
                node_id=current,
                node_data=node_data,
                depth=depth,
                path=path,
                edge_type=edge_type,
            )
            
            if depth >= max_depth:
                continue
            
            for neighbor in self.graph.successors(current):
                if neighbor not in visited:
                    edge_data = self.graph.edges[current, neighbor].get("data", {})
                    curr_edge_type = edge_data.get("type")
                    
                    if edge_types and curr_edge_type not in [t.value for t in edge_types]:
                        continue
                    
                    stack.append((neighbor, depth + 1, path + [neighbor], curr_edge_type))
    
    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> list[list[str]]:
        """Find all paths between source and target nodes."""
        if source not in self.graph or target not in self.graph:
            return []
        
        paths = []
        try:
            for path in nx.all_simple_paths(self.graph, source, target, cutoff=max_depth):
                paths.append(path)
        except nx.NetworkXNoPath:
            pass
        
        return paths
    
    def find_callers(self, node_id: str, max_depth: int = 3) -> list[TraversalStep]:
        """Find all nodes that call a given function."""
        if node_id not in self.graph:
            return []
        
        callers = []
        reverse_graph = self.graph.reverse()
        
        visited = {node_id}
        queue = deque([(node_id, 0, [node_id])])
        
        while queue:
            current, depth, path = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            for predecessor in reverse_graph.successors(current):
                if predecessor in visited:
                    continue
                
                edge_data = self.graph.edges[predecessor, current].get("data", {})
                if edge_data.get("type") == EdgeType.CALLS.value:
                    visited.add(predecessor)
                    new_path = [predecessor] + path
                    
                    callers.append(TraversalStep(
                        node_id=predecessor,
                        node_data=self.graph.nodes[predecessor].get("data", {}),
                        depth=depth + 1,
                        path=new_path,
                        edge_type="calls",
                    ))
                    
                    queue.append((predecessor, depth + 1, new_path))
        
        return callers
    
    def find_callees(self, node_id: str, max_depth: int = 3) -> list[TraversalStep]:
        """Find all functions called by a given node."""
        callees = []
        
        for step in self.bfs(node_id, max_depth, edge_types=[EdgeType.CALLS]):
            if step.node_id != node_id:
                callees.append(step)
        
        return callees
    
    def trace_execution_flow(
        self,
        entry_point: str,
        max_steps: int = 20,
    ) -> list[TraversalStep]:
        """Trace execution flow from an entry point."""
        if entry_point not in self.graph:
            return []
        
        flow = []
        visited = set()
        
        def trace(node_id: str, depth: int, path: list[str]):
            if len(flow) >= max_steps or node_id in visited:
                return
            
            visited.add(node_id)
            node_data = self.graph.nodes[node_id].get("data", {})
            
            flow.append(TraversalStep(
                node_id=node_id,
                node_data=node_data,
                depth=depth,
                path=path,
            ))
            
            # Follow CALLS edges
            for neighbor in self.graph.successors(node_id):
                edge_data = self.graph.edges[node_id, neighbor].get("data", {})
                if edge_data.get("type") == EdgeType.CALLS.value:
                    trace(neighbor, depth + 1, path + [neighbor])
        
        trace(entry_point, 0, [entry_point])
        return flow
    
    def get_node_context(
        self,
        node_id: str,
        context_depth: int = 2,
    ) -> dict:
        """Get contextual information about a node including neighbors."""
        if node_id not in self.graph:
            return {}
        
        node_data = self.graph.nodes[node_id].get("data", {})
        
        # Get predecessors (what points to this node)
        predecessors = []
        for pred in self.graph.predecessors(node_id):
            edge_data = self.graph.edges[pred, node_id].get("data", {})
            predecessors.append({
                "node_id": pred,
                "node_data": self.graph.nodes[pred].get("data", {}),
                "edge_type": edge_data.get("type"),
            })
        
        # Get successors (what this node points to)
        successors = []
        for succ in self.graph.successors(node_id):
            edge_data = self.graph.edges[node_id, succ].get("data", {})
            successors.append({
                "node_id": succ,
                "node_data": self.graph.nodes[succ].get("data", {}),
                "edge_type": edge_data.get("type"),
            })
        
        return {
            "node": node_data,
            "predecessors": predecessors,
            "successors": successors,
            "in_degree": self.graph.in_degree(node_id),
            "out_degree": self.graph.out_degree(node_id),
        }
    
    def search_nodes(
        self,
        query: str,
        node_types: list[NodeType] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search nodes by name or content."""
        results = []
        query_lower = query.lower()
        
        for node_id, attrs in self.graph.nodes(data=True):
            if len(results) >= limit:
                break
            
            data = attrs.get("data", {})
            
            # Filter by node type
            if node_types:
                if data.get("type") not in [t.value for t in node_types]:
                    continue
            
            # Search in name, qualified_name, signature, docstring
            searchable = " ".join([
                data.get("name", ""),
                data.get("qualified_name", ""),
                data.get("signature", "") or "",
                data.get("docstring", "") or "",
            ]).lower()
            
            if query_lower in searchable:
                results.append({
                    "node_id": node_id,
                    "data": data,
                    "score": 1.0 if query_lower == data.get("name", "").lower() else 0.5,
                })
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
