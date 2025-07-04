from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class SubmissionStatus(str, Enum):
    """Enumeration for submission status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class LinkType(str, Enum):
    """Enumeration for link types"""

    S3 = "s3"
    GITHUB = "github"
    GITLAB = "gitlab"


class SubmissionBase(SQLModel):
    """Base submission model with common fields"""

    link: str = Field(description="Link to S3, GitHub, or GitLab repository")
    project_uuid: UUID = Field(description="UUID of the associated project")
    group_uuid: UUID = Field(description="UUID of the associated group")
    project_step_uuid: UUID = Field(description="UUID of the project step")

    # Optional fields that will be useful
    link_type: Optional[LinkType] = Field(default=None, description="Type of the submission link")
    description: Optional[str] = Field(
        default=None, max_length=1000, description="Optional description of the submission"
    )
    submitted_by_uuid: Optional[UUID] = Field(default=None, description="UUID of the submitter")
    file_size_bytes: Optional[int] = Field(default=None, ge=0, description="Size of the submission in bytes")
    file_count: Optional[int] = Field(default=None, ge=0, description="Number of files in the submission")

    @field_validator("link")
    def validate_link(cls, v):
        """Validate that the link is a proper URL or S3 path"""
        if not v:
            raise ValueError("Link cannot be empty")

        # Basic validation for different link types
        v_lower = v.lower()
        if ".s3." in v_lower or "amazonaws.com" in v_lower:
            return v
        elif "github.com" in v_lower or "gitlab.com" in v_lower:
            if not v_lower.startswith("https://"):
                raise ValueError("GitHub/GitLab links must start with https://")
            return v
        else:
            raise ValueError("Link must be an S3 path (s3://) or a GitHub/GitLab URL")


class Submission(SubmissionBase, table=True):
    """Database model for submissions"""

    __tablename__ = "submission"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    upload_date_time: datetime = Field(default_factory=datetime.utcnow, description="When the submission was uploaded")
    status: SubmissionStatus = Field(default=SubmissionStatus.PENDING, description="Current status of the submission")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was created")
    updated_at: Optional[datetime] = Field(default=None, description="When the record was last updated")

    # Metadata fields
    ip_address: Optional[str] = Field(default=None, max_length=45, description="IP address of the submitter")
    user_agent: Optional[str] = Field(default=None, max_length=500, description="User agent of the submitter")

    # Rule validation results
    rule_results: Optional[str] = Field(default=None, description="JSON string containing rule validation results")
