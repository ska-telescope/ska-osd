from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator

from ska_ost_osd.osd.osd_schema_validator import CapabilityError

from .constant import ARRAY_ASSEMBLY_PATTERN


class UpdateRequestModel(BaseModel):
    cycle_id: Optional[int] = Field(..., description="Cycle ID must be an integer")
    array_assembly: Optional[str] = Field(
        ...,
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    capabilities: Optional[str] = Field(..., description="Capabilites must be str")


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
