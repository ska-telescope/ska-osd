"""The storage models: each tmdata file as it is stored, validated as a
whole. ``storage`` reads the files into these, and ``TMDataRepository`` maps
them to the reader models."""

from typing import Self

from pydantic import Field, model_validator

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowArrayAssemblyModes,
    LowArrayAssemblyStations,
    LowArrayAssemblySubarrayBeams,
    LowBasicCapabilities,
    LowCBFMode,
    MidArrayAssemblyDishes,
    MidArrayAssemblyModes,
    MidBasicCapabilities,
    MidCBFMode,
)
from ska_ost_osd.osd.models.cycles import (
    ProposalPolicy,
    ProposalWindow,
    TelescopeCapabilities,
)
from ska_ost_osd.osd.models.defaults import (
    CSPSPFRx,
    LowQualityAttributeMetrics,
    OSDBaseModel,
    TargetSPFRx,
)
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate


class MidCapabilitySetFile(OSDBaseModel):
    """Model for telescopes/ska_mid/capabilities/<name>.json. The file is
    named after its capability set, so it holds neither the name nor the
    telescope."""

    available_bandwidth_hz: float = Field(gt=0)
    number_fsps: int = Field(ge=0)
    # The array assembly whose subarray templates the capability set offers,
    # e.g. "AA2"; Mid_ITF has none
    array_assembly: str | None = None
    modes: MidArrayAssemblyModes
    allowed_channel_width_values_hz: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_count_range_max: list[int]
    receivers: list[str]
    cbf_modes: list[MidCBFMode]
    dishes: MidArrayAssemblyDishes

    @model_validator(mode="after")
    def check_cbf_modes(self) -> Self:
        for cbf_mode, mode in (
            (MidCBFMode.PSS, self.modes.pss),
            (MidCBFMode.PST, self.modes.pst),
        ):
            if (cbf_mode in self.cbf_modes) != (mode.max_beams > 0):
                raise ValueError(
                    f"cbf_modes must list {cbf_mode} exactly when "
                    f"modes.{cbf_mode}.max_beams is above 0"
                )
        return self


class LowCapabilitySetFile(OSDBaseModel):
    """Model for telescopes/ska_low/capabilities/<name>.json. The file is
    named after its capability set, so it holds neither the name nor the
    telescope."""

    available_bandwidth_hz: float = Field(gt=0)
    number_fsps: int = Field(ge=0)
    # The array assembly whose subarray templates the capability set offers,
    # e.g. "AA2"; Low_ITF has none
    array_assembly: str | None = None
    subarray_beams: LowArrayAssemblySubarrayBeams
    cbf_modes: list[LowCBFMode]
    modes: LowArrayAssemblyModes
    stations: LowArrayAssemblyStations

    @model_validator(mode="after")
    def check_cbf_modes(self) -> Self:
        # vis isn't checked against modes.spectral: some capability sets list
        # vis but offer no zoom windows
        for cbf_mode, mode in (
            (LowCBFMode.PSS, self.modes.pss),
            (LowCBFMode.PST, self.modes.pst),
        ):
            if (cbf_mode in self.cbf_modes) != (mode.max_beams > 0):
                raise ValueError(
                    f"cbf_modes must list {cbf_mode} exactly when "
                    f"modes.{cbf_mode}.max_beams is above 0"
                )
        return self


# Basic capabilities file structure matches the reader models
MidBasicCapabilitiesFile = MidBasicCapabilities
"""Model for telescopes/ska_mid/basic_capabilities.json."""

LowBasicCapabilitiesFile = LowBasicCapabilities
"""Model for telescopes/ska_low/basic_capabilities.json."""


class AvoidanceConstraints(OSDBaseModel):
    """
    Sun, moon and Jupiter avoidance angles.
    """

    sun_avoidance_angle_deg: float = Field(examples=[30.0])
    moon_avoidance_angle_deg: float = Field(examples=[10.0])
    jupiter_avoidance_angle_deg: float = Field(examples=[10.0])


class MidTargetDefaults(OSDBaseModel):
    """The SPFRx parameters each Mid target starts with."""

    dish_spfrx_params: TargetSPFRx


class MidCSPConfigurationDefaults(OSDBaseModel):
    """The SPFRx settings Mid's CSP configuration starts with."""

    spfrx: CSPSPFRx


class MidDefaultsFile(OSDBaseModel):
    """Top-level model for telescopes/ska_mid/defaults.json."""

    constraints: AvoidanceConstraints
    target: MidTargetDefaults
    csp_configuration: MidCSPConfigurationDefaults


class LowDefaultsFile(OSDBaseModel):
    """Top-level model for telescopes/ska_low/defaults.json."""

    constraints: AvoidanceConstraints
    quality_attribute_metrics: LowQualityAttributeMetrics


class CycleFile(OSDBaseModel):
    """Top-level model for a cycle file, cycles/<name>.json."""

    id: str
    name: str
    description: str
    number: int | None = Field(default=None, ge=0, examples=[1])
    proposal_window: ProposalWindow
    proposal_policy: ProposalPolicy
    capabilities: dict[Telescope, TelescopeCapabilities] = Field(min_length=1)


class SubarrayTemplateLibraryFile(OSDBaseModel):
    """Top-level model for telescopes/<telescope>/subarray_templates/<array
    assembly>.json: one array assembly's templates."""

    templates: list[SubarrayTemplate]

    @model_validator(mode="after")
    def check_unique_names(self) -> Self:
        if len({template.name for template in self.templates}) != len(self.templates):
            raise ValueError("template names are not unique")
        return self
