import logging
from typing import List

from fastapi.responses import JSONResponse

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


async def development_exception_handler(exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error (non-production)", "error": str(exc)},
    )
