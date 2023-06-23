from typing import Any, Dict, Optional
from fastapi.exceptions import HTTPException
from pydantic import BaseModel


class ErrorDetails(BaseModel):
    """Base error class.

    Provides an ability to specify error details inside the message
    field as well as the error code in the code field.
    """

    message: str
    code: int


class ErrorResponse(BaseModel):
    """API error response."""

    detail: ErrorDetails


def build_http_exception_response(
    message, code, headers: Optional[Dict[str, Any]] = None
):
    """
    Build and return API error response object.

    :param message: str, error message
    :param code: int, HTTP error code
    """

    raise HTTPException(
        status_code=code, detail={"message": message, "code": code}, headers=headers
    )


class ServiceBaseError(Exception):
    """Base error class for all service-related errors."""

    def __init__(self, message: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.message = message
