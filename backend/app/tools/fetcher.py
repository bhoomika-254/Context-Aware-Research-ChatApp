"""
Content fetching and processing tools for extracting information from web pages.
"""
import asyncio
import aiohttp
import logging
import warnings
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time

# Suppress SSL warnings and resource warnings
warnings.filterwarnings("ignore", message="unclosed.*ssl.SSLSocket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)

logger = logging.getLogger(__name__)

class FetchedContent(BaseModel):
    """Fetched and processed content from a web page."""
    url: str
    title: str
    content: str
    word_count: int
    metadata: Dict[str, Any]
    fetch_time: float
    success: bool
    error_message: Optional[str] = None

class ContentFetcher:
    """Tool for fetching and processing web content."""
    
    def __init__(self, timeout: int = 30, max_content_length: int = 50000):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            # Import brotli for handling compressed content
            import brotli
        except ImportError:
            logger.warning("Brotli compression library not installed. Some content may not be properly fetched.")
            
        # Enhanced headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers=headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def extract_text_from_html(self, html: str, url: str) -> Dict[str, Any]:
        """Extract clean text and metadata from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else urlparse(url).path
            
            # Extract main content
            # Try to find main content areas
            main_content = None
            for selector in ['main', 'article', '.content', '#content', '.post', '.entry']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body') or soup
            
            # Extract text
            text = main_content.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract metadata
            metadata = {}
            
            # Meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property', '').replace('og:', '')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
            
            # Extract headings for structure
            headings = []
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                headings.append(heading.get_text().strip())
            metadata['headings'] = headings[:10]  # Limit headings
            
            return {
                'title': title,
                'content': text[:self.max_content_length],
                'word_count': len(text.split()),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")
            return {
                'title': url,
                'content': '',
                'word_count': 0,
                'metadata': {},
                'error': str(e)
            }
    
    async def fetch_url(self, url: str) -> FetchedContent:
        """Fetch content from a single URL."""
        start_time = time.time()
        
        try:
            logger.info(f"Fetching content from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract and process content
                    extracted = self.extract_text_from_html(html, url)
                    
                    fetch_time = time.time() - start_time
                    
                    return FetchedContent(
                        url=url,
                        title=extracted['title'],
                        content=extracted['content'],
                        word_count=extracted['word_count'],
                        metadata=extracted['metadata'],
                        fetch_time=fetch_time,
                        success=True
                    )
                elif response.status in (403, 429, 503):
                    # Handle access denied (403), rate limiting (429), or service unavailable (503)
                    status_messages = {
                        403: "HTTP 403 - Access Forbidden (website blocked the request)",
                        429: "HTTP 429 - Too Many Requests (rate limited)",
                        503: "HTTP 503 - Service Unavailable (website temporarily unavailable)"
                    }
                    error_msg = status_messages.get(response.status, f"HTTP {response.status}")
                    logger.warning(f"Access issue for {url}: {error_msg}")
                    
                    # Return partial content with URL and domain info for research context
                    domain = urlparse(url).netloc
                    site_name = domain.replace("www.", "").split(".")[0].capitalize()
                    
                    # Create meaningful fallback content based on the URL and domain
                    fallback_content = (
                        f"Content from {site_name} ({domain}) could not be accessed due to {error_msg}. "
                        f"The requested URL was: {url}. "
                        f"Based on the URL, this appears to be content about {' '.join(url.split('/')[-1].split('-'))}. "
                        f"The site {site_name} is known for providing information on this topic. "
                        f"Consider checking this source directly in a browser or using an alternative source."
                    )
                    
                    return FetchedContent(
                        url=url,
                        title=f"Access Issue - {site_name}",
                        content=fallback_content,
                        word_count=len(fallback_content.split()),
                        metadata={'status': 'access_restricted', 'domain': domain, 'http_status': response.status},
                        fetch_time=time.time() - start_time,
                        success=False,
                        error_message=error_msg
                    )
                else:
                    error_msg = f"HTTP {response.status}"
                    logger.warning(f"Failed to fetch {url}: {error_msg}")
                    
                    # Create a more helpful empty response
                    domain = urlparse(url).netloc
                    site_name = domain.replace("www.", "").split(".")[0].capitalize()
                    
                    fallback_content = (
                        f"Unable to retrieve content from {site_name} ({domain}). "
                        f"The server returned HTTP status {response.status}. "
                        f"This may be temporary - consider trying again later."
                    )
                    
                    return FetchedContent(
                        url=url,
                        title=f"Retrieval Failed - {site_name}",
                        content=fallback_content,
                        word_count=len(fallback_content.split()),
                        metadata={'status': response.status, 'domain': domain},
                        fetch_time=time.time() - start_time,
                        success=False,
                        error_message=error_msg
                    )
                    
        except aiohttp.ClientError as e:
            error_msg = str(e)
            logger.error(f"Client error fetching {url}: {error_msg}")
            
            # Create informative content for client errors
            domain = urlparse(url).netloc
            site_name = domain.replace("www.", "").split(".")[0].capitalize()
            
            fallback_content = (
                f"Unable to connect to {site_name} ({domain}). "
                f"Error: {error_msg}. "
                f"This could be due to network issues, DNS problems, or the site being unavailable."
            )
            
            return FetchedContent(
                url=url,
                title=f"Connection Error - {site_name}",
                content=fallback_content,
                word_count=len(fallback_content.split()),
                metadata={'error_type': 'client_error', 'domain': domain},
                fetch_time=time.time() - start_time,
                success=False,
                error_message=error_msg
            )
    
    async def fetch_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[FetchedContent]:
        """Fetch content from multiple URLs concurrently."""
        if not urls:
            return []
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url):
            async with semaphore:
                return await self.fetch_url(url)
        
        # Execute fetches concurrently
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        fetched_content = []
        for result in results:
            if isinstance(result, FetchedContent):
                fetched_content.append(result)
            else:
                logger.error(f"Fetch task failed: {result}")
        
        return fetched_content

# Convenience function
async def fetch_web_content(urls: List[str]) -> List[FetchedContent]:
    """Fetch content from web URLs."""
    async with ContentFetcher() as fetcher:
        return await fetcher.fetch_multiple(urls)

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
    class ContentFetcherLangChainTool(BaseTool):
        """LangChain wrapper for content fetching tool."""
        name = "fetch_web_content"
        description = "Fetch and extract clean text content from web pages. Provide a list of URLs to extract readable content."
        
        def _run(self, urls: str) -> str:
            """Synchronous version (not implemented)."""
            raise NotImplementedError("This tool only supports async operation")
        
        async def _arun(
            self,
            urls: str,
            run_manager = None,
        ) -> str:
            """Asynchronous content fetching."""
            try:
                # Parse URLs (expect comma-separated string)
                url_list = [url.strip() for url in urls.split(',') if url.strip()]
                
                if not url_list:
                    return "No valid URLs provided."
                
                # Fetch content
                fetched_results = await fetch_web_content(url_list[:5])  # Limit to 5 URLs
                
                if not fetched_results:
                    return "Failed to fetch content from any of the provided URLs."
                
                # Format results for LLM
                formatted_results = []
                for result in fetched_results:
                    if result.success and result.content:
                        formatted_results.append(
                            f"**{result.title}**\n"
                            f"URL: {result.url}\n"
                            f"Word Count: {result.word_count}\n"
                            f"Content Preview: {result.content[:500]}...\n"
                            f"---"
                        )
                    else:
                        formatted_results.append(
                            f"**Failed: {result.url}**\n"
                            f"Error: {result.error_message or 'Unknown error'}\n"
                            f"---"
                        )
                
                return "\n".join(formatted_results)
                
            except Exception as e:
                logger.error(f"Content fetcher tool error: {e}")
                return f"Content fetching failed: {str(e)}"
else:
    # Placeholder when LangChain is not available
    class ContentFetcherLangChainTool:
        def __init__(self):
            raise ImportError("LangChain not available for tool integration")
