import logging
from http import HTTPStatus
from typing import Any, Dict, List

from fastapi import Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from ska_ost_osd.common.utils import convert_to_response_object

LOGGER = logging.getLogger(__name__)


class BaseOSDError(Exception):
    """Base exception class for OSD errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class OSDModelError(BaseOSDError):
    """Exception raised for model validation errors."""


class CapabilityError(BaseOSDError):
    """Exception raised for capability-related errors."""


class ValidationErrorFormatter:
    @staticmethod
    def format(exc: RequestValidationError) -> Dict[str, Any]:
        missing_fields = []
        parsing_errors = []
        payload_str = ""

        if not isinstance(exc, RequestValidationError):
            return str(exc)

        for err in exc.errors():
            err_type = err.get("type")
            loc = ".".join(str(loc_part) for loc_part in err.get("loc", []))
            msg = err.get("msg", "Invalid input")
            input_value = err.get("input", "")

            if err_type == "missing":
                missing_fields.append(loc)
            elif err_type == "int_parsing":
                parsing_errors.append(f"{loc}: {msg}, provided value: {input_value}")
            else:
                parsing_errors.append(f"{loc}: {msg}")

            if input_value and not payload_str:
                payload_str = str(input_value)

        parts = []
        if missing_fields:
            parts.append(f"Missing field(s): {', '.join(missing_fields)}")
        if parsing_errors:
            parts.extend(parsing_errors)

        error_message = ". ".join(parts)
        if payload_str:
            error_message += f", invalid payload: {payload_str}"

        return error_message


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


async def request_validation_error_handler(
    _: Request, err: ResponseValidationError, status=HTTPStatus.INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """A custom handler function that returns a verbose HTTP 500 response
    containing detailed traceback information."""

    formatted = ValidationErrorFormatter.format(err)

    result = convert_to_response_object(
        formatted,
        result_code=HTTPStatus.UNPROCESSABLE_ENTITY,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status,
    )


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
