import shutil
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import tree_sitter_python as tspython
from tree_sitter import Parser, Language

from app.shared.exceptions import ValidationException
from app.domains.detection.similarity_detection_service import SimilarityDetectionService

logger = logging.getLogger(__name__)

class TokenizationService:
    def __init__(self):
        """Initialize the tokenization service with tree-sitter parsers"""
        self.parsers = {}
        self.similarity_service = SimilarityDetectionService()
        self._setup_parsers()

    def _setup_parsers(self):
        """Set up tree-sitter parsers for different languages"""
        try:
            # Python parser - use tree-sitter 0.24.0 API
            python_language = Language(tspython.language())
            py_parser = Parser()
            py_parser.language = python_language
            self.parsers['python'] = py_parser
            self.parsers['.py'] = py_parser

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
        return '.py'

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
            self._extract_tokens(root_node, text.encode('utf8'), tokens)

            return tokens

        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            return []

    def _extract_tokens(self, node, source_code: bytes, tokens: List[Dict[str, Any]]):
        """Recursively extract tokens from the syntax tree"""
        # Add current node as token if it has meaningful content and is named
        if node.start_byte < node.end_byte and node.is_named:
            token_text = source_code[node.start_byte:node.end_byte].decode('utf8')

            token = {
                'type': node.type,
                'text': token_text,
                'start': node.start_point[0],  # Just row number
                'end': node.end_point[0]       # Just row number
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
            return ' '.join(token.get('text', '') for token in tokens if token.get('text'))

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
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    tokens = self.tokenize(content, file_path)
                    logger.debug(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(f"Tokenized {file_path}: {len(tokens)} tokens")
                    print(tokens)
                    print("\n\n\n\n")

                    # Optionally save tokens or process further
                except Exception as e:
                    logger.error(f"Failed to tokenize {file_path}: {str(e)}")
            else :
                logger.warning(f"Skipping non-file path: {file_path}")

    def _create_temp_directory(self) -> str:
        """Create a temporary directory for repository cloning"""

        temp_dir = tempfile.mkdtemp(prefix="submission_validation_")
        logger.debug(f"Created temporary directory: {temp_dir}")
        return temp_dir

    def _clone_github_repo(self, repo_url: str, temp_dir: str) -> Path:
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout

            if result.returncode != 0:
                error_msg = f"Git clone failed: {result.stderr}"
                logger.error(error_msg)
                raise ValidationException(error_msg)

            # delete .git directory to avoid unnecessary files
            git_dir = repo_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
                logger.debug(f"Removed .git directory from: {repo_path}")

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

        # Handle other formats if needed
        return url