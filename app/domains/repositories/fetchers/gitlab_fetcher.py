import logging
import subprocess
from pathlib import Path

from app.domains.repositories.exceptions import GitCloneException, GitTimeoutException, UnsupportedRepositoryException

logger = logging.getLogger(__name__)


def _extract_repo_name(repo_url: str) -> str:
    """Extract repository name from GitLab URL"""
    # Handle various GitLab URL formats
    url_parts = repo_url.rstrip("/").split("/")
    if len(url_parts) >= 2:
        repo_name = url_parts[-1]
        # Remove .git suffix if present
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        return repo_name
    return "repo"


def _normalize_gitlab_url(repo_url: str) -> str:
    """
    Normalize GitLab URL for cloning

    Args:
        repo_url: GitLab repository URL

    Returns:
        Normalized HTTPS URL for cloning

    Raises:
        UnsupportedRepositoryException: If URL format is not supported
    """
    if not repo_url or not repo_url.strip():
        raise UnsupportedRepositoryException(
            "Empty repository URL", ["https://gitlab.com/user/repo", "git@gitlab.com:user/repo"]
        )

    url = repo_url.strip()

    try:
        # Handle different GitLab URL formats
        if url.startswith("https://gitlab.com/"):
            # GitLab.com HTTPS format
            if not url.endswith(".git"):
                url += ".git"
            # Validate it has user/repo format
            path_part = url.replace("https://gitlab.com/", "").replace(".git", "")
            if "/" not in path_part:
                raise UnsupportedRepositoryException(repo_url, ["https://gitlab.com/user/repo"])
            return url
        elif url.startswith("git@gitlab.com:"):
            # GitLab.com SSH format
            repo_path = url.replace("git@gitlab.com:", "").rstrip("/")
            if not repo_path or "/" not in repo_path:
                raise UnsupportedRepositoryException(repo_url, ["git@gitlab.com:user/repo"])
            return f"https://gitlab.com/{repo_path}.git"
        elif url.startswith("https://") and "gitlab" in url.lower():
            # Self-hosted GitLab instance
            if not url.endswith(".git"):
                url += ".git"
            # Basic validation for self-hosted
            if url.count("/") < 4:  # https://domain/user/repo
                raise UnsupportedRepositoryException(repo_url, ["https://gitlab.example.com/user/repo"])
            return url
        elif url.startswith("git@") and "gitlab" in url.lower():
            # Self-hosted GitLab SSH
            if ":" not in url:
                raise UnsupportedRepositoryException(repo_url, ["git@gitlab.example.com:user/repo"])
            # Convert to HTTPS format
            parts = url.split(":")
            if len(parts) != 2:
                raise UnsupportedRepositoryException(repo_url, ["git@gitlab.example.com:user/repo"])
            host = parts[0].replace("git@", "")
            repo_path = parts[1].rstrip("/")
            if not repo_path or "/" not in repo_path:
                raise UnsupportedRepositoryException(repo_url, ["git@gitlab.example.com:user/repo"])
            return f"https://{host}/{repo_path}.git"
        else:
            # Unsupported format
            raise UnsupportedRepositoryException(
                repo_url,
                ["https://gitlab.com/user/repo", "git@gitlab.com:user/repo", "https://gitlab.example.com/user/repo"],
            )
    except UnsupportedRepositoryException:
        raise
    except Exception as e:
        logger.error(f"Error normalizing GitLab URL {repo_url}: {str(e)}")
        raise UnsupportedRepositoryException(
            repo_url,
            ["https://gitlab.com/user/repo", "git@gitlab.com:user/repo", "https://gitlab.example.com/user/repo"],
        )


class GitlabFetcher:
    def clone_gitlab_repo(self, repo_url: str, temp_dir: str) -> Path:
        """
        Clone a GitLab repository to the temporary directory

        Args:
            repo_url: GitLab repository URL
            temp_dir: Temporary directory path

        Returns:
            Path to the cloned repository

        Raises:
            GitCloneException: If cloning fails
            GitTimeoutException: If cloning times out
        """
        try:
            # Validate and normalize the URL
            clone_url = _normalize_gitlab_url(repo_url)
            repo_name = _extract_repo_name(repo_url)
            repo_path = Path(temp_dir) / repo_name

            logger.info(f"Starting GitLab clone: {clone_url} -> {repo_path}")

            # Validate temporary directory
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                try:
                    temp_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise GitCloneException(repo_url, "gitlab", f"Failed to create temporary directory: {str(e)}")

            # Check if destination already exists
            if repo_path.exists():
                logger.warning(f"Destination path already exists, removing: {repo_path}")
                import shutil

                try:
                    shutil.rmtree(repo_path)
                except OSError as e:
                    raise GitCloneException(repo_url, "gitlab", f"Failed to remove existing directory: {str(e)}")

            # Prepare git clone command
            cmd = ["git", "clone", "--depth", "1", "--single-branch", clone_url, str(repo_path)]

            logger.debug(f"Executing command: {' '.join(cmd)}")

            # Execute git clone with timeout
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=temp_dir)  # 5 minutes
            except subprocess.TimeoutExpired as e:
                logger.error(f"GitLab clone timed out after 300 seconds: {repo_url}")
                raise GitTimeoutException(repo_url, "gitlab", 300)

            # Check clone result
            if result.returncode != 0:
                error_output = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Git clone failed for {repo_url}: {error_output}")

                # Analyze error for more specific messages
                if "not found" in error_output.lower() or "repository not found" in error_output.lower():
                    raise GitCloneException(
                        repo_url, "gitlab", "Repository not found or access denied", result.returncode
                    )
                elif "authentication" in error_output.lower() or "permission denied" in error_output.lower():
                    raise GitCloneException(
                        repo_url, "gitlab", "Authentication failed or access denied", result.returncode
                    )
                elif "network" in error_output.lower() or "could not resolve" in error_output.lower():
                    raise GitCloneException(
                        repo_url, "gitlab", "Network error or DNS resolution failed", result.returncode
                    )
                else:
                    raise GitCloneException(repo_url, "gitlab", error_output, result.returncode)

            # Verify the clone was successful
            if not repo_path.exists():
                raise GitCloneException(repo_url, "gitlab", "Clone completed but repository directory not found")

            # Check if it's a valid git repository
            git_dir = repo_path / ".git"
            if not git_dir.exists():
                raise GitCloneException(repo_url, "gitlab", "Clone completed but .git directory not found")

            # Log success with repository info
            try:
                file_count = len(list(repo_path.rglob("*")))
                logger.info(f"Successfully cloned GitLab repository to: {repo_path} ({file_count} items)")
            except Exception:
                logger.info(f"Successfully cloned GitLab repository to: {repo_path}")

            return repo_path

        except (GitCloneException, GitTimeoutException):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error cloning GitLab repository {repo_url}: {str(e)}")
            raise GitCloneException(repo_url, "gitlab", f"Unexpected error: {str(e)}")
