from datetime import datetime
from sqlmodel import SQLModel


class HealthCheck(SQLModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    database_status: str


class DatabaseHealth(SQLModel):
    """Database health information"""
    status: str
    connection_time_ms: float
    query_test_passed: bool


class ServiceHealth(SQLModel):
    """Overall service health information"""
    api_status: str
    database: DatabaseHealth
    uptime_seconds: float
    memory_usage_mb: float 