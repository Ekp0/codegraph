"""
CodeGraph Backend - Query Routes
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    Citation,
    ReasoningStep,
)
from app.services.query import QueryService
from app.config import settings
import time

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def ask_question(query: QueryRequest):
    """Ask a question about the code in a repository."""
    start_time = time.time()
    
    try:
        # Initialize query service
        query_service = QueryService(
            provider=query.provider or settings.default_llm_provider,
            model=query.model or settings.default_llm_model,
        )
        
        # Process the query
        result = await query_service.process_query(
            repository_id=query.repository_id,
            question=query.question,
        )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            reasoning_steps=result.get("reasoning_steps", []),
            confidence=result.get("confidence", 0.0),
            tokens_used=result.get("tokens_used"),
            processing_time_ms=processing_time_ms,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/{query_id}")
async def get_query(query_id: str):
    """Get a previously executed query and its results."""
    # TODO: Implement query history retrieval from database
    raise HTTPException(status_code=404, detail="Query not found")


@router.post("/explain-function")
async def explain_function(
    repository_id: str,
    file_path: str,
    function_name: str
):
    """Explain a specific function in detail."""
    try:
        query_service = QueryService()
        result = await query_service.explain_function(
            repository_id=repository_id,
            file_path=file_path,
            function_name=function_name,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trace-execution")
async def trace_execution(
    repository_id: str,
    entry_point: str
):
    """Trace execution flow from an entry point."""
    try:
        query_service = QueryService()
        result = await query_service.trace_execution(
            repository_id=repository_id,
            entry_point=entry_point,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
