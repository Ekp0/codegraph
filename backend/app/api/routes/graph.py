"""
CodeGraph Backend - Graph Visualization Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    GraphData,
    GraphNode,
    GraphEdge,
    GraphQuery,
    NodeType,
    EdgeType,
)
from app.core.graph.builder import GraphBuilder

router = APIRouter()

# In-memory graph store (will be replaced with persistent storage)
_graphs: dict[str, GraphData] = {}


@router.get("/{repository_id}", response_model=GraphData)
async def get_graph(repository_id: str):
    """Get the full code graph for a repository."""
    if repository_id not in _graphs:
        # Try to load from builder
        try:
            builder = GraphBuilder()
            graph_data = await builder.load_graph(repository_id)
            _graphs[repository_id] = graph_data
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Graph not found for repository: {repository_id}"
            )
    
    return _graphs[repository_id]


@router.post("/query", response_model=GraphData)
async def query_graph(query: GraphQuery):
    """Query the graph with filters."""
    if query.repository_id not in _graphs:
        raise HTTPException(
            status_code=404,
            detail="Repository graph not found"
        )
    
    graph = _graphs[query.repository_id]
    
    # Filter nodes
    filtered_nodes = graph.nodes
    if query.node_types:
        filtered_nodes = [
            n for n in filtered_nodes 
            if n.type in query.node_types
        ]
    
    # Filter edges
    filtered_edges = graph.edges
    if query.edge_types:
        filtered_edges = [
            e for e in filtered_edges 
            if e.type in query.edge_types
        ]
    
    # If start_node specified, do BFS traversal
    if query.start_node:
        filtered_nodes, filtered_edges = _bfs_subgraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            start_node=query.start_node,
            max_depth=query.max_depth,
        )
    
    return GraphData(
        nodes=filtered_nodes,
        edges=filtered_edges,
        stats={
            "node_count": len(filtered_nodes),
            "edge_count": len(filtered_edges),
        }
    )


@router.get("/{repository_id}/node/{node_id}")
async def get_node(repository_id: str, node_id: str):
    """Get details for a specific node."""
    if repository_id not in _graphs:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    graph = _graphs[repository_id]
    for node in graph.nodes:
        if node.id == node_id:
            return node
    
    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/{repository_id}/neighbors/{node_id}")
async def get_neighbors(repository_id: str, node_id: str, depth: int = 1):
    """Get neighboring nodes within specified depth."""
    if repository_id not in _graphs:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    graph = _graphs[repository_id]
    nodes, edges = _bfs_subgraph(
        nodes=graph.nodes,
        edges=graph.edges,
        start_node=node_id,
        max_depth=depth,
    )
    
    return GraphData(
        nodes=nodes,
        edges=edges,
        stats={"node_count": len(nodes), "edge_count": len(edges)}
    )


def _bfs_subgraph(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    start_node: str,
    max_depth: int
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Extract subgraph using BFS from start node."""
    node_map = {n.id: n for n in nodes}
    
    if start_node not in node_map:
        return [], []
    
    # Build adjacency list
    adj = {}
    for edge in edges:
        if edge.source not in adj:
            adj[edge.source] = []
        adj[edge.source].append(edge.target)
        # Also add reverse for undirected traversal
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.target].append(edge.source)
    
    # BFS
    visited = {start_node}
    queue = [(start_node, 0)]
    result_nodes = [node_map[start_node]]
    
    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        
        for neighbor in adj.get(current, []):
            if neighbor not in visited and neighbor in node_map:
                visited.add(neighbor)
                result_nodes.append(node_map[neighbor])
                queue.append((neighbor, depth + 1))
    
    # Get edges within visited nodes
    result_edges = [
        e for e in edges
        if e.source in visited and e.target in visited
    ]
    
    return result_nodes, result_edges
