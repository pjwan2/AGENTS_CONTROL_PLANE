"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes import router
from backend.api.runs import router as runs_router
from backend.db.database import engine
from backend.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    print("AgentOps Control Plane starting up...")
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created/verified successfully")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")

    yield

    # Shutdown
    print("AgentOps Control Plane shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="AgentOps Control Plane",
    description="Observability, evaluation, and replay platform for enterprise AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(router)
app.include_router(runs_router)
