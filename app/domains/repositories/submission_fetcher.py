import logging
import tempfile
from pathlib import Path

from app.domains.repositories.exceptions import (
    RepositoryFetchException,
    SubmissionValidationException,
    TemporaryDirectoryException,
    UnsupportedRepositoryException,
)
from app.domains.repositories.fetchers.github_fetcher import GithubFetcher
from app.domains.repositories.fetchers.gitlab_fetcher import GitlabFetcher
from app.domains.repositories.fetchers.s3_fetcher import S3Fetcher
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto

logger = logging.getLogger(__name__)


def cleanup_temp_directory(repo_path: Path) -> None:
    """
    Clean up the temporary directory after fetching

    Args:
        repo_path: Path to the fetched repository

    Raises:
        Exception: If cleanup fails
    """
    try:
        if repo_path and repo_path.exists():
            logger.debug(f"Cleaning up temporary directory: {repo_path}")
            import shutil

            shutil.rmtree(repo_path, ignore_errors=True)
            logger.info(f"Successfully cleaned up temporary directory: {repo_path}")
    except Exception as e:
        logger.error(f"Failed to clean up temporary directory {repo_path}: {str(e)}")
        raise TemporaryDirectoryException("cleanup", str(e), str(repo_path))


class SubmissionFetcher:
    """Unified fetcher for submissions from different sources"""

    def __init__(self):
        """
        Initialize submission fetcher
        """
        self.github_fetcher = GithubFetcher()
        self.gitlab_fetcher = GitlabFetcher()
        self.s3_fetcher = S3Fetcher()

    def fetch_submission(self, submission: CreateSubmissionDto) -> Path | None:
        """
        Fetch a submission from any supported source

        Args:
            submission: Submission object containing the project URL and metadata
            temp_dir: Optional temporary directory path. If not provided, creates one.

        Returns:
            Path to the fetched submission

        Raises:
            RepositoryFetchException: If URL is not supported or fetching fails
            SubmissionValidationException: If submission validation fails
        """

        try:
            # Validate submission
            if not submission or not submission.link:
                raise SubmissionValidationException(
                    "Submission must have a valid link",
                    submission_id=str(submission.project_uuid) if submission else None,
                )

            project_url = submission.link.strip()
            if not project_url:
                raise SubmissionValidationException(
                    "Submission link cannot be empty", submission_id=str(submission.project_uuid)
                )

            # Create temporary directory
            temp_dir = self._create_temp_directory(project_url)

            # Validate temporary directory
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                try:
                    temp_path.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created temporary directory path: {temp_path}")
                except Exception as e:
                    raise TemporaryDirectoryException("creation", str(e), str(temp_path))

            # Determine the source type and fetch accordingly
            try:
                project_type = self._determine_project_type(project_url)
            except UnsupportedRepositoryException:
                raise
            except Exception as e:
                raise UnsupportedRepositoryException(project_url, self.get_supported_types())

            logger.info(
                f"Fetching {project_type} submission: {project_url} (Project: {submission.project_uuid}, Group: {submission.group_uuid})"
            )

            # Fetch from appropriate source
            try:
                if project_type == "github":
                    result_path = self.github_fetcher.clone_github_repo(project_url, temp_dir)
                elif project_type == "gitlab":
                    result_path = self.gitlab_fetcher.clone_gitlab_repo(project_url, temp_dir)
                elif project_type == "s3":
                    result_path = self.s3_fetcher.fetch_s3_content(project_url, temp_dir)
                else:
                    raise UnsupportedRepositoryException(project_url, self.get_supported_types())

                # Validate the result
                if not result_path or not result_path.exists():
                    raise RepositoryFetchException(
                        f"Fetch completed but no content found at: {result_path}", project_type, project_url
                    )

                # Log successful fetch with statistics
                try:
                    file_count = len(list(result_path.rglob("*")))
                    logger.info(
                        f"Successfully fetched {project_type} submission: {project_url} -> {result_path} ({file_count} items)"
                    )
                except Exception:
                    logger.info(f"Successfully fetched {project_type} submission: {project_url} -> {result_path}")

                return result_path

            except (RepositoryFetchException, UnsupportedRepositoryException):
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error during {project_type} fetch: {str(e)}")
                raise RepositoryFetchException(
                    f"Unexpected error during {project_type} fetch: {str(e)}", project_type, project_url
                )

        except (RepositoryFetchException, SubmissionValidationException, TemporaryDirectoryException):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching submission {submission.project_uuid}/{submission.group_uuid}: {str(e)}"
            )
            raise RepositoryFetchException(
                f"Unexpected error fetching submission: {str(e)}",
                source_url=project_url if "project_url" in locals() else submission.link if submission else None,
            )

    def _create_temp_directory(self, project_url: str) -> str:
        """Create a temporary directory for submission fetching"""
        # Create a safe prefix from the URL
        safe_prefix = "submission_fetch_"
        temp_dir = tempfile.mkdtemp(prefix=safe_prefix)
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir

    def _determine_project_type(self, project_url: str) -> str:
        """
        Determine the type of project based on the URL

        Args:
            project_url: URL of the project

        Returns:
            Project type ("github", "gitlab", or "s3")

        Raises:
            UnsupportedRepositoryException: If URL type cannot be determined
        """
        if not project_url or not project_url.strip():
            raise UnsupportedRepositoryException(
                "Empty project URL",
                ["https://github.com/user/repo", "https://gitlab.com/user/repo", "s3://bucket/path"],
            )

        url_lower = project_url.lower().strip()

        try:
            if url_lower.startswith("s3://"):
                return "s3"
            elif "github.com" in url_lower:
                return "github"
            elif "gitlab.com" in url_lower or "/gitlab" in url_lower:
                return "gitlab"
            else:
                raise UnsupportedRepositoryException(
                    project_url, ["https://github.com/user/repo", "https://gitlab.com/user/repo", "s3://bucket/path"]
                )
        except UnsupportedRepositoryException:
            raise
        except Exception as e:
            logger.error(f"Error determining project type for {project_url}: {str(e)}")
            raise UnsupportedRepositoryException(
                project_url, ["https://github.com/user/repo", "https://gitlab.com/user/repo", "s3://bucket/path"]
            )

    def is_supported_submission(self, submission: CreateSubmissionDto) -> bool:
        """
        Check if the submission URL is supported

        Args:
            submission: Submission to check

        Returns:
            True if supported, False otherwise
        """
        try:
            if not submission or not submission.link:
                return False
            self._determine_project_type(submission.link)
            return True
        except (UnsupportedRepositoryException, SubmissionValidationException):
            return False
        except Exception as e:
            logger.warning(f"Error checking if submission is supported: {str(e)}")
            return False

    def get_supported_types(self) -> list[str]:
        """
        Get list of supported project types

        Returns:
            List of supported project types
        """
        return ["github", "gitlab", "s3"]
