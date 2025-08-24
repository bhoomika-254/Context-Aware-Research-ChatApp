"""LangGraph workflow orchestration for research brief generation."""


from typing import Any, Dict, Optional
from datetime import datetime
import time
import logging
from langgraph.graph import StateGraph, START, END
from app.structure.pydantic import GraphState, NodeStatus, LLMProvider
from app.services.llm import llm_service
from app.services.monitoring import monitoring_service
from app.config import settings


# Node imports (to be implemented in app/nodes/)
from app.nodes.context import context_summarization_node
from app.nodes.planning import planning_node
from app.nodes.search import search_node
from app.nodes.fetching import content_fetching_node
from app.nodes.summarization import per_source_summarization_node
from app.nodes.synthesis import synthesis_node
from app.nodes.postprocess import post_processing_node


class ResearchGraph(StateGraph):
    """LangGraph for orchestrating research brief generation with tracing and monitoring."""
    def __init__(self):
        super().__init__(GraphState)
        self.add_nodes()
        self.add_edges()

    def add_nodes(self):
        self.add_node("context_summarization", context_summarization_node)
        self.add_node("planning", planning_node)
        self.add_node("search", search_node)
        self.add_node("content_fetching", content_fetching_node)
        self.add_node("per_source_summarization", per_source_summarization_node)
        self.add_node("synthesis", synthesis_node)
        self.add_node("post_processing", post_processing_node)

    def add_edges(self):
        # Add edges from START to first node and from last node to END
        self.add_edge(START, "context_summarization")
        
        # Simple linear flow for now
        self.add_edge("context_summarization", "planning")
        self.add_edge("planning", "search")
        self.add_edge("search", "content_fetching")
        self.add_edge("content_fetching", "per_source_summarization")
        self.add_edge("per_source_summarization", "synthesis")
        self.add_edge("synthesis", "post_processing")
        
        # Add edge from last node to END
        self.add_edge("post_processing", END)

    def compile_graph(self):
        """Compile the graph for execution."""
        compiled = self.compile()
        return compiled

# Entrypoint for running the graph with tracing, latency, and token usage tracking
async def run_research_graph(initial_state: GraphState) -> GraphState:
    logger = logging.getLogger("research-graph")
    logger.info("Starting research graph execution.")
    start_time = time.time()
    initial_state.start_time = datetime.utcnow()
    
    # Create and compile the graph
    graph_builder = ResearchGraph()
    compiled_graph = graph_builder.compile_graph()
    
    # Execute the graph with monitoring
    try:
        # Add monitoring integration for node-level tracking
        state_dict = initial_state.dict()
        
        # Add monitoring hooks if available
        if hasattr(initial_state, 'request_id') and initial_state.request_id:
            logger.info(f"Starting graph execution for request {initial_state.request_id}")
        
        result = await compiled_graph.ainvoke(state_dict, {"configurable": {"thread_id": "research-session"}})
        
        # Convert back to GraphState
        if isinstance(result, dict):
            final_state = GraphState(**result)
        else:
            final_state = result
            
        final_state.end_time = datetime.utcnow()
        final_state.processing_time_seconds = time.time() - start_time
        logger.info(f"Graph execution complete in {final_state.processing_time_seconds:.2f}s.")
        
        # Add node metrics to monitoring if request_id is available
        if hasattr(final_state, 'request_id') and final_state.request_id:
            # Add total execution metrics
            monitoring_service.add_node_metrics(
                final_state.request_id, 
                "graph_execution", 
                final_state.processing_time_seconds,
                sum(final_state.token_usage.values()) if hasattr(final_state, 'token_usage') and final_state.token_usage else 0
            )
        
        # Token usage tracking
        if hasattr(final_state, "token_usage") and final_state.token_usage:
            logger.info(f"Token usage: {final_state.token_usage}")
            
        # LangSmith trace link
        if settings.langsmith_api_key and hasattr(final_state, 'request_id'):
            logger.info(f"Trace available in LangSmith: https://smith.langchain.com/o/your-org/projects/p/context-aware-research-app/r/{final_state.request_id}")
            
        return final_state
    except Exception as e:
        logger.exception("Graph execution failed.")
        raise
