from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.domains.submissions.submissions_models import ProjectStep, SubmissionStatus, LinkType


class SubmissionResponseDto(BaseModel):
    """DTO for reading submission data"""
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "link": "https://github.com/user/repository.git",
                "project_uuid": "550e8400-e29b-41d4-a716-446655440001",
                "group_uuid": "550e8400-e29b-41d4-a716-446655440002",
                "project_step": "step_1",
                "link_type": "github",
                "description": "Final submission for project step 1",
                "submitted_by": "John Doe",
                "file_size_bytes": 1024000,
                "file_count": 25,
                "upload_date_time": "2024-01-15T10:30:00Z",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T11:00:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        }
    )
    
    id: UUID
    link: str
    project_uuid: UUID
    group_uuid: UUID
    project_step: ProjectStep
    link_type: Optional[LinkType]
    description: Optional[str]
    submitted_by: Optional[str]
    file_size_bytes: Optional[int]
    file_count: Optional[int]
    upload_date_time: datetime
    status: SubmissionStatus
    created_at: datetime
    updated_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str] 