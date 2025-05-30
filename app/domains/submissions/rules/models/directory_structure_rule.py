import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from app.domains.submissions.rules.models.rule import Rule


class DirectoryStructureRule(Rule):
    name = "directory_structure"

    def validate(self, submission_path: Path) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        try:
            missing_dirs = []
            forbidden_dirs = []

            required_directories = self.params.get("required_directories", [])
            forbidden_directories = self.params.get("forbidden_directories", [])
            max_depth = self.params.get("max_depth")
            allow_empty_dirs = self.params.get("allow_empty_dirs", True)

            # Validate parameter types
            if required_directories and not isinstance(required_directories, list):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "required_directories",
                    "expected_type": "array",
                    "actual_type": type(required_directories).__name__,
                    "actual_value": required_directories,
                    "message": f"Parameter 'required_directories' must be a list of directory patterns, got {type(required_directories).__name__}: {required_directories}",
                }

            if forbidden_directories and not isinstance(forbidden_directories, list):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "forbidden_directories",
                    "expected_type": "array",
                    "actual_type": type(forbidden_directories).__name__,
                    "actual_value": forbidden_directories,
                    "message": f"Parameter 'forbidden_directories' must be a list of directory patterns, got {type(forbidden_directories).__name__}: {forbidden_directories}",
                }

            if max_depth is not None and not isinstance(max_depth, int):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "max_depth",
                    "expected_type": "integer",
                    "actual_type": type(max_depth).__name__,
                    "actual_value": max_depth,
                    "message": f"Parameter 'max_depth' must be an integer, got {type(max_depth).__name__}: {max_depth}",
                }

            if max_depth is not None and max_depth < 1:
                return False, {
                    "code": "invalidParameterValue",
                    "parameter": "max_depth",
                    "value": max_depth,
                    "constraint": "must be greater than 0",
                    "message": f"Parameter 'max_depth' must be greater than 0, got: {max_depth}",
                }

            if not isinstance(allow_empty_dirs, bool):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "allow_empty_dirs",
                    "expected_type": "boolean",
                    "actual_type": type(allow_empty_dirs).__name__,
                    "actual_value": allow_empty_dirs,
                    "message": f"Parameter 'allow_empty_dirs' must be a boolean, got {type(allow_empty_dirs).__name__}: {allow_empty_dirs}",
                }

            # Require at least one validation parameter
            if not required_directories and not forbidden_directories and max_depth is None:
                return False, {
                    "code": "missingRequiredParameters",
                    "required_parameters": ["required_directories", "forbidden_directories", "max_depth"],
                    "message": "At least one validation parameter must be specified: 'required_directories', 'forbidden_directories', or 'max_depth'",
                }

            # Get all directories in the submission
            all_directories = self._get_all_directories(submission_path)

            # Check for required directories
            if required_directories:
                for pattern in required_directories:
                    if not isinstance(pattern, str):
                        return False, {
                            "code": "invalidPatternType",
                            "parameter": "required_directories",
                            "pattern": pattern,
                            "expected_type": "string",
                            "actual_type": type(pattern).__name__,
                            "message": f"All patterns in 'required_directories' must be strings, got {type(pattern).__name__}: {pattern}",
                        }

                    # Check if any directory matches the pattern
                    if not any(
                        submission_path.glob(pattern)
                        for pattern in [pattern]
                        if (submission_path / pattern).is_dir() or any(submission_path.rglob(pattern.split("/")[-1]))
                    ):
                        # More sophisticated pattern matching
                        found = False
                        for dir_path in all_directories:
                            relative_path = str(dir_path.relative_to(submission_path))
                            if self._matches_pattern(relative_path, pattern):
                                found = True
                                break
                        if not found:
                            missing_dirs.append(pattern)

            # Check for forbidden directories
            if forbidden_directories:
                for pattern in forbidden_directories:
                    if not isinstance(pattern, str):
                        return False, {
                            "code": "invalidPatternType",
                            "parameter": "forbidden_directories",
                            "pattern": pattern,
                            "expected_type": "string",
                            "actual_type": type(pattern).__name__,
                            "message": f"All patterns in 'forbidden_directories' must be strings, got {type(pattern).__name__}: {pattern}",
                        }

                    # Check if any directory matches the forbidden pattern
                    for dir_path in all_directories:
                        relative_path = str(dir_path.relative_to(submission_path))
                        if self._matches_pattern(relative_path, pattern):
                            forbidden_dirs.append(relative_path)

            # Check maximum depth
            depth_violations = []
            if max_depth is not None:
                for dir_path in all_directories:
                    relative_path = dir_path.relative_to(submission_path)
                    depth = len(relative_path.parts)
                    if depth > max_depth:
                        depth_violations.append(
                            {"directory": str(relative_path), "depth": depth, "max_allowed": max_depth}
                        )

            # Check for empty directories if not allowed
            empty_dirs = []
            if not allow_empty_dirs:
                for dir_path in all_directories:
                    if self._is_directory_empty(dir_path):
                        relative_path = str(dir_path.relative_to(submission_path))
                        empty_dirs.append(relative_path)

            # Create structured error response if there are violations
            errors = []

            if missing_dirs:
                errors.append(
                    {
                        "code": "missingRequiredDirectories",
                        "missing_directories": missing_dirs,
                        "patterns": required_directories,
                        "message": f"Missing required directories: {', '.join(missing_dirs)}",
                    }
                )

            if forbidden_dirs:
                # Remove duplicates
                unique_forbidden = list(set(forbidden_dirs))
                errors.append(
                    {
                        "code": "forbiddenDirectoriesFound",
                        "forbidden_directories": unique_forbidden,
                        "patterns": forbidden_directories,
                        "message": f"Forbidden directories found: {', '.join(unique_forbidden)}",
                    }
                )

            if depth_violations:
                errors.append(
                    {
                        "code": "directoryDepthExceeded",
                        "violations": depth_violations,
                        "max_depth": max_depth,
                        "message": f"Directory depth exceeded: {len(depth_violations)} directories exceed maximum depth of {max_depth}",
                    }
                )

            if empty_dirs:
                errors.append(
                    {
                        "code": "emptyDirectoriesFound",
                        "empty_directories": empty_dirs,
                        "message": f"Empty directories found: {', '.join(empty_dirs)}",
                    }
                )

            if errors:
                return False, {
                    "code": "directoryStructureValidationFailed",
                    "errors": errors,
                    "message": f"Directory structure validation failed with {len(errors)} error(s)",
                }
            else:
                total_dirs = len(all_directories)
                message = f"Directory structure validation passed: {total_dirs} directories checked"
                if max_depth:
                    message += f", max depth: {max_depth}"
                return True, message

        except Exception as e:
            # Catch any unexpected errors and return them in a clean format
            return False, {
                "code": "ruleExecutionError",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Rule execution error: {str(e)}",
            }

    def _get_all_directories(self, path: Path) -> List[Path]:
        """Get all directories recursively"""
        directories = []
        try:
            for item in path.rglob("*"):
                if item.is_dir():
                    directories.append(item)
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
        return directories

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a pattern (simple implementation)"""
        # Handle exact matches
        if path == pattern:
            return True

        # Handle wildcards
        if "*" in pattern:
            # Simple wildcard matching
            pattern_parts = pattern.split("*")
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                return path.startswith(prefix) and path.endswith(suffix)

        # Handle directory separator patterns
        if "/" in pattern:
            return path == pattern or path.startswith(pattern + "/") or ("/" + pattern + "/") in path

        # Handle simple name matching
        path_parts = path.split("/")
        return pattern in path_parts

    def _is_directory_empty(self, dir_path: Path) -> bool:
        """Check if a directory is empty (no files or subdirectories)"""
        try:
            return not any(dir_path.iterdir())
        except (PermissionError, OSError):
            return False


# Example usage:
# {
#     "name": "directory_structure",
#     "params": {
#       "required_directories": ["src", "tests", "docs", "src/components"],
#       "forbidden_directories": ["node_modules", "__pycache__", "*.tmp"],
#       "max_depth": 5,
#       "allow_empty_dirs": false
#     }
# }
