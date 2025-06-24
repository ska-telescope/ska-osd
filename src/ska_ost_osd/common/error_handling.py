import logging
from typing import Any, Dict

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ska_ost_osd.common.utils import (
    convert_to_response_object,
    get_status_code_from_exception,
)

LOGGER = logging.getLogger(__name__)


class ValidationErrorFormatter:
    @staticmethod
    def format(exc: RequestValidationError) -> Dict[str, Any]:
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

    status_code = get_status_code_from_exception(err)

    result = convert_to_response_object(
        formatted,
        result_code=status_code,
    )

    return JSONResponse(
        content=result.model_dump(mode="json", exclude_none=True),
        status_code=status_code,
    )
