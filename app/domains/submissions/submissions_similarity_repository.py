import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlmodel import Session, select

from app.domains.submissions.submissions_models import SimilarityStatus, SubmissionSimilarity
from app.shared.exceptions import DatabaseException, NotFoundException


class SubmissionSimilarityRepository:
    """Repository for submission similarity data access operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, similarity_data: dict) -> SubmissionSimilarity:
        """Create a new similarity record"""
        try:
            similarity = SubmissionSimilarity(**similarity_data)
            self.session.add(similarity)
            self.session.commit()
            self.session.refresh(similarity)
            return similarity
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to create similarity record: {str(e)}")

    def get_by_id(self, similarity_id: UUID) -> Optional[SubmissionSimilarity]:
        """Get similarity record by ID"""
        try:
            statement = select(SubmissionSimilarity).where(SubmissionSimilarity.id == similarity_id)
            return self.session.exec(statement).first()
        except Exception as e:
            raise DatabaseException(f"Failed to get similarity record: {str(e)}")

    def get_by_submission_id(self, submission_id: UUID) -> List[SubmissionSimilarity]:
        """Get all similarity records for a specific submission (bidirectional)"""
        try:
            statement = (
                select(SubmissionSimilarity)
                .where(
                    or_(
                        SubmissionSimilarity.submission_id == submission_id,
                        SubmissionSimilarity.compared_submission_id == submission_id,
                    )
                )
                .order_by(SubmissionSimilarity.overall_similarity.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to get similarity records for submission: {str(e)}")

    def get_by_project_step(self, project_uuid: UUID, project_step_uuid: UUID) -> List[SubmissionSimilarity]:
        """Get all similarity records for a specific project step"""
        try:
            statement = (
                select(SubmissionSimilarity)
                .where(
                    SubmissionSimilarity.project_uuid == project_uuid,
                    SubmissionSimilarity.project_step_uuid == project_step_uuid,
                )
                .order_by(SubmissionSimilarity.overall_similarity.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to get similarity records for project step: {str(e)}")

    def get_high_similarity_pairs(
        self, project_uuid: UUID, project_step_uuid: UUID, similarity_threshold: float = 0.7
    ) -> List[SubmissionSimilarity]:
        """Get similarity pairs above a certain threshold for a project step"""
        try:
            statement = (
                select(SubmissionSimilarity)
                .where(
                    SubmissionSimilarity.project_uuid == project_uuid,
                    SubmissionSimilarity.project_step_uuid == project_step_uuid,
                    SubmissionSimilarity.overall_similarity >= similarity_threshold,
                )
                .order_by(SubmissionSimilarity.overall_similarity.desc())
            )
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise DatabaseException(f"Failed to get high similarity pairs: {str(e)}")

    def get_comparison_pair(self, submission_id: UUID, compared_submission_id: UUID) -> Optional[SubmissionSimilarity]:
        """Get specific comparison between two submissions"""
        try:
            statement = select(SubmissionSimilarity).where(
                SubmissionSimilarity.submission_id == submission_id,
                SubmissionSimilarity.compared_submission_id == compared_submission_id,
            )
            return self.session.exec(statement).first()
        except Exception as e:
            raise DatabaseException(f"Failed to get comparison pair: {str(e)}")

    def update_status(
        self, similarity_id: UUID, status: SimilarityStatus, error_message: Optional[str] = None
    ) -> SubmissionSimilarity:
        """Update the status of a similarity record"""
        try:
            similarity = self.get_by_id(similarity_id)
            if not similarity:
                raise NotFoundException(f"Similarity record with ID {similarity_id} not found")

            similarity.status = status
            similarity.updated_at = datetime.utcnow()

            if error_message:
                similarity.error_message = error_message

            self.session.add(similarity)
            self.session.commit()
            self.session.refresh(similarity)
            return similarity
        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to update similarity status: {str(e)}")

    def update_results(self, similarity_id: UUID, results: dict) -> SubmissionSimilarity:
        """Update similarity results"""
        try:
            similarity = self.get_by_id(similarity_id)
            if not similarity:
                raise NotFoundException(f"Similarity record with ID {similarity_id} not found")

            # Update similarity metrics
            similarity.jaccard_similarity = results.get("jaccard_similarity", 0.0)
            similarity.type_similarity = results.get("type_similarity", 0.0)
            similarity.overall_similarity = results.get("overall_similarity", 0.0)
            similarity.shared_blocks_count = results.get("shared_blocks_count", 0)
            similarity.average_shared_similarity = results.get("average_shared_similarity", 0.0)
            similarity.structural_similarity = results.get("structural_similarity", 0.0)
            similarity.type_sequence_similarity = results.get("type_sequence_similarity", 0.0)
            similarity.flow_similarity = results.get("flow_similarity", 0.0)
            similarity.operation_similarity = results.get("operation_similarity", 0.0)

            # Update detailed results
            similarity.similarity_details = results.get("similarity_details")
            similarity.shared_blocks = results.get("shared_blocks")
            similarity.visualization_data = results.get("visualization_data")

            # Update timing and status
            similarity.processing_time_seconds = results.get("processing_time_seconds")
            similarity.status = SimilarityStatus.COMPLETED
            similarity.updated_at = datetime.utcnow()

            self.session.add(similarity)
            self.session.commit()
            self.session.refresh(similarity)
            return similarity
        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to update similarity results: {str(e)}")

    def delete(self, similarity_id: UUID) -> bool:
        """Delete a similarity record"""
        try:
            similarity = self.get_by_id(similarity_id)
            if not similarity:
                raise NotFoundException(f"Similarity record with ID {similarity_id} not found")

            self.session.delete(similarity)
            self.session.commit()
            return True
        except NotFoundException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete similarity record: {str(e)}")

    def delete_by_submission_id(self, submission_id: UUID) -> bool:
        """Delete all similarity records for a specific submission"""
        try:
            statement = select(SubmissionSimilarity).where(
                or_(
                    SubmissionSimilarity.submission_id == submission_id,
                    SubmissionSimilarity.compared_submission_id == submission_id,
                )
            )
            similarities = list(self.session.exec(statement).all())

            if not similarities:
                return False

            for similarity in similarities:
                self.session.delete(similarity)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete similarity records for submission: {str(e)}")

    def get_statistics(self, project_uuid: UUID, project_step_uuid: UUID) -> dict:
        """Get similarity statistics for a project step"""
        try:
            statement = select(SubmissionSimilarity).where(
                SubmissionSimilarity.project_uuid == project_uuid,
                SubmissionSimilarity.project_step_uuid == project_step_uuid,
            )
            similarities = list(self.session.exec(statement).all())

            if not similarities:
                return {
                    "total_comparisons": 0,
                    "high_similarity_pairs": 0,
                    "average_similarity": 0.0,
                    "max_similarity": 0.0,
                    "status_breakdown": {},
                }

            total_comparisons = len(similarities)
            high_similarity_pairs = len([s for s in similarities if s.overall_similarity >= 0.7])
            average_similarity = sum(s.overall_similarity for s in similarities) / total_comparisons
            max_similarity = max(s.overall_similarity for s in similarities)

            status_breakdown = {}
            for similarity in similarities:
                status = similarity.status
                status_breakdown[status] = status_breakdown.get(status, 0) + 1

            return {
                "total_comparisons": total_comparisons,
                "high_similarity_pairs": high_similarity_pairs,
                "average_similarity": round(average_similarity, 3),
                "max_similarity": round(max_similarity, 3),
                "status_breakdown": status_breakdown,
            }
        except Exception as e:
            raise DatabaseException(f"Failed to get similarity statistics: {str(e)}")

    def check_existing_comparison(self, submission_id: UUID, compared_submission_id: UUID) -> bool:
        """Check if a comparison already exists between two submissions"""
        try:
            statement = select(SubmissionSimilarity).where(
                SubmissionSimilarity.submission_id == submission_id,
                SubmissionSimilarity.compared_submission_id == compared_submission_id,
            )
            return self.session.exec(statement).first() is not None
        except Exception as e:
            raise DatabaseException(f"Failed to check existing comparison: {str(e)}")
