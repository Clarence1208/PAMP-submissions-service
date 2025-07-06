import logging
import subprocess
from pathlib import Path

from app.shared.exceptions import ValidationException

logger = logging.getLogger(__name__)


class GithubFetcher:

    def clone_github_repo(self, repo_url: str, temp_dir: str) -> Path:
        """
        Clone a GitHub repository to the temporary directory

        Args:
            repo_url: GitHub repository URL
            temp_dir: Temporary directory path

        Returns:
            Path to the cloned repository

        Raises:
            ValidationException: If cloning fails
        """
        repo_name = self._extract_repo_name(repo_url)
        repo_path = Path(temp_dir) / repo_name

        try:
            # Prepare git clone command
            clone_url = self._normalize_github_url(repo_url)
            cmd = ["git", "clone", "--depth", "1", clone_url, str(repo_path)]

            logger.info(f"Cloning repository: {clone_url}")

            # Execute git clone
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                error_msg = f"Git clone failed: {result.stderr}"
                logger.error(error_msg)
                raise ValidationException(error_msg)

            logger.info(f"Successfully cloned repository to: {repo_path}")
            return repo_path

        except subprocess.TimeoutExpired:
            raise ValidationException("Repository cloning timed out (5 minutes)")
        except Exception as e:
            raise ValidationException(f"Failed to clone repository: {str(e)}")

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from GitHub URL"""
        # Handle various GitHub URL formats
        url_parts = repo_url.rstrip("/").split("/")
        if len(url_parts) >= 2:
            repo_name = url_parts[-1]
            # Remove .git suffix if present
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            return repo_name
        return "repo"

    def _normalize_github_url(self, repo_url: str) -> str:
        """Normalize GitHub URL for cloning"""
        url = repo_url.strip()

        # If it's already a .git URL, use it as is
        if url.endswith(".git"):
            return url

        # If it's a web URL, convert to .git URL
        if url.startswith("https://github.com/"):
            if not url.endswith(".git"):
                url += ".git"
            return url

        # else we don't know the format, return as is
        return url
