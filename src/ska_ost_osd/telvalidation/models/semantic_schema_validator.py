import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator

from ska_ost_osd.telvalidation.common.constant import INTERFACE_PATTERN


class SemanticModel(BaseModel):
    """SemanticModel represents the structured input required for executing an
    observing command within the system.

    :param observing_command_input (dict): Mandatory. Contains the input
        parameters for the observing command. :param interface
        (Optional[str]): Optional. Specifies the interface type. :param
        raise_semantic (Optional[bool]): Optional. Indicates whether to
        raise semantic validation errors. Defaults to True. :param
        array_assembly (Optional[str]): Optional. Represents the array
        assembly ID or name. :param osd_data (Optional[dict]): Optional.
        Holds relevant data from the OSD. :param tm_data
        (Optional[object]): Optional. Can contain telemodel data.
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
    """SemanticValidationModel defines the schema for validating semantic input
    data related to observing commands and system configuration.

    :param interface (Optional[str]): An optional string representing
    the command interface type.

    :param observing_command_input (Dict[str, Any]): A required
    dictionary containing the core input parameters for an observing
    command.

    :param osd_data (Optional[Dict[str, Any]]): Optional data fetched
    from the OSD.

    :param raise_semantic (Optional[bool]): Flag to indicate whether
    semantic validation errors should be raised. Defaults to True.

    :param sources (Optional[str]): An optional string that may
    reference data sources, including dynamic placeholders such as
    '{osd_version}'.
    """

    interface: Optional[str] = None
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
