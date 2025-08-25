import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from gitlab import GitlabGetError
from pydantic import ValidationError

from ska_ost_osd.common.constant import EXCEPTION_STATUS_MAP
from ska_ost_osd.common.utils import convert_to_response_object
from ska_ost_osd.osd.common.error_handling import OSDModelError
from ska_ost_osd.telvalidation.common.error_handling import SchematicValidationError

LOGGER = logging.getLogger(__name__)


exception_types = [
    OSDModelError,
    SchematicValidationError,
    RequestValidationError,
    ResponseValidationError,
    ValueError,
    FileNotFoundError,
    RuntimeError,
    ValidationError,
    GitlabGetError,
]


def get_http_status_from_map(exc: Exception) -> int:
    """Get the HTTP status code from the predefined exception-to-status
    mapping.

    This function checks the type of the given exception against a
    mapping of exception types to HTTP status codes. If a match is
    found, the corresponding status code is returned. If no match is
    found, a default `500 Internal Server Error` status code is
    returned.

    :param exc: Exception, the exception instance for which the HTTP
        status code is to be determined.
    :return: int, the corresponding HTTP status code.
    """
    exc_type = type(exc)
    for key, status_code in EXCEPTION_STATUS_MAP.items():
        if isinstance(key, tuple):
            if exc_type in key:  # pylint: disable=I0021
                return status_code
        elif exc_type == key:
            return status_code
    return status.HTTP_500_INTERNAL_SERVER_ERROR  # Default fallback


class ValidationErrorFormatter:
    @staticmethod
    def format(exc: RequestValidationError) -> Dict[str, Any]:
        """Format a FastAPI RequestValidationError into a structured error
        message.

        This method processes validation errors to identify:
        - Missing required fields (`type == "missing"`)
        - The invalid input value that triggered the error

        Returns a dictionary with a single "error" key containing a
        human-readable summary, including the names of missing
        fields and the payload value that caused the failure.

        Example return:
        {
            "error": "Missing field(s): cycle_id, osd_version, invalid payload: false"
        }

        :param exc: RequestValidationError, the exception raised during
            request validation.
        :return: Dict[str, Any], a dictionary containing the formatted error message.
        """
        missing_fields = []
        parsing_errors = []
        payload_str = ""

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
        if payload_str and not type(input_value) == dict:
            error_message += f", invalid payload: {payload_str}"

        return error_message


async def generic_exception_handler(_: Request, err: Exception) -> JSONResponse:
    """A custom handler function that returns a verbose HTTP error response
    containing detailed traceback information.

    This handler processes both validation and generic exceptions. For validation
    errors, it uses the ValidationErrorFormatter to create a structured message.
    For other exceptions, it attempts to extract a list/dictionary message from
    the exception arguments, or falls back to a string representation.

    The HTTP status code is determined by mapping the exception type to a status
    code using `get_http_status_from_map`. The final result is converted into a
    standardized response object and returned as a JSONResponse.

    :param _: Request, the incoming HTTP request (unused in this handler).
    :param err: Exception, the exception instance to handle.
    :return: JSONResponse, the structured HTTP error response.
    """

    if isinstance(err, RequestValidationError):
        formatted = ValidationErrorFormatter.format(err)
    else:
        if err.args and isinstance(err.args[0], (list, dict)):
            formatted = err.args[0]
        else:
            formatted = str(err)

    status_code = get_http_status_from_map(err)

    result = convert_to_response_object(
        formatted,
        result_code=status_code,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status_code,
    )
