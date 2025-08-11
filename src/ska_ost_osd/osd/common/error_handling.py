import logging
from typing import List

LOGGER = logging.getLogger(__name__)


class BaseOSDError(Exception):
    """Base exception class for OSD errors.

    :param errors: List[dict], a list of error details.
    """

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class OSDModelError(BaseOSDError):
    """Exception raised for model validation errors.

    :param errors: List[dict], a list of error details related to model
        validation.
    """


class CapabilityError(BaseOSDError):
    """Exception raised for capability-related errors.

    :param errors: List[dict], a list of error details related to
        capability checks.
    """
