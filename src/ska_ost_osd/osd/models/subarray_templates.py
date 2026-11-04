"""The subarray template reader model. The storage model for the template
library file is in ``ska_ost_osd.osd.adapters.tmdata.models``."""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class SubarrayType(StrEnum):
    CUSTOM = "custom"
    AA2 = "AA2"
    AA4 = "AA4"
    AA_STAR = "AA*"


class SubarrayTemplate(OSDBaseModel):
    """One template. tmdata: a top-level value."""

    name: str = Field(examples=["SKA_MID_FULL_AA2"])
    subarray_type: SubarrayType
    custom_stations: list[str] = Field(examples=[["SKA001", "SKA013"]])
    description: str

    @model_validator(mode="after")
    def check_custom_stations(self) -> Self:
        if self.subarray_type == SubarrayType.CUSTOM and not self.custom_stations:
            raise ValueError(f"{self.name}: a custom template lists no custom_stations")
        if self.subarray_type != SubarrayType.CUSTOM and self.custom_stations:
            raise ValueError(f"{self.name}: only custom templates list custom_stations")
        return self
