"""
CodeGraph Backend - LangGraph Agent Orchestrator
"""
from typing import TypedDict, Annotated, Literal
import operator
import logging

from app.llm.factory import get_provider
from app.llm.base import Message, MessageRole, LLMResponse
from app.core.graph.builder import get_graph_builder
from app.core.graph.traversal import GraphTraversal
from app.core.embeddings.vectorstore import get_vectorstore
from app.core.embeddings.encoder import get_encoder
from app.models.schemas import Citation, ReasoningStep

logger = logging.getLogger(__name__)


# Agent State
class AgentState(TypedDict):
    """State for the code understanding agent."""
    question: str
    repository_id: str
    messages: list[dict]
    reasoning_steps: Annotated[list[ReasoningStep], operator.add]
    citations: Annotated[list[Citation], operator.add]
    current_node: str | None
    visited_nodes: list[str]
    answer: str | None
    confidence: float
    iterations: int


class CodeGraphAgent:
    """LangGraph-style agent for code understanding with multi-hop reasoning."""
    
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        max_iterations: int = 10,
    ):
        self.llm = get_provider(provider, model)
        self.max_iterations = max_iterations
        self.graph_builder = get_graph_builder()
    
    async def run(
        self,
        question: str,
        repository_id: str,
    ) -> dict:
        """Run the agent to answer a question about the code."""
        
        # Initialize state
        state: AgentState = {
            "question": question,
            "repository_id": repository_id,
            "messages": [],
            "reasoning_steps": [],
            "citations": [],
            "current_node": None,
            "visited_nodes": [],
            "answer": None,
            "confidence": 0.0,
            "iterations": 0,
        }
        
        # Get the code graph
        graph = self.graph_builder.get_graph(repository_id)
        if not graph:
            return {
                "answer": "Repository not indexed. Please index the repository first.",
                "citations": [],
                "reasoning_steps": [],
                "confidence": 0.0,
            }
        
        traversal = GraphTraversal(graph)
        
        # Step 1: Understand the question and find relevant entry points
        state = await self._plan_step(state, traversal)
        
        # Step 2: Navigate the graph to gather context
        while state["iterations"] < self.max_iterations and not state["answer"]:
            state = await self._navigate_step(state, traversal)
            state["iterations"] += 1
        
        # Step 3: Generate final answer
        if not state["answer"]:
            state = await self._answer_step(state)
        
        return {
            "answer": state["answer"] or "Unable to find an answer.",
            "citations": state["citations"],
            "reasoning_steps": state["reasoning_steps"],
            "confidence": state["confidence"],
            "tokens_used": None,  # Would track from LLM responses
        }
    
    async def _plan_step(
        self,
        state: AgentState,
        traversal: GraphTraversal,
    ) -> AgentState:
        """Plan which nodes to visit based on the question."""
        
        # Search for relevant nodes
        search_results = traversal.search_nodes(
            state["question"],
            limit=10,
        )
        
        state["reasoning_steps"].append(ReasoningStep(
            step_number=len(state["reasoning_steps"]) + 1,
            action="search",
            observation=f"Found {len(search_results)} potentially relevant code elements",
        ))
        
        if search_results:
            # Start with the highest scoring node
            best_match = search_results[0]
            state["current_node"] = best_match["node_id"]
            state["visited_nodes"].append(best_match["node_id"])
            
            # Add citation
            node_data = best_match["data"]
            state["citations"].append(Citation(
                file_path=node_data.get("file_path", ""),
                start_line=node_data.get("start_line", 0),
                end_line=node_data.get("end_line", 0),
                content=node_data.get("source_code", node_data.get("signature", "")),
                node_type=node_data.get("type"),
                node_name=node_data.get("name"),
            ))
        
        return state
    
    async def _navigate_step(
        self,
        state: AgentState,
        traversal: GraphTraversal,
    ) -> AgentState:
        """Navigate to related nodes and gather more context."""
        
        if not state["current_node"]:
            # No more nodes to explore, generate answer
            state = await self._answer_step(state)
            return state
        
        # Get context for current node
        context = traversal.get_node_context(state["current_node"])
        
        # Decide what to do based on question and context
        prompt = self._build_navigation_prompt(state, context)
        
        response = await self.llm.chat([
            Message(role=MessageRole.SYSTEM, content=self._get_system_prompt()),
            Message(role=MessageRole.USER, content=prompt),
        ])
        
        # Parse response to determine next action
        action = self._parse_navigation_response(response.content, context)
        
        state["reasoning_steps"].append(ReasoningStep(
            step_number=len(state["reasoning_steps"]) + 1,
            action=action["type"],
            node_visited=state["current_node"],
            observation=action.get("observation"),
        ))
        
        if action["type"] == "answer":
            state["answer"] = action.get("answer")
            state["confidence"] = action.get("confidence", 0.8)
        elif action["type"] == "navigate" and action.get("next_node"):
            next_node = action["next_node"]
            if next_node not in state["visited_nodes"]:
                state["current_node"] = next_node
                state["visited_nodes"].append(next_node)
                
                # Add citation for new node
                node_data = traversal.graph.nodes[next_node].get("data", {})
                state["citations"].append(Citation(
                    file_path=node_data.get("file_path", ""),
                    start_line=node_data.get("start_line", 0),
                    end_line=node_data.get("end_line", 0),
                    content=node_data.get("source_code", node_data.get("signature", "")),
                    node_type=node_data.get("type"),
                    node_name=node_data.get("name"),
                ))
            else:
                state["current_node"] = None
        else:
            state["current_node"] = None
        
        return state
    
    async def _answer_step(self, state: AgentState) -> AgentState:
        """Generate the final answer based on gathered context."""
        
        # Build context from citations
        context_text = "\n\n".join([
            f"## {c.node_name or 'Code'} ({c.file_path}:{c.start_line}-{c.end_line})\n```\n{c.content}\n```"
            for c in state["citations"]
        ])
        
        prompt = f"""Based on the following code context, answer the user's question.

Question: {state["question"]}

Code Context:
{context_text}

Provide a clear, detailed answer that references the specific code shown. If you cannot answer from the given context, say so."""
        
        response = await self.llm.chat([
            Message(role=MessageRole.SYSTEM, content=self._get_system_prompt()),
            Message(role=MessageRole.USER, content=prompt),
        ])
        
        state["answer"] = response.content
        state["confidence"] = 0.85 if state["citations"] else 0.5
        
        state["reasoning_steps"].append(ReasoningStep(
            step_number=len(state["reasoning_steps"]) + 1,
            action="answer",
            observation="Generated final answer from gathered context",
        ))
        
        return state
    
    def _get_system_prompt(self) -> str:
        return """You are a code understanding assistant. Your job is to navigate a code graph and answer questions about the codebase.

When analyzing code:
1. Pay attention to function signatures, return types, and docstrings
2. Trace call chains when understanding how functions work together
3. Note imports and dependencies between modules
4. Look for patterns and design decisions

Always base your answers on the actual code provided. Cite specific files and line numbers when relevant."""
    
    def _build_navigation_prompt(self, state: AgentState, context: dict) -> str:
        node_data = context.get("node", {})
        
        # Format predecessor/successor info
        related = []
        for pred in context.get("predecessors", [])[:5]:
            related.append(f"- Called by: {pred['node_data'].get('name', 'unknown')}")
        for succ in context.get("successors", [])[:5]:
            related.append(f"- Calls: {succ['node_data'].get('name', 'unknown')}")
        
        related_text = "\n".join(related) if related else "No direct relationships."
        
        return f"""Question: {state["question"]}

Current node: {node_data.get('name', 'unknown')} ({node_data.get('type', 'unknown')})
File: {node_data.get('file_path', 'unknown')}
Signature: {node_data.get('signature', 'N/A')}

Related nodes:
{related_text}

Based on this context, decide:
1. If you can answer the question now, respond with: ANSWER: [your answer]
2. If you need to explore a related node, respond with: NAVIGATE: [node_name]
3. If you've gathered enough context, respond with: DONE

What is your decision?"""
    
    def _parse_navigation_response(self, response: str, context: dict) -> dict:
        response_upper = response.upper()
        
        if "ANSWER:" in response_upper:
            answer_start = response.find("ANSWER:") + 7
            return {
                "type": "answer",
                "answer": response[answer_start:].strip(),
                "confidence": 0.85,
            }
        elif "NAVIGATE:" in response_upper:
            nav_start = response.find("NAVIGATE:") + 9
            target_name = response[nav_start:].strip().split()[0]
            
            # Find the node ID for this name
            for succ in context.get("successors", []):
                if target_name.lower() in succ["node_data"].get("name", "").lower():
                    return {
                        "type": "navigate",
                        "next_node": succ["node_id"],
                        "observation": f"Navigating to {target_name}",
                    }
            
            for pred in context.get("predecessors", []):
                if target_name.lower() in pred["node_data"].get("name", "").lower():
                    return {
                        "type": "navigate",
                        "next_node": pred["node_id"],
                        "observation": f"Navigating to {target_name}",
                    }
            
            return {"type": "done", "observation": f"Could not find node: {target_name}"}
        
        return {"type": "done", "observation": "Finished exploration"}
