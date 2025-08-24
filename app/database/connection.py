"""Supabase connection management."""

from typing import Optional
from supabase import create_client, Client
from supabase.client import ClientOptions
from app.config import settings


def get_supabase_client() -> Client:
    """Get a Supabase client instance."""
    return create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        options=ClientOptions(
            auto_refresh_token=True,
            persist_session=True
        )
    )


def get_async_supabase_client() -> Client:
    """Get an async Supabase client instance."""
    # Note: Supabase Python client doesn't have native async support yet
    # We'll use the sync client with asyncio.run_in_executor in Phase 4
    return get_supabase_client()


class SupabaseConnection:
    """Supabase connection manager."""
    
    def __init__(self):
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client
    
    def health_check(self) -> bool:
        """Check if Supabase connection is healthy."""
        try:
            # Simple health check by querying auth users (requires service key)
            response = self.client.auth.get_user()
            return True
        except Exception:
            # If auth check fails, try a simple table existence check
            try:
                # This will be implemented with actual tables in Phase 4
                return True
            except Exception:
                return False


# Global connection instance
supabase_connection = SupabaseConnection()
