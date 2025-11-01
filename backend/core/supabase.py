"""
Supabase integration utilities.

This module provides utilities for connecting to Supabase and extracting
connection information from Supabase configuration.
"""

from typing import Optional

from structlog import get_logger

from ..config import get_settings

logger = get_logger(__name__)


def get_supabase_client():
    """
    Get Supabase client instance if configured.

    Returns:
        Supabase client instance or None if not configured

    Example:
        ```python
        supabase = get_supabase_client()
        if supabase:
            # Use Supabase REST API, Storage, etc.
            result = supabase.table('memory_items').select('*').execute()
        ```
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        logger.warning("Supabase client not installed. Install with: pip install supabase")
        return None

    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_key:
        return None

    try:
        client: Client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client created", url=settings.supabase_url)
        return client
    except Exception as e:
        logger.error("Failed to create Supabase client", error=str(e), exc_info=True)
        return None


def get_supabase_postgres_url() -> Optional[str]:
    """
    Get PostgreSQL connection URL from Supabase configuration.

    Returns:
        PostgreSQL connection string or None if Supabase not configured

    Note:
        Supabase provides PostgreSQL connection strings in the format:
        postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

        This function constructs the URL if Supabase URL and key are provided.
        However, for production, you should use the direct connection string
        from Supabase dashboard (Settings > Database > Connection string).
    """
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_key:
        return None

    # Extract project reference from Supabase URL
    # Format: https://[PROJECT_REF].supabase.co
    try:
        url_parts = settings.supabase_url.replace("https://", "").replace("http://", "").split(".")
        if len(url_parts) >= 2:
            project_ref = url_parts[0]
            # Construct PostgreSQL connection URL
            # Note: This is a best-effort construction. For production,
            # use the direct connection string from Supabase dashboard
            postgres_url = f"postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres"
            logger.info(
                "Constructed Supabase PostgreSQL URL",
                project_ref=project_ref,
                note="Use direct connection string from Supabase dashboard for production",
            )
            return postgres_url
    except Exception as e:
        logger.warning("Failed to construct Supabase PostgreSQL URL", error=str(e))

    return None


def is_supabase_configured() -> bool:
    """
    Check if Supabase is configured.

    Returns:
        True if both Supabase URL and key are set
    """
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_key)

