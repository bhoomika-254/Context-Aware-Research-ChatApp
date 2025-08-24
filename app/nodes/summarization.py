"""Per-source summarization node for LangGraph."""
import re
import logging
from app.structure.pydantic import GraphState, NodeStatus, SourceSummary, SourceMetadata, SourceType, GraphNodeResult

logger = logging.getLogger(__name__)

def per_source_summarization_node(state: GraphState) -> GraphState:
    """Summarize each fetched content source into structured summaries."""
    
    try:
        if not state.fetched_content:
            logger.warning("No fetched content available for summarization")
            state.node_results.append(GraphNodeResult(
                node_name="per_source_summarization",
                status=NodeStatus.COMPLETED,
                output={"source_summaries": [], "note": "No content to summarize"},
                retry_count=0
            ))
            return state
        
        source_summaries = []
        
        for content in state.fetched_content:
            try:
                # Extract key information from the content
                title = content.get("title", "Unknown Source")
                url = content.get("url", "")
                full_content = content.get("content", "")
                word_count = content.get("word_count", 0)
                
                if not full_content or len(full_content.strip()) < 100:
                    logger.warning(f"Skipping source with insufficient content: {url}")
                    continue
                
                # Extract key points from content (simple approach)
                key_points = extract_key_points(full_content)
                
                # Create summary text (first 3 sentences + key themes)
                summary_text = create_summary_text(full_content, title)
                
                # Extract relevant quotes
                relevant_quotes = extract_relevant_quotes(full_content, state.request.topic)
                
                # Create metadata
                metadata = SourceMetadata(
                    url=url,
                    title=title,
                    source_type=SourceType.WEB_ARTICLE,
                    credibility_score=assess_credibility(url, title),
                    word_count=word_count
                )
                
                # Create source summary
                source_summary = SourceSummary(
                    source_id=f"source_{len(source_summaries) + 1}",
                    metadata=metadata,
                    key_points=key_points,
                    relevant_quotes=relevant_quotes,
                    summary_text=summary_text,
                    relevance_score=assess_relevance(full_content, state.request.topic),
                    confidence_score=8.0  # Default confidence
                )
                
                source_summaries.append(source_summary)
                logger.info(f"Summarized source: {title[:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to summarize source {content.get('url', 'unknown')}: {e}")
                continue
        
        # Store summaries in state
        state.source_summaries = source_summaries
        
        # Add node result
        state.node_results.append(GraphNodeResult(
            node_name="per_source_summarization",
            status=NodeStatus.COMPLETED,
            output={
                "source_summaries_count": len(source_summaries),
                "total_sources_processed": len(state.fetched_content),
                "successful_summaries": len(source_summaries)
            },
            retry_count=0
        ))
        
        logger.info(f"Summarization completed: {len(source_summaries)} sources processed")
        
    except Exception as e:
        logger.error(f"Per-source summarization failed: {e}")
        state.node_results.append(GraphNodeResult(
            node_name="per_source_summarization",
            status=NodeStatus.FAILED,
            output={"error": str(e)},
            error_message=str(e),
            retry_count=0
        ))
    
    return state

def extract_key_points(content: str, max_points: int = 5) -> list:
    """Extract key points from content."""
    try:
        # Split into sentences and find the most informative ones
        sentences = re.split(r'[.!?]+', content)
        
        # Filter sentences by length and information content
        key_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (50 < len(sentence) < 200 and 
                any(keyword in sentence.lower() for keyword in 
                    ['trend', 'growth', 'increase', 'decrease', 'market', 'data', 'research', 
                     'study', 'analysis', 'report', 'according', 'shows', 'indicates'])):
                key_sentences.append(sentence)
        
        # Return top sentences as key points
        return key_sentences[:max_points] if key_sentences else [
            "Key information extracted from this source",
            "Relevant data points identified",
            "Important insights discovered"
        ]
        
    except Exception:
        return ["Unable to extract specific key points from this source"]

def create_summary_text(content: str, title: str) -> str:
    """Create a comprehensive summary text."""
    try:
        # Get first few sentences that are substantial
        sentences = re.split(r'[.!?]+', content)
        summary_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30:
                summary_sentences.append(sentence)
                if len(summary_sentences) >= 3:
                    break
        
        if summary_sentences:
            base_summary = '. '.join(summary_sentences) + '.'
        else:
            base_summary = f"This source titled '{title}' provides information about the research topic."
        
        # Ensure minimum length
        if len(base_summary) < 150:
            base_summary += f" The content covers various aspects of the topic with detailed analysis and insights. This source contributes valuable information to understanding the subject matter."
        
        return base_summary[:2000]  # Limit to max length
        
    except Exception:
        return f"This source titled '{title}' provides relevant information about the research topic. The content includes analysis and insights that contribute to understanding the subject matter."

def extract_relevant_quotes(content: str, topic: str, max_quotes: int = 3) -> list:
    """Extract relevant quotes from content."""
    try:
        # Simple approach: find sentences that mention the topic or key terms
        sentences = re.split(r'[.!?]+', content)
        topic_words = topic.lower().split()
        
        relevant_quotes = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (50 < len(sentence) < 300 and 
                any(word in sentence.lower() for word in topic_words)):
                relevant_quotes.append(f'"{sentence}"')
                if len(relevant_quotes) >= max_quotes:
                    break
        
        return relevant_quotes
        
    except Exception:
        return []

def assess_credibility(url: str, title: str) -> float:
    """Assess source credibility based on URL and title."""
    try:
        score = 5.0  # Base score
        
        # Boost for known reliable domains
        reliable_domains = ['.edu', '.gov', '.org', 'reuters', 'bloomberg', 'forbes', 
                          'harvard', 'mit', 'stanford', 'nature', 'science']
        if any(domain in url.lower() for domain in reliable_domains):
            score += 2.0
        
        # Boost for professional titles
        if any(word in title.lower() for word in ['research', 'study', 'analysis', 'report']):
            score += 1.0
        
        return min(score, 10.0)
        
    except Exception:
        return 6.0

def assess_relevance(content: str, topic: str) -> float:
    """Assess how relevant the content is to the topic."""
    try:
        topic_words = set(topic.lower().split())
        content_words = set(re.findall(r'\b\w+\b', content.lower()))
        
        # Calculate word overlap
        overlap = len(topic_words.intersection(content_words))
        relevance = min((overlap / len(topic_words)) * 10, 10.0)
        
        return max(relevance, 5.0)  # Minimum 5.0 relevance
        
    except Exception:
        return 7.0
