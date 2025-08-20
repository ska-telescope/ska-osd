import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from ska_ost_osd.osd.common.constant import ARRAY_ASSEMBLY_PATTERN
from ska_ost_osd.telvalidation.common.constant import INTERFACE_PATTERN


class SemanticModel(BaseModel):
    """Represents the structured input required for executing an observing
    command.

    :param observing_command_input: dict, mandatory. Input parameters
        for the observing command.
    :param interface: Optional[str], optional. Specifies the interface
        type.
    :param raise_semantic: Optional[bool], optional. Indicates whether
        to raise semantic validation errors. Defaults to True.
    :param array_assembly: Optional[str], optional. Represents the array
        assembly ID or name.
    :param osd_data: Optional[dict], optional. Holds relevant data from
        the OSD.
    :param tm_data: Optional[object], optional. Can contain telemodel
        data.
    """

    observing_command_input: dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = True
    array_assembly: Optional[str] = None
    osd_data: Optional[dict] = None
    tm_data: Optional[object] = None

    @field_validator("observing_command_input")
    @classmethod
    def validate_observing_command_input(cls, v: Any) -> dict:
        """observing_command_input: Ensures the input is a dictionary."""
        if not isinstance(v, dict):
            raise ValueError(
                "observing_command_input field is required and must be a dictionary"
            )
        return v

    @field_validator("interface")
    @classmethod
    def validate_interface(cls, v: Optional[str]) -> Optional[str]:
        """interface: Ensures the value is a string and matches the
        specified regex pattern."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Interface must be a string")
            if not re.match(INTERFACE_PATTERN, v):
                raise ValueError(f"Interface must match pattern: {INTERFACE_PATTERN}")
        return v


class SemanticValidationModel(BaseModel):
    """Defines the schema for validating semantic input data related to
    observing commands and system configuration.

    :param interface: Optional[str], optional. Command interface type.
    :param observing_command_input: Dict[str, Any], required. Core input
        parameters for an observing command.
    :param osd_data: Optional[Dict[str, Any]], optional. Data fetched
        from the OSD.
    :param raise_semantic: Optional[bool], optional. Flag to indicate
        whether semantic validation errors should be raised. Defaults to
        True.
    :param sources: Optional[str], optional. Data sources, may include
        placeholders such as '{osd_version}'.
    """

    interface: Optional[str] = None
    array_assembly: Optional[str] = Field(
        default="AA0.5",
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    observing_command_input: Dict[str, Any]
    osd_data: Optional[Dict[str, Any]] = None
    raise_semantic: Optional[bool] = True
    sources: Optional[str] = None

    @field_validator("sources")
    @classmethod
    def validate_sources_contains_osd_version(cls, v: Optional[str]) -> Optional[str]:
        """sources: Ensures the 'sources' field does not contain an unreplaced
        '{osd_version}' placeholder. Raises a ValueError if present."""
        if v is not None and "{osd_version}" in v:
            raise ValueError(
                "Please provide 'osd_version' by replacing '{osd_version}' placeholder"
            )
        return v
