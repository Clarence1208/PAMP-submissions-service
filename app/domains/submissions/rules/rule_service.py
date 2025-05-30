import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from app.domains.submissions.dto.create_submission_dto import CreateSubmissionDto
from app.domains.submissions.dto.rule_dto import RuleDto
from app.domains.submissions.rules.rule_registry import rule_registry
from app.shared.exceptions import ValidationException

logger = logging.getLogger(__name__)


class RuleExecutionResult:
    """Result of rule execution"""

    def __init__(self, rule_name: str, passed: bool, message: str, params: dict = None, error_details: dict = None):
        self.rule_name = rule_name
        self.passed = passed
        self.message = message
        self.params = params or {}
        self.error_details = error_details  # Structured error data

    def to_dict(self):
        """Convert result to dictionary format"""
        result = {"rule_name": self.rule_name, "passed": self.passed, "message": self.message, "params": self.params}

        if self.error_details:
            result["error_details"] = self.error_details

        return result


class RuleService:
    """Service for executing validation rules on submissions"""

    def __init__(self):
        self.registry = rule_registry

    def validate_submission(self, submission_data: CreateSubmissionDto) -> List[RuleExecutionResult]:
        """
        Validate a submission by executing all specified rules

        Args:
            submission_data: The submission data containing rules to execute

        Returns:
            List of rule execution results

        Raises:
            ValidationException: If rules are invalid or execution fails
        """
        if not submission_data.rules:
            logger.info("No rules specified for submission validation")
            return []

        # Convert RuleDto objects to dict format for validation
        rule_data_list = [{"name": rule.name, "params": rule.params} for rule in submission_data.rules]

        # Assert all rules exist
        missing_rules = self.registry.validate_rules(rule_data_list)
        if missing_rules:
            raise ValidationException(
                f"Unknown rules specified: {missing_rules}. " f"Available rules: {self.registry.get_rule_names()}"
            )

        # Only handle GitHub repositories for now
        if not self._is_github_repo(submission_data.link):
            raise ValidationException("Rule validation currently only supports GitHub repositories")

        # Create temporary directory and clone repository
        temp_dir = None
        try:
            temp_dir = self._create_temp_directory()
            repo_path = self._clone_github_repo(submission_data.link, temp_dir)

            # Execute all rules
            results = []
            for rule_dto in submission_data.rules:
                try:
                    result = self._execute_rule(rule_dto, repo_path)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to execute rule '{rule_dto.name}': {str(e)}")
                    results.append(
                        RuleExecutionResult(
                            rule_name=rule_dto.name,
                            passed=False,
                            message=f"Rule execution failed: {str(e)}",
                            params=rule_dto.params,
                        )
                    )

            return results

        finally:
            # Clean up temporary directory
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")

    def _is_github_repo(self, link: str) -> bool:
        """Check if the link is a GitHub repository"""
        return "github.com" in link.lower()

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

    def _execute_rule(self, rule_dto: RuleDto, repo_path: Path) -> RuleExecutionResult:
        """
        Execute a single rule on the repository

        Args:
            rule_dto: Rule to execute
            repo_path: Path to the cloned repository

        Returns:
            Rule execution result with structured error details
        """
        try:
            # Create rule instance
            rule = self.registry.create_rule(rule_dto.name, rule_dto.params)

            # Execute rule validation
            validation_result = rule.validate(repo_path)

            # Ensure we got a proper tuple result
            if not isinstance(validation_result, tuple) or len(validation_result) != 2:
                logger.error(f"Rule '{rule_dto.name}' returned invalid result format: {validation_result}")
                return RuleExecutionResult(
                    rule_name=rule_dto.name,
                    passed=False,
                    message=f"Rule implementation error: expected (bool, str/dict) tuple, got {type(validation_result).__name__}",
                    params=rule_dto.params,
                    error_details={
                        "code": "ruleImplementationError",
                        "error_type": "invalid_return_format",
                        "expected": "(bool, str/dict)",
                        "actual": str(type(validation_result).__name__),
                        "message": f"Rule implementation error: expected (bool, str/dict) tuple, got {type(validation_result).__name__}",
                    },
                )

            passed, result_data = validation_result

            # Validate result types
            if not isinstance(passed, bool):
                logger.error(f"Rule '{rule_dto.name}' returned non-boolean passed value: {passed}")
                return RuleExecutionResult(
                    rule_name=rule_dto.name,
                    passed=False,
                    message=f"Rule implementation error: expected boolean for passed, got {type(passed).__name__}: {passed}",
                    params=rule_dto.params,
                    error_details={
                        "code": "ruleImplementationError",
                        "error_type": "invalid_passed_type",
                        "expected": "bool",
                        "actual": type(passed).__name__,
                        "value": passed,
                        "message": f"Rule implementation error: expected boolean for passed, got {type(passed).__name__}: {passed}",
                    },
                )

            # Handle structured error data (dict) vs simple message (str)
            if isinstance(result_data, dict):
                # Structured error data
                message = result_data.get("message", "No message provided")
                error_details = result_data if not passed else None
            elif isinstance(result_data, str):
                # Simple string message
                message = result_data
                error_details = None
            else:
                # Convert to string as fallback
                logger.warning(f"Rule '{rule_dto.name}' returned unexpected message type: {type(result_data)}")
                message = str(result_data)
                error_details = None

            logger.debug(f"Rule '{rule_dto.name}' result: passed={passed}, message='{message}'")

            return RuleExecutionResult(
                rule_name=rule_dto.name,
                passed=passed,
                message=message,
                params=rule_dto.params,
                error_details=error_details,
            )

        except ValueError as e:
            # Handle rule creation or parameter validation errors
            logger.error(f"Parameter validation error for rule '{rule_dto.name}': {str(e)}")
            return RuleExecutionResult(
                rule_name=rule_dto.name,
                passed=False,
                message=f"Parameter validation error: {str(e)}",
                params=rule_dto.params,
                error_details={
                    "code": "parameterValidationError",
                    "error_type": "ValueError",
                    "error_message": str(e),
                    "message": f"Parameter validation error: {str(e)}",
                },
            )
        except Exception as e:
            # Handle any other unexpected errors
            logger.error(f"Unexpected error executing rule '{rule_dto.name}': {str(e)}")
            return RuleExecutionResult(
                rule_name=rule_dto.name,
                passed=False,
                message=f"Unexpected rule execution error: {str(e)}",
                params=rule_dto.params,
                error_details={
                    "code": "unexpectedRuleError",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "message": f"Unexpected rule execution error: {str(e)}",
                },
            )

    def get_available_rules(self) -> List[str]:
        """Get list of available rule names"""
        return self.registry.get_rule_names()

    def validate_rule_names(self, rule_names: List[str]) -> List[str]:
        """Validate rule names and return any that don't exist"""
        return [name for name in rule_names if not self.registry.rule_exists(name)]
