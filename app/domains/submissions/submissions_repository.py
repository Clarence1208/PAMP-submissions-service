from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
import pytz

from sqlmodel import Session, select

from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.submissions.dto.submission_update_dto import SubmissionUpdateDto
from app.domains.submissions.submissions_models import LinkType, Submission
from app.shared.exceptions import DatabaseException, NotFoundException

# Paris timezone
PARIS_TZ = pytz.timezone('Europe/Paris')

def get_paris_time() -> datetime:
    """Get current time in Paris timezone"""
    return datetime.now(PARIS_TZ)


class SubmissionRepository:
    """Repository for submission data access operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        submission_data: CreateSubmissionDto,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        rule_results_json: Optional[str] = None,
    ) -> Submission:
        """Create a new submission"""
        try:
            # Set upload_date_time to current time in Paris timezone if not provided
            upload_time = submission_data.upload_date_time or get_paris_time()

            # Use provided link_type from DTO, or determine it automatically if not provided
            link_type = submission_data.link_type
            if not link_type:
                # Determine link type based on the link
                link_lower = submission_data.link.lower()
                if link_lower.startswith("s3://") or ".s3." in link_lower or "amazonaws.com" in link_lower:
                    link_type = LinkType.S3
                elif "github.com" in link_lower:
                    link_type = LinkType.GITHUB
                elif "gitlab.com" in link_lower:
                    link_type = LinkType.GITLAB

            # Create submission instance
            submission_dict = submission_data.model_dump(exclude={"upload_date_time", "rules"})

            submission_dict.update(
                {
                    "upload_date_time": upload_time,
                    "link_type": link_type,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            )

            # Handle rule_results if provided
            if rule_results_json:
                submission_dict["rule_results"] = rule_results_json
            submission = Submission(**submission_dict)

            self.session.add(submission)
            self.session.commit()
            self.session.refresh(submission)
            return submission

        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to create submission: {str(e)}")

    def get_by_id(self, submission_id: UUID) -> Optional[Submission]:
        """Get submission by ID"""
        try:
            statement = select(Submission).where(Submission.id == submission_id)
            return self.session.exec(statement).first()
        except Exception as e:
            raise DatabaseException(f"Failed to get submission: {str(e)}")

    def get_by_project_and_group(self, project_uuid: UUID, group_uuid: UUID) -> List[Submission]:
        """Get all submissions for a specific project and group"""
        try:
            statement = (
                select(Submission)
                .where(Submission.project_uuid == project_uuid, Submission.group_uuid == group_uuid)
                .order_by(Submission.upload_date_time.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to get submissions: {str(e)}")

    def get_by_project_step(self, project_uuid: UUID, project_step_uuid: UUID) -> List[Submission]:
        """Get all submissions for a specific project step"""
        try:
            statement = (
                select(Submission)
                .where(Submission.project_uuid == project_uuid, Submission.project_step_uuid == project_step_uuid)
                .order_by(Submission.upload_date_time.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to get submissions by step: {str(e)}")

    def update(self, submission_id: UUID, update_data: SubmissionUpdateDto) -> Optional[Submission]:
        """Update a submission"""
        try:
            submission = self.get_by_id(submission_id)
            if not submission:
                raise NotFoundException(f"Submission with ID {submission_id} not found")

            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(submission, field, value)

            # Always update the updated_at timestamp with Paris timezone
            submission.updated_at = get_paris_time()

            self.session.add(submission)
            self.session.commit()
            self.session.refresh(submission)
            return submission

        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to update submission: {str(e)}")

    def delete(self, submission_id: UUID) -> bool:
        """Delete a submission"""
        try:
            submission = self.get_by_id(submission_id)
            if not submission:
                raise NotFoundException(f"Submission with ID {submission_id} not found")

            self.session.delete(submission)
            self.session.commit()
            return True

        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete submission: {str(e)}")

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Submission]:
        """List all submissions with pagination"""
        try:
            statement = select(Submission).order_by(Submission.upload_date_time.desc()).offset(skip).limit(limit)
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to list submissions: {str(e)}")

    def count_by_project_and_group(self, project_uuid: UUID, group_uuid: UUID) -> int:
        """Count submissions for a specific project and group"""
        try:
            statement = select(Submission).where(
                Submission.project_uuid == project_uuid, Submission.group_uuid == group_uuid
            )
            return len(list(self.session.exec(statement).all()))
        except Exception as e:
            raise DatabaseException(f"Failed to count submissions: {str(e)}")

    def check_duplicate_submission(
        self, project_uuid: UUID, group_uuid: UUID, project_step_uuid: UUID, link: str
    ) -> bool:
        """Check if a duplicate submission exists"""
        try:
            statement = select(Submission).where(
                Submission.project_uuid == project_uuid,
                Submission.group_uuid == group_uuid,
                Submission.project_step_uuid == project_step_uuid,
                Submission.link == link,
            )
            existing = self.session.exec(statement).first()
            return existing is not None
        except Exception as e:
            raise DatabaseException(f"Failed to check for duplicate submission: {str(e)}")
