from pathlib import Path
from typing import Union, Dict, Any, Tuple

from app.domains.submissions.rules.models.rule import Rule


class FilePresenceRule(Rule):
    name = "file_presence"

    def validate(self, submission_path: Path) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        try:
            missing = []
            forbidden = []

            must_exist_patterns = self.params.get("must_exist", [])
            forbidden_patterns = self.params.get("forbidden", [])

            # Validate parameter types
            if must_exist_patterns and not isinstance(must_exist_patterns, list):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "must_exist",
                    "expected_type": "array",
                    "actual_type": type(must_exist_patterns).__name__,
                    "actual_value": must_exist_patterns,
                    "message": f"Parameter 'must_exist' must be a list of patterns, got {type(must_exist_patterns).__name__}: {must_exist_patterns}"
                }

            if forbidden_patterns and not isinstance(forbidden_patterns, list):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "forbidden",
                    "expected_type": "array",
                    "actual_type": type(forbidden_patterns).__name__,
                    "actual_value": forbidden_patterns,
                    "message": f"Parameter 'forbidden' must be a list of patterns, got {type(forbidden_patterns).__name__}: {forbidden_patterns}"
                }

            # assert there is at least one pattern for must_exist or forbidden
            if not must_exist_patterns and not forbidden_patterns:
                return False, {
                    "code": "missingRequiredParameters",
                    "required_parameters": ["must_exist", "forbidden"],
                    "message": "At least one 'must_exist' or 'forbidden' pattern must be specified"
                }

            # Check for required files
            if must_exist_patterns:
                for pattern in must_exist_patterns:
                    if not isinstance(pattern, str):
                        return False, {
                            "code": "invalidPatternType",
                            "parameter": "must_exist",
                            "pattern": pattern,
                            "expected_type": "string",
                            "actual_type": type(pattern).__name__,
                            "message": f"All patterns in 'must_exist' must be strings, got {type(pattern).__name__}: {pattern}"
                        }
                    if not any(submission_path.glob(pattern)):
                        missing.append(pattern)

            # Check for forbidden files
            if forbidden_patterns:
                for pattern in forbidden_patterns:
                    if not isinstance(pattern, str):
                        return False, {
                            "code": "invalidPatternType",
                            "parameter": "forbidden",
                            "pattern": pattern,
                            "expected_type": "string",
                            "actual_type": type(pattern).__name__,
                            "message": f"All patterns in 'forbidden' must be strings, got {type(pattern).__name__}: {pattern}"
                        }
                    if any(submission_path.glob(pattern)):
                        forbidden.append(pattern)

            # Create structured error response if there are violations
            errors = []

            if missing:
                errors.append({
                    "code": "missingRequiredFiles",
                    "missing_files": missing,
                    "patterns": must_exist_patterns,
                    "message": f"Missing required files: {', '.join(missing)}"
                })

            if forbidden:
                errors.append({
                    "code": "forbiddenFilesFound",
                    "forbidden_files": forbidden,
                    "patterns": forbidden_patterns,
                    "message": f"Forbidden files found: {', '.join(forbidden)}"
                })

            if errors:
                return False, {
                    "code": "fileValidationFailed",
                    "errors": errors,
                    "message": f"File validation failed with {len(errors)} error(s)"
                }
            else:
                return True, "All required files are present and no forbidden files found"

        except Exception as e:
            # Catch any unexpected errors and return them in a clean format
            return False, {
                "code": "ruleExecutionError",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Rule execution error: {str(e)}"
            }
