"""Pydantic models for structured data validation across the research assistant."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, validator


# Enums for type safety
class ResearchDepth(str, Enum):
    """Research depth levels."""
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


class SourceType(str, Enum):
    """Types of research sources."""
    WEB_ARTICLE = "web_article"
    ACADEMIC_PAPER = "academic_paper"
    NEWS_ARTICLE = "news_article"
    BLOG_POST = "blog_post"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class NodeStatus(str, Enum):
    """Status of graph node execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    LLAMA = "llama"


# Base models
class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response models
class ResearchRequest(BaseModel):
    """Request model for research brief generation."""
    topic: str = Field(..., min_length=5, max_length=500, description="Research topic")
    depth: int = Field(..., ge=1, le=3, description="Research depth level (1=shallow, 2=medium, 3=deep)")
    follow_up: bool = Field(False, description="Whether this is a follow-up query")
    user_id: str = Field(..., min_length=1, max_length=100, description="Unique user identifier")
    context_limit: Optional[int] = Field(5, ge=1, le=10, description="Maximum context entries to consider")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Previous conversation history for context")
    
    @property
    def depth_str(self) -> str:
        """Convert integer depth to string representation."""
        depth_mapping = {1: "shallow", 2: "medium", 3: "deep"}
        return depth_mapping.get(self.depth, "medium")


# Research Planning models
class ResearchStep(BaseModel):
    """Individual research step in the planning phase."""
    step_id: str = Field(..., description="Unique identifier for the step")
    description: str = Field(..., min_length=10, description="Description of what this step accomplishes")
    search_queries: List[str] = Field(..., min_items=1, max_items=5, description="Search queries for this step")
    expected_sources: int = Field(..., ge=1, le=10, description="Expected number of sources")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest, 5=lowest)")


class ResearchPlanningSteps(BaseModel):
    """Structured research planning output."""
    topic: str = Field(..., description="Original research topic")
    refined_topic: str = Field(..., description="Refined and clarified research topic")
    research_questions: List[str] = Field(..., min_items=1, max_items=8, description="Key research questions to answer")
    steps: List[ResearchStep] = Field(..., min_items=1, max_items=10, description="Ordered research steps")
    estimated_duration_minutes: int = Field(..., ge=5, le=120, description="Estimated research duration")
    complexity_score: float = Field(..., ge=1.0, le=10.0, description="Research complexity (1=simple, 10=highly complex)")


# Source and Content models
class SourceMetadata(BaseModel):
    """Metadata for a research source."""
    url: Optional[HttpUrl] = Field(None, description="Source URL if available")
    title: Optional[str] = Field(None, description="Source title")
    author: Optional[str] = Field(None, description="Source author")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    source_type: SourceType = Field(SourceType.OTHER, description="Type of source")
    credibility_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Credibility assessment (0-10)")
    word_count: Optional[int] = Field(None, ge=0, description="Source word count")


class SourceSummary(BaseModel):
    """Summary of an individual research source."""
    source_id: str = Field(..., description="Unique identifier for the source")
    metadata: SourceMetadata = Field(..., description="Source metadata")
    key_points: List[str] = Field(..., min_items=1, max_items=10, description="Key points from the source")
    relevant_quotes: List[str] = Field(default_factory=list, max_items=5, description="Relevant quotes with context")
    summary_text: str = Field(..., min_length=100, max_length=2000, description="Comprehensive summary")
    relevance_score: float = Field(..., ge=0.0, le=10.0, description="Relevance to research topic (0-10)")
    confidence_score: float = Field(..., ge=0.0, le=10.0, description="Confidence in summary accuracy (0-10)")


# Context and History models
class ContextEntry(BaseModel):
    """Single entry in user context history."""
    entry_id: str = Field(..., description="Unique identifier for context entry")
    topic: str = Field(..., description="Original research topic")
    brief_summary: str = Field(..., min_length=50, max_length=500, description="Brief summary of the research")
    key_findings: List[str] = Field(..., max_items=5, description="Key findings from the research")
    timestamp: datetime = Field(..., description="When this research was conducted")


class UserContext(BaseModel):
    """User's research context and history."""
    user_id: str = Field(..., description="User identifier")
    context_entries: List[ContextEntry] = Field(default_factory=list, description="Historical context entries")
    total_interactions: int = Field(0, ge=0, description="Total number of interactions")
    
    @validator('context_entries')
    def validate_context_entries(cls, v):
        """Ensure context entries are sorted by timestamp (newest first)."""
        return sorted(v, key=lambda x: x.timestamp, reverse=True)


