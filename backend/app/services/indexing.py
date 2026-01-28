"""
CodeGraph Backend - Indexing Service
"""
from pathlib import Path
import logging

from app.core.parsing.tree_sitter import get_parser
from app.core.graph.builder import get_graph_builder
from app.core.embeddings.vectorstore import get_vectorstore
from app.core.embeddings.encoder import get_encoder

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing repositories into graphs and vector stores."""
    
    def __init__(self):
        self.parser = get_parser()
        self.graph_builder = get_graph_builder()
    
    async def index_repository(
        self,
        repo_id: str,
        local_path: Path | str,
    ) -> dict:
        """Index a repository's code into the graph and vector store."""
        
        local_path = Path(local_path)
        logger.info(f"Indexing repository {repo_id} from {local_path}")
        
        # Build the code graph
        graph = self.graph_builder.build_graph(repo_id, local_path)
        
        # Count files and nodes
        file_count = len(set(
            data.get("data", {}).get("file_path", "")
            for _, data in graph.nodes(data=True)
            if data.get("data", {}).get("type") == "module"
        ))
        
        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()
        
        # Optionally build vector embeddings
        try:
            await self._build_embeddings(repo_id, graph)
        except Exception as e:
            logger.warning(f"Could not build embeddings: {e}")
        
        stats = {
            "file_count": file_count,
            "node_count": node_count,
            "edge_count": edge_count,
        }
        
        logger.info(f"Indexed {repo_id}: {stats}")
        return stats
    
    async def _build_embeddings(self, repo_id: str, graph):
        """Build vector embeddings for code nodes."""
        try:
            vectorstore = get_vectorstore()
            encoder = get_encoder()
        except Exception as e:
            logger.info(f"Skipping embeddings: {e}")
            return
        
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for node_id, attrs in graph.nodes(data=True):
            data = attrs.get("data", {})
            
            # Skip modules, focus on functions and classes
            if data.get("type") in ["function", "method", "class"]:
                # Create document text
                doc_text = f"{data.get('name', '')}\n{data.get('signature', '')}\n{data.get('docstring', '')}"
                
                if doc_text.strip():
                    documents.append(doc_text)
                    ids.append(node_id)
                    metadatas.append({
                        "node_id": node_id,
                        "type": data.get("type", ""),
                        "name": data.get("name", ""),
                        "file_path": data.get("file_path", ""),
                        "start_line": data.get("start_line", 0),
                        "end_line": data.get("end_line", 0),
                    })
        
        if documents:
            # Batch encode
            logger.info(f"Encoding {len(documents)} documents...")
            embeddings = encoder.encode(documents, show_progress=True)
            
            # Store in vector database
            vectorstore.add_documents(
                repo_id=repo_id,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            
            logger.info(f"Stored {len(documents)} embeddings for {repo_id}")
