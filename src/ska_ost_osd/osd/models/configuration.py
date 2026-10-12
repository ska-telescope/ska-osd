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
    LowBasicCapabilities,
    LowCapabilitiesFile,
    LowCapabilitySet,
    MidCapabilitiesFile,
    MidCapabilitySet,
    MidFrequencyBand,
    TelescopeCapabilitiesFileBase,
)
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
    LowDefaultsFile,
    LowQualityAttributeMetrics,
    MidDefaultsFile,
    OSDBaseModel,
    SPFRxParameters,
    TelescopeDefaultsFileBase,
)
from ska_ost_osd.osd.models.observatory_policies import ObservatoryPolicy
from ska_ost_osd.osd.osd import get_available_cycles


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


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidCapabilitySet]
    spfrx_defaults: SPFRxParameters

    @classmethod
    def combine(
        cls, capabilities: MidCapabilitiesFile, defaults: MidDefaultsFile
    ) -> Self:
        return cls(
            frequency_band=capabilities.basic_capabilities.frequency_bands,
            constraints=Constraints.combine(capabilities, defaults),
            subarrays=capabilities.subarrays,
            spfrx_defaults=defaults.spfrx_defaults,
        )


class LowConfiguration(ConfigurationModel):
    frequency_band: LowBasicCapabilities
    constraints: Constraints
    quality_attribute_metrics: LowQualityAttributeMetrics
    subarrays: list[LowCapabilitySet]

    @classmethod
    def combine(
        cls, capabilities: LowCapabilitiesFile, defaults: LowDefaultsFile
    ) -> Self:
        return cls(
            frequency_band=capabilities.basic_capabilities,
            constraints=Constraints.combine(capabilities, defaults),
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
                MidCapabilitiesFile.model_validate(read(MID_CONSTANT_JSON_FILE_PATH)),
                MidDefaultsFile.model_validate(read(MID_DEFAULTS_JSON_FILE_PATH)),
            ),
            ska_low=LowConfiguration.combine(
                LowCapabilitiesFile.model_validate(read(LOW_CONSTANT_JSON_FILE_PATH)),
                LowDefaultsFile.model_validate(read(LOW_DEFAULTS_JSON_FILE_PATH)),
            ),
            observatory_policies=[
                ObservatoryPolicy.model_validate(
                    read(f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{cycle}.json")
                )
                for cycle in sorted(get_available_cycles(tmdata))
            ],
        )
