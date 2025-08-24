"""Repository classes for Supabase data operations."""

from typing import List, Optional
from datetime import datetime
from supabase import Client
from app.database.connection import get_supabase_client
from app.database.models import UserContextModel, ResearchBriefModel
from app.structure.pydantic import UserContext, FinalBrief, ResearchRequest


class BaseRepository:
    """Base repository with common Supabase operations."""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase_client()


class ContextRepository(BaseRepository):
    """Repository for user context operations."""
    
    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get user context by user ID."""
        try:
            response = self.client.table("user_contexts").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                model = UserContextModel(**response.data[0])
                return model.to_user_context()
            return None
        except Exception as e:
            print(f"Error fetching user context: {e}")
            return None
    
    async def save_user_context(self, user_context: UserContext) -> bool:
        """Save or update user context."""
        try:
            model = UserContextModel.from_user_context(user_context)
            
            # Check if context exists
            existing = await self.get_user_context(user_context.user_id)
            
            if existing:
                # Update existing
                response = self.client.table("user_contexts").update(
                    model.dict(exclude={"id"})
                ).eq("user_id", user_context.user_id).execute()
            else:
                # Insert new
                response = self.client.table("user_contexts").insert(
                    model.dict(exclude={"id"})
                ).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error saving user context: {e}")
            return False
    
    async def get_recent_contexts(self, user_id: str, limit: int = 5) -> List[UserContext]:
        """Get recent contexts for a user."""
        try:
            response = self.client.table("user_contexts").select("*").eq(
                "user_id", user_id
            ).order("last_interaction", desc=True).limit(limit).execute()
            
            contexts = []
            for data in response.data:
                model = UserContextModel(**data)
                contexts.append(model.to_user_context())
            
            return contexts
        except Exception as e:
            print(f"Error fetching recent contexts: {e}")
            return []


class BriefRepository(BaseRepository):
    """Repository for research brief operations."""
    
    async def save_brief(self, brief: FinalBrief, request: ResearchRequest) -> bool:
        """Save a research brief."""
        try:
            model = ResearchBriefModel.from_final_brief(brief, request)
            
            response = self.client.table("research_briefs").insert(
                model.dict(exclude={"id"})
            ).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error saving research brief: {e}")
            return False
    
    async def get_brief_by_request_id(self, request_id: str) -> Optional[FinalBrief]:
        """Get research brief by request ID."""
        try:
            response = self.client.table("research_briefs").select("*").eq(
                "request_id", request_id
            ).execute()
            
            if response.data:
                model = ResearchBriefModel(**response.data[0])
                return model.to_final_brief()
            return None
        except Exception as e:
            print(f"Error fetching research brief: {e}")
            return None
    
    async def get_user_briefs(self, user_id: str, limit: int = 10) -> List[FinalBrief]:
        """Get research briefs for a user."""
        try:
            response = self.client.table("research_briefs").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            briefs = []
            for data in response.data:
                model = ResearchBriefModel(**data)
                briefs.append(model.to_final_brief())
            
            return briefs
        except Exception as e:
            print(f"Error fetching user briefs: {e}")
            return []
    
    async def get_brief_analytics(self, user_id: Optional[str] = None) -> dict:
        """Get analytics data for briefs."""
        try:
            query = self.client.table("research_briefs").select("*")
            if user_id:
                query = query.eq("user_id", user_id)
            
            response = query.execute()
            
            total_briefs = len(response.data)
            follow_up_count = sum(1 for brief in response.data if brief.get("is_follow_up", False))
            
            return {
                "total_briefs": total_briefs,
                "follow_up_briefs": follow_up_count,
                "unique_users": len(set(brief["user_id"] for brief in response.data)),
                "avg_processing_time": sum(
                    brief.get("processing_time_seconds", 0) for brief in response.data
                ) / max(total_briefs, 1)
            }
        except Exception as e:
            print(f"Error fetching brief analytics: {e}")
            return {}
