"""
Application settings and configuration management.

This module uses Pydantic Settings to load and validate environment variables.
All configuration values are type-checked and can have defaults.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/multi_agent_db",
        description="PostgreSQL database URL",
    )
    pool_size: int = Field(default=10, description="Database connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")


class Neo4jSettings(BaseSettings):
    """Neo4j graph database settings."""

    model_config = SettingsConfigDict(env_prefix="NEO4J_")

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j connection URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(default="neo4j", description="Neo4j password")
    max_connection_lifetime: int = Field(
        default=3600, description="Max connection lifetime in seconds"
    )


class OpenAISettings(BaseSettings):
    """OpenAI API settings."""

    model_config = SettingsConfigDict(env_prefix="OPENAI_")

    api_key: Optional[str] = Field(
        default=None,
        description=(
            "OpenAI API key. Required for LLM-powered agents. "
            "Set the OPENAI_API_KEY environment variable to enable agent execution."
        ),
    )
    model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model to use")
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Model temperature")
    timeout: int = Field(default=60, description="API request timeout in seconds")

    def is_configured(self) -> bool:
        """Return True if an API key is configured."""
        return bool(self.api_key)


class BudgetSettings(BaseSettings):
    """Budget tracking and guardrail settings."""

    model_config = SettingsConfigDict(env_prefix="BUDGET_")

    daily_limit: float = Field(default=100.0, description="Daily budget limit in USD")
    task_limit: float = Field(default=10.0, description="Per-task budget limit in USD")
    enable_tracking: bool = Field(default=True, description="Enable budget tracking")
    warning_threshold: float = Field(
        default=0.8, description="Warning threshold as fraction of limit"
    )


class MCPSettings(BaseSettings):
    """MCP server settings."""

    model_config = SettingsConfigDict(env_prefix="MCP_")

    server_port: int = Field(default=8001, description="MCP server port")
    server_host: str = Field(default="localhost", description="MCP server host")
    enable_sandbox: bool = Field(default=True, description="Enable sandboxed execution")


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")

    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    budget: BudgetSettings = Field(default_factory=BudgetSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    # Supabase (optional)
    supabase_url: Optional[str] = Field(
        default="https://pwwrzmwtgrsfdqykcomh.supabase.co",
        description="Supabase project URL",
    )
    supabase_key: Optional[str] = Field(default=None, description="Supabase API key")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: The application settings instance.

    Note:
        This function uses LRU cache to ensure settings are loaded only once.
        Settings are reloaded when the application restarts.
    """
    return Settings()

