"""Context management utilities for user history and summarization."""
from typing import List, Optional
from app.structure.pydantic import UserContext, ContextEntry, ContextSummary


def summarize_context_entries(entries: List[ContextEntry]) -> ContextSummary:
    """Summarize a list of context entries into a ContextSummary."""
    if not entries:
        return ContextSummary(
            previous_topics=[],
            recurring_themes=[],
            knowledge_gaps=[],
            summary_text="No prior research context available."
        )
    previous_topics = [e.topic for e in entries]
    # Simple theme extraction: most common words in topics
    all_text = " ".join(e.brief_summary for e in entries)
    recurring_themes = list(set(word for word in all_text.lower().split() if len(word) > 4))[:5]
    knowledge_gaps = ["Further research needed"] if len(entries) < 3 else []
    summary_text = f"Previous research topics: {', '.join(previous_topics)}. Themes: {', '.join(recurring_themes)}."
    return ContextSummary(
        previous_topics=previous_topics,
        recurring_themes=recurring_themes,
        knowledge_gaps=knowledge_gaps,
        summary_text=summary_text
    )


def get_context_for_user(user_id: str, context_repo) -> Optional[ContextSummary]:
    """Fetch and summarize user context for follow-up queries."""
    user_context = context_repo.get_user_context(user_id)
    if user_context and user_context.context_entries:
        return summarize_context_entries(user_context.context_entries)
    return None
