import re
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator

from ska_ost_osd.telvalidation.common.constant import INTERFACE_PATTERN


class SemanticModel(BaseModel):
    observing_command_input: dict
    interface: Optional[str] = None
    raise_semantic: Optional[bool] = True
    array_assembly: Optional[str] = None
    osd_data: Optional[dict] = None
    tm_data: Optional[object] = None

    @field_validator("observing_command_input")
    @classmethod
    def validate_observing_command_input(cls, v: Any) -> dict:
        if not isinstance(v, dict):
            raise ValueError(
                "observing_command_input field is required and must be a dictionary"
            )
        return v

    @field_validator("interface")
    @classmethod
    def validate_interface(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Interface must be a string")
            if not re.match(INTERFACE_PATTERN, v):
                raise ValueError(f"Interface must match pattern: {INTERFACE_PATTERN}")
        return v


class SemanticValidationModel(BaseModel):
    interface: Optional[str] = None
    observing_command_input: Dict[str, Any]
    osd_data: Optional[Dict[str, Any]] = None
    raise_semantic: Optional[bool] = True
    sources: Optional[str] = None

    @field_validator("sources")
    @classmethod
    def validate_sources_contains_osd_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and "{osd_version}" in v:
            raise ValueError(
                "Please provide 'osd_version' by replacing '{osd_version}' placeholder"
            )
        return v
