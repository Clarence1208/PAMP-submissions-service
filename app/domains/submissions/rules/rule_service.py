import logging
import shutil
import tempfile
from pathlib import Path
from typing import List

from app.domains.repositories.exceptions import (
    RepositoryFetchException, UnsupportedRepositoryException,
    SubmissionValidationException, TemporaryDirectoryException
)
from app.domains.repositories.submission_fetcher import SubmissionFetcher, cleanup_temp_directory
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
        self.submission_fetcher = SubmissionFetcher()

    def validate_submission(self, submission_data: CreateSubmissionDto) -> List[RuleExecutionResult]:
        """
        Validate a submission by executing all specified rules

        Args:
            submission_data: The submission data containing rules to execute

        Returns:
            List of rule execution results

        Raises:
            ValidationException: If rules are invalid or execution fails
            RepositoryFetchException: If submission fetching fails
            UnsupportedRepositoryException: If submission URL format is not supported
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

        # Check if the submission URL is supported
        if not self.submission_fetcher.is_supported_submission(submission_data):
            supported_types = ", ".join(self.submission_fetcher.get_supported_types())
            raise UnsupportedRepositoryException(
                submission_data.link if submission_data and submission_data.link else "unknown",
                supported_types
            )

        try:
            # Fetch submission with comprehensive error handling
            try:
                repo_path = self.submission_fetcher.fetch_submission(submission_data)
                logger.info(f"Successfully fetched submission for validation: {repo_path}")
            except UnsupportedRepositoryException as e:
                logger.error(f"Unsupported repository type: {str(e)}")
                raise  # Re-raise to let caller handle
            except RepositoryFetchException as e:
                logger.error(f"Repository fetch failed: {str(e)}")
                raise  # Re-raise to let caller handle
            except SubmissionValidationException as e:
                logger.error(f"Submission validation failed: {str(e)}")
                raise ValidationException(f"Submission validation failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during submission fetch: {str(e)}")
                raise RepositoryFetchException(f"Unexpected error during submission fetch: {str(e)}")

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
                            error_details={
                                "code": "ruleExecutionError",
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "message": f"Rule execution failed: {str(e)}",
                            },
                        )
                    )

            logger.info(f"Completed validation of {len(results)} rules for submission")
            return results

        finally:
            if repo_path and repo_path.exists():
                cleanup_temp_directory(repo_path)

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
