import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.detection.visualization import VisualizationService
from app.domains.repositories.submission_fetcher import SubmissionFetcher, cleanup_temp_directory
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.submissions.submissions_models import SimilarityStatus, Submission
from app.domains.submissions.submissions_repository import SubmissionRepository
from app.domains.submissions.submissions_similarity_repository import SubmissionSimilarityRepository
from app.domains.tokenization.tokenization_service import TokenizationService
from app.shared.exceptions import DatabaseException, ValidationException

logger = logging.getLogger(__name__)


class DetectionIntegrationService:
    """Service for integrating similarity detection with submissions"""

    def __init__(self, session: Session):
        self.session = session
        self.submission_repository = SubmissionRepository(session)
        self.similarity_repository = SubmissionSimilarityRepository(session)
        self.tokenization_service = TokenizationService()
        self.similarity_service = SimilarityDetectionService()
        self.visualization_service = VisualizationService(self.tokenization_service)
        self.submission_fetcher = SubmissionFetcher()

        # Create thread pool with limited workers to prevent server overload
        self.similarity_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="similarity")

        # Thread-local storage for database sessions
        self._local = threading.local()

    def _get_thread_session(self) -> Session:
        """Get thread-local database session"""
        if not hasattr(self._local, "session"):
            from app.shared.database import get_session

            self._local.session = next(get_session())
        return self._local.session

    def process_submission_similarities_async(self, submission: Submission) -> None:
        """
        Process similarity detection asynchronously - doesn't block submission creation
        """
        try:
            # Get all other submissions in the same project step
            other_submissions = self.submission_repository.get_by_project_step(
                submission.project_uuid, submission.project_step_uuid
            )

            # Filter out the current submission and get only completed ones
            other_submissions = [
                s for s in other_submissions if s.id != submission.id and s.group_uuid != submission.group_uuid
            ]

            if not other_submissions:
                logger.info(f"No other submissions found for comparison with submission {submission.id}")
                return

            # Submit all comparisons to thread pool (fire and forget)
            for other_submission in other_submissions:
                self.similarity_executor.submit(
                    self._process_single_comparison_threaded,
                    submission.id,
                    other_submission.id,
                    submission.project_uuid,
                    submission.project_step_uuid,
                )

            logger.info(
                f"Started async similarity processing for submission {submission.id} "
                f"against {len(other_submissions)} other submissions"
            )

        except Exception as e:
            logger.error(f"Failed to start async similarity processing: {str(e)}")

    def _process_single_comparison_threaded(
        self, submission1_id: UUID, submission2_id: UUID, project_uuid: UUID, project_step_uuid: UUID
    ) -> None:
        """Process a single comparison in a thread with its own database session"""
        try:
            # Get thread-local session and repositories
            thread_session = self._get_thread_session()
            thread_submission_repo = SubmissionRepository(thread_session)
            thread_similarity_repo = SubmissionSimilarityRepository(thread_session)

            # Get submissions
            submission1 = thread_submission_repo.get_by_id(submission1_id)
            submission2 = thread_submission_repo.get_by_id(submission2_id)

            if not submission1 or not submission2:
                logger.error(f"Submissions not found: {submission1_id}, {submission2_id}")
                return

            # Check if comparison already exists
            if thread_similarity_repo.check_existing_comparison(submission1_id, submission2_id):
                logger.info(f"Comparison already exists between {submission1_id} and {submission2_id}")
                return

            # Create similarity record
            similarity_record = thread_similarity_repo.create(
                {
                    "submission_id": submission1_id,
                    "compared_submission_id": submission2_id,
                    "project_uuid": project_uuid,
                    "project_step_uuid": project_step_uuid,
                    "status": SimilarityStatus.PENDING,
                }
            )

            # Process the comparison using existing logic
            self._process_single_comparison_with_repos(
                similarity_record, submission1, submission2, thread_submission_repo, thread_similarity_repo
            )

            logger.info(f"Completed async comparison between {submission1_id} and {submission2_id}")

        except Exception as e:
            logger.error(f"Failed async comparison between {submission1_id} and {submission2_id}: {str(e)}")

    def _process_single_comparison_with_repos(
        self,
        similarity_record,
        submission1: Submission,
        submission2: Submission,
        submission_repo: SubmissionRepository,
        similarity_repo: SubmissionSimilarityRepository,
    ) -> None:
        """Process comparison with provided repositories (for thread safety)"""
        start_time = time.time()

        try:
            # Update status to processing
            similarity_repo.update_status(similarity_record.id, SimilarityStatus.PROCESSING)

            # Fetch both submissions
            submission1_data = CreateSubmissionDto(
                link=submission1.link,
                project_uuid=submission1.project_uuid,
                group_uuid=submission1.group_uuid,
                project_step_uuid=submission1.project_step_uuid,
                link_type=submission1.link_type,
            )

            submission2_data = CreateSubmissionDto(
                link=submission2.link,
                project_uuid=submission2.project_uuid,
                group_uuid=submission2.group_uuid,
                project_step_uuid=submission2.project_step_uuid,
                link_type=submission2.link_type,
            )

            # Fetch repositories
            repo1_path = None
            repo2_path = None

            try:
                repo1_path = self.submission_fetcher.fetch_submission(submission1_data)
                repo2_path = self.submission_fetcher.fetch_submission(submission2_data)

                if not repo1_path.exists() or not repo2_path.exists():
                    raise HTTPException(status_code=404, detail="Test projects not found")

                # Tokenize all files
                tokens1 = []
                tokens2 = []

                repo1_compatible_files = self.tokenization_service.extract_supported_files_from_directory(repo1_path)
                repo2_compatible_files = self.tokenization_service.extract_supported_files_from_directory(repo2_path)

                for file_path in repo1_compatible_files:
                    if not file_path.is_file():
                        continue
                    content = self._read_file_with_encoding_detection(file_path)
                    if content is not None:
                        tokens = self.tokenization_service.tokenize(content, file_path)
                        tokens1.extend(tokens)

                for file_path in repo2_compatible_files:
                    if not file_path.is_file():
                        continue
                    content = self._read_file_with_encoding_detection(file_path)
                    if content is not None:
                        tokens = self.tokenization_service.tokenize(content, file_path)
                        tokens2.extend(tokens)

                # Perform similarity analysis
                similarity_result = self.similarity_service.compare_similarity(tokens1, tokens2)

                files_with_similarities_visualization = []

                for file_path in repo1_compatible_files:
                    content1 = self._read_file_with_encoding_detection(file_path)

                    for file_path2 in repo2_compatible_files:
                        content2 = self._read_file_with_encoding_detection(file_path2)

                        if content1 is None or content2 is None:
                            continue

                        react_flow_data = self.visualization_service.generate_react_flow_ast(
                            content1, content2, file_path.name, file_path2.name, "elk"
                        )

                        if react_flow_data.get("has_similarity", False):
                            files_with_similarities_visualization.append(
                                {
                                    "file_pair": {
                                        "file_from_submission1": f"{file_path.name}",
                                        "file_from_submission2": f"{file_path2.name}",
                                    },
                                    "react_flow": react_flow_data,
                                }
                            )

                # Sort by similarity
                files_with_similarities_visualization.sort(
                    key=lambda x: x["react_flow"].get("analysis_metadata", {}).get("average_similarity", 0.0),
                    reverse=True,
                )

                # Prepare results
                processing_time = time.time() - start_time

                results = {
                    "jaccard_similarity": similarity_result["jaccard_similarity"],
                    "type_similarity": similarity_result["type_similarity"],
                    "processing_time_seconds": processing_time,
                    "similarity_details": {
                        "algorithm": "ast_similarity",
                        "common_elements": similarity_result["common_elements"],
                        "total_unique_elements": similarity_result["total_unique_elements"],
                        "tokens_count": {"submission1": len(tokens1), "submission2": len(tokens2)},
                        "files_count": {
                            "submission1": len(repo1_compatible_files),
                            "submission2": len(repo2_compatible_files),
                        },
                    },
                    "visualization_data": files_with_similarities_visualization,
                }

                # Update the similarity record with results
                similarity_repo.update_results(similarity_record.id, results)

            finally:
                # Clean up temporary directories
                if repo1_path and repo1_path.exists():
                    cleanup_temp_directory(repo1_path)
                if repo2_path and repo2_path.exists():
                    cleanup_temp_directory(repo2_path)

        except Exception as e:
            # Update status to failed
            similarity_repo.update_status(similarity_record.id, SimilarityStatus.FAILED, str(e))
            logger.error(f"Failed to process comparison: {str(e)}")
            raise

    def process_submission_similarities(self, submission: Submission) -> List[str]:
        """
        Process similarity detection for a new submission against all other submissions
        in the same project step.

        Returns:
            List of similarity record IDs that were created
        """
        try:
            # Get all other submissions in the same project step
            other_submissions = self.submission_repository.get_by_project_step(
                submission.project_uuid, submission.project_step_uuid
            )

            # Filter out the current submission and get only completed ones
            other_submissions = [
                s for s in other_submissions if s.id != submission.id and s.status.value == "completed"
            ]

            if not other_submissions:
                logger.info(f"No other submissions found for comparison with submission {submission.id}")
                return []

            similarity_ids = []

            # Compare against each other submission
            for other_submission in other_submissions:
                try:
                    # Check if comparison already exists
                    if self.similarity_repository.check_existing_comparison(submission.id, other_submission.id):
                        logger.info(f"Comparison already exists between {submission.id} and {other_submission.id}")
                        continue

                    # Create similarity record
                    similarity_record = self.similarity_repository.create(
                        {
                            "submission_id": submission.id,
                            "compared_submission_id": other_submission.id,
                            "project_uuid": submission.project_uuid,
                            "project_step_uuid": submission.project_step_uuid,
                            "status": SimilarityStatus.PENDING,
                        }
                    )

                    similarity_ids.append(str(similarity_record.id))

                    # Process the comparison
                    self._process_single_comparison(similarity_record, submission, other_submission)

                except Exception as e:
                    logger.error(
                        f"Failed to process comparison between {submission.id} and {other_submission.id}: {str(e)}"
                    )
                    continue

            return similarity_ids

        except Exception as e:
            logger.error(f"Failed to process submission similarities: {str(e)}")
            raise DatabaseException(f"Failed to process submission similarities: {str(e)}")

    def _process_single_comparison(self, similarity_record, submission1: Submission, submission2: Submission) -> None:
        """Process a single comparison between two submissions"""
        start_time = time.time()

        try:
            # Update status to processing
            self.similarity_repository.update_status(similarity_record.id, SimilarityStatus.PROCESSING)

            # Fetch both submissions
            submission1_data = CreateSubmissionDto(
                link=submission1.link,
                project_uuid=submission1.project_uuid,
                group_uuid=submission1.group_uuid,
                project_step_uuid=submission1.project_step_uuid,
                link_type=submission1.link_type,
            )

            submission2_data = CreateSubmissionDto(
                link=submission2.link,
                project_uuid=submission2.project_uuid,
                group_uuid=submission2.group_uuid,
                project_step_uuid=submission2.project_step_uuid,
                link_type=submission2.link_type,
            )

            # Fetch repositories
            repo1_path = None
            repo2_path = None

            try:
                repo1_path = self.submission_fetcher.fetch_submission(submission1_data)
                repo2_path = self.submission_fetcher.fetch_submission(submission2_data)

                if not repo1_path.exists() or not repo2_path.exists():
                    raise HTTPException(status_code=404, detail="Test projects not found")

                # Tokenize all files
                tokens1 = []
                tokens2 = []
                source1 = ""
                source2 = ""

                repo1_compatible_files = self.tokenization_service.extract_supported_files_from_directory(repo1_path)
                repo2_compatible_files = self.tokenization_service.extract_supported_files_from_directory(repo2_path)

                for file_path in repo1_compatible_files:
                    if not file_path.is_file():
                        continue

                    # Read and tokenize the file with encoding detection
                    content = self._read_file_with_encoding_detection(file_path)
                    if content is not None:
                        tokens = self.tokenization_service.tokenize(content, file_path)
                        tokens1.extend(tokens)
                        source1 += f"\n# === {file_path.name} ===\n" + content + "\n"

                for file_path in repo2_compatible_files:
                    if not file_path.is_file():
                        continue

                    # Read and tokenize the file with encoding detection
                    content = self._read_file_with_encoding_detection(file_path)
                    if content is not None:
                        tokens = self.tokenization_service.tokenize(content, file_path)
                        tokens2.extend(tokens)
                        source2 += f"\n# === {file_path.name} ===\n" + content + "\n"

                # Perform similarity analysis
                similarity_result = self.similarity_service.compare_similarity(tokens1, tokens2)

                files_with_similarities_visualization = []

                for file_path in repo1_compatible_files:
                    content1 = self._read_file_with_encoding_detection(file_path)

                    for file_path2 in repo2_compatible_files:
                        content2 = self._read_file_with_encoding_detection(file_path2)

                        if content1 is None or content2 is None:
                            continue

                        react_flow_data = self.visualization_service.generate_react_flow_ast(
                            content1, content2, file_path.name, file_path2.name, "elk"  # Always use ELK
                        )

                        if react_flow_data.get("has_similarity", False):
                            files_with_similarities_visualization.append(
                                {
                                    "file_pair": {
                                        "file_from_submission1": f"{file_path.name}",
                                        "file_from_submission2": f"{file_path2.name}",
                                    },
                                    "react_flow": react_flow_data,
                                }
                            )

                # order the files pairs by the "analysis_metadata" -> "average_similarity" from the react_flow_data, most similar first
                files_with_similarities_visualization.sort(
                    key=lambda x: x["react_flow"].get("analysis_metadata", {}).get("average_similarity", 0.0),
                    reverse=True,
                )

                # Calculate overall similarity score
                # overall_similarity = self._calculate_overall_similarity(
                #     similarity_result, shared_blocks_result
                # )

                # Prepare results
                processing_time = time.time() - start_time

                results = {
                    "jaccard_similarity": similarity_result["jaccard_similarity"],
                    "type_similarity": similarity_result["type_similarity"],
                    # "overall_similarity": overall_similarity,
                    # "shared_blocks_count": shared_blocks_result['total_shared_blocks'],
                    # "average_shared_similarity": shared_blocks_result['average_similarity'],
                    "processing_time_seconds": processing_time,
                    "similarity_details": {
                        "algorithm": "ast_similarity",
                        "common_elements": similarity_result["common_elements"],
                        "total_unique_elements": similarity_result["total_unique_elements"],
                        "tokens_count": {"submission1": len(tokens1), "submission2": len(tokens2)},
                        "files_count": {
                            "submission1": len(repo1_compatible_files),
                            "submission2": len(repo2_compatible_files),
                        },
                    },
                    # "shared_blocks": {
                    #     "blocks": shared_blocks_result['shared_blocks'],
                    #     "functions_file1": shared_blocks_result['functions_file1'],
                    #     "functions_file2": shared_blocks_result['functions_file2'],
                    #     "shared_percentage": shared_blocks_result['shared_percentage']
                    # },
                    "visualization_data": files_with_similarities_visualization,
                }

                # Update the similarity record with results
                self.similarity_repository.update_results(similarity_record.id, results)

                # logger.info(f"Successfully processed comparison between {submission1.id} and {submission2.id} "
                #            f"with overall similarity: {overall_similarity:.3f}")

            finally:
                # Clean up temporary directories
                if repo1_path and repo1_path.exists():
                    cleanup_temp_directory(repo1_path)
                if repo2_path and repo2_path.exists():
                    cleanup_temp_directory(repo2_path)

        except Exception as e:
            # Update status to failed
            self.similarity_repository.update_status(similarity_record.id, SimilarityStatus.FAILED, str(e))
            logger.error(f"Failed to process comparison: {str(e)}")
            raise

    def _detect_shared_blocks_multifile(
        self,
        repo1_path: Path,
        repo2_path: Path,
        repo1_files: List[Path],
        repo2_files: List[Path],
        submission1: Submission,
        submission2: Submission,
    ) -> Dict[str, Any]:
        """
        Optimized detection of shared code blocks between multi-file submissions.
        Pre-processes files once and uses smart pairing to avoid redundant work.
        """
        # Step 1: Pre-process all files once (extract functions and group by language)
        repo1_processed = self._preprocess_files(repo1_files, repo1_path, "submission1")
        repo2_processed = self._preprocess_files(repo2_files, repo2_path, "submission2")

        if not repo1_processed or not repo2_processed:
            return {
                "shared_blocks": [],
                "total_shared_blocks": 0,
                "average_similarity": 0.0,
                "functions_file1": 0,
                "functions_file2": 0,
                "shared_percentage": 0.0,
                "file_comparisons": 0,
                "successful_comparisons": 0,
            }

        # Step 2: Smart pairing - only compare files that make sense
        file_pairs = self._create_smart_file_pairs(repo1_processed, repo2_processed)

        # Step 3: Compare file pairs efficiently
        all_shared_blocks = []
        successful_comparisons = 0

        for file1_data, file2_data in file_pairs:
            try:
                comparison_result = self._compare_processed_files(file1_data, file2_data, repo1_path, repo2_path)

                if comparison_result and comparison_result.get("shared_blocks"):
                    all_shared_blocks.extend(comparison_result["shared_blocks"])
                    successful_comparisons += 1

            except Exception as e:
                logger.warning(f"Failed to compare {file1_data['name']} vs {file2_data['name']}: {e}")
                continue

        # Calculate aggregate statistics
        total_similarity = sum(block.get("similarity_score", 0.0) for block in all_shared_blocks)
        average_similarity = total_similarity / len(all_shared_blocks) if all_shared_blocks else 0.0

        result = {
            "shared_blocks": all_shared_blocks,
            "total_shared_blocks": len(all_shared_blocks),
            "average_similarity": average_similarity,
            "functions_file1": sum(1 for block in all_shared_blocks if "function1_name" in block),
            "functions_file2": sum(1 for block in all_shared_blocks if "function2_name" in block),
            "shared_percentage": (successful_comparisons / len(file_pairs)) * 100 if file_pairs else 0.0,
            "file_comparisons": len(file_pairs),
            "successful_comparisons": successful_comparisons,
        }

        logger.info(
            f"Optimized comparison: {successful_comparisons}/{len(file_pairs)} smart file pairs had similarities, {len(all_shared_blocks)} total shared blocks found"
        )
        return result

    def _preprocess_files(self, files: List[Path], repo_path: Path, repo_name: str) -> Dict[str, List[Dict]]:
        """
        Pre-process all files once: read content, detect language, extract functions.
        Groups files by language for smart pairing.
        """
        processed_by_language = {}

        for file_path in files:
            if not file_path.is_file():
                continue

            content = self._read_file_with_encoding_detection(file_path)
            if content is None:
                continue

            # Detect language once
            language = self.tokenization_service._detect_language(file_path)

            # Extract functions once
            functions = self.tokenization_service.extract_functions_with_positions(content, file_path)

            file_data = {
                "path": file_path,
                "name": file_path.name,
                "relative_path": str(file_path.relative_to(repo_path)),
                "content": content,
                "language": language,
                "functions": functions,
                "function_count": len(functions),
            }

            # Group by language for smart pairing
            if language not in processed_by_language:
                processed_by_language[language] = []
            processed_by_language[language].append(file_data)

        logger.info(
            f"Pre-processed {sum(len(files) for files in processed_by_language.values())} files from {repo_name} across {len(processed_by_language)} languages"
        )
        return processed_by_language

    def _create_smart_file_pairs(self, repo1_processed: Dict, repo2_processed: Dict) -> List[tuple]:
        """
        Create smart file pairs for comparison. Only pair files that make sense:
        1. Same language
        2. Similar file names (optional optimization)
        3. Both have functions (skip empty files)
        """
        file_pairs = []

        # Only compare files of the same language
        for language in repo1_processed.keys():
            if language not in repo2_processed:
                continue

            files1 = repo1_processed[language]
            files2 = repo2_processed[language]

            # Filter files that have functions (skip empty files)
            files1_with_functions = [f for f in files1 if f["function_count"] > 0]
            files2_with_functions = [f for f in files2 if f["function_count"] > 0]

            # Create all combinations for this language
            for file1 in files1_with_functions:
                for file2 in files2_with_functions:
                    file_pairs.append((file1, file2))

        logger.info(f"Created {len(file_pairs)} smart file pairs for comparison")
        return file_pairs

    def _compare_processed_files(self, file1_data: Dict, file2_data: Dict, repo1_path: Path, repo2_path: Path) -> Dict:
        """
        Compare two pre-processed files using their already extracted functions.
        """
        comparison_result = self.similarity_service.detect_shared_code_blocks(
            source1=file1_data["content"],
            source2=file2_data["content"],
            file1_name=file1_data["name"],
            file2_name=file2_data["name"],
            file1_path=file1_data["path"],
            file2_path=file2_data["path"],
            tokenization_service=self.tokenization_service,
        )

        # Add file context to shared blocks
        if comparison_result.get("shared_blocks"):
            for block in comparison_result["shared_blocks"]:
                block["file1_path"] = file1_data["relative_path"]
                block["file2_path"] = file2_data["relative_path"]
                block["language"] = file1_data["language"]

        return comparison_result

    def _calculate_overall_similarity(self, similarity_result: dict, shared_blocks_result: dict) -> float:
        """Calculate overall similarity score combining multiple metrics"""
        jaccard_similarity = similarity_result.get("jaccard_similarity", 0.0)
        type_similarity = similarity_result.get("type_similarity", 0.0)
        shared_blocks_similarity = shared_blocks_result.get("average_similarity", 0.0)

        # Weighted combination of similarity metrics
        overall_similarity = jaccard_similarity * 0.4 + type_similarity * 0.3 + shared_blocks_similarity * 0.3

        return round(overall_similarity, 4)

    def _read_file_with_encoding_detection(self, file_path) -> Optional[str]:
        """
        Read a file with multiple encoding attempts to handle various file encodings.

        Args:
            file_path: Path to the file to read

        Returns:
            File content as string, or None if reading fails
        """
        encodings_to_try = [
            "utf-8",
            "utf-8-sig",  # UTF-8 with BOM
            "latin-1",
            "cp1252",  # Windows-1252
            "iso-8859-1",
            "ascii",
        ]

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"Successfully read {file_path} with encoding: {encoding}")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Failed to read {file_path} with encoding {encoding}: {e}")
                continue

        # If all encodings fail, try with error handling
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            logger.warning(f"Read {file_path} with UTF-8 and replaced invalid characters")
            return content
        except Exception as e:
            logger.error(f"Failed to read {file_path} with all encoding attempts: {e}")
            return None

    def get_submission_similarities(self, submission_id: UUID) -> List[dict]:
        """Get all similarity results for a submission (bidirectional)"""
        try:
            similarities = self.similarity_repository.get_by_submission_id(submission_id)

            results = []
            for similarity in similarities:
                # Check if we need to swap the IDs (when the requested submission is in compared_submission_id)
                if similarity.compared_submission_id == submission_id:
                    # Swap the IDs - the requested submission should be the main submission
                    main_submission_id = submission_id
                    compared_submission_id = similarity.submission_id
                else:
                    # Keep the original order
                    main_submission_id = similarity.submission_id
                    compared_submission_id = similarity.compared_submission_id

                # Get the compared submission info
                compared_submission = self.submission_repository.get_by_id(compared_submission_id)

                result = {
                    "similarity_id": similarity.id,
                    "compared_submission_id": compared_submission_id,
                    "compared_submission_link": compared_submission.link if compared_submission else None,
                    "overall_similarity": similarity.overall_similarity,
                    "jaccard_similarity": similarity.jaccard_similarity,
                    "type_similarity": similarity.type_similarity,
                    "shared_blocks_count": similarity.shared_blocks_count,
                    "average_shared_similarity": similarity.average_shared_similarity,
                    "status": similarity.status,
                    "created_at": similarity.created_at,
                    "processing_time_seconds": similarity.processing_time_seconds,
                    "error_message": similarity.error_message,
                    # Add a flag to indicate if this was a swapped result for debugging
                    "is_swapped": similarity.compared_submission_id == submission_id,
                }

                results.append(result)

            return results

        except Exception as e:
            raise DatabaseException(f"Failed to get submission similarities: {str(e)}")

    def get_detailed_comparison(self, similarity_id: UUID) -> dict:
        """Get detailed comparison results including visualization data"""
        try:
            similarity = self.similarity_repository.get_by_id(similarity_id)
            if not similarity:
                raise ValidationException(f"Similarity record with ID {similarity_id} not found")

            # Get submission details
            submission1 = self.submission_repository.get_by_id(similarity.submission_id)
            submission2 = self.submission_repository.get_by_id(similarity.compared_submission_id)

            return {
                "similarity_id": similarity.id,
                "submissions": {
                    "submission1": {
                        "id": submission1.id,
                        "link": submission1.link,
                        "description": submission1.description,
                        "submitted_by_uuid": submission1.submitted_by_uuid,
                        "upload_date_time": submission1.upload_date_time,
                    },
                    "submission2": {
                        "id": submission2.id,
                        "link": submission2.link,
                        "description": submission2.description,
                        "submitted_by_uuid": submission2.submitted_by_uuid,
                        "upload_date_time": submission2.upload_date_time,
                    },
                },
                "similarity_metrics": {
                    "overall_similarity": similarity.overall_similarity,
                    "jaccard_similarity": similarity.jaccard_similarity,
                    "type_similarity": similarity.type_similarity,
                    "shared_blocks_count": similarity.shared_blocks_count,
                    "average_shared_similarity": similarity.average_shared_similarity,
                },
                "analysis_metadata": {
                    "detection_algorithm": similarity.detection_algorithm,
                    "detection_version": similarity.detection_version,
                    "status": similarity.status,
                    "created_at": similarity.created_at,
                    "updated_at": similarity.updated_at,
                    "processing_time_seconds": similarity.processing_time_seconds,
                    "error_message": similarity.error_message,
                },
                "detailed_results": {
                    "similarity_details": similarity.similarity_details,
                    "shared_blocks": similarity.shared_blocks,
                    "visualization_data": similarity.visualization_data,
                },
            }

        except Exception as e:
            raise DatabaseException(f"Failed to get detailed comparison: {str(e)}")

    def get_project_step_statistics(self, project_uuid: UUID, project_step_uuid: UUID) -> dict:
        """Get similarity statistics for a project step"""
        try:
            return self.similarity_repository.get_statistics(project_uuid, project_step_uuid)
        except Exception as e:
            raise DatabaseException(f"Failed to get project step statistics: {str(e)}")

    def get_high_similarity_alerts(
        self, project_uuid: UUID, project_step_uuid: UUID, threshold: float = 0.7
    ) -> List[dict]:
        """Get high similarity alerts for a project step"""
        try:
            high_similarities = self.similarity_repository.get_high_similarity_pairs(
                project_uuid, project_step_uuid, threshold
            )

            alerts = []
            for similarity in high_similarities:
                submission1 = self.submission_repository.get_by_id(similarity.submission_id)
                submission2 = self.submission_repository.get_by_id(similarity.compared_submission_id)

                alert = {
                    "similarity_id": similarity.id,
                    "overall_similarity": similarity.overall_similarity,
                    "shared_blocks_count": similarity.shared_blocks_count,
                    "submission1": {
                        "id": submission1.id,
                        "link": submission1.link,
                        "submitted_by_uuid": submission1.submitted_by_uuid,
                        "upload_date_time": submission1.upload_date_time,
                    },
                    "submission2": {
                        "id": submission2.id,
                        "link": submission2.link,
                        "submitted_by_uuid": submission2.submitted_by_uuid,
                        "upload_date_time": submission2.upload_date_time,
                    },
                    "detected_at": similarity.created_at,
                }

                alerts.append(alert)

            return alerts

        except Exception as e:
            raise DatabaseException(f"Failed to get high similarity alerts: {str(e)}")
