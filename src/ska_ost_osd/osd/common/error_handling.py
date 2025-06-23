import logging
from typing import List

from fastapi.responses import JSONResponse

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
