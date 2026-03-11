from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    logger.info("✅ Supabase client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Supabase: {e}")
    supabase = None


def get_supabase() -> Client:
    """Get Supabase client instance"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    return supabase


async def check_database_connection():
    """Check if database connection is working"""
    try:
        response = supabase.table("admin").select("*").limit(1).execute()
        return {"status": "connected", "message": "Database connection successful"}
    except Exception as e:
        return {"status": "failed", "message": f"Database connection failed: {str(e)}"}
