import time
from datetime import datetime

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text

from app.config.config import get_settings
from app.domains.health.models import DatabaseHealth, HealthCheck, ServiceHealth
from app.shared.database import get_session

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()

# Store application start time for uptime calculation
app_start_time = time.time()


@router.get("", response_model=HealthCheck)
async def health_check(session: Session = Depends(get_session)):
    """
    Basic health check endpoint to verify API and database status
    """
    # Test database connectivity
    try:
        result = session.exec(text("SELECT 1")).first()
        database_status = "healthy" if result else "unhealthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"

    return HealthCheck(
        status="healthy" if database_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database_status=database_status,
    )


@router.get("/detailed", response_model=ServiceHealth)
async def detailed_health_check(session: Session = Depends(get_session)):
    """
    Detailed health check with system metrics
    """
    # Database health check with timing
    start_time = time.time()
    try:
        result = session.exec(text("SELECT 1")).first()
        connection_time_ms = (time.time() - start_time) * 1000
        db_health = DatabaseHealth(
            status="healthy", connection_time_ms=connection_time_ms, query_test_passed=result == 1
        )
    except Exception as e:
        connection_time_ms = (time.time() - start_time) * 1000
        db_health = DatabaseHealth(status="unhealthy", connection_time_ms=connection_time_ms, query_test_passed=False)

    # System metrics
    current_time = time.time()
    uptime_seconds = current_time - app_start_time

    try:
        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024 / 1024
    except:
        memory_usage_mb = 0.0

    return ServiceHealth(
        api_status="healthy", database=db_health, uptime_seconds=uptime_seconds, memory_usage_mb=memory_usage_mb
    )


@router.get("/readiness")
async def readiness_check(session: Session = Depends(get_session)):
    """
    Readiness check for Kubernetes/container orchestration
    """
    try:
        # Test if we can execute a simple query
        session.exec(text("SELECT 1")).first()
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/liveness")
async def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration
    """
    return {"status": "alive", "timestamp": datetime.now()}


@router.get("/database")
async def database_health(session: Session = Depends(get_session)):
    """
    Specific database health check
    """
    try:
        start_time = time.time()

        # Test basic connectivity
        basic_result = session.exec(text("SELECT 1")).first()

        # Test table existence
        table_result = session.exec(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name IN ('submission', 'cheatdetection')
        """
            )
        ).first()

        connection_time = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "connection_time_ms": connection_time,
            "basic_query_success": basic_result == 1,
            "required_tables_exist": table_result == 2,
            "timestamp": datetime.now(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now()}
