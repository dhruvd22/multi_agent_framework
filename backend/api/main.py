"""
Main FastAPI application.

This module sets up the FastAPI application with all routes, middleware,
and startup/shutdown handlers.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from neo4j import AsyncGraphDatabase
from structlog import get_logger

from ..config import get_settings
from ..core.logger import setup_logging
from ..core.supabase import get_supabase_client, is_supabase_configured
from ..memory import GraphStore, PostgresStore, initialize_memory_router
from ..mcp.server import initialize_tools, start_mcp_server
from .routes import agents, logs, memory, tasks
from .websocket import router as websocket_router

logger = get_logger(__name__)


# Global database connections
_postgres_pool: asyncpg.Pool | None = None
_neo4j_driver = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks:
    - Database connections
    - Memory router initialization
    - MCP server startup
    - Agent registration
    """
    global _postgres_pool, _neo4j_driver

    settings = get_settings()

    # Setup logging
    setup_logging(settings.log_level)

    logger.info("Starting application", environment=settings.environment)

    # Check if Supabase is configured
    if is_supabase_configured():
        supabase_client = get_supabase_client()
        if supabase_client:
            logger.info("Supabase client initialized")
            app.state.supabase_client = supabase_client

    # Initialize PostgreSQL connection pool
    try:
        _postgres_pool = await asyncpg.create_pool(
            settings.database.url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=2,
            max_size=settings.database.pool_size,
        )
        logger.info("PostgreSQL connection pool created")

        # Create tables
        postgres_store = PostgresStore(_postgres_pool)
        await postgres_store.create_table()

    except Exception as e:
        logger.error("Failed to connect to PostgreSQL", error=str(e), exc_info=True)
        raise

    # Initialize Neo4j driver
    try:
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.user, settings.neo4j.password),
        )
        await _neo4j_driver.verify_connectivity()
        logger.info("Neo4j connection verified")

        graph_store = GraphStore(_neo4j_driver)

    except Exception as e:
        logger.error("Failed to connect to Neo4j", error=str(e), exc_info=True)
        raise

    # Initialize memory router
    memory_router = initialize_memory_router(postgres_store, graph_store)
    logger.info("Memory router initialized")

    # Initialize MCP server and tools
    initialize_tools(workspace_root="./workspace")
    await start_mcp_server()
    logger.info("MCP server initialized")

    # Initialize agents
    from ..agents import AgentRegistry, BuilderAgent, CriticAgent, PlannerAgent

    registry = AgentRegistry()
    registry.register(
        PlannerAgent(agent_id="planner", memory_router=memory_router), "planner"
    )
    registry.register(
        BuilderAgent(agent_id="builder", memory_router=memory_router), "builder"
    )
    registry.register(
        CriticAgent(agent_id="critic", memory_router=memory_router), "critic"
    )
    logger.info("Agents registered", count=len(registry.get_all()))

    # Store in app state
    app.state.postgres_pool = _postgres_pool
    app.state.neo4j_driver = _neo4j_driver
    app.state.memory_router = memory_router
    app.state.agent_registry = registry

    yield

    # Shutdown
    logger.info("Shutting down application")

    if _postgres_pool:
        await _postgres_pool.close()
        logger.info("PostgreSQL connection pool closed")

    if _neo4j_driver:
        await _neo4j_driver.close()
        logger.info("Neo4j driver closed")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Framework API",
    description="API for multi-agent framework with Planner, Builder, and Critic agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# Serve static files (frontend) if they exist
# In Docker: /app/backend/api/main.py -> /app/static
# Locally: backend/api/main.py -> backend/../static (project root)
static_dir = Path("/app/static")
if not static_dir.exists():
    # Fall back to relative path (for local development)
    static_dir = Path(__file__).parent.parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/")
    async def root():
        """Serve frontend index.html."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"message": "Multi-Agent Framework API", "version": "0.1.0"}
    
    # Catch-all route for frontend routing (SPA)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """
        Serve frontend routes.
        
        This catches all non-API routes and serves the frontend SPA.
        """
        # Don't serve API routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if it's a static file
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Otherwise serve index.html for SPA routing
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Not found")
else:
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Multi-Agent Framework API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "postgres": _postgres_pool is not None,
        "neo4j": _neo4j_driver is not None,
    }

