import json
import logging
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from app.domains.submissions.detection_integration_service import DetectionIntegrationService
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.submissions.dto.create_submission_response_dto import CreateSubmissionResponseDto
from app.domains.submissions.dto.submission_response_dto import SubmissionResponseDto
from app.domains.submissions.dto.submission_update_dto import SubmissionUpdateDto
from app.domains.submissions.rules.rule_service import RuleService
from app.domains.submissions.submissions_models import LinkType, SubmissionStatus
from app.domains.submissions.submissions_repository import SubmissionRepository
from app.shared.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for submission business logic"""

    def __init__(self, session: Session):
        self.repository = SubmissionRepository(session)
        self.rule_service = RuleService()
        self.detection_service = DetectionIntegrationService(session)

    def create_submission(
        self,
        submission_data: CreateSubmissionDto,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        allow_duplicates: bool = False,
    ) -> CreateSubmissionResponseDto:
        """Create a new submission with business logic validation"""

        # Check for duplicate submissions if not allowed
        if not allow_duplicates:
            is_duplicate = self.repository.check_duplicate_submission(
                project_uuid=submission_data.project_uuid,
                group_uuid=submission_data.group_uuid,
                project_step_uuid=submission_data.project_step_uuid,
            )

            if is_duplicate:
                raise ValidationException("A submission with the same project, group and step already exists")

        # Validate business rules
        self._validate_submission_data(submission_data)

        if not submission_data.link_type:
            # Determine link type based on the link
            link_lower = submission_data.link.lower()
            if link_lower.startswith("s3://"):
                submission_data.link_type = LinkType.S3
            elif "github.com" in link_lower:
                submission_data.link_type = LinkType.GITHUB
            elif "gitlab.com" in link_lower:
                submission_data.link_type = LinkType.GITLAB

        # Execute validation rules if specified and requested
        rule_results = []
        if submission_data.rules:
            try:
                logger.info(f"Executing {len(submission_data.rules)} validation rules")
                rule_results = self.rule_service.validate_submission(submission_data)

                # Check if any rules failed
                failed_rules = [r for r in rule_results if not r.passed]
                if failed_rules:
                    # Create structured error response
                    errors = []

                    for failed_rule in failed_rules:
                        if failed_rule.error_details:
                            # Use structured error data from the rule
                            error_info = failed_rule.error_details.copy()
                            error_info["rule_name"] = failed_rule.rule_name
                            error_info["rule_params"] = failed_rule.params
                            errors.append(error_info)
                        else:
                            # Fallback for simple string errors
                            errors.append(
                                {
                                    "code": "ruleValidationFailed",
                                    "rule_name": failed_rule.rule_name,
                                    "rule_params": failed_rule.params,
                                    "message": failed_rule.message,
                                }
                            )

                    # Create detailed error response
                    error_response = {
                        "validation_failed": True,
                        "failed_rule_count": len(failed_rules),
                        "total_rule_count": len(rule_results),
                        "errors": errors,
                        "summary": f"Submission validation failed: {len(failed_rules)} of {len(rule_results)} rules failed",
                    }

                    # Log the detailed failure information
                    logger.warning(f"Rule validation failed: {error_response}")

                    # If force_rules is True, continue with submission creation but store failed results
                    if submission_data.force_rules:
                        logger.info("force_rules is True - continuing with submission creation despite rule failures")
                        # Store rule results for later storage in the repository
                        rule_results_json = json.dumps([r.to_dict() for r in rule_results])
                    else:
                        # Raise structured validation exception
                        raise ValidationException(
                            f"Submission validation failed: {len(failed_rules)} of {len(rule_results)} rules failed",
                            details=error_response,
                        )

                logger.info("All validation rules passed successfully")

            except ValidationException:
                # Re-raise validation exceptions as-is
                raise
            except Exception as e:
                # Log unexpected errors but don't fail the submission
                logger.error(f"Unexpected error during rule execution: {str(e)}")
                raise ValidationException(
                    f"Rule execution failed: {str(e)}",
                    details={"error_type": type(e).__name__, "error_message": str(e)},
                )

        # Create the submission
        submission = self.repository.create(
            submission_data=submission_data,
            ip_address=ip_address,
            user_agent=user_agent,
            rule_results_json=rule_results_json if "rule_results_json" in locals() else None,
        )

        # Update submission status to completed for similarity detection
        update_data = SubmissionUpdateDto(status=SubmissionStatus.COMPLETED)
        submission = self.repository.update(submission.id, update_data)

        # Start similarity detection asynchronously (non-blocking)
        try:
            logger.info(f"Starting async similarity detection for submission {submission.id}")
            self.detection_service.process_submission_similarities_async(submission)
            logger.info(f"Async similarity detection initiated for submission {submission.id}")
        except Exception as e:
            logger.error(f"Failed to start async similarity detection for submission {submission.id}: {str(e)}")
            # Log the error but don't fail the submission creation, it should be logged in the similarity entity either way

        # Add rule execution results to the response if any were executed
        response_data = {
            "success": True,
            "message": "Submission created successfully",
            "submission_id": submission.id,
            "data": SubmissionResponseDto.model_validate(submission.model_dump()),
        }

        # Add similarity detection metadata
        response_data["similarity_detection"] = {
            "status": "processing_async",
            "message": "Similarity detection has been started in the background. Results will be available shortly.",
        }

        # Include rule results from execution or from stored submission
        if rule_results:
            response_data["rule_results"] = [
                {"rule_name": r.rule_name, "passed": r.passed, "message": r.message, "params": r.params}
                for r in rule_results
            ]
        elif submission.rule_results:
            # Parse stored rule results from the submission
            try:
                stored_results = json.loads(submission.rule_results)
                response_data["rule_results"] = stored_results
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse stored rule results: {e}")
                # Don't include rule_results if parsing fails

        return CreateSubmissionResponseDto(**response_data)

    def get_submission(self, submission_id: UUID) -> CreateSubmissionResponseDto:
        """Get a submission by ID"""
        submission = self.repository.get_by_id(submission_id)

        if not submission:
            raise NotFoundException(f"Submission with ID {submission_id} not found")

        response_data = {
            "success": True,
            "message": "Submission retrieved successfully",
            "submission_id": submission.id,
            "data": SubmissionResponseDto.model_validate(submission.model_dump()),
        }

        # Include stored rule results if they exist
        if submission.rule_results:
            try:
                stored_results = json.loads(submission.rule_results)
                response_data["rule_results"] = stored_results
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse stored rule results: {e}")
                # Don't include rule_results if parsing fails

        return CreateSubmissionResponseDto(**response_data)

    def get_submission_by_project_group_step(self, project_uuid, group_uuid, project_step_uuid):
        """Get a submission by project, group and step"""
        submission = self.repository.get_by_project_group_step(
            project_uuid=project_uuid,
            group_uuid=group_uuid,
            project_step_uuid=project_step_uuid,
        )

        if not submission:
            raise NotFoundException(
                f"Submission for project {project_uuid}, group {group_uuid}, and step {project_step_uuid} not found"
            )

        response_data = {
            "success": True,
            "message": "Submission retrieved successfully",
            "submission_id": submission.id,
            "data": SubmissionResponseDto.model_validate(submission.model_dump()),
        }

        # Include stored rule results if they exist
        if submission.rule_results:
            try:
                stored_results = json.loads(submission.rule_results)
                response_data["rule_results"] = stored_results
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse stored rule results: {e}")
                # Don't include rule_results if parsing fails

        return CreateSubmissionResponseDto(**response_data)

    def get_submissions_by_project_and_group(self, project_uuid: UUID, group_uuid: UUID) -> List[SubmissionResponseDto]:
        """Get all submissions for a specific project and group"""
        submissions = self.repository.get_by_project_and_group(project_uuid, group_uuid)
        return [SubmissionResponseDto.model_validate(sub.model_dump()) for sub in submissions]

    def get_submissions_by_project_step(
        self, project_uuid: UUID, project_step_uuid: UUID
    ) -> List[SubmissionResponseDto]:
        """Get all submissions for a specific project step"""
        submissions = self.repository.get_by_project_step(project_uuid, project_step_uuid)
        return [SubmissionResponseDto.model_validate(sub.model_dump()) for sub in submissions]

    def update_submission(self, submission_id: UUID, update_data: SubmissionUpdateDto) -> CreateSubmissionResponseDto:
        """Update a submission"""
        submission = self.repository.update(submission_id, update_data)

        return CreateSubmissionResponseDto(
            success=True,
            message="Submission updated successfully",
            submission_id=submission.id,
            data=SubmissionResponseDto.model_validate(submission.model_dump()),
        )

    def delete_submission(self, submission_id: UUID) -> CreateSubmissionResponseDto:
        """Delete a submission"""
        success = self.repository.delete(submission_id)

        return CreateSubmissionResponseDto(
            success=success, message="Submission deleted successfully", submission_id=submission_id
        )

    def list_submissions(self, skip: int = 0, limit: int = 100) -> List[SubmissionResponseDto]:
        """List all submissions with pagination"""
        if limit > 1000:  # Prevent excessive data retrieval
            limit = 1000

        submissions = self.repository.list_all(skip=skip, limit=limit)
        return [SubmissionResponseDto.model_validate(sub.model_dump()) for sub in submissions]

    def get_submission_statistics(self, project_uuid: UUID, group_uuid: UUID) -> dict:
        """Get submission statistics for a project and group"""
        submissions = self.repository.get_by_project_and_group(project_uuid, group_uuid)

        total_count = len(submissions)
        status_counts = {}
        step_counts = {}
        link_type_counts = {}

        for submission in submissions:
            # Count by status
            status = submission.status
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by step
            step = submission.project_step_uuid
            step_counts[str(step)] = step_counts.get(str(step), 0) + 1

            # Count by link type
            link_type = submission.link_type or "unknown"
            link_type_counts[link_type] = link_type_counts.get(link_type, 0) + 1

        return {
            "total_submissions": total_count,
            "status_breakdown": status_counts,
            "step_breakdown": step_counts,
            "link_type_breakdown": link_type_counts,
            "latest_submission": submissions[0].upload_date_time.isoformat() if submissions else None,
        }

    def _validate_submission_data(self, submission_data: CreateSubmissionDto) -> None:
        """Validate submission data according to business rules"""

        # Validate link format based on type
        link = submission_data.link.lower()

        if "github.com" in link:
            # GitHub repository validation
            if "/tree/" in link or "/blob/" in link:
                raise ValidationException(
                    "GitHub link should point to the repository root, not specific files or branches"
                )
            if not link.endswith(".git") and "/archive/" not in link:
                # Allow both .git URLs and archive URLs
                pass

        elif "gitlab.com" in link:
            # GitLab repository validation
            if "/tree/" in link or "/blob/" in link:
                raise ValidationException(
                    "GitLab link should point to the repository root, not specific files or branches"
                )

        # Validate file size if provided
        if submission_data.file_size_bytes is not None:
            max_size = 1024 * 1024 * 1024 * 5  # 5GB limit
            if submission_data.file_size_bytes > max_size:
                raise ValidationException("File size cannot exceed 5GB")

        # Validate file count if provided
        if submission_data.file_count is not None:
            if submission_data.file_count > 10000:
                raise ValidationException("File count cannot exceed 10,000 files")

        # Validate description length
        if submission_data.description and len(submission_data.description) > 1000:
            raise ValidationException("Description cannot exceed 1000 characters")

    def get_submission_similarities(self, submission_id: UUID) -> List[dict]:
        """Get all similarity results for a submission"""
        return self.detection_service.get_submission_similarities(submission_id)

    def get_detailed_comparison(self, similarity_id: UUID) -> dict:
        """Get detailed comparison results including visualization data"""
        return self.detection_service.get_detailed_comparison(similarity_id)

    def get_project_step_statistics(self, project_uuid: UUID, project_step_uuid: UUID) -> dict:
        """Get similarity statistics for a project step"""
        return self.detection_service.get_project_step_statistics(project_uuid, project_step_uuid)

    def get_high_similarity_alerts(
        self, project_uuid: UUID, project_step_uuid: UUID, threshold: float = 0.7
    ) -> List[dict]:
        """Get high similarity alerts for a project step"""
        return self.detection_service.get_high_similarity_alerts(project_uuid, project_step_uuid, threshold)
