"""Search node for LangGraph with external web search integration."""
import asyncio
import logging
from app.structure.pydantic import GraphState, NodeStatus, GraphNodeResult

# Import search tools
try:
    from app.tools.search import web_search, SearchResult
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    web_search = None
    SearchResult = None

logger = logging.getLogger(__name__)

def search_node(state: GraphState) -> GraphState:
    """Perform web search using external tools based on research topic and depth."""
    
    if not SEARCH_AVAILABLE:
        logger.warning("Search tools not available - using placeholder")
        state.node_results.append(GraphNodeResult(
            node_name="search",
            status=NodeStatus.COMPLETED,
            output={"search_results": [], "note": "External search tools not available"},
            retry_count=0
        ))
        return state
    
    try:
        # Determine search parameters based on research depth
        depth_search_map = {
            1: {"max_results": 5, "query_variations": 1},    # Shallow
            2: {"max_results": 10, "query_variations": 2},   # Medium  
            3: {"max_results": 15, "query_variations": 3}    # Deep
        }
        
        search_params = depth_search_map.get(state.request.depth, depth_search_map[2])
        
        # Create search queries
        base_query = state.request.topic
        search_queries = [base_query]
        
        # Add query variations for deeper research
        if search_params["query_variations"] > 1:
            search_queries.extend([
                f"{base_query} research analysis",
                f"{base_query} current trends 2025"
            ])
        
        if search_params["query_variations"] > 2:
            search_queries.extend([
                f"{base_query} challenges limitations",
                f"{base_query} future prospects"
            ])
        
        # Perform searches (async function called from sync context)
        all_results = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for query in search_queries[:search_params["query_variations"]]:
                results = loop.run_until_complete(
                    web_search(query, max_results=search_params["max_results"])
                )
                all_results.extend(results)
        finally:
            loop.close()
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls and len(unique_results) < search_params["max_results"]:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Convert to dict format for storage
        search_results = []
        for result in unique_results:
            search_results.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet,
                "source": result.source,
                "relevance_score": result.relevance_score
            })
        
        # Store results in state
        state.search_results = search_results
        
        # Add node result
        state.node_results.append(GraphNodeResult(
            node_name="search",
            status=NodeStatus.COMPLETED,
            output={
                "search_results_count": len(search_results),
                "queries_used": search_queries[:search_params["query_variations"]],
                "depth_level": state.request.depth
            },
            retry_count=0
        ))
        
        logger.info(f"Search completed: {len(search_results)} results found")
        
    except Exception as e:
        logger.error(f"Search node failed: {e}")
        state.node_results.append(GraphNodeResult(
            node_name="search",
            status=NodeStatus.FAILED,
            output={"error": str(e)},
            error_message=str(e),
            retry_count=0
        ))
    
    return state
