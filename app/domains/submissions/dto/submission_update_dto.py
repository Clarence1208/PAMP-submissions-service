from datetime import datetime
from typing import Optional
from uuid import UUID
import pytz

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.submissions.submissions_models import SubmissionStatus

# Paris timezone
PARIS_TZ = pytz.timezone('Europe/Paris')

def get_paris_time() -> datetime:
    """Get current time in Paris timezone"""
    return datetime.now(PARIS_TZ)


class SubmissionUpdateDto(BaseModel):
    """DTO for updating submission data"""

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "description": "Updated description for the submission",
                "status": "completed",
                "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
                "file_size_bytes": 2048000,
                "file_count": 30,
                "updated_at": "2024-01-15T12:00:00Z",
            }
        },
    )

    description: Optional[str] = None
    status: Optional[SubmissionStatus] = None
    submitted_by_uuid: Optional[UUID] = None
    file_size_bytes: Optional[int] = None
    file_count: Optional[int] = None
    updated_at: datetime = Field(default_factory=get_paris_time)

    @field_validator("description")
    def validate_description(cls, v):
        """Validate description length"""
        if v is not None and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v

    @field_validator("file_size_bytes")
    def validate_file_size_bytes(cls, v):
        """Validate file_size_bytes is non-negative"""
        if v is not None and v < 0:
            raise ValueError("File size must be non-negative")
        return v

    @field_validator("file_count")
    def validate_file_count(cls, v):
        """Validate file_count is non-negative"""
        if v is not None and v < 0:
            raise ValueError("File count must be non-negative")
        return v
