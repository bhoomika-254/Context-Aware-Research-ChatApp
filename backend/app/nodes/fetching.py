"""Content fetching node for LangGraph with web content extraction."""
import asyncio
import logging
from app.structure.pydantic import GraphState, NodeStatus, GraphNodeResult

# Import content fetching tools
try:
    from app.tools.fetcher import fetch_web_content, FetchedContent
    FETCHER_AVAILABLE = True
except ImportError:
    FETCHER_AVAILABLE = False
    fetch_web_content = None
    FetchedContent = None

logger = logging.getLogger(__name__)

def content_fetching_node(state: GraphState) -> GraphState:
    """Fetch content from URLs found in search results based on research depth."""
    
    if not FETCHER_AVAILABLE:
        logger.warning("Content fetcher tools not available - using placeholder")
        state.node_results.append(GraphNodeResult(
            node_name="content_fetching",
            status=NodeStatus.COMPLETED,
            output={"fetched_content": [], "note": "Content fetcher tools not available"},
            retry_count=0
        ))
        return state
    
    try:
        # Check if we have search results to fetch from
        if not state.search_results:
            logger.warning("No search results available for content fetching")
            state.node_results.append(GraphNodeResult(
                node_name="content_fetching",
                status=NodeStatus.COMPLETED,
                output={"fetched_content": [], "note": "No search results to fetch from"},
                retry_count=0
            ))
            return state
        
        # Determine how many URLs to fetch based on research depth
        depth_fetch_map = {
            1: 3,   # Shallow - fetch top 3 URLs
            2: 6,   # Medium - fetch top 6 URLs
            3: 10   # Deep - fetch top 10 URLs
        }
        
        max_urls = depth_fetch_map.get(state.request.depth, 6)
        
        # Extract URLs from search results
        urls_to_fetch = []
        for result in state.search_results[:max_urls]:
            if result.get("url"):
                urls_to_fetch.append(result["url"])
        
        if not urls_to_fetch:
            logger.warning("No valid URLs found in search results")
            state.node_results.append(GraphNodeResult(
                node_name="content_fetching",
                status=NodeStatus.COMPLETED,
                output={"fetched_content": [], "note": "No valid URLs in search results"},
                retry_count=0
            ))
            return state
        
        # Fetch content (async function called from sync context)
        logger.info(f"Fetching content from {len(urls_to_fetch)} URLs")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            fetched_results = loop.run_until_complete(
                fetch_web_content(urls_to_fetch)
            )
        finally:
            loop.close()
        
        # Convert to dict format and filter successful fetches
        fetched_content = []
        successful_fetches = 0
        
        for result in fetched_results:
            if result.success and result.content:
                fetched_content.append({
                    "url": result.url,
                    "title": result.title,
                    "content": result.content,
                    "word_count": result.word_count,
                    "metadata": result.metadata,
                    "fetch_time": result.fetch_time
                })
                successful_fetches += 1
            else:
                logger.warning(f"Failed to fetch content from {result.url}: {result.error_message}")
        
        # Store results in state
        state.fetched_content = fetched_content
        
        # Add node result
        state.node_results.append(GraphNodeResult(
            node_name="content_fetching",
            status=NodeStatus.COMPLETED,
            output={
                "total_urls_attempted": len(urls_to_fetch),
                "successful_fetches": successful_fetches,
                "failed_fetches": len(urls_to_fetch) - successful_fetches,
                "total_words_fetched": sum(item["word_count"] for item in fetched_content),
                "depth_level": state.request.depth
            },
            retry_count=0
        ))
        
        logger.info(f"Content fetching completed: {successful_fetches}/{len(urls_to_fetch)} successful")
        
    except Exception as e:
        logger.error(f"Content fetching node failed: {e}")
        state.node_results.append(GraphNodeResult(
            node_name="content_fetching",
            status=NodeStatus.FAILED,
            output={"error": str(e)},
            error_message=str(e),
            retry_count=0
        ))
    
    return state
