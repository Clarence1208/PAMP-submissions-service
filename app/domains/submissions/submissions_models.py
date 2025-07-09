from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import pytz
from pydantic import field_validator
from sqlmodel import Field, SQLModel, JSON, Column

# Paris timezone
PARIS_TZ = pytz.timezone("Europe/Paris")


def get_paris_time() -> datetime:
    """Get current time in Paris timezone"""
    return datetime.now(PARIS_TZ)


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


class SimilarityStatus(str, Enum):
    """Enumeration for similarity detection status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
        if not v_lower.startswith("s3://"):
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
    upload_date_time: datetime = Field(default_factory=get_paris_time, description="When the submission was uploaded")
    status: SubmissionStatus = Field(default=SubmissionStatus.PENDING, description="Current status of the submission")
    created_at: datetime = Field(default_factory=get_paris_time, description="When the record was created")
    updated_at: Optional[datetime] = Field(default=None, description="When the record was last updated")

    # Metadata fields
    ip_address: Optional[str] = Field(default=None, max_length=45, description="IP address of the submitter")
    user_agent: Optional[str] = Field(default=None, max_length=500, description="User agent of the submitter")

    # Rule validation results
    rule_results: Optional[str] = Field(default=None, description="JSON string containing rule validation results")


class SubmissionSimilarity(SQLModel, table=True):
    """Database model for storing similarity detection results between submissions"""

    __tablename__ = "submission_similarity"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # Submission references
    submission_id: UUID = Field(foreign_key="submission.id", description="ID of the submission being compared")
    compared_submission_id: UUID = Field(foreign_key="submission.id", description="ID of the submission being compared against")
    
    # Project context
    project_uuid: UUID = Field(description="UUID of the associated project")
    project_step_uuid: UUID = Field(description="UUID of the project step")
    
    # Similarity metrics
    jaccard_similarity: float = Field(default=0.0, description="Jaccard similarity score (0.0 to 1.0)")
    type_similarity: float = Field(default=0.0, description="Type similarity score (0.0 to 1.0)")
    overall_similarity: float = Field(default=0.0, description="Overall similarity score (0.0 to 1.0)")
    
    # Shared code analysis
    shared_blocks_count: int = Field(default=0, description="Number of shared code blocks detected")
    average_shared_similarity: float = Field(default=0.0, description="Average similarity of shared code blocks")
    
    # Detection metadata
    detection_algorithm: str = Field(default="ast_similarity_v2", description="Algorithm used for detection")
    detection_version: str = Field(default="2.1.0", description="Version of the detection system")
    
    # Detailed results (stored as JSON)
    similarity_details: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Detailed similarity analysis results")
    shared_blocks: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Detailed shared code blocks information")
    visualization_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="React Flow visualization data")
    
    # Status and timing
    status: SimilarityStatus = Field(default=SimilarityStatus.PENDING, description="Status of the similarity detection")
    created_at: datetime = Field(default_factory=get_paris_time, description="When the similarity analysis was created")
    updated_at: Optional[datetime] = Field(default=None, description="When the similarity analysis was last updated")
    processing_time_seconds: Optional[float] = Field(default=None, description="Time taken to process the similarity analysis")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if similarity detection failed")
