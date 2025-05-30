from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """Raised when a resource is not found"""

    def __init__(self, resource: str, identifier: str = None):
        detail = f"{resource} not found"
        if identifier:
            detail += f" with identifier: {identifier}"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationException(HTTPException):
    """Raised when validation fails"""

    def __init__(self, detail: str, details: Optional[Dict[str, Any]] = None):
        if details:
            # Put structured details directly in the detail field
            super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=details)
        else:
            super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class DatabaseException(HTTPException):
    """Raised when database operation fails"""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
