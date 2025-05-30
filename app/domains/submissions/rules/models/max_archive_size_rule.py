import logging
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Union

from app.domains.submissions.rules.models.rule import Rule


class MaxArchiveSizeRule(Rule):
    name = "max_archive_size"

    def validate(self, submission_path: Path) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        """Validate that the repository size doesn't exceed the maximum allowed size"""
        try:
            max_size_mb = self.params.get("max_size_mb", 100)  # Default 100MB

            # Validate parameter type
            if not isinstance(max_size_mb, (int, float)):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "max_size_mb",
                    "expected_type": "number",
                    "actual_type": type(max_size_mb).__name__,
                    "actual_value": max_size_mb,
                    "message": f"Parameter 'max_size_mb' must be a number, got {type(max_size_mb).__name__}: {max_size_mb}",
                }

            if max_size_mb <= 0:
                return False, {
                    "code": "invalidParameterValue",
                    "parameter": "max_size_mb",
                    "value": max_size_mb,
                    "constraint": "must be greater than 0",
                    "message": f"Parameter 'max_size_mb' must be greater than 0, got: {max_size_mb}",
                }

            # Calculate total size of all files in the directory
            total_size_bytes = 0
            file_count = 0
            for dirpath, dirnames, filenames in os.walk(submission_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size_bytes += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        # Skip files that can't be accessed
                        continue

            total_size_mb = total_size_bytes / (1024 * 1024)

            if total_size_mb <= max_size_mb:
                return True, f"Repository size {total_size_mb:.2f}MB is within limit of {max_size_mb}MB"
            else:
                return False, {
                    "code": "repositorySizeExceeded",
                    "actual_size_mb": round(total_size_mb, 2),
                    "actual_size_bytes": total_size_bytes,
                    "max_size_mb": max_size_mb,
                    "file_count": file_count,
                    "excess_mb": round(total_size_mb - max_size_mb, 2),
                    "message": f"Repository size {total_size_mb:.2f}MB exceeds maximum allowed size of {max_size_mb}MB",
                }

        except Exception as e:
            logging.error(f"Error calculating repository size: {str(e)}")
            return False, {
                "code": "ruleExecutionError",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Failed to validate repository size: {str(e)}",
            }
