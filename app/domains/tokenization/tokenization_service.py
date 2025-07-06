import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from app.domains.detection.similarity_detection_service import SimilarityDetectionService
from app.domains.repositories.exceptions import (
    RepositoryFetchException,
    SubmissionValidationException,
    TemporaryDirectoryException,
    UnsupportedRepositoryException,
)
from app.domains.repositories.submission_fetcher import SubmissionFetcher, cleanup_temp_directory
from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.shared.exceptions import ValidationException

logger = logging.getLogger(__name__)


class TokenizationService:
    def __init__(self):
        """Initialize the tokenization service with tree-sitter parsers"""
        self.parsers = {}
        self.similarity_service = SimilarityDetectionService()
        self.submission_fetcher = SubmissionFetcher()
        self._setup_parsers()

    def _setup_parsers(self):
        """Set up tree-sitter parsers for different languages"""
        try:
            # Python parser - use tree-sitter 0.24.0 API
            python_language = Language(tspython.language())
            py_parser = Parser()
            py_parser.language = python_language
            self.parsers["python"] = py_parser
            self.parsers[".py"] = py_parser

            logger.info("Tree-sitter parsers initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize parsers: {e}")
            raise

    def _detect_language(self, file_path: Optional[Path] = None, content: Optional[str] = None) -> str:
        """Detect the programming language based on file extension or content"""
        if file_path:
            suffix = file_path.suffix.lower()
            if suffix in self.parsers:
                return suffix

        # Only Python for now
        return ".py"

    def tokenize(self, text: str, file_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Tokenizes the input text into a list of tokens using tree-sitter.
        """
        try:
            # Detect language
            lang_key = self._detect_language(file_path)
            parser = self.parsers.get(lang_key)

            if not parser:
                logger.warning(f"No parser available for {lang_key}, skipping tokenization")
                return []

            # Parse the text
            tree = parser.parse(bytes(text, "utf8"))
            root_node = tree.root_node

            # Extract tokens
            tokens = []
            self._extract_tokens(root_node, text.encode("utf8"), tokens)

            return tokens

        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return []

    def _extract_tokens(self, node, source_code: bytes, tokens: List[Dict[str, Any]]):
        """Recursively extract tokens from the syntax tree"""
        # Add current node as token if it has meaningful content and is named
        if node.start_byte < node.end_byte and node.is_named:
            token_text = source_code[node.start_byte : node.end_byte].decode("utf8")

            token = {
                "type": node.type,
                "text": token_text,
                "start": node.start_point[0],  # Just row number
                "end": node.end_point[0],  # Just row number
            }
            tokens.append(token)

        # Recursively process child nodes
        for child in node.children:
            self._extract_tokens(child, source_code, tokens)

    def detokenize(self, tokens: List[Dict[str, Any]]) -> str:
        """
        Detokenizes a list of tokens back into a string.
        """
        if not tokens:
            return ""

        try:
            # concatenate token texts with spaces
            return " ".join(token.get("text", "") for token in tokens if token.get("text"))

        except Exception as e:
            logger.error(f"Detokenization failed: {e}")
            return ""

    def tokenize_project(self, project_path: Path) -> None:
        """
        Tokenizes all files in the given project directory.
        """
        # Implement tokenization logic for project files
        if not project_path.is_dir():
            raise ValidationException(f"Invalid project path: {project_path}")
        logger.info(f"Tokenizing project files in: {project_path}")
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    tokens = self.tokenize(content, file_path)
                    logger.debug(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(tokens)
                    print("\n\n\n\n")

                    # Optionally save tokens or process further
                except Exception as e:
                    logger.error(f"Failed to tokenize {file_path}: {str(e)}")
            else:
                logger.warning(f"Skipping non-file path: {file_path}")

    def tokenize_project_from_url(self, project_url: str) -> None:
        """
        Fetch and tokenize a project from a URL (GitHub, GitLab, or S3)

        Args:
            project_url: URL of the project to tokenize

        Raises:
            RepositoryFetchException: If URL is not supported or fetching fails
            UnsupportedRepositoryException: If URL format is not supported
            ValidationException: If tokenization fails
        """
        if not project_url or not project_url.strip():
            raise ValidationException("Project URL cannot be empty")

        try:
            # Create a temporary submission object for fetching
            temp_submission = CreateSubmissionDto(
                link=project_url.strip(),
                project_uuid=uuid4(),  # Temporary UUID for tokenization
                group_uuid=uuid4(),  # Temporary UUID for tokenization
                project_step="tokenization",
            )

            logger.info(f"Starting tokenization for project: {project_url}")

            # Fetch submission with simplified error handling
            try:
                repo_path = self.submission_fetcher.fetch_submission(temp_submission)
                logger.info(f"Successfully fetched project for tokenization: {repo_path}")
            except (UnsupportedRepositoryException, RepositoryFetchException):
                # Re-raise repository-specific exceptions
                raise
            except SubmissionValidationException as e:
                # Convert to ValidationException for consistency
                raise ValidationException(f"Submission validation failed: {str(e)}")
            except Exception as e:
                # Handle any other unexpected errors
                logger.error(f"Unexpected error during project fetch for tokenization: {str(e)}")
                raise RepositoryFetchException(f"Unexpected error during project fetch: {str(e)}")

            # Verify the fetched project
            if not repo_path.exists():
                raise ValidationException(f"Fetched project path does not exist: {repo_path}")

            # Remove .git directory if it exists (for git repositories)
            git_dir = repo_path / ".git"
            if git_dir.exists():
                try:
                    shutil.rmtree(git_dir)
                    logger.debug(f"Removed .git directory from: {repo_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove .git directory: {str(e)}")

            # Tokenize the project
            try:
                self.tokenize_project(repo_path)
                logger.info(f"Successfully tokenized project: {project_url}")
            except Exception as e:
                logger.error(f"Failed to tokenize project {project_url}: {str(e)}")
                raise ValidationException(f"Tokenization failed: {str(e)}")

        finally:
            if "repo_path" in locals() and repo_path and repo_path.exists():
                cleanup_temp_directory(repo_path)
