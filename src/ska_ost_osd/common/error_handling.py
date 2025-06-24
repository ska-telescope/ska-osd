import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ska_ost_osd.common.constant import EXCEPTION_STATUS_MAP
from ska_ost_osd.common.utils import convert_to_response_object

LOGGER = logging.getLogger(__name__)


class ValidationErrorFormatter:
    @staticmethod
    def format(exc: RequestValidationError) -> Dict[str, Any]:
        """
        Format a FastAPI RequestValidationError into a structured
        error message.

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

        Args:
            exc (RequestValidationError): The exception raised during
            request validation.

        Returns:
            Dict[str, Any]: A dictionary containing the formatted error message.
        """
        missing_fields = []
        payload_str = ""

        for err in exc.errors():
            if err.get("type") == "missing":
                missing_fields.append(err["loc"][-1])
            payload_str = err["input"]

        parts = []
        if missing_fields:
            parts.append(f"Missing field(s): {', '.join(missing_fields)}")

        return ". ".join(parts) + f", invalid payload: {payload_str}"


async def generic_exception_handler(_: Request, err: Exception) -> JSONResponse:
    """A custom handler function that returns a verbose HTTP error response
    containing detailed traceback information."""

    if isinstance(err, RequestValidationError):
        formatted = ValidationErrorFormatter.format(err)
    else:
        formatted = str(err)

    status_code = EXCEPTION_STATUS_MAP.get(
        err.__class__, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    result = convert_to_response_object(
        formatted,
        result_code=status_code,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status_code,
    )
