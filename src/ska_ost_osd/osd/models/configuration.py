from typing import Self

from pydantic import ConfigDict
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    LOW_CONSTANT_JSON_FILE_PATH,
    LOW_DEFAULTS_JSON_FILE_PATH,
    MID_CONSTANT_JSON_FILE_PATH,
    MID_DEFAULTS_JSON_FILE_PATH,
    OBSERVING_CYCLES_TMDATA_DIR,
)
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
from ska_ost_osd.osd.osd import get_available_cycles


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
    # ToDo: remove once we're out of the contract phase of moving the
    # osd defaults to defaults.json
    merged = {
        **capabilities.constraints.model_dump(),
        **defaults.constraints.model_dump(),
    }
    return Constraints(**merged)


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidSubarray]
    spfrx_defaults: SPFRxParameters

    @classmethod
    def combine(cls, capabilities: MidCapabilities, defaults: MidDefaults) -> Self:
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
    subarrays: list[LowSubarray]

    @classmethod
    def combine(cls, capabilities: LowCapabilities, defaults: LowDefaults) -> Self:
        return cls(
            frequency_band=capabilities.frequency_band,
            constraints=_merge_constraints(capabilities, defaults),
            quality_attribute_metrics=defaults.quality_attribute_metrics,
            subarrays=capabilities.subarrays,
        )


class Configuration(ConfigurationModel):
    ska_mid: MidConfiguration
    ska_low: LowConfiguration
    observatory_policies: list[ObservatoryPolicy]

    @classmethod
    def from_tmdata(cls, tmdata: TMData) -> Self:
        """Read and combine the capabilities, defaults and cycle files."""

        def read(path: str) -> dict:
            return tmdata[path].get_dict()

        return cls(
            ska_mid=MidConfiguration.combine(
                MidCapabilities.model_validate(read(MID_CONSTANT_JSON_FILE_PATH)),
                MidDefaults.model_validate(read(MID_DEFAULTS_JSON_FILE_PATH)),
            ),
            ska_low=LowConfiguration.combine(
                LowCapabilities.model_validate(read(LOW_CONSTANT_JSON_FILE_PATH)),
                LowDefaults.model_validate(read(LOW_DEFAULTS_JSON_FILE_PATH)),
            ),
            observatory_policies=[
                ObservatoryPolicy.model_validate(
                    read(f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{cycle}.json")
                )
                for cycle in sorted(get_available_cycles(tmdata))
            ],
        )
