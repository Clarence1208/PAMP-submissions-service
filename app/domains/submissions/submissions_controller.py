from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session

from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.submissions.dto.create_submission_response_dto import CreateSubmissionResponseDto
from app.domains.submissions.dto.similarity_response_dto import (
    SimilarityListResponseDto,
    DetailedComparisonDto,
    SimilarityStatisticsDto,
    SimilarityAlertsResponseDto,
)
from app.domains.submissions.dto.submission_response_dto import SubmissionResponseDto
from app.domains.submissions.dto.submission_update_dto import SubmissionUpdateDto
from app.domains.submissions.submissions_service import SubmissionService
from app.domains.submissions.submissions_similarity_repository import SubmissionSimilarityRepository
from app.shared.database import get_session
from app.shared.exceptions import DatabaseException, NotFoundException, ValidationException

router = APIRouter(prefix="/submissions", tags=["submissions"])


def get_submission_service(session: Session = Depends(get_session)) -> SubmissionService:
    """Dependency to get submission service"""
    return SubmissionService(session)


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request"""
    # Get real IP address considering reverse proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else None

    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post("", response_model=CreateSubmissionResponseDto, status_code=201)
async def create_submission(
    submission_data: CreateSubmissionDto,
    request: Request,
    allow_duplicates: bool = Query(False, description="Allow duplicate submissions"),
    service: SubmissionService = Depends(get_submission_service),
):
    """
    Create a new submission

    - **link**: URL to S3, GitHub, or GitLab repository (required)
    - **project_uuid**: UUID of the associated project (required)
    - **group_uuid**: UUID of the associated group (required)
    - **project_step_uuid**: UUID of the project step (required)
    - **upload_date_time**: Upload timestamp (optional, defaults to current time)
    - **description**: Optional description of the submission
    - **submitted_by_uuid**: UUID of the submitter (optional)
    - **file_size_bytes**: Size of the submission in bytes
    - **file_count**: Number of files in the submission
    - **rules**: List of validation rules to execute (optional)
    - **force_rules**: If True, submission is created even if validation rules fail (optional, defaults to False)
    """
    try:
        ip_address, user_agent = get_client_info(request)

        return service.create_submission(
            submission_data=submission_data,
            ip_address=ip_address,
            user_agent=user_agent,
            allow_duplicates=allow_duplicates,
        )
    except ValidationException as e:
        # Return structured error details if available
        if hasattr(e, "detail") and isinstance(e.detail, dict):
            raise HTTPException(status_code=422, detail=e.detail)
        else:
            raise HTTPException(status_code=422, detail=str(e.detail))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{submission_id}", response_model=CreateSubmissionResponseDto)
async def get_submission(submission_id: UUID, service: SubmissionService = Depends(get_submission_service)):
    """Get a submission by ID"""
    try:
        return service.get_submission(submission_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/project/{project_uuid}/group/{group_uuid}/step/{project_step_uuid}", response_model=CreateSubmissionResponseDto
)
async def get_submission_by_project_group_step(
    project_uuid: UUID,
    group_uuid: UUID,
    project_step_uuid: UUID,
    service: SubmissionService = Depends(get_submission_service),
):
    """Get a submission by project, group and step"""
    try:
        return service.get_submission_by_project_group_step(project_uuid, group_uuid, project_step_uuid)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[SubmissionResponseDto])
async def list_submissions(
    skip: int = Query(0, ge=0, description="Number of submissions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of submissions to return"),
    service: SubmissionService = Depends(get_submission_service),
):
    """List all submissions with pagination"""
    try:
        return service.list_submissions(skip=skip, limit=limit)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/group/{group_uuid}", response_model=List[SubmissionResponseDto])
async def get_submissions_by_project_and_group(
    project_uuid: UUID, group_uuid: UUID, service: SubmissionService = Depends(get_submission_service)
):
    """Get all submissions for a specific project and group"""
    try:
        return service.get_submissions_by_project_and_group(project_uuid, group_uuid)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/step/{project_step_uuid}", response_model=List[SubmissionResponseDto])
async def get_submissions_by_project_step(
    project_uuid: UUID, project_step_uuid: UUID, service: SubmissionService = Depends(get_submission_service)
):
    """Get all submissions for a specific project step"""
    try:
        return service.get_submissions_by_project_step(project_uuid, project_step_uuid)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/group/{group_uuid}/statistics")
async def get_submission_statistics(
    project_uuid: UUID, group_uuid: UUID, service: SubmissionService = Depends(get_submission_service)
):
    """Get submission statistics for a project and group"""
    try:
        return service.get_submission_statistics(project_uuid, group_uuid)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{submission_id}", response_model=CreateSubmissionResponseDto)
async def update_submission(
    submission_id: UUID,
    update_data: SubmissionUpdateDto,
    service: SubmissionService = Depends(get_submission_service),
):
    """Update a submission"""
    try:
        return service.update_submission(submission_id, update_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{submission_id}", response_model=CreateSubmissionResponseDto)
async def delete_submission(
    submission_id: UUID, 
    service: SubmissionService = Depends(get_submission_service),
    session: Session = Depends(get_session)
):
    """Delete a submission"""
    # first check if a similarity exists for this submission if so, delete it first
    try:
        similarity_repository = SubmissionSimilarityRepository(session)
        similarity_repository.delete_by_submission_id(submission_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        return service.delete_submission(submission_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/documentation")
async def get_rules_documentation():
    """Get detailed documentation for all available validation rules"""
    try:
        documentation = {
            "available_rules": [
                {
                    "name": "file_presence",
                    "description": "Validates presence of required files and absence of forbidden files",
                    "parameters": {
                        "must_exist": {
                            "type": "array of strings",
                            "description": "List of file patterns that must be present (glob patterns supported)",
                            "required": False,
                            "examples": ["README*", "*.md", "package.json", "src/**/*.py"],
                        },
                        "forbidden": {
                            "type": "array of strings",
                            "description": "List of file patterns that must NOT be present (glob patterns supported)",
                            "required": False,
                            "examples": ["*.tmp", "*.log", "*.class", "node_modules/*", "*.exe"],
                        },
                    },
                    "validation": "At least one of 'must_exist' or 'forbidden' must be specified",
                    "example": {
                        "name": "file_presence",
                        "params": {"must_exist": ["README*", "*.md"], "forbidden": ["*.tmp", "*.log", "*.class"]},
                    },
                },
                {
                    "name": "max_archive_size",
                    "description": "Validates that the repository size doesn't exceed a maximum limit",
                    "parameters": {
                        "max_size_mb": {
                            "type": "number",
                            "description": "Maximum allowed size in megabytes",
                            "required": False,
                            "default": 100,
                            "examples": [10, 50, 100, 500],
                        }
                    },
                    "validation": "Repository size is calculated including all files",
                    "example": {"name": "max_archive_size", "params": {"max_size_mb": 100}},
                },
                {
                    "name": "directory_structure",
                    "description": "Validates project directory structure and architecture patterns",
                    "parameters": {
                        "required_directories": {
                            "type": "array of strings",
                            "description": "List of directory patterns that must be present",
                            "required": False,
                            "examples": ["src", "tests", "docs", "src/components", "config"],
                        },
                        "forbidden_directories": {
                            "type": "array of strings",
                            "description": "List of directory patterns that must NOT be present",
                            "required": False,
                            "examples": ["node_modules", "__pycache__", "*.tmp", "build", "dist"],
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum allowed directory nesting depth",
                            "required": False,
                            "examples": [3, 5, 8],
                        },
                        "allow_empty_dirs": {
                            "type": "boolean",
                            "description": "Whether empty directories are allowed",
                            "required": False,
                            "default": True,
                            "examples": [True, False],
                        },
                    },
                    "validation": "At least one of 'required_directories', 'forbidden_directories', or 'max_depth' must be specified",
                    "example": {
                        "name": "directory_structure",
                        "params": {
                            "required_directories": ["src", "tests", "docs"],
                            "forbidden_directories": ["node_modules", "__pycache__"],
                            "max_depth": 5,
                            "allow_empty_dirs": False,
                        },
                    },
                },
                {
                    "name": "file_content",
                    "description": "Validates that specific files contain expected text or match regex patterns",
                    "parameters": {
                        "checks": {
                            "type": "array of objects",
                            "description": "List of file content checks to perform",
                            "required": True,
                            "items": {
                                "file_pattern": {
                                    "type": "string",
                                    "description": "Glob pattern to match files for content checking",
                                    "required": True,
                                    "examples": ["README.md", "*.py", "src/**/*.js", "package.json"],
                                },
                                "text": {
                                    "type": "string",
                                    "description": "Exact text that must be present in the file (mutually exclusive with regex)",
                                    "required": False,
                                    "examples": ["Copyright 2024", "#!/usr/bin/env python", "import unittest"],
                                },
                                "regex": {
                                    "type": "string",
                                    "description": "Regular expression pattern that must match content in the file (mutually exclusive with text)",
                                    "required": False,
                                    "examples": ["^#!/usr/bin/env", "class\\s+\\w+Test", "def\\s+test_\\w+"],
                                },
                                "case_sensitive": {
                                    "type": "boolean",
                                    "description": "Whether text/regex matching should be case sensitive",
                                    "required": False,
                                    "default": True,
                                    "examples": [True, False],
                                },
                                "multiline": {
                                    "type": "boolean",
                                    "description": "For regex: whether ^ and $ match line boundaries (regex only)",
                                    "required": False,
                                    "default": False,
                                    "examples": [True, False],
                                },
                                "dotall": {
                                    "type": "boolean",
                                    "description": "For regex: whether . matches newline characters (regex only)",
                                    "required": False,
                                    "default": False,
                                    "examples": [True, False],
                                },
                            },
                        }
                    },
                    "validation": "Each check must specify either 'text' or 'regex' (not both), and at least one check must be provided",
                    "example": {
                        "name": "file_content",
                        "params": {
                            "checks": [
                                {"file_pattern": "README.md", "text": "## Installation", "case_sensitive": False},
                                {"file_pattern": "*.py", "regex": "^#!/usr/bin/env python", "multiline": True},
                                {"file_pattern": "tests/*.py", "regex": "def\\s+test_\\w+", "case_sensitive": True},
                            ]
                        },
                    },
                },
            ],
            "common_errors": {
                "parameter_type_error": "Ensure parameters match expected types (arrays for patterns, numbers for sizes, booleans for flags)",
                "missing_parameters": "Each rule requires specific parameters - check the documentation",
                "invalid_patterns": "Directory patterns should be valid paths (e.g., 'src', 'tests/unit', 'config/*')",
                "malformed_json": "Ensure arrays are properly formatted with square brackets []",
            },
            "usage_notes": [
                "Directory patterns support simple wildcards and path separators",
                "Directory paths are relative to the repository root",
                "Rules are executed on the cloned repository structure",
                "All rules must pass for the submission to be accepted",
                "Empty directories are allowed by default but can be forbidden",
            ],
        }
        return documentation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rules documentation: {str(e)}")


@router.get("/rules/available")
async def get_available_rules(service: SubmissionService = Depends(get_submission_service)):
    """Get list of available validation rules"""
    try:
        available_rules = service.rule_service.get_available_rules()
        return {
            "available_rules": available_rules,
            "total_count": len(available_rules),
            "description": "These rules can be used in the 'rules' field when creating submissions",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available rules: {str(e)}")


@router.get("/{submission_id}/similarities", response_model=SimilarityListResponseDto)
async def get_submission_similarities(
    submission_id: UUID, 
    service: SubmissionService = Depends(get_submission_service)
):
    """Get all similarity results for a specific submission"""
    try:
        similarities = service.get_submission_similarities(submission_id)
        
        # Count high similarity results (>= 0.7)
        high_similarity_count = len([s for s in similarities if s.get("overall_similarity", 0) >= 0.7])
        
        return SimilarityListResponseDto(
            submission_id=submission_id,
            total_comparisons=len(similarities),
            high_similarity_count=high_similarity_count,
            similarities=similarities
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similarities/{similarity_id}/detailed", response_model=DetailedComparisonDto)
async def get_detailed_comparison(
    similarity_id: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """Get detailed comparison results including visualization data"""
    try:
        detailed_comparison = service.get_detailed_comparison(similarity_id)
        return DetailedComparisonDto(**detailed_comparison)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/step/{project_step_uuid}/similarity-statistics", response_model=SimilarityStatisticsDto)
async def get_project_step_similarity_statistics(
    project_uuid: UUID,
    project_step_uuid: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """Get similarity statistics for a project step"""
    try:
        statistics = service.get_project_step_statistics(project_uuid, project_step_uuid)
        return SimilarityStatisticsDto(**statistics)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/step/{project_step_uuid}/similarity-alerts", response_model=SimilarityAlertsResponseDto)
async def get_high_similarity_alerts(
    project_uuid: UUID,
    project_step_uuid: UUID,
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold for alerts"),
    service: SubmissionService = Depends(get_submission_service)
):
    """Get high similarity alerts for a project step"""
    try:
        alerts = service.get_high_similarity_alerts(project_uuid, project_step_uuid, threshold)
        
        return SimilarityAlertsResponseDto(
            project_uuid=project_uuid,
            project_step_uuid=project_step_uuid,
            similarity_threshold=threshold,
            total_alerts=len(alerts),
            alerts=alerts
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_uuid}/step/{project_step_uuid}/similarity-overview")
async def get_project_step_similarity_overview(
    project_uuid: UUID,
    project_step_uuid: UUID,
    service: SubmissionService = Depends(get_submission_service)
):
    """Get comprehensive similarity overview for a project step"""
    try:
        statistics = service.get_project_step_statistics(project_uuid, project_step_uuid)
        alerts = service.get_high_similarity_alerts(project_uuid, project_step_uuid, 0.7)
        
        return {
            "project_uuid": project_uuid,
            "project_step_uuid": project_step_uuid,
            "statistics": statistics,
            "high_similarity_alerts": {
                "threshold": 0.7,
                "total_alerts": len(alerts),
                "alerts": alerts[:10]  # Limit to top 10 alerts
            },
            "recommendations": {
                "review_required": len(alerts) > 0,
                "investigation_priority": "high" if len(alerts) > 5 else "medium" if len(alerts) > 0 else "low",
                "total_flagged_pairs": len(alerts)
            }
        }
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/check")
async def submissions_health_check(service: SubmissionService = Depends(get_submission_service)):
    """Health check for submissions domain"""
    try:
        # Try to perform a simple database operation
        submissions = service.list_submissions(skip=0, limit=1)
        return {
            "status": "healthy",
            "domain": "submissions",
            "database_accessible": True,
            "sample_count": len(submissions),
        }
    except Exception as e:
        return {"status": "unhealthy", "domain": "submissions", "database_accessible": False, "error": str(e)}
