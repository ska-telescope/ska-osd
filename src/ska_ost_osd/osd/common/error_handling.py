import logging
from typing import List

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
