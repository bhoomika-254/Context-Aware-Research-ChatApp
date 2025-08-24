"""Configuration management for the Context-Aware Research Assistant."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # LLM API Keys
    google_api_key: str = Field(..., description="Google AI Studio API key")
    together_api_key: str = Field(..., description="Together AI API key")
    langsmith_api_key: Optional[str] = Field(None, description="LangSmith API key for tracing")
    
    # External Tool API Keys
    tavily_api_key: Optional[str] = Field(None, description="Tavily API key for enhanced web search")
    serper_api_key: Optional[str] = Field(None, description="Serper API key for Google search")
    
    # LangSmith Configuration
    langchain_tracing_v2: bool = Field(True, description="Enable LangChain tracing")
    langchain_endpoint: str = Field("https://api.smith.langchain.com", description="LangSmith endpoint")
    langchain_project: str = Field("context-aware-research-app", description="LangSmith project name")
    
    # Application Configuration
    app_name: str = Field("Context-Aware Research Assistant", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")
    api_workers: int = Field(1, description="Number of API workers")
    
    # LLM Configuration
    default_llm_provider: str = Field("gemini", description="Default LLM provider")
    gemini_model: str = Field("gemini-1.5-flash", description="Gemini model name")
    llama_model: str = Field("meta-llama/Llama-2-7b-chat-hf", description="Llama model name")
    max_tokens: int = Field(4096, description="Maximum tokens per request")
    temperature: float = Field(0.1, description="LLM temperature")
    
    # Rate Limiting
    requests_per_minute: int = Field(60, description="Requests per minute limit")
    burst_limit: int = Field(10, description="Burst request limit")
    
    # Search Configuration
    max_search_results: int = Field(10, description="Maximum search results to fetch")
    max_content_length: int = Field(50000, description="Maximum content length to process")
    
    # Context Configuration
    max_context_history: int = Field(5, description="Maximum context history to maintain")
    context_summary_length: int = Field(1000, description="Maximum context summary length")


# Global settings instance
settings = Settings()