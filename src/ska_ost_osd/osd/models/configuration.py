from typing import List

from pydantic import ConfigDict

from ska_ost_osd.osd.models.capabilities import (
    ElevationConstraints,
    LowCapabilities,
    LowFrequencyBand,
    LowSubarray,
    MidCapabilities,
    MidFrequencyBand,
    MidSubarray,
    TelescopeCapabilitiesBase,
)
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
    LowDefaults,
    LowQualityAttributeMetrics,
    MidDefaults,
    OSDBaseModel,
    SPFRxParameters,
    TelescopeDefaults,
)
from ska_ost_osd.osd.models.observatory_policies import ObservatoryPolicy


class ConfigurationModel(OSDBaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )


class Constraints(ElevationConstraints, AvoidanceConstraints):
    """The constraints are spread across the two tmdata files - combining them"""


def _merge_constraints(
    capabilities: TelescopeCapabilitiesBase, defaults: TelescopeDefaults
) -> Constraints:
    """
    The defaults file's avoidance angles with the capabilities file's
    elevation limits.
    """
    merged = {
        **capabilities.constraints.model_dump(),
        **defaults.constraints.model_dump(),
    }
    return Constraints(**merged)


class MidConfiguration(ConfigurationModel):
    frequency_band: List[MidFrequencyBand]
    constraints: Constraints
    subarrays: List[MidSubarray]
    spfrx_defaults: SPFRxParameters

    @classmethod
    def combine(
        cls, capabilities: MidCapabilities, defaults: MidDefaults
    ) -> "MidConfiguration":
        return cls(
            frequency_band=capabilities.frequency_band,
            constraints=_merge_constraints(capabilities, defaults),
            subarrays=capabilities.subarrays,
            spfrx_defaults=defaults.spfrx_defaults,
        )


class LowConfiguration(ConfigurationModel):
    frequency_band: LowFrequencyBand
    constraints: Constraints
    quality_attribute_metrics: LowQualityAttributeMetrics
    subarrays: List[LowSubarray]

    @classmethod
    def combine(
        cls, capabilities: LowCapabilities, defaults: LowDefaults
    ) -> "LowConfiguration":
        return cls(
            frequency_band=capabilities.frequency_band,
            constraints=_merge_constraints(capabilities, defaults),
            quality_attribute_metrics=defaults.quality_attribute_metrics,
            subarrays=capabilities.subarrays,
        )


class Configuration(ConfigurationModel):
    ska_mid: MidConfiguration
    ska_low: LowConfiguration
    observatory_policy: ObservatoryPolicy
