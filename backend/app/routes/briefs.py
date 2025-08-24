"""API routes for research brief generation."""

from fastapi import APIRouter, HTTPException
from app.structure.pydantic import ResearchRequest, FinalBrief
from app.graph.workflow import run_research_graph
from app.structure.pydantic import GraphState
from app.services.monitoring import monitoring_service, ExecutionMetrics
import uuid
import logging
import time
from typing import Dict, Any

router = APIRouter(tags=["briefs"])

@router.post("/brief", response_model=FinalBrief)
async def generate_brief(request: ResearchRequest):
    """Generate a research brief based on the provided topic and parameters."""
    
    # Initialize monitoring
    request_id = str(uuid.uuid4())
    metrics = monitoring_service.start_execution(request_id)
    
    try:
        # Create initial graph state
        state = GraphState(
            request=request,
            request_id=request_id,
            user_context=None,
            context_summary=None,
            research_plan=None,
            search_results=[],
            fetched_content=[],
            source_summaries=[],
            final_brief=None,
            node_results=[],
            current_node=None,
            error_state=None,
            start_time=metrics.start_time,
            end_time=None,
            llm_calls={},
            token_usage={}
        )
        
        # Run the LangGraph workflow
        final_state = await run_research_graph(state)
        
        # Finish monitoring
        completed_metrics = monitoring_service.finish_execution(request_id)
        
        # Add execution metrics to the response
        if final_state.final_brief:
            # Update the existing fields in the brief
            if completed_metrics:
                final_state.final_brief.processing_time_seconds = completed_metrics.duration_seconds
                final_state.final_brief.token_usage = completed_metrics.token_usage
                final_state.final_brief.metadata = {
                    "execution_time_seconds": round(completed_metrics.duration_seconds, 2),
                    "total_tokens_used": completed_metrics.get_total_tokens(),
                    "node_breakdown": completed_metrics.node_metrics,
                    "request_id": request_id,
                    "trace_url": f"https://smith.langchain.com/o/your-org/projects/p/context-aware-research-app/r/{request_id}"
                }
            
            return final_state.final_brief
        else:
            monitoring_service.finish_execution(request_id, "Failed to generate research brief")
            raise HTTPException(status_code=500, detail="Failed to generate research brief.")
            
    except Exception as e:
        monitoring_service.finish_execution(request_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics():
    """Get application metrics for monitoring."""
    return {
        "status": "healthy",
        "features": {
            "langsmith_tracing": True,
            "token_tracking": True,
            "latency_monitoring": True,
            "node_level_metrics": True
        },
        "endpoints": {
            "generate_brief": "/brief",
            "health_check": "/health",
            "metrics": "/metrics"
        },
        "monitoring": {
            "active_executions": len(monitoring_service.active_executions),
            "langsmith_project": "context-aware-research-app",
            "trace_endpoint": "https://smith.langchain.com"
        }
    }

@router.get("/execution/{request_id}")
async def get_execution_metrics(request_id: str):
    """Get metrics for a specific execution."""
    metrics = monitoring_service.get_execution_summary(request_id)
    if metrics:
        return metrics
    else:
        raise HTTPException(status_code=404, detail="Execution not found or already completed")