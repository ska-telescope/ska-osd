"""The storage models: each tmdata file as it is stored, validated as a
whole. ``storage`` reads the files into these, and ``TMDataRepository`` maps
them to the reader models."""

from typing import Self

from pydantic import Field, model_validator

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowArrayAssemblyModes,
    LowArrayAssemblyReceptors,
    LowArrayAssemblySubarrayBeams,
    LowBasicCapabilities,
    LowCBFMode,
    MidArrayAssemblyModes,
    MidArrayAssemblyReceptors,
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


class MidArrayAssemblyFile(OSDBaseModel):
    """Model for telescopes/ska_mid/array_assemblies/<name>.json: one array
    assembly, identified by its ``array_assembly``. Its subarray templates are
    the library of the same name, if there is one."""

    available_bandwidth_hz: float = Field(gt=0)
    number_fsps: int = Field(ge=0)
    array_assembly: str = Field(examples=["AA2"])
    modes: MidArrayAssemblyModes
    allowed_channel_width_values_hz: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_count_range_max: list[int]
    receivers: list[str]
    cbf_modes: list[MidCBFMode]
    receptors: MidArrayAssemblyReceptors

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


class LowArrayAssemblyFile(OSDBaseModel):
    """Model for telescopes/ska_low/array_assemblies/<name>.json: one array
    assembly, identified by its ``array_assembly``. Its subarray templates are
    the library of the same name, if there is one."""

    available_bandwidth_hz: float = Field(gt=0)
    number_fsps: int = Field(ge=0)
    array_assembly: str = Field(examples=["AA2"])
    subarray_beams: LowArrayAssemblySubarrayBeams
    cbf_modes: list[LowCBFMode]
    modes: LowArrayAssemblyModes
    receptors: LowArrayAssemblyReceptors

    @model_validator(mode="after")
    def check_cbf_modes(self) -> Self:
        # vis isn't checked against modes.spectral: some array assemblies list
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


class MidPolicySpectralMode(OSDBaseModel):
    max_zoom_windows: int | None = Field(default=None, ge=0)
    max_zoom_channels: int | None = Field(default=None, ge=0)


class MidPolicyPSSMode(OSDBaseModel):
    max_beams: int | None = Field(default=None, ge=0)
    beam_bandwidth_hz: float | None = Field(default=None, ge=0)


class MidPolicyPSTMode(OSDBaseModel):
    max_beams: int | None = Field(default=None, ge=0)


class MidPolicyModes(OSDBaseModel):
    spectral: MidPolicySpectralMode | None = None
    pss: MidPolicyPSSMode | None = None
    pst: MidPolicyPSTMode | None = None


class MidPolicyReceptors(OSDBaseModel):
    number_ska_dishes: int | None = Field(default=None, ge=0)
    number_meerkat_dishes: int | None = Field(default=None, ge=0)
    number_meerkatplus_dishes: int | None = Field(default=None, ge=0)
    max_baseline_km: float | None = Field(default=None, gt=0)
    ids: list[str] | None = None


class MidPolicyFile(OSDBaseModel):
    """Model for telescopes/ska_mid/policies/<name>.json: what a cycle
    offers of an array assembly. It mirrors MidArrayAssemblyFile with every
    field optional, and sets only what it changes; the cycle names the array
    assembly it applies to."""

    policy: str = Field(examples=["cycle_1_science_verification"])
    available_bandwidth_hz: float | None = Field(default=None, gt=0)
    number_fsps: int | None = Field(default=None, ge=0)
    modes: MidPolicyModes | None = None
    allowed_channel_width_values_hz: list[int] | None = None
    allowed_channel_count_range_min: list[int] | None = None
    allowed_channel_count_range_max: list[int] | None = None
    receivers: list[str] | None = None
    cbf_modes: list[MidCBFMode] | None = None
    receptors: MidPolicyReceptors | None = None


class LowPolicySpectralMode(OSDBaseModel):
    max_zoom_windows: int | None = Field(default=None, ge=0)
    max_zoom_channels: int | None = Field(default=None, ge=0)
    zoom_factors: list[int] | None = None


class LowPolicyPSSMode(OSDBaseModel):
    max_beams: int | None = Field(default=None, ge=0)
    beam_bandwidth_hz: float | None = Field(default=None, ge=0)


class LowPolicyPSTMode(OSDBaseModel):
    max_beams: int | None = Field(default=None, ge=0)


class LowPolicyVLBIMode(OSDBaseModel):
    max_beams: int | None = Field(default=None, ge=0)


class LowPolicyModes(OSDBaseModel):
    spectral: LowPolicySpectralMode | None = None
    pss: LowPolicyPSSMode | None = None
    pst: LowPolicyPSTMode | None = None
    vlbi: LowPolicyVLBIMode | None = None


class LowPolicySubarrayBeams(OSDBaseModel):
    max_subarray_beams: int | None = Field(default=None, ge=0)
    max_substations_per_subarray_beam: int | None = Field(default=None, ge=0)


class LowPolicyReceptors(OSDBaseModel):
    number_stations: int | None = Field(default=None, ge=0)
    max_baseline_km: float | None = Field(default=None, gt=0)
    ids: list[int] | None = None


class LowPolicyFile(OSDBaseModel):
    """Model for telescopes/ska_low/policies/<name>.json: what a cycle
    offers of an array assembly. It mirrors LowArrayAssemblyFile with every
    field optional, and sets only what it changes; the cycle names the array
    assembly it applies to."""

    policy: str = Field(examples=["cycle_1_science_verification"])
    available_bandwidth_hz: float | None = Field(default=None, gt=0)
    number_fsps: int | None = Field(default=None, ge=0)
    subarray_beams: LowPolicySubarrayBeams | None = None
    cbf_modes: list[LowCBFMode] | None = None
    modes: LowPolicyModes | None = None
    receptors: LowPolicyReceptors | None = None


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

    cycle_id: str
    name: str
    description: str
    cycle_number: int | None = Field(default=None, ge=0, examples=[1])
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
