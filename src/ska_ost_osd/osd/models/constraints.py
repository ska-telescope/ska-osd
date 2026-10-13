from typing import Self

from pydantic import Field, model_validator

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class Constraints(OSDBaseModel):
    """A telescope's observing constraints: its sun, moon and Jupiter
    avoidance angles and its elevation limits."""

    sun_avoidance_angle_deg: float = Field(examples=[30.0])
    moon_avoidance_angle_deg: float = Field(examples=[10.0])
    jupiter_avoidance_angle_deg: float = Field(examples=[10.0])
    min_elevation_deg: float = Field(ge=0, le=90, examples=[45.0])
    max_elevation_deg: float = Field(ge=0, le=90, examples=[90.0])

    @model_validator(mode="after")
    def check_elevation_range(self) -> Self:
        if self.min_elevation_deg > self.max_elevation_deg:
            raise ValueError("min_elevation_deg must not exceed max_elevation_deg")
        return self
