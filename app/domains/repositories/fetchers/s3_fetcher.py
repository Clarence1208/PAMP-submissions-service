import logging
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None

from app.config.config import get_settings
from app.domains.repositories.exceptions import (
    S3BucketException,
    S3ConfigurationException,
    S3CredentialsException,
    S3ExtractionException,
    S3FetchException,
    S3ObjectException,
)

logger = logging.getLogger(__name__)


class S3Fetcher:
    """Fetcher for downloading and extracting files from S3"""

    def __init__(self):
        """
        Initialize S3 fetcher with credentials from config
        """
        if boto3 is None:
            raise S3ConfigurationException("boto3 is required for S3 fetcher. Install with: pip install boto3")

        try:
            # Get AWS credentials from configuration
            settings = get_settings()
            self.aws_access_key_id = settings.aws_access_key_id
            self.aws_secret_access_key = settings.aws_secret_access_key
            self.aws_default_region = settings.aws_default_region

            logger.debug(f"S3Fetcher initialized successfully with region: {self.aws_default_region}")
        except Exception as e:
            logger.error(f"Failed to initialize S3Fetcher: {str(e)}")
            raise S3ConfigurationException(f"Failed to load S3 configuration: {str(e)}")

    def fetch_s3_content(self, s3_url: str, temp_dir: str) -> Path:
        """
        Download and extract content from S3 URL

        Args:
            s3_url: S3 URL (e.g., s3://bucket-name/path/to/file.zip)
            temp_dir: Temporary directory path

        Returns:
            Path to the extracted content

        Raises:
            S3FetchException: If download/extraction fails
        """
        temp_file_path = None
        extract_path = None

        try:
            bucket_name, object_key = self._parse_s3_url(s3_url)
            logger.info(f"Starting S3 fetch for bucket '{bucket_name}', key '{object_key}'")

            # Initialize S3 client
            s3_client = self._get_s3_client(s3_url)

            # Create a temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
                temp_file_path = temp_file.name

                logger.info(f"Downloading from S3: {s3_url}")

                # Download file from S3
                try:
                    s3_client.download_file(bucket_name, object_key, temp_file_path)
                    logger.debug(f"Download completed: {temp_file_path}")
                except ClientError as e:
                    self._handle_s3_client_error(e, bucket_name, object_key, s3_url)

                # Verify download
                if not Path(temp_file_path).exists() or Path(temp_file_path).stat().st_size == 0:
                    raise S3ObjectException(bucket_name, object_key, s3_url, "Downloaded file is empty or missing")

                # Extract the content
                extract_path = Path(temp_dir) / self._get_extract_folder_name(object_key)
                try:
                    extract_path.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Created extraction directory: {extract_path}")
                except OSError as e:
                    raise S3ExtractionException(
                        s3_url, f"Failed to create extraction directory: {str(e)}", bucket_name, object_key
                    )

                # Check if it's a zip file and extract
                try:
                    if self._is_zip_file(temp_file_path):
                        self._extract_zip(temp_file_path, extract_path)
                        logger.debug(f"Extracted ZIP file to: {extract_path}")
                        
                        # Check if we need to use a nested directory as the project root
                        project_root = self._get_project_root_path(extract_path)
                        if project_root != extract_path:
                            logger.info(f"Using nested directory as project root: {project_root}")
                            extract_path = project_root
                    else:
                        # If not a zip, just copy the file
                        target_file = extract_path / Path(object_key).name
                        target_file.write_bytes(Path(temp_file_path).read_bytes())
                        logger.debug(f"Copied file to: {target_file}")
                except Exception as e:
                    raise S3ExtractionException(s3_url, str(e), bucket_name, object_key)

                logger.info(f"Successfully downloaded and extracted S3 content to: {extract_path}")
                return extract_path

        except NoCredentialsError as e:
            logger.error(f"AWS credentials error for {s3_url}: {str(e)}")
            raise S3CredentialsException(s3_url)
        except (S3FetchException, S3ConfigurationException, S3CredentialsException):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching S3 content from {s3_url}: {str(e)}")
            # Clean up on unexpected errors
            if extract_path and extract_path.exists():
                try:
                    import shutil

                    shutil.rmtree(extract_path, ignore_errors=True)
                    logger.debug(f"Cleaned up partial extraction: {extract_path}")
                except Exception:
                    pass
            raise S3FetchException(f"Unexpected error fetching S3 content: {str(e)}", s3_url)
        finally:
            # Clean up temporary file
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {str(e)}")

    def _parse_s3_url(self, s3_url: str) -> tuple[str, str]:
        """Parse S3 URL into bucket and object key"""
        try:
            if not s3_url.startswith("s3://"):
                raise S3ConfigurationException(
                    "Invalid S3 URL format. Expected format: s3://bucket-name/path/to/file", s3_url
                )

            parsed = urlparse(s3_url)
            bucket_name = parsed.netloc
            object_key = parsed.path.lstrip("/")

            if not bucket_name:
                raise S3ConfigurationException("S3 URL must include bucket name", s3_url)
            if not object_key:
                raise S3ConfigurationException("S3 URL must include object key", s3_url)

            return bucket_name, object_key
        except Exception as e:
            if isinstance(e, S3ConfigurationException):
                raise
            raise S3ConfigurationException(f"Failed to parse S3 URL: {str(e)}", s3_url)

    def _get_s3_client(self, s3_url: str = None):
        """Get configured S3 client"""
        try:
            # Use region from config
            region = getattr(self, "aws_default_region", "us-east-1")

            if self.aws_access_key_id and self.aws_secret_access_key:
                client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=region,
                )
                logger.debug(f"Using configured AWS credentials with region: {region}")
            else:
                # Use default credentials (environment variables, IAM role, etc.)
                client = boto3.client("s3", region_name=region)
                logger.debug(f"Using default AWS credentials with region: {region}")
            return client
        except NoCredentialsError:
            raise S3CredentialsException(s3_url or "unknown")
        except Exception as e:
            logger.error(f"Failed to create S3 client: {str(e)}")
            raise S3ConfigurationException(f"Failed to create S3 client: {str(e)}", s3_url)

    def _handle_s3_client_error(self, error: ClientError, bucket: str, key: str, s3_url: str):
        """Handle S3 client errors and raise appropriate exceptions"""
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        logger.error(f"S3 ClientError ({error_code}) for {s3_url}: {str(error)}")

        if error_code in ["NoSuchBucket", "InvalidBucketName"]:
            raise S3BucketException(bucket, s3_url, error_code)
        elif error_code in ["NoSuchKey", "InvalidObjectName"]:
            raise S3ObjectException(bucket, key, s3_url, error_code)
        elif error_code == "AccessDenied":
            # Could be bucket or object level
            if key:
                raise S3ObjectException(bucket, key, s3_url, error_code)
            else:
                raise S3BucketException(bucket, s3_url, error_code)
        else:
            # Generic S3 error
            raise S3FetchException(f"S3 error ({error_code}): {str(error)}", s3_url, bucket, key)

    def _get_extract_folder_name(self, object_key: str) -> str:
        """Get folder name for extracted content"""
        # Use the object key's filename without extension
        filename = Path(object_key).stem
        return filename if filename else "extracted_content"

    def _is_zip_file(self, file_path: str) -> bool:
        """Check if file is a ZIP file"""
        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                return True
        except zipfile.BadZipFile:
            return False

    def _extract_zip(self, zip_path: str, extract_path: Path):
        """Extract ZIP file to specified path"""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Validate ZIP file structure
                zip_ref.testzip()

                # Extract all contents
                zip_ref.extractall(extract_path)

                # Verify extraction
                extracted_files = list(extract_path.rglob("*"))
                if not extracted_files:
                    raise Exception("No files were extracted from ZIP")

                logger.debug(f"Extracted {len(extracted_files)} items from ZIP to: {extract_path}")

        except zipfile.BadZipFile as e:
            logger.error(f"Invalid ZIP file {zip_path}: {str(e)}")
            raise Exception(f"Invalid ZIP file: {str(e)}")
        except zipfile.LargeZipFile as e:
            logger.error(f"ZIP file too large {zip_path}: {str(e)}")
            raise Exception(f"ZIP file too large: {str(e)}")
        except PermissionError as e:
            logger.error(f"Permission denied extracting {zip_path}: {str(e)}")
            raise Exception(f"Permission denied during extraction: {str(e)}")
        except OSError as e:
            logger.error(f"OS error extracting {zip_path}: {str(e)}")
            raise Exception(f"File system error during extraction: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to extract ZIP file {zip_path}: {str(e)}")
            raise Exception(f"Failed to extract ZIP file: {str(e)}")

    def _get_project_root_path(self, extract_path: Path) -> Path:
        """
        Get the actual project root path, handling nested directory structures.
        
        If there's a single subdirectory, use that as the project root instead
        of the extraction directory.
        
        Args:
            extract_path: Path to the extracted content directory
            
        Returns:
            Path to use as the project root
        """
        try:
            # Get all items in the extraction directory (exclude hidden files)
            items = [item for item in extract_path.iterdir() if not item.name.startswith('.')]
            
            # If there's exactly one item and it's a directory, use it as the project root
            if len(items) == 1 and items[0].is_dir():
                nested_dir = items[0]
                logger.debug(f"Found single nested directory, using as project root: {nested_dir}")
                return nested_dir
            else:
                logger.debug(f"Using extraction directory as project root: {extract_path} (contains {len(items)} items)")
                return extract_path
                
        except Exception as e:
            # If anything goes wrong, fall back to the extraction path
            logger.warning(f"Error determining project root path in {extract_path}: {e}")
            return extract_path
