from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.domains.submissions.dto.rule_dto import RuleDto
from app.domains.submissions.submissions_models import LinkType, ProjectStep


class CreateSubmissionDto(BaseModel):
    """DTO for creating a new submission"""

    model_config = ConfigDict(
        # Use enum values in schema instead of enum objects
        use_enum_values=True,
        # Include an example in the schema
        json_schema_extra={
            "example": {
                "link": "https://github.com/user/repository.git",
                "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "group_uuid": "550e8400-e29b-41d4-a716-446655440001",
                "project_step": "step_1",
                "description": "Final submission for project step 1",
                "submitted_by": "John Doe",
                "file_size_bytes": 1024000,
                "file_count": 25,
                "upload_date_time": "2024-01-15T10:30:00Z",
                "rules": [
                    {"name": "max_archive_size", "params": {"max_size_mb": 100}},
                    {
                        "name": "file_presence",
                        "params": {
                            "must_exist": ["README*", "*.md"],
                            "forbidden": ["*.tmp", "*.log", "*.class", "*.exe"],
                        },
                    },
                ],
            }
        },
    )

    # Required fields
    link: str
    project_uuid: UUID
    group_uuid: UUID
    project_step: ProjectStep

    # Optional fields that will be useful
    link_type: Optional[LinkType] = None
    description: Optional[str] = None
    submitted_by: Optional[str] = None
    file_size_bytes: Optional[int] = None
    file_count: Optional[int] = None
    upload_date_time: Optional[datetime] = None

    # Rules as properly typed DTOs for OpenAPI schema
    rules: Optional[List[RuleDto]] = None

    @field_validator("link")
    def validate_link(cls, v):
        """Validate that the link is a proper URL or S3 path"""
        if not v:
            raise ValueError("Link cannot be empty")

        # Basic validation for different link types
        v_lower = v.lower()
        if v_lower.startswith("s3://"):
            return v
        elif "github.com" in v_lower or "gitlab.com" in v_lower:
            if not v_lower.startswith("https://"):
                raise ValueError("GitHub/GitLab links must start with https://")
            return v
        else:
            raise ValueError("Link must be an S3 path (s3://) or a GitHub/GitLab URL")

    @field_validator("description")
    def validate_description(cls, v):
        """Validate description length"""
        if v is not None and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v

    @field_validator("submitted_by")
    def validate_submitted_by(cls, v):
        """Validate submitted_by length"""
        if v is not None and len(v) > 255:
            raise ValueError("Submitted_by cannot exceed 255 characters")
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
