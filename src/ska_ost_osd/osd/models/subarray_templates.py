"""Pydantic models for tmdata/subarray_templates/subarray_template_library.json."""

from enum import StrEnum
from typing import Any, List

from pydantic import Field, field_validator, model_validator

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class SubarrayType(StrEnum):
    CUSTOM = "custom"
    AA2 = "AA2"
    AA4 = "AA4"
    AA_STAR = "AA*"


class SubarrayTemplate(OSDBaseModel):
    """One template. tmdata: a top-level key and its value."""

    name: str = Field(examples=["MID_FULL_AA2"])
    subarray_type: SubarrayType
    custom_stations: List[str] = Field(examples=[["SKA001", "SKA013"]])
    description: str

    @field_validator("custom_stations", mode="before")
    @classmethod
    def split_stations(cls, value: Any) -> Any:
        """tmdata lists the stations as one comma-separated string."""
        if isinstance(value, str):
            return [station.strip() for station in value.split(",") if station.strip()]
        return value

    @model_validator(mode="after")
    def check_custom_stations(self):
        if self.subarray_type == SubarrayType.CUSTOM and not self.custom_stations:
            raise ValueError(f"{self.name}: a custom template lists no custom_stations")
        if self.subarray_type != SubarrayType.CUSTOM and self.custom_stations:
            raise ValueError(f"{self.name}: only custom templates list custom_stations")
        return self


class SubarrayTemplateLibrary(OSDBaseModel):
    """Top-level model for subarray_template_library.json."""

    templates: List[SubarrayTemplate]

    @model_validator(mode="before")
    @classmethod
    def collect_templates(cls, data: Any) -> Any:
        """In tmdata each template is a top-level key; gather them into
        ``templates``, using the key as the template name."""
        if not isinstance(data, dict) or "templates" in data:
            return data
        return {
            "templates": [{"name": name, **template} for name, template in data.items()]
        }
