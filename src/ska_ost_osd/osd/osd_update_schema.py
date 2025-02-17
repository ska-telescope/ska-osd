import re
from typing import Any, Dict

from pydantic import BaseModel, Field, model_validator

ARRAY_ASSEMBLY_PATTERN = r"^AA(\d+|\d+)"


class UpdateRequestModel(BaseModel):
    cycle_id: int = Field(..., description="Cycle ID must be an integer")
    array_assembly: str = Field(
        ...,
        pattern=ARRAY_ASSEMBLY_PATTERN,
        description="Array assembly in format AA[0-9].[0-9]",
    )
    capabilities: str = Field(..., description="Capabilites must be string")

    @model_validator(mode="before")
    @classmethod
    def validate_capabilities(cls, values):
        if not values.get("cycle_id"):
            raise ValueError("cycle_id field is required")
        if not values.get("array_assembly"):
            raise ValueError("array_assembly field is required")
        if not values.get("capabilities"):
            raise ValueError("capabilities field is required")
        return values


class ValidationOnCapabilities(BaseModel):
    capabilities: Dict[str, Dict[str, Any]]

    @model_validator(mode="before")
    @classmethod
    def validate_capabilities(cls, values):
        if not values.get("capabilities"):
            raise ValueError("capabilities field is required")

        capabilities = values["capabilities"]
        if not isinstance(capabilities, dict) or len(capabilities) != 1:
            raise ValueError("capabilities must contain exactly one telescope key")

        telescope_data = next(iter(capabilities.values()))
        if not isinstance(telescope_data, dict):
            raise ValueError("telescope data must be a dictionary")

        return values