class ContextSummary(BaseModel):
    """Summarized context for follow-up queries."""
    previous_topics: List[str] = Field(..., description="Previously researched topics")
    recurring_themes: List[str] = Field(default_factory=list, description="Recurring themes across interactions")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Identified knowledge gaps")
    summary_text: str = Field(..., min_length=50, max_length=1000, description="Narrative summary of context")


# Final output models
class ResearchInsight(BaseModel):
    """Individual insight from the research."""
    insight_id: str = Field(..., description="Unique identifier for the insight")
    category: str = Field(..., description="Category or theme of the insight")
    description: str = Field(..., min_length=50, description="Detailed description of the insight")
    supporting_sources: List[str] = Field(..., description="Source IDs that support this insight")
    confidence_level: float = Field(..., ge=0.0, le=10.0, description="Confidence in this insight (0-10)")


class FinalBrief(TimestampedModel):
    """Final structured research brief output."""
    request_id: str = Field(..., description="Unique identifier for this research request")
    topic: str = Field(..., description="Research topic")
    executive_summary: str = Field(..., min_length=200, max_length=1000, description="Executive summary of findings")
    
    # Core content
    key_findings: List[str] = Field(..., min_items=3, max_items=15, description="Key research findings")
    detailed_analysis: str = Field(..., min_length=500, description="Detailed analysis and synthesis")
    insights: List[ResearchInsight] = Field(..., min_items=1, description="Research insights")
    
    # Sources and references
    sources: List[SourceSummary] = Field(..., min_items=1, description="Source summaries")
    source_count: int = Field(..., ge=1, description="Total number of sources used")
    
    # Metadata
    research_depth: ResearchDepth = Field(..., description="Depth of research conducted")
    confidence_score: float = Field(..., ge=0.0, le=10.0, description="Overall confidence in findings")
    limitations: List[str] = Field(default_factory=list, description="Research limitations and caveats")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggestions for follow-up research")
    
    # Context information (for follow-ups)
    is_follow_up: bool = Field(False, description="Whether this was a follow-up query")
    context_used: Optional[ContextSummary] = Field(None, description="Context summary used for follow-ups")
    
    # Performance metrics
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Total processing time")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage by provider")
    
    # Execution metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution metadata including trace URLs and detailed metrics")


# Graph State models
class GraphNodeResult(BaseModel):
    """Result from a single graph node execution."""
    node_name: str = Field(..., description="Name of the executed node")
    status: NodeStatus = Field(..., description="Execution status")
    output: Optional[Dict[str, Any]] = Field(None, description="Node output data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time_seconds: Optional[float] = Field(None, ge=0, description="Node execution time")
    retry_count: int = Field(0, ge=0, description="Number of retries attempted")


class GraphState(BaseModel):
    """Complete state for the LangGraph execution."""
    # Request information
    request: ResearchRequest = Field(..., description="Original research request")
    request_id: str = Field(..., description="Unique request identifier")
    
    # Context and planning
    user_context: Optional[UserContext] = Field(None, description="User's historical context")
    context_summary: Optional[ContextSummary] = Field(None, description="Summarized context for follow-ups")
    research_plan: Optional[ResearchPlanningSteps] = Field(None, description="Research planning steps")
    
    # Source collection and processing
    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="Raw search results")
    fetched_content: List[Dict[str, Any]] = Field(default_factory=list, description="Fetched content from sources")
    source_summaries: List[SourceSummary] = Field(default_factory=list, description="Individual source summaries")
    
    # Final output
    final_brief: Optional[FinalBrief] = Field(None, description="Final research brief")
    
    # Execution tracking
    node_results: List[GraphNodeResult] = Field(default_factory=list, description="Results from graph nodes")
    current_node: Optional[str] = Field(None, description="Currently executing node")
    error_state: Optional[str] = Field(None, description="Error state if execution failed")
    
    # Performance tracking
    start_time: Optional[datetime] = Field(None, description="Graph execution start time")
    end_time: Optional[datetime] = Field(None, description="Graph execution end time")
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Total processing time")
    llm_calls: Dict[LLMProvider, int] = Field(default_factory=dict, description="Count of LLM calls by provider")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage tracking")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        extra = "forbid"
        validate_assignment = True


# Error models
class ValidationError(BaseModel):
    """Structured validation error information."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    invalid_value: Optional[Any] = Field(None, description="The invalid value")


class APIError(BaseModel):
    """Structured API error response."""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    validation_errors: Optional[List[ValidationError]] = Field(None, description="Validation errors if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")