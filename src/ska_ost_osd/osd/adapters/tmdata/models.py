"""The storage models: each tmdata file as it is stored, validated as a
whole. ``storage`` reads the files into these, and ``TMDataRepository`` maps
them to the reader models."""

from typing import Literal, Self

from pydantic import AliasChoices, Field, model_validator

from ska_ost_osd.osd.models.capabilities import (
    LowBasicCapabilities,
    LowCBFMode,
    MidBasicCapabilities,
    MidCBFMode,
)
from ska_ost_osd.osd.models.cycles import (
    CycleID,
    CycleInformation,
    CyclePolicies,
    TelescopeCapabilities,
)
from ska_ost_osd.osd.models.defaults import (
    LowQualityAttributeMetrics,
    OSDBaseModel,
    SPFRxParameters,
)
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate


class CapabilitySetFileBase(OSDBaseModel):
    """Base for the Mid and Low capability set file models. Each file is
    named after its capability set, so it holds neither the name nor the
    telescope."""

    available_bandwidth_hz: float = Field(gt=0)
    number_pst_beams: int = Field(ge=0)
    number_fsps: int = Field(ge=0)
    max_baseline_km: float = Field(gt=0)
    number_zoom_windows: int = Field(ge=0)
    number_zoom_channels: int = Field(ge=0)
    number_pss_beams: int = Field(ge=0)
    ps_beam_bandwidth_hz: float = Field(ge=0)
    # The array assembly whose subarray templates the capability set offers,
    # e.g. "AA2"; the *_ITF capability sets have none
    array_assembly: str | None = None


class MidCapabilitySetFile(CapabilitySetFileBase):
    """Model for ska1_mid/capabilities/<name>.json."""

    number_dish_ids: list[str]
    allowed_channel_width_values_hz: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_count_range_max: list[int]
    available_receivers: list[str]
    cbf_modes: list[MidCBFMode]
    number_ska_dishes: int = Field(ge=0)
    number_meerkat_dishes: int = Field(ge=0)
    number_meerkatplus_dishes: int = Field(ge=0)

    @model_validator(mode="after")
    def check_dish_count(self) -> Self:
        # number_dish_ids lists SKA dishes only; MeerKAT dishes are counted
        # separately
        if self.number_ska_dishes != len(self.number_dish_ids):
            raise ValueError(
                f"number_ska_dishes ({self.number_ska_dishes}) does not match "
                f"the number of dish IDs ({len(self.number_dish_ids)})"
            )
        return self


class LowCapabilitySetFile(CapabilitySetFileBase):
    """Model for ska1_low/capabilities/<name>.json."""

    number_station_ids: list[int]
    number_substations: int = Field(ge=0)
    number_subarray_beams: int = Field(ge=0)
    number_stations: int = Field(ge=0)
    cbf_modes: list[LowCBFMode]
    number_vlbi_beams: int = Field(ge=0)
    allowed_zoom_factors: list[int]

    @model_validator(mode="after")
    def check_station_count(self) -> Self:
        if self.number_stations != len(self.number_station_ids):
            raise ValueError(
                f"number_stations ({self.number_stations}) does not match "
                f"the number of station IDs ({len(self.number_station_ids)})"
            )
        return self


# Basic capabilities file structure matches the reader models
MidBasicCapabilitiesFile = MidBasicCapabilities
"""Model for ska1_mid/basic_capabilities.json."""

LowBasicCapabilitiesFile = LowBasicCapabilities
"""Model for ska1_low/basic_capabilities.json."""


class AvoidanceConstraints(OSDBaseModel):
    """
    Sun, moon and Jupiter avoidance angles.
    """

    sun_avoidance_angle_deg: float = Field(examples=[30.0])
    moon_avoidance_angle_deg: float = Field(examples=[10.0])
    jupiter_avoidance_angle_deg: float = Field(examples=[10.0])


class TelescopeDefaultsFileBase(OSDBaseModel):
    """Base for the Mid and Low defaults file models."""

    constraints: AvoidanceConstraints


class MidDefaultsFile(TelescopeDefaultsFileBase):
    """Top-level model for mid_defaults.json."""

    telescope: Literal["Mid"] = "Mid"
    spfrx_defaults: SPFRxParameters = Field(
        validation_alias=AliasChoices("spfrx_defaults", "defaults")
    )


class LowDefaultsFile(TelescopeDefaultsFileBase):
    """Top-level model for low_defaults.json."""

    telescope: Literal["Low"] = "Low"
    quality_attribute_metrics: LowQualityAttributeMetrics


class CycleFile(OSDBaseModel):
    """Top-level model for cycles/cycle_<N>.json, and for the legacy
    observatory_policies.json."""

    cycle_number: CycleID
    cycle_id: str | None = None
    type: str | None = Field(default=None, examples=["Science Verification"])
    cycle_description: str
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: TelescopeCapabilities


class SubarrayTemplateLibraryFile(OSDBaseModel):
    """Top-level model for ska1_<telescope>/subarray_templates/<array
    assembly>.json: one array assembly's templates."""

    templates: list[SubarrayTemplate]

    @model_validator(mode="after")
    def check_unique_names(self) -> Self:
        if len({template.name for template in self.templates}) != len(self.templates):
            raise ValueError("template names are not unique")
        return self
