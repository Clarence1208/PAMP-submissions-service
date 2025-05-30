from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import get_settings
from app.shared.database import create_db_and_tables

# Import domain routers
from app.domains.health.router import router as health_router
from app.domains.submissions.submissions_controller import router as submissions_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup: Create database tables
    create_db_and_tables()
    print("🚀 Database tables created successfully")
    print(f"📊 Starting {settings.app_name} v{settings.app_version}")
    print(f"🔧 Debug mode: {settings.debug}")
    yield
    # Shutdown: Cleanup if needed
    print("🛑 Application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A clean, domain-driven microservice for detecting cheating in project submissions",
    lifespan=lifespan,
    docs_url="/swagger-ui",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include domain routers
app.include_router(health_router)
app.include_router(submissions_router)


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "architecture": "Clean Architecture with Domain-Driven Design",
        "swagger": "/swagger-ui",
        "health": "/health",
        "domains": {
            "health": "/health",
            "submissions": "/submissions"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )