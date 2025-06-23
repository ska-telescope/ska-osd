import logging
from http import HTTPStatus
from typing import List

from fastapi import Request
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


async def development_exception_handler(exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error (non-production)", "error": str(exc)},
    )


async def schematic_validation_error_handler(
    _: Request, err: SchematicValidationError
) -> JSONResponse:
    """A custom handler function to deal with SchematicValidationError raised
    while schema validation return the correct HTTP response."""

    LOGGER.exception("Semantic Validation Error")

    result = convert_to_response_object(err.message, result_code=HTTPStatus.OK)

    return JSONResponse(content=result.model_dump(), status_code=HTTPStatus.OK)
