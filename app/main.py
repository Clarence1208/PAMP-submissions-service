import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import get_settings
from app.domains.detection.router import router as detection_router

# Import domain routers
from app.domains.health.router import router as health_router
from app.domains.submissions.submissions_controller import router as submissions_router
from app.shared.database import create_db_and_tables

settings = get_settings()


# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log") if not settings.debug else logging.NullHandler(),
        ],
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # Create and configure the main application logger
    logger = logging.getLogger("app")
    logger.setLevel(log_level)

    return logger


# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup: Create database tables
    create_db_and_tables()
    logger.info("🚀 Database tables created successfully")
    
    # Initialize singleton services
    from app.shared.services import init_services, cleanup_services
    init_services()
    logger.info("🔧 Singleton services initialized")
    
    logger.info(f"📊 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    yield
    
    # Shutdown: Cleanup services
    cleanup_services()
    logger.info("🛑 Application shutting down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A clean, domain-driven microservice for detecting cheating in project submissions",
    lifespan=lifespan,
    docs_url="/swagger-ui",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
app.include_router(detection_router)


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    logger.info("Root endpoint accessed")
    logger.debug("Debug message from root endpoint")
    logger.warning("Warning message from root endpoint")
    logger.error("Error message from root endpoint")

    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "architecture": "Clean Architecture with Domain-Driven Design",
        "swagger": "/swagger-ui",
        "health": "/health",
        "domains": {"health": "/health", "submissions": "/submissions", "detection": "/detection"},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
