"""Context summarization node for LangGraph using session-based storage."""
from app.structure.pydantic import GraphState, NodeStatus, ContextSummary
from typing import List, Dict, Any
import logging

def summarize_conversation_history(conversation_history: List[Dict[str, Any]]) -> ContextSummary:
    """Summarize conversation history into structured context."""
    if not conversation_history:
        return ContextSummary(
            previous_topics=[],
            recurring_themes=[],
            knowledge_gaps=[],
            summary_text="This is the beginning of a new research conversation. No prior research context is available from previous interactions. The system will generate comprehensive research briefs based on the current query."
        )
    
    # Extract topics from previous queries
    previous_topics = []
    all_content = []
    
    for entry in conversation_history:
        if "query" in entry:
            previous_topics.append(entry["query"])
        if "response" in entry:
            # Extract key points from response
            response_summary = entry["response"][:200] + "..." if len(entry["response"]) > 200 else entry["response"]
            all_content.append(response_summary)
    
    # Simple theme extraction from combined content
    all_text = " ".join(all_content).lower()
    # Extract common meaningful words (simple approach)
    words = [word for word in all_text.split() if len(word) > 4 and word.isalpha()]
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Get top recurring themes
    recurring_themes = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    recurring_themes = [theme[0] for theme in recurring_themes]
    
    # Identify knowledge gaps (areas that might need follow-up)
    knowledge_gaps = []
    if len(conversation_history) < 3:
        knowledge_gaps.append("Limited research history - may need more comprehensive analysis")
    
    # Create summary text
    topics_text = ", ".join(previous_topics[-3:]) if previous_topics else "general topics"
    themes_text = ", ".join(recurring_themes[:3]) if recurring_themes else "initial exploration"
    
    summary_text = f"Previous research in this session has covered: {topics_text}. Key recurring themes identified include: {themes_text}. This follow-up query should build on these previous insights and expand the research scope to provide comprehensive analysis."
    
    # Ensure summary meets minimum length requirement
    if len(summary_text) < 50:
        summary_text += " The research assistant will integrate this context to provide more targeted and relevant information for the user's continued investigation."
    
    return ContextSummary(
        previous_topics=previous_topics,
        recurring_themes=recurring_themes,
        knowledge_gaps=knowledge_gaps,
        summary_text=summary_text
    )

def context_summarization_node(state: GraphState) -> GraphState:
    """Summarize user context for follow-up queries using session history."""
    logger = logging.getLogger("context_node")
    
    try:
        # Get conversation history from the request context
        # This will be passed from the API route
        conversation_history = getattr(state.request, 'conversation_history', [])
        
        if conversation_history:
            logger.info(f"Summarizing context from {len(conversation_history)} previous interactions")
            context_summary = summarize_conversation_history(conversation_history)
        else:
            logger.info("No previous context found - starting fresh conversation")
            context_summary = ContextSummary(
                previous_topics=[],
                recurring_themes=[],
                knowledge_gaps=[],
                summary_text="This is the beginning of a new research conversation. No previous context is available. The user is starting fresh with their research inquiry and this system will help build comprehensive research briefs based on their questions and interests."
            )
        
        state.context_summary = context_summary
        status = NodeStatus.COMPLETED
        output = {
            "context_summary": context_summary.dict(),
            "previous_topics_count": len(context_summary.previous_topics),
            "has_context": len(context_summary.previous_topics) > 0
        }
        
        logger.info(f"Context summarization completed. Found {len(context_summary.previous_topics)} previous topics")
        
    except Exception as e:
        logger.error(f"Context summarization failed: {e}")
        status = NodeStatus.FAILED
        output = {"error": str(e)}
        # Set empty context on failure
        state.context_summary = ContextSummary(
            previous_topics=[],
            recurring_themes=[],
            knowledge_gaps=[],
            summary_text="Context summarization is currently unavailable due to a technical issue. The system will proceed with generating research briefs based on the current query without previous context integration."
        )
    
    state.node_results.append({
        "node_name": "context_summarization",
        "status": status,
        "output": output,
        "retry_count": 0
    })
    
    return state
