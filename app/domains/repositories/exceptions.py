"""Repository-specific exceptions for better error handling"""

from app.shared.exceptions import ValidationException


class RepositoryFetchException(ValidationException):
    """Base exception for repository fetching operations"""
    
    def __init__(self, message: str, source_type: str = None, source_url: str = None, details: dict = None):
        super().__init__(message, details)
        self.source_type = source_type
        self.source_url = source_url


class UnsupportedRepositoryException(RepositoryFetchException):
    """Raised when repository URL format is not supported"""
    
    def __init__(self, url: str, supported_types: list = None):
        supported_msg = f"Supported types: {', '.join(supported_types)}" if supported_types else ""
        message = f"Unsupported repository URL format: {url}. {supported_msg}"
        super().__init__(message, source_url=url, details={
            "error_type": "unsupported_repository",
            "url": url,
            "supported_types": supported_types or []
        })


class GitRepositoryException(RepositoryFetchException):
    """Base exception for Git repository operations"""
    
    def __init__(self, message: str, source_type: str, source_url: str, git_error: str = None, details: dict = None):
        super().__init__(message, source_type, source_url, details)
        self.git_error = git_error


class GitCloneException(GitRepositoryException):
    """Raised when git clone operation fails"""
    
    def __init__(self, url: str, source_type: str, git_error: str, return_code: int = None):
        message = f"Failed to clone {source_type} repository: {url}"
        if git_error:
            message += f". Git error: {git_error}"
        
        super().__init__(message, source_type, url, git_error, details={
            "error_type": "git_clone_failed",
            "source_type": source_type,
            "url": url,
            "git_error": git_error,
            "return_code": return_code
        })


class GitTimeoutException(GitRepositoryException):
    """Raised when git operations timeout"""
    
    def __init__(self, url: str, source_type: str, timeout_seconds: int = 300):
        message = f"{source_type} repository cloning timed out after {timeout_seconds} seconds: {url}"
        super().__init__(message, source_type, url, details={
            "error_type": "git_timeout",
            "source_type": source_type,
            "url": url,
            "timeout_seconds": timeout_seconds
        })


class S3FetchException(RepositoryFetchException):
    """Base exception for S3 operations"""
    
    def __init__(self, message: str, s3_url: str, bucket: str = None, key: str = None, details: dict = None):
        super().__init__(message, "s3", s3_url, details)
        self.bucket = bucket
        self.key = key


class S3ConfigurationException(S3FetchException):
    """Raised when S3 configuration is invalid"""
    
    def __init__(self, message: str, s3_url: str = None):
        super().__init__(message, s3_url or "unknown", details={
            "error_type": "s3_configuration_error",
            "message": message
        })


class S3CredentialsException(S3FetchException):
    """Raised when S3 credentials are missing or invalid"""
    
    def __init__(self, s3_url: str):
        message = f"AWS credentials not found or invalid for S3 access: {s3_url}"
        super().__init__(message, s3_url, details={
            "error_type": "s3_credentials_error",
            "url": s3_url,
            "message": "Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        })


class S3BucketException(S3FetchException):
    """Raised when S3 bucket operations fail"""
    
    def __init__(self, bucket: str, s3_url: str, error_code: str = None):
        if error_code == "NoSuchBucket":
            message = f"S3 bucket '{bucket}' does not exist"
        elif error_code == "AccessDenied":
            message = f"Access denied to S3 bucket '{bucket}'"
        else:
            message = f"S3 bucket error for '{bucket}': {error_code or 'Unknown error'}"
            
        super().__init__(message, s3_url, bucket, details={
            "error_type": "s3_bucket_error",
            "bucket": bucket,
            "error_code": error_code,
            "url": s3_url
        })


class S3ObjectException(S3FetchException):
    """Raised when S3 object operations fail"""
    
    def __init__(self, bucket: str, key: str, s3_url: str, error_code: str = None):
        if error_code == "NoSuchKey":
            message = f"S3 object '{key}' does not exist in bucket '{bucket}'"
        elif error_code == "AccessDenied":
            message = f"Access denied to S3 object '{key}' in bucket '{bucket}'"
        else:
            message = f"S3 object error for '{key}' in bucket '{bucket}': {error_code or 'Unknown error'}"
            
        super().__init__(message, s3_url, bucket, key, details={
            "error_type": "s3_object_error",
            "bucket": bucket,
            "key": key,
            "error_code": error_code,
            "url": s3_url
        })


class S3ExtractionException(S3FetchException):
    """Raised when S3 content extraction fails"""
    
    def __init__(self, s3_url: str, extraction_error: str, bucket: str = None, key: str = None):
        message = f"Failed to extract S3 content from {s3_url}: {extraction_error}"
        super().__init__(message, s3_url, bucket, key, details={
            "error_type": "s3_extraction_error",
            "url": s3_url,
            "extraction_error": extraction_error,
            "bucket": bucket,
            "key": key
        })


class SubmissionValidationException(ValidationException):
    """Raised when submission validation fails"""
    
    def __init__(self, message: str, submission_id: str = None, validation_errors: list = None):
        super().__init__(message, details={
            "error_type": "submission_validation_error",
            "submission_id": submission_id,
            "validation_errors": validation_errors or []
        })
        self.submission_id = submission_id
        self.validation_errors = validation_errors or []


class TemporaryDirectoryException(ValidationException):
    """Raised when temporary directory operations fail"""
    
    def __init__(self, operation: str, error: str, path: str = None):
        message = f"Temporary directory {operation} failed: {error}"
        super().__init__(message, details={
            "error_type": "temporary_directory_error",
            "operation": operation,
            "error": error,
            "path": path
        }) 