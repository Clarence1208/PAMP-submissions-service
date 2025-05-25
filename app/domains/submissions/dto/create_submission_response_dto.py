from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.domains.submissions.dto.submission_response_dto import SubmissionResponseDto


class CreateSubmissionResponseDto(BaseModel):
    """DTO for submission creation operation responses"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Submission created successfully",
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "link": "https://github.com/user/repository.git",
                    "project_uuid": "550e8400-e29b-41d4-a716-446655440001",
                    "group_uuid": "550e8400-e29b-41d4-a716-446655440002",
                    "project_step": "step_1",
                    "status": "pending"
                },
                "rule_results": [
                    {
                        "rule_name": "max_archive_size",
                        "passed": True,
                        "message": "Archive size is within limits"
                    },
                    {
                        "rule_name": "file_presence",
                        "passed": True,
                        "message": "All required files are present"
                    }
                ]
            }
        }
    )
    
    success: bool
    message: str
    submission_id: Optional[UUID] = None
    data: Optional[SubmissionResponseDto] = None
    rule_results: Optional[List[Dict[str, Any]]] = None 