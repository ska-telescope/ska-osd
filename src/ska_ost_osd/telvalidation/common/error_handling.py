import logging
from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from ska_ost_osd.common.utils import convert_to_response_object

LOGGER = logging.getLogger(__name__)


class SchematicValidationError(ValueError):
    """Class to accept the various error messages from validator module."""

    def __init__(self, message="Undefined error", **_):
        self.message = message
        super().__init__(self.message)


class SchemanticValidationKeyError(KeyError):
    """Class to raise invalid input key for schemantic validation."""

    # flake8: noqa E501
    def __init__(
        self,
        message="It seems there is an issue with Validator JSON schema file, Please check and correct the JSON keys and try again.",
        **_,
    ):
        self.message = message
        super().__init__(self.message)


async def schematic_validation_error_handler(
    _: Request, err: SchematicValidationError
) -> JSONResponse:
    """A custom handler function to deal with SchematicValidationError raised
    while schema validation return the correct HTTP response."""

    LOGGER.exception("Semantic Validation Error")
    error_list = err.message.split("\n")

    result = convert_to_response_object(
        error_list, result_code=HTTPStatus.UNPROCESSABLE_ENTITY
    )

    return JSONResponse(content=result.model_dump(), status_code=HTTPStatus.OK)
