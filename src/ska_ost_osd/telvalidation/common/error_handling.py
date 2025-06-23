import logging
from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from ska_ost_osd.common.utils import convert_to_response_object
from ska_ost_osd.telvalidation.common.schematic_validation_exceptions import (
    SchematicValidationError,
)

LOGGER = logging.getLogger(__name__)


async def schematic_validation_error_handler(
    _: Request, err: SchematicValidationError
) -> JSONResponse:
    """A custom handler function to deal with SchematicValidationError raised
    while schema validation return the correct HTTP response."""

    LOGGER.exception("Semantic Validation Error")

    result = convert_to_response_object(err.message, result_code=HTTPStatus.OK)

    return JSONResponse(content=result.model_dump(), status_code=HTTPStatus.OK)
