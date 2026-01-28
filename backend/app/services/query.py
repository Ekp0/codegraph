"""
CodeGraph Backend - Query Service
"""
import logging

from app.core.agents.orchestrator import CodeGraphAgent
from app.core.graph.builder import get_graph_builder
from app.core.graph.traversal import GraphTraversal
from app.config import settings

logger = logging.getLogger(__name__)


class QueryService:
    """Service for processing natural language queries about code."""
    
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_llm_model
        self.graph_builder = get_graph_builder()
    
    async def process_query(
        self,
        repository_id: str,
        question: str,
    ) -> dict:
        """Process a natural language query about a repository."""
        
        logger.info(f"Processing query for {repository_id}: {question}")
        
        # Use the agent for complex queries
        agent = CodeGraphAgent(
            provider=self.provider,
            model=self.model,
        )
        
        result = await agent.run(question, repository_id)
        return result
    
    async def explain_function(
        self,
        repository_id: str,
        file_path: str,
        function_name: str,
    ) -> dict:
        """Generate detailed explanation of a function."""
        
        graph = self.graph_builder.get_graph(repository_id)
        if not graph:
            return {"error": "Repository not indexed"}
        
        traversal = GraphTraversal(graph)
        
        # Find the function node
        results = traversal.search_nodes(function_name, limit=5)
        
        target_node = None
        for result in results:
            data = result["data"]
            if data.get("name") == function_name and file_path in data.get("file_path", ""):
                target_node = result
                break
        
        if not target_node:
            return {"error": f"Function {function_name} not found in {file_path}"}
        
        # Get function context
        context = traversal.get_node_context(target_node["node_id"])
        
        # Get callers and callees
        callers = traversal.find_callers(target_node["node_id"], max_depth=2)
        callees = traversal.find_callees(target_node["node_id"], max_depth=2)
        
        return {
            "function": target_node["data"],
            "callers": [c.node_data for c in callers],
            "callees": [c.node_data for c in callees],
            "context": context,
        }
    
    async def trace_execution(
        self,
        repository_id: str,
        entry_point: str,
    ) -> dict:
        """Trace execution flow from an entry point."""
        
        graph = self.graph_builder.get_graph(repository_id)
        if not graph:
            return {"error": "Repository not indexed"}
        
        traversal = GraphTraversal(graph)
        
        # Find the entry point node
        results = traversal.search_nodes(entry_point, limit=1)
        
        if not results:
            return {"error": f"Entry point {entry_point} not found"}
        
        node_id = results[0]["node_id"]
        
        # Trace execution
        flow = traversal.trace_execution_flow(node_id, max_steps=30)
        
        return {
            "entry_point": results[0]["data"],
            "execution_flow": [
                {
                    "step": step.depth,
                    "node": step.node_data,
                    "path": step.path,
                }
                for step in flow
            ],
        }
