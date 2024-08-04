import re
from typing import List, Optional

from pydantic import BaseModel, model_validator

from ska_ost_osd.osd.constant import ARRAY_ASSEMBLY_PATTERN, OSD_VERSION_PATTERN
from ska_ost_osd.osd.osd_validation_messages import (
    ARRAY_ASSEMBLY_INVALID_ERROR_MESSAGE,
    CYCLE_ID_CAPABILITIES_ERROR_MESSAGE,
    CYCLE_ID_GITLAB_BRANCH_ERROR_MESSAGE,
    GITLAB_BRANCH_ERROR_MESSAGE,
    OSD_VERSION_INVALID_ERROR_MESSAGE,
)


class OSDModelError(Exception):
    """Custom exception class for validation errors."""

    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(errors)


class OSDModel(BaseModel):
    cycle_id: Optional[int] = None
    osd_version: Optional[str] = None
    source: Optional[str] = None
    gitlab_branch: Optional[str] = None
    capabilities: Optional[str] = None
    array_assembly: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_combinations(cls, values: dict) -> dict:
        cycle_id = values.get("cycle_id")
        osd_version = values.get("osd_version")
        gitlab_branch = values.get("gitlab_branch")
        capabilities = values.get("capabilities")
        array_assembly = values.get("array_assembly")

        errors = []
        # Validate forbidden combinations
        if gitlab_branch and osd_version:
            errors.append(
                {
                    "msg": GITLAB_BRANCH_ERROR_MESSAGE,
                }
            )
        if cycle_id and array_assembly:
            errors.append(
                {
                    "msg": CYCLE_ID_GITLAB_BRANCH_ERROR_MESSAGE,
                }
            )

        # Validate either combination
        if not (cycle_id or capabilities):
            errors.append(
                {
                    "msg": CYCLE_ID_CAPABILITIES_ERROR_MESSAGE,
                }
            )

        # Validate patterns
        if osd_version and not re.match(OSD_VERSION_PATTERN, osd_version):
            errors.append(
                {"msg": OSD_VERSION_INVALID_ERROR_MESSAGE.format(osd_version)}
            )
        if array_assembly and not re.match(ARRAY_ASSEMBLY_PATTERN, array_assembly):
            errors.append(
                {"msg": ARRAY_ASSEMBLY_INVALID_ERROR_MESSAGE.format(array_assembly)}
            )
        if errors:
            raise OSDModelError(errors)

        return values
