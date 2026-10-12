from typing import Self

from pydantic import ConfigDict

from ska_ost_osd.osd.models.capabilities import (
    ElevationConstraints,
    LowBasicCapabilities,
    MidFrequencyBand,
    TelescopeCapabilitiesFileBase,
)
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
    OSDBaseModel,
    SPFRxParameters,
    TelescopeDefaultsFileBase,
)


class ConfigurationModel(OSDBaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )


class Constraints(ElevationConstraints, AvoidanceConstraints):
    """A telescope's observing constraints, which tmdata stores in two
    files."""

    @classmethod
    def combine(
        cls,
        capabilities: TelescopeCapabilitiesFileBase,
        defaults: TelescopeDefaultsFileBase,
    ) -> Self:
        """The elevation limits from the capabilities file with the sun,
        moon and Jupiter avoidance angles from the defaults file."""
        return cls(
            **capabilities.constraints.model_dump(),
            **defaults.constraints.model_dump(),
        )


# The view models below are what ska-oso-services serves to the ODT from
# GET /configuration: the reader models narrowed to the fields it serves.


class ConfigurationCapabilitySetBase(ConfigurationModel):
    """The fields of a capability set the configuration serves for both
    telescopes."""

    name: str
    receptors: list[str | int]
    available_bandwidth_hz: float
    number_pst_beams: int
    number_fsps: int


class MidConfigurationCapabilitySet(ConfigurationCapabilitySetBase):
    allowed_channel_width_values_hz: list[int]


class LowConfigurationCapabilitySet(ConfigurationCapabilitySetBase):
    number_substations: int
    number_subarray_beams: int


class ConfigurationLowCBFMetrics(ConfigurationModel):
    processors_ready_percent: float


class ConfigurationLowQualityAttributeMetrics(ConfigurationModel):
    cbf: ConfigurationLowCBFMetrics


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidConfigurationCapabilitySet]
    spfrx_defaults: SPFRxParameters


class LowConfiguration(ConfigurationModel):
    frequency_band: LowBasicCapabilities
    constraints: Constraints
    quality_attribute_metrics: ConfigurationLowQualityAttributeMetrics
    subarrays: list[LowConfigurationCapabilitySet]


class Configuration(ConfigurationModel):
    """The ODT configuration: both telescopes' bands, constraints, defaults
    and capability sets."""

    ska_mid: MidConfiguration
    ska_low: LowConfiguration
