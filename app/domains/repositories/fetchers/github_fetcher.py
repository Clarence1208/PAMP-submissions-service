import logging
import subprocess
from pathlib import Path

from app.domains.repositories.exceptions import (
    GitCloneException, GitTimeoutException, UnsupportedRepositoryException
)

logger = logging.getLogger(__name__)


def _normalize_github_url(repo_url: str) -> str:
    """
    Normalize GitHub URL for cloning

    Args:
        repo_url: GitHub repository URL

    Returns:
        Normalized HTTPS URL for cloning

    Raises:
        UnsupportedRepositoryException: If URL format is not supported
    """
    if not repo_url or not repo_url.strip():
        raise UnsupportedRepositoryException("Empty repository URL",
                                             ["https://github.com/user/repo", "git@github.com:user/repo"])

    url = repo_url.strip()

    try:
        # Handle different GitHub URL formats
        if url.startswith("https://github.com/"):
            # Already in HTTPS format
            if not url.endswith(".git"):
                url += ".git"
            # Validate it has user/repo format
            path_part = url.replace("https://github.com/", "").replace(".git", "")
            if "/" not in path_part or path_part.count("/") != 1:
                raise UnsupportedRepositoryException(repo_url, ["https://github.com/user/repo"])
            return url
        elif url.startswith("git@github.com:"):
            # Convert SSH to HTTPS
            repo_path = url.replace("git@github.com:", "").rstrip("/")
            if not repo_path or "/" not in repo_path:
                raise UnsupportedRepositoryException(repo_url, ["git@github.com:user/repo"])
            return f"https://github.com/{repo_path}.git"
        elif "/" in url and not url.startswith("http"):
            # Assume it's a "user/repo" format
            repo_path = url.rstrip("/")
            # Validate format
            if repo_path.count("/") != 1:
                raise UnsupportedRepositoryException(repo_url, ["user/repo"])
            return f"https://github.com/{repo_path}.git"
        else:
            # Unsupported format
            raise UnsupportedRepositoryException(repo_url,
                                                 ["https://github.com/user/repo", "git@github.com:user/repo",
                                                  "user/repo"])
    except UnsupportedRepositoryException:
        raise
    except Exception as e:
        logger.error(f"Error normalizing GitHub URL {repo_url}: {str(e)}")
        raise UnsupportedRepositoryException(repo_url, ["https://github.com/user/repo", "git@github.com:user/repo",
                                                        "user/repo"])


def _extract_repo_name(repo_url: str) -> str:
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
            GitCloneException: If cloning fails
            GitTimeoutException: If cloning times out
        """
        try:
            # Validate and normalize the URL
            clone_url = _normalize_github_url(repo_url)
            repo_name = _extract_repo_name(repo_url)
            repo_path = Path(temp_dir) / repo_name

            logger.info(f"Starting GitHub clone: {clone_url} -> {repo_path}")

            # Validate temporary directory
            temp_path = Path(temp_dir)
            if not temp_path.exists():
                try:
                    temp_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise GitCloneException(repo_url, "github", f"Failed to create temporary directory: {str(e)}")

            # Check if destination already exists
            if repo_path.exists():
                logger.warning(f"Destination path already exists, removing: {repo_path}")
                import shutil
                try:
                    shutil.rmtree(repo_path)
                except OSError as e:
                    raise GitCloneException(repo_url, "github", f"Failed to remove existing directory: {str(e)}")

            # Prepare git clone command
            cmd = ["git", "clone", "--depth", "1", "--single-branch", clone_url, str(repo_path)]

            logger.debug(f"Executing command: {' '.join(cmd)}")

            # Execute git clone with timeout
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes
                    cwd=temp_dir
                )
            except subprocess.TimeoutExpired as e:
                logger.error(f"GitHub clone timed out after 300 seconds: {repo_url}")
                raise GitTimeoutException(repo_url, "github", 300)

            # Check clone result
            if result.returncode != 0:
                error_output = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Git clone failed for {repo_url}: {error_output}")

                # Analyze error for more specific messages
                if "not found" in error_output.lower() or "repository not found" in error_output.lower():
                    raise GitCloneException(repo_url, "github", "Repository not found or access denied",
                                            result.returncode)
                elif "authentication" in error_output.lower() or "permission denied" in error_output.lower():
                    raise GitCloneException(repo_url, "github", "Authentication failed or access denied",
                                            result.returncode)
                elif "network" in error_output.lower() or "could not resolve" in error_output.lower():
                    raise GitCloneException(repo_url, "github", "Network error or DNS resolution failed",
                                            result.returncode)
                else:
                    raise GitCloneException(repo_url, "github", error_output, result.returncode)

            # Verify the clone was successful
            if not repo_path.exists():
                raise GitCloneException(repo_url, "github", "Clone completed but repository directory not found")

            # Check if it's a valid git repository
            git_dir = repo_path / ".git"
            if not git_dir.exists():
                raise GitCloneException(repo_url, "github", "Clone completed but .git directory not found")

            # Log success with repository info
            try:
                file_count = len(list(repo_path.rglob("*")))
                logger.info(f"Successfully cloned GitHub repository to: {repo_path} ({file_count} items)")
            except Exception:
                logger.info(f"Successfully cloned GitHub repository to: {repo_path}")

            return repo_path

        except (GitCloneException, GitTimeoutException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error cloning GitHub repository {repo_url}: {str(e)}")
            raise GitCloneException(repo_url, "github", f"Unexpected error: {str(e)}")
