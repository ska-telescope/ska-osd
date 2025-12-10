import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypeVar

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


class OSDUpdateModel(BaseModel):
    """Pydantic model representing the OSD update payload.

    :param cycle_id: Optional; ID of the cycle (must be an integer).
    :param array_assembly: Optional; array assembly string in the format
        ``AA[0-9].[0-9]``.
    :param capabilities: Optional; system capabilities, can be either
        ``"mid"`` or ``"low"``.
    """

    cycle_id: Optional[int] = Field(..., description="Cycle ID must be an integer")
    array_assembly: Optional[str] = Field(
        ...,
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    capabilities: Optional[Literal["mid", "low"]] = Field(
        default=None,
        description="System capabilities",
        title="Capabilities",
        example="mid",
    )


class CycleModel(BaseModel):
    """Pydantic model representing a list of cycle IDs.

    :param cycles: A list of integer cycle IDs.
    """

    cycles: List[int]


class OSDModel(BaseModel):
    """Pydantic model representing the parameters used for retrieving or
    validating an OSD (Observatory Science Data) release.

    **Field Rules:**
    - `gitlab_branch` and `osd_version` cannot both be set.
    - `cycle_id` and `array_assembly` cannot both be set.
    - At least one of `cycle_id` or `capabilities` must be provided.
    - `osd_version` must match the pattern: ``OSD_VERSION_PATTERN``.
    - `array_assembly` must match the pattern: ``ARRAY_ASSEMBLY_PATTERN``.

    :param cycle_id: Integer ID representing the OSD cycle.
    :param osd_version: String version identifier for the OSD release.
    :param source: Source of the OSD data.
    :param gitlab_branch: GitLab branch name used for retrieving OSD data.
    :param capabilities: System capabilities (`"mid"` or `"low"`).
    :param array_assembly: Array assembly identifier (format: `AA[0-9].[0-9]`).
    """

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
    """Validate the structure of the `capabilities` field.

    This model enforces:
    - The presence of the `capabilities` field.
    - The field must contain exactly one telescope key.
    - The value of the telescope key must be a dictionary.

    :param capabilities: dict[str, dict[str, Any]], dictionary containing capabilities
        for a single telescope. The key represents the telescope name
        (e.g., "mid", "low") and its value contains the related configuration data.
    :raises CapabilityError: If the `capabilities` field is missing, does not contain
        exactly one telescope key, or the telescope key's value is not a dictionary.
    """

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


class ReleaseType(str, Enum):
    """Enumeration of possible release types for OSD.

    This enum is used to distinguish between major and minor releases.
    It inherits from ``str`` to allow string comparisons and serialization.

    :cvar minor: Represents a minor release.
    :cvar major: Represents a major release.
    """

    minor = "minor"
    major = "major"


class OSDRelease(BaseModel):
    """Represents an OSD (Observation Scheduling Data) release metadata object.

    This model stores key details about a specific OSD release,
    including a human-readable release message, the release version,
    and the associated cycle ID.

    :param message: str, description or notes about the release.
    :param version: str, release version string (e.g., ``"1.2.0"``).
    :param cycle_id: str, identifier for the cycle associated with this release.

    **Example:**

    .. code-block:: python

        release = OSDRelease(
            message="Updated observation constraints for mid telescope",
            version="4.1.0",
            cycle_id="4"
        )
    """

    message: str
    version: str
    cycle_id: str


class OSDQueryParams(BaseModel):
    """Query parameters for retrieving OSD details.

    :param cycle_id: Optional[int], the ID of the release cycle.
        Example: 1
    :param osd_version: Optional[str], the version of the OSD to retrieve.
        Example: "1.0.0"
    :param source: Optional[Literal["car", "file", "gitlab"]], the source from
        which the OSD is obtained. Defaults to "file". Valid options: "car",
        "file", "gitlab".
        Example: "file"
    :param gitlab_branch: Optional[str], the name of the GitLab branch
        associated with the OSD release.
        Example: "gitlab_branch"
    :param capabilities: Optional[Literal["mid", "low"]], the system capabilities
        used in the release. Valid options: "mid", "low".
        Example: "mid"
    :param array_assembly: Optional[str], the version identifier of the Array
        Assembly component.
        Example: "AA0.5"
    """

    cycle_id: Optional[int] = Field(
        default=None, example=1, description="Cycle ID", title="Cycle ID"
    )
    osd_version: Optional[str] = Field(
        default=None,
        example="1.0.0",
        description="OSD Version (e.g., 1.0.0)",
        title="OSD Version",
    )
    source: Optional[Literal["car", "file", "gitlab"]] = Field(
        default="car",
        description="Source of OSD release",
        title="Source",
        example="file",
    )
    gitlab_branch: Optional[str] = Field(
        default=None,
        description="GitLab branch name",
        title="GitLab Branch",
        example="gitlab_branch",
    )
    capabilities: Optional[Literal["mid", "low"]] = Field(
        default=None,
        description="System capabilities",
        title="Capabilities",
        example="mid",
    )
    array_assembly: Optional[str] = Field(
        default=None,
        description="Array Assembly version",
        title="Array Assembly",
        example="AA0.5",
    )
