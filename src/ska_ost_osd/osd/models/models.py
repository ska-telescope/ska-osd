import re
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

from ska_ost_osd.osd.common.constant import ARRAY_ASSEMBLY_PATTERN, OSD_VERSION_PATTERN
from ska_ost_osd.osd.common.error_handling import CapabilityError, OSDModelError
from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_INVALID_ERROR_MESSAGE,
    CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE,
    CYCLE_ID_CAPABILITIES_ERROR_MESSAGE,
    GITLAB_BRANCH_ERROR_MESSAGE,
    OSD_VERSION_INVALID_ERROR_MESSAGE,
)

T = TypeVar("T")


class UpdateRequestModel(BaseModel):
    cycle_id: Optional[int] = Field(..., description="Cycle ID must be an integer")
    array_assembly: Optional[str] = Field(
        ...,
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    capabilities: Optional[str] = Field(..., description="Capabilities must be str")


class CycleModel(BaseModel):
    cycles: List[int]


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
            errors.append(GITLAB_BRANCH_ERROR_MESSAGE)
        if cycle_id and array_assembly:
            errors.append(CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE)

        # Validate either combination
        if not (cycle_id or capabilities):
            errors.append(CYCLE_ID_CAPABILITIES_ERROR_MESSAGE)

        # Validate patterns
        if osd_version and not re.match(OSD_VERSION_PATTERN, osd_version):
            errors.append(OSD_VERSION_INVALID_ERROR_MESSAGE.format(osd_version))
        if array_assembly and not re.match(ARRAY_ASSEMBLY_PATTERN, array_assembly):
            errors.append(ARRAY_ASSEMBLY_INVALID_ERROR_MESSAGE.format(array_assembly))
        if errors:
            raise OSDModelError(errors)

        return values


class ValidationOnCapabilities(BaseModel):
    capabilities: Dict[str, Dict[str, Any]]

    @model_validator(mode="before")
    @classmethod
    def validate_capabilities(cls, values):
        if not values.get("capabilities"):
            raise CapabilityError("capabilities field is required")

        capabilities = values["capabilities"]
        if not isinstance(capabilities, dict) or len(capabilities) != 1:
            raise CapabilityError("capabilities must contain exactly one telescope key")

        telescope_data = next(iter(capabilities.values()))
        if not isinstance(telescope_data, dict):
            raise CapabilityError("telescope data must be a dictionary")

        return values
