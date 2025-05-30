from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.submissions.submissions_models import SubmissionStatus


class SubmissionUpdateDto(BaseModel):
    """DTO for updating submission data"""

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "description": "Updated description for the submission",
                "status": "completed",
                "file_size_bytes": 2048000,
                "file_count": 30,
                "updated_at": "2024-01-15T12:00:00Z",
            }
        },
    )

    description: Optional[str] = None
    status: Optional[SubmissionStatus] = None
    file_size_bytes: Optional[int] = None
    file_count: Optional[int] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
