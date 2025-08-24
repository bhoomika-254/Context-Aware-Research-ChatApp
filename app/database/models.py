"""Database models for Supabase tables."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.structure.pydantic import (
    UserContext, 
    ContextEntry, 
    FinalBrief, 
    ResearchRequest,
    TimestampedModel
)


class UserContextModel(TimestampedModel):
    """Database model for user context storage in Supabase."""
    
    id: Optional[str] = Field(None, description="Supabase auto-generated ID")
    user_id: str = Field(..., description="User identifier")
    context_data: Dict[str, Any] = Field(..., description="Serialized UserContext data")
    last_interaction: datetime = Field(..., description="Last interaction timestamp")
    total_interactions: int = Field(0, description="Total number of interactions")
    
    @classmethod
    def from_user_context(cls, user_context: UserContext) -> "UserContextModel":
        """Create model from UserContext."""
        return cls(
            user_id=user_context.user_id,
            context_data=user_context.dict(),
            last_interaction=datetime.utcnow(),
            total_interactions=user_context.total_interactions
        )
    
    def to_user_context(self) -> UserContext:
        """Convert to UserContext."""
        return UserContext(**self.context_data)


class ResearchBriefModel(TimestampedModel):
    """Database model for research briefs storage in Supabase."""
    
    id: Optional[str] = Field(None, description="Supabase auto-generated ID")
    request_id: str = Field(..., description="Unique request identifier")
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Research topic")
    brief_data: Dict[str, Any] = Field(..., description="Serialized FinalBrief data")
    is_follow_up: bool = Field(False, description="Whether this was a follow-up query")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")
    
    @classmethod
    def from_final_brief(cls, brief: FinalBrief, request: ResearchRequest) -> "ResearchBriefModel":
        """Create model from FinalBrief and ResearchRequest."""
        return cls(
            request_id=brief.request_id,
            user_id=request.user_id,
            topic=brief.topic,
            brief_data=brief.dict(),
            is_follow_up=brief.is_follow_up,
            processing_time_seconds=brief.processing_time_seconds,
            token_usage=brief.token_usage
        )
    
    def to_final_brief(self) -> FinalBrief:
        """Convert to FinalBrief."""
        return FinalBrief(**self.brief_data)


class ResearchSessionModel(TimestampedModel):
    """Database model for research sessions."""
    
    id: Optional[str] = Field(None, description="Supabase auto-generated ID")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    request_ids: List[str] = Field(default_factory=list, description="List of request IDs in this session")
    session_summary: Optional[str] = Field(None, description="Session summary")
    total_requests: int = Field(0, description="Total requests in session")
    session_duration_seconds: Optional[float] = Field(None, description="Session duration")


# Supabase table schemas (for reference in Phase 4)
SUPABASE_TABLES = {
    "user_contexts": {
        "id": "uuid primary key default gen_random_uuid()",
        "user_id": "text not null",
        "context_data": "jsonb not null",
        "last_interaction": "timestamp with time zone not null",
        "total_interactions": "integer default 0",
        "created_at": "timestamp with time zone default now()",
        "updated_at": "timestamp with time zone default now()"
    },
    "research_briefs": {
        "id": "uuid primary key default gen_random_uuid()",
        "request_id": "text unique not null",
        "user_id": "text not null",
        "topic": "text not null",
        "brief_data": "jsonb not null",
        "is_follow_up": "boolean default false",
        "processing_time_seconds": "real",
        "token_usage": "jsonb",
        "created_at": "timestamp with time zone default now()",
        "updated_at": "timestamp with time zone default now()"
    },
    "research_sessions": {
        "id": "uuid primary key default gen_random_uuid()",
        "session_id": "text unique not null",
        "user_id": "text not null",
        "request_ids": "text[]",
        "session_summary": "text",
        "total_requests": "integer default 0",
        "session_duration_seconds": "real",
        "created_at": "timestamp with time zone default now()",
        "updated_at": "timestamp with time zone default now()"
    }
}
