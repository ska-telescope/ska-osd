import logging
from http import HTTPStatus
from typing import Any, Dict, List

from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from ska_ost_osd.common.utils import convert_to_response_object
from ska_ost_osd.telvalidation.common.schematic_validation_exceptions import (
    SchematicValidationError,
)

LOGGER = logging.getLogger(__name__)


class OSDModelError(Exception):
    """Custom exception class for validation errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class CapabilityError(Exception):
    """Custom exception class for validation errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class ValidationErrorFormatter:
    @staticmethod
    def format(exc: RequestValidationError) -> Dict[str, Any]:
        missing_fields = []
        payload_str = ""
        if isinstance(exc, Exception):
            return str(exc)
        for err in exc.errors():
            if err.get("type") == "missing":
                missing_fields.append(err["loc"][-1])
            payload_str = err["input"]

        parts = []
        if missing_fields:
            parts.append(f"Missing field(s): {', '.join(missing_fields)}")

        return ". ".join(parts) + f", invalid payload: {payload_str}"


async def internal_server_error_handler(
    _: Request, err: Exception, status=HTTPStatus.INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """A custom handler function that returns a verbose HTTP 500 response
    containing detailed traceback information."""

    formatted = ValidationErrorFormatter.format(err)

    result = convert_to_response_object(
        formatted,
        result_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status,
    )


async def response_validation_error_handler(
    _: Request, err: ResponseValidationError, status=HTTPStatus.INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """A custom handler function that returns a verbose HTTP 500 response
    containing detailed traceback information."""

    formatted = ValidationErrorFormatter.format(err)

    result = convert_to_response_object(
        formatted,
        result_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status,
    )


async def schematic_validation_error_handler(
    _: Request, err: SchematicValidationError
) -> JSONResponse:
    """A custom handler function to deal with SchematicValidationError raised
    while schema validation return the correct HTTP response."""

    LOGGER.exception("Semantic Validation Error")

    result = convert_to_response_object(err.message, result_code=HTTPStatus.OK)

    return JSONResponse(content=result.model_dump(), status_code=HTTPStatus.OK)


async def file_not_found_error_handler(
    _: Request, err: FileNotFoundError
) -> JSONResponse:
    """A custom handler function to deal with SchematicValidationError raised
    while schema validation return the correct HTTP response."""

    LOGGER.exception("File Not Found error")

    formatted = ValidationErrorFormatter.format(err)

    result = convert_to_response_object(
        formatted,
        result_code=HTTPStatus.NOT_FOUND,
    )

    return JSONResponse(content=result.model_dump(), status_code=HTTPStatus.NOT_FOUND)
