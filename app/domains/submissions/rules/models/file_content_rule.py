import re
from pathlib import Path
from typing import Union, Dict, Any, Tuple, List

from app.domains.submissions.rules.models.rule import Rule


class FileContentRule(Rule):
    name = "file_content"

    def validate(self, submission_path: Path) -> Tuple[bool, Union[str, Dict[str, Any]]]:
        try:
            # Get parameters
            checks = self.params.get("checks", [])
            
            # Validate parameter types
            if not isinstance(checks, list):
                return False, {
                    "code": "invalidParameterType",
                    "parameter": "checks",
                    "expected_type": "array",
                    "actual_type": type(checks).__name__,
                    "actual_value": checks,
                    "message": f"Parameter 'checks' must be a list of file content checks, got {type(checks).__name__}: {checks}"
                }
            
            if not checks:
                return False, {
                    "code": "missingRequiredParameters",
                    "required_parameters": ["checks"],
                    "message": "At least one file content check must be specified in 'checks' array"
                }
            
            # Validate each check
            errors = []
            for i, check in enumerate(checks):
                if not isinstance(check, dict):
                    return False, {
                        "code": "invalidCheckType",
                        "check_index": i,
                        "expected_type": "object",
                        "actual_type": type(check).__name__,
                        "actual_value": check,
                        "message": f"Each check must be an object, got {type(check).__name__} at index {i}: {check}"
                    }
                
                # Validate required fields
                file_pattern = check.get("file_pattern")
                if not file_pattern:
                    return False, {
                        "code": "missingFilePattern",
                        "check_index": i,
                        "check": check,
                        "message": f"Each check must specify a 'file_pattern' field at index {i}"
                    }
                
                if not isinstance(file_pattern, str):
                    return False, {
                        "code": "invalidFilePattern",
                        "check_index": i,
                        "file_pattern": file_pattern,
                        "expected_type": "string",
                        "actual_type": type(file_pattern).__name__,
                        "message": f"'file_pattern' must be a string, got {type(file_pattern).__name__} at index {i}: {file_pattern}"
                    }
                
                # Must have either text or regex, but not both
                has_text = "text" in check
                has_regex = "regex" in check
                
                if not has_text and not has_regex:
                    return False, {
                        "code": "missingContentCheck",
                        "check_index": i,
                        "check": check,
                        "required_fields": ["text", "regex"],
                        "message": f"Each check must specify either 'text' or 'regex' field at index {i}"
                    }
                
                if has_text and has_regex:
                    return False, {
                        "code": "conflictingContentChecks",
                        "check_index": i,
                        "check": check,
                        "message": f"Each check must specify either 'text' OR 'regex', not both, at index {i}"
                    }
                
                # Validate text content
                if has_text:
                    text = check.get("text")
                    if not isinstance(text, str):
                        return False, {
                            "code": "invalidTextType",
                            "check_index": i,
                            "text": text,
                            "expected_type": "string",
                            "actual_type": type(text).__name__,
                            "message": f"'text' must be a string, got {type(text).__name__} at index {i}: {text}"
                        }
                
                # Validate regex content
                if has_regex:
                    regex = check.get("regex")
                    if not isinstance(regex, str):
                        return False, {
                            "code": "invalidRegexType",
                            "check_index": i,
                            "regex": regex,
                            "expected_type": "string",
                            "actual_type": type(regex).__name__,
                            "message": f"'regex' must be a string, got {type(regex).__name__} at index {i}: {regex}"
                        }
                    
                    # Test if regex is valid
                    try:
                        re.compile(regex)
                    except re.error as e:
                        return False, {
                            "code": "invalidRegexPattern",
                            "check_index": i,
                            "regex": regex,
                            "regex_error": str(e),
                            "message": f"Invalid regex pattern at index {i}: {regex} - {str(e)}"
                        }
                
                # Perform the actual validation for this check
                check_result = self._validate_single_check(submission_path, check, i)
                if not check_result[0]:
                    errors.append(check_result[1])
            
            # Return results
            if errors:
                return False, {
                    "code": "fileContentValidationFailed",
                    "errors": errors,
                    "message": f"File content validation failed with {len(errors)} error(s)"
                }
            else:
                return True, f"All {len(checks)} file content checks passed successfully"
                
        except Exception as e:
            # Catch any unexpected errors and return them in a clean format
            return False, {
                "code": "ruleExecutionError",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": f"Rule execution error: {str(e)}"
            }

    def _validate_single_check(self, submission_path: Path, check: dict, check_index: int) -> Tuple[bool, Dict[str, Any]]:
        """Validate a single file content check"""
        file_pattern = check["file_pattern"]
        
        # Find matching files
        matching_files = list(submission_path.glob(file_pattern))
        
        if not matching_files:
            return False, {
                "code": "noMatchingFiles",
                "check_index": check_index,
                "file_pattern": file_pattern,
                "message": f"No files found matching pattern '{file_pattern}' for check {check_index}"
            }
        
        # Check content in each matching file
        failed_files = []
        
        for file_path in matching_files:
            # Skip directories
            if file_path.is_dir():
                continue
                
            try:
                # Try to read file as text with common encodings
                content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    failed_files.append({
                        "file": str(file_path.relative_to(submission_path)),
                        "reason": "Unable to decode file as text with any common encoding"
                    })
                    continue
                
                # Perform content check
                check_passed = False
                
                if "text" in check:
                    text_to_find = check["text"]
                    case_sensitive = check.get("case_sensitive", True)
                    
                    if case_sensitive:
                        check_passed = text_to_find in content
                    else:
                        check_passed = text_to_find.lower() in content.lower()
                        
                    if not check_passed:
                        failed_files.append({
                            "file": str(file_path.relative_to(submission_path)),
                            "reason": f"Text '{text_to_find}' not found in file",
                            "case_sensitive": case_sensitive
                        })
                
                elif "regex" in check:
                    regex_pattern = check["regex"]
                    regex_flags = 0
                    
                    # Support regex flags
                    if not check.get("case_sensitive", True):
                        regex_flags |= re.IGNORECASE
                    if check.get("multiline", False):
                        regex_flags |= re.MULTILINE
                    if check.get("dotall", False):
                        regex_flags |= re.DOTALL
                    
                    try:
                        compiled_regex = re.compile(regex_pattern, regex_flags)
                        check_passed = bool(compiled_regex.search(content))
                        
                        if not check_passed:
                            failed_files.append({
                                "file": str(file_path.relative_to(submission_path)),
                                "reason": f"Regex pattern '{regex_pattern}' did not match any content in file",
                                "regex_flags": regex_flags
                            })
                    except re.error as e:
                        failed_files.append({
                            "file": str(file_path.relative_to(submission_path)),
                            "reason": f"Regex execution error: {str(e)}",
                            "regex_pattern": regex_pattern
                        })
                        
            except Exception as e:
                failed_files.append({
                    "file": str(file_path.relative_to(submission_path)),
                    "reason": f"File reading error: {str(e)}"
                })
        
        if failed_files:
            return False, {
                "code": "contentCheckFailed",
                "check_index": check_index,
                "file_pattern": file_pattern,
                "check_type": "text" if "text" in check else "regex",
                "check_value": check.get("text") or check.get("regex"),
                "total_files_checked": len(matching_files),
                "failed_files": failed_files,
                "message": f"Content check failed for {len(failed_files)} out of {len(matching_files)} files matching pattern '{file_pattern}'"
            }
        
        return True, {
            "check_index": check_index,
            "file_pattern": file_pattern,
            "files_checked": len(matching_files),
            "message": f"Content check passed for all {len(matching_files)} files matching pattern '{file_pattern}'"
        } 