"""
Web search tools using DuckDuckGo and Tavily APIs for research.
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from ddgs import DDGS
from app.config import settings

logger = logging.getLogger(__name__)

class SearchResult(BaseModel):
    """Single search result."""
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0

class WebSearchTool:
    """Web search tool using multiple providers."""
    
    def __init__(self):
        self.tavily_api_key = getattr(settings, 'tavily_api_key', None)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo (free, no API key needed)."""
        try:
            logger.info(f"Searching DuckDuckGo for: {query}")
            results = []
            
            # Run DuckDuckGo search in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            
            def _search():
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=max_results))
                    return search_results
            
            search_results = await loop.run_in_executor(None, _search)
            
            for result in search_results:
                search_result = SearchResult(
                    title=result.get('title', ''),
                    url=result.get('href', ''),
                    snippet=result.get('body', ''),
                    source='duckduckgo',
                    relevance_score=0.8  # Default score
                )
                results.append(search_result)
            
            logger.info(f"Found {len(results)} results from DuckDuckGo")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    async def search_tavily(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Tavily API (requires API key)."""
        if not self.tavily_api_key:
            logger.warning("Tavily API key not configured, skipping Tavily search")
            return []
        
        try:
            logger.info(f"Searching Tavily for: {query}")
            
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": True,
                "max_results": max_results
            }
            
            async with self.session.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('results', []):
                        search_result = SearchResult(
                            title=item.get('title', ''),
                            url=item.get('url', ''),
                            snippet=item.get('content', ''),
                            source='tavily',
                            relevance_score=item.get('score', 0.9)
                        )
                        results.append(search_result)
                    
                    logger.info(f"Found {len(results)} results from Tavily")
                    return results
                else:
                    logger.error(f"Tavily API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    async def search(self, query: str, max_results: int = 10, use_multiple_sources: bool = True) -> List[SearchResult]:
        """
        Perform web search using available providers.
        
        Args:
            query: Search query
            max_results: Maximum number of results per source
            use_multiple_sources: Whether to use multiple search providers
        """
        all_results = []
        
        # Always try DuckDuckGo (free)
        ddg_results = await self.search_duckduckgo(query, max_results)
        all_results.extend(ddg_results)
        
        # Try Tavily if API key is available and multiple sources requested
        if use_multiple_sources and self.tavily_api_key:
            tavily_results = await self.search_tavily(query, max_results)
            all_results.extend(tavily_results)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by relevance score
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit total results
        return unique_results[:max_results * 2]  # Allow more results when combining sources

# Convenience function for direct usage
async def web_search(query: str, max_results: int = 10) -> List[SearchResult]:
    """Perform web search using the WebSearchTool."""
    async with WebSearchTool() as search_tool:
        return await search_tool.search(query, max_results)

# LangChain Tool wrapper
try:
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks.manager import AsyncCallbackManagerForToolUse
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.tools import BaseTool
        from langchain.callbacks.manager import AsyncCallbackManagerForToolUse
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        BaseTool = None
        AsyncCallbackManagerForToolUse = None

if LANGCHAIN_AVAILABLE:
    class WebSearchLangChainTool(BaseTool):
        """LangChain wrapper for web search tool."""
        name = "web_search"
        description = "Search the web for current information on any topic. Use this to find recent articles, research papers, and reliable sources."
        
        def _run(self, query: str) -> str:
            """Synchronous version (not implemented)."""
            raise NotImplementedError("This tool only supports async operation")
        
        async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolUse] = None,
        ) -> str:
            """Asynchronous search execution."""
            try:
                results = await web_search(query, max_results=8)
                
                if not results:
                    return "No search results found for the given query."
                
                # Format results for LLM consumption
                formatted_results = []
                for i, result in enumerate(results[:8], 1):
                    formatted_results.append(
                        f"{i}. **{result.title}**\n"
                        f"   URL: {result.url}\n"
                        f"   Summary: {result.snippet}\n"
                        f"   Source: {result.source} (Score: {result.relevance_score:.1f})\n"
                    )
                
                return "\n".join(formatted_results)
                
            except Exception as e:
                logger.error(f"Web search tool error: {e}")
                return f"Search failed: {str(e)}"
else:
    # Placeholder when LangChain is not available
    class WebSearchLangChainTool:
        def __init__(self):
            raise ImportError("LangChain not available for tool integration")
