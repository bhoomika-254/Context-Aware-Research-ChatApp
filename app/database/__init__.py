"""Database models and configuration using Supabase."""

from .connection import get_supabase_client, get_async_supabase_client
from .models import UserContextModel, ResearchBriefModel
from .repository import ContextRepository, BriefRepository

__all__ = [
    "get_supabase_client",
    "get_async_supabase_client", 
    "UserContextModel",
    "ResearchBriefModel",
    "ContextRepository",
    "BriefRepository"
]

# This will be fully implemented in Phase 4
