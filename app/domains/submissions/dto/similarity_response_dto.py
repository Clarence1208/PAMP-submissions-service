from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domains.submissions.submissions_models import SimilarityStatus


class SimilarityMetricsDto(BaseModel):
    """DTO for similarity metrics"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_similarity": 0.85,
                "jaccard_similarity": 0.78,
                "type_similarity": 0.92,
                "shared_blocks_count": 5,
                "average_shared_similarity": 0.87,
            }
        }
    )

    overall_similarity: float
    jaccard_similarity: float
    type_similarity: float
    structural_similarity: Optional[float] = None
    type_sequence_similarity: Optional[float] = None
    flow_similarity: Optional[float] = None
    operation_similarity: Optional[float] = None


class SubmissionSummaryDto(BaseModel):
    """DTO for submission summary in similarity results"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "link": "https://github.com/user/repository.git",
                "description": "Student submission for assignment 1",
                "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
                "upload_date_time": "2024-01-15T10:30:00Z",
            }
        }
    )

    id: UUID
    link: str
    description: Optional[str]
    submitted_by_uuid: Optional[UUID]
    upload_date_time: datetime


class SimilarityResponseDto(BaseModel):
    """DTO for similarity detection results"""

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "similarity_id": "550e8400-e29b-41d4-a716-446655440000",
                "compared_submission_id": "550e8400-e29b-41d4-a716-446655440001",
                "compared_submission_link": "https://github.com/user/other-repo.git",
                "overall_similarity": 0.85,
                "jaccard_similarity": 0.78,
                "type_similarity": 0.92,
                "shared_blocks_count": 5,
                "average_shared_similarity": 0.87,
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "processing_time_seconds": 12.5,
                "error_message": None,
            }
        },
    )

    similarity_id: UUID
    compared_submission_id: UUID
    compared_submission_link: Optional[str]
    overall_similarity: float
    jaccard_similarity: float
    type_similarity: float
    structural_similarity: Optional[float] = None
    type_sequence_similarity: Optional[float] = None
    flow_similarity: Optional[float] = None
    operation_similarity: Optional[float] = None
    status: SimilarityStatus
    created_at: datetime
    processing_time_seconds: Optional[float]
    error_message: Optional[str]


class DetailedComparisonDto(BaseModel):
    """DTO for detailed comparison results"""

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "similarity_id": "550e8400-e29b-41d4-a716-446655440000",
                "submissions": {
                    "submission1": {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "link": "https://github.com/user/repo1.git",
                        "description": "First submission",
                        "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
                        "upload_date_time": "2024-01-15T10:30:00Z",
                    },
                    "submission2": {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "link": "https://github.com/user/repo2.git",
                        "description": "Second submission",
                        "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440006",
                        "upload_date_time": "2024-01-15T11:00:00Z",
                    },
                },
                "similarity_metrics": {
                    "overall_similarity": 0.85,
                    "jaccard_similarity": 0.78,
                    "type_similarity": 0.92,
                    "shared_blocks_count": 5,
                    "average_shared_similarity": 0.87,
                },
                "analysis_metadata": {
                    "detection_algorithm": "ast_similarity_v2",
                    "detection_version": "2.1.0",
                    "status": "completed",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:32:00Z",
                    "processing_time_seconds": 12.5,
                    "error_message": None,
                },
            }
        },
    )

    similarity_id: UUID
    submissions: Dict[str, SubmissionSummaryDto]
    similarity_metrics: SimilarityMetricsDto
    analysis_metadata: Dict[str, Any]
    detailed_results: Optional[Dict[str, Any]] = None


class SimilarityAlertDto(BaseModel):
    """DTO for high similarity alerts"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "similarity_id": "550e8400-e29b-41d4-a716-446655440000",
                "overall_similarity": 0.95,
                "shared_blocks_count": 8,
                "submission1": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "link": "https://github.com/user/repo1.git",
                    "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
                    "upload_date_time": "2024-01-15T10:30:00Z",
                },
                "submission2": {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "link": "https://github.com/user/repo2.git",
                    "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440006",
                    "upload_date_time": "2024-01-15T11:00:00Z",
                },
                "detected_at": "2024-01-15T10:32:00Z",
            }
        }
    )

    similarity_id: UUID
    overall_similarity: float
    shared_blocks_count: int
    submission1: SubmissionSummaryDto
    submission2: SubmissionSummaryDto
    detected_at: datetime


class SimilarityStatisticsDto(BaseModel):
    """DTO for similarity statistics"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_comparisons": 25,
                "high_similarity_pairs": 3,
                "average_similarity": 0.245,
                "max_similarity": 0.87,
                "status_breakdown": {"completed": 20, "failed": 3, "processing": 2},
            }
        }
    )

    total_comparisons: int
    high_similarity_pairs: int
    average_similarity: float
    max_similarity: float
    status_breakdown: Dict[str, int]


class SimilarityListResponseDto(BaseModel):
    """DTO for list of similarity results"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_comparisons": 10,
                "high_similarity_count": 2,
                "similarities": [
                    {
                        "similarity_id": "550e8400-e29b-41d4-a716-446655440001",
                        "compared_submission_id": "550e8400-e29b-41d4-a716-446655440002",
                        "compared_submission_link": "https://github.com/user/other-repo.git",
                        "overall_similarity": 0.85,
                        "jaccard_similarity": 0.78,
                        "type_similarity": 0.92,
                        "shared_blocks_count": 5,
                        "average_shared_similarity": 0.87,
                        "status": "completed",
                        "created_at": "2024-01-15T10:30:00Z",
                        "processing_time_seconds": 12.5,
                        "error_message": None,
                    }
                ],
            }
        }
    )

    submission_id: UUID
    total_comparisons: int
    high_similarity_count: int
    similarities: List[SimilarityResponseDto]


class SimilarityAlertsResponseDto(BaseModel):
    """DTO for similarity alerts response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "project_step_uuid": "550e8400-e29b-41d4-a716-446655440001",
                "similarity_threshold": 0.7,
                "total_alerts": 5,
                "alerts": [
                    {
                        "similarity_id": "550e8400-e29b-41d4-a716-446655440002",
                        "overall_similarity": 0.95,
                        "shared_blocks_count": 8,
                        "submission1": {
                            "id": "550e8400-e29b-41d4-a716-446655440003",
                            "link": "https://github.com/user/repo1.git",
                            "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440005",
                            "upload_date_time": "2024-01-15T10:30:00Z",
                        },
                        "submission2": {
                            "id": "550e8400-e29b-41d4-a716-446655440004",
                            "link": "https://github.com/user/repo2.git",
                            "submitted_by_uuid": "550e8400-e29b-41d4-a716-446655440006",
                            "upload_date_time": "2024-01-15T11:00:00Z",
                        },
                        "detected_at": "2024-01-15T10:32:00Z",
                    }
                ],
            }
        }
    )

    project_uuid: UUID
    project_step_uuid: UUID
    similarity_threshold: float
    total_alerts: int
    alerts: List[SimilarityAlertDto]
