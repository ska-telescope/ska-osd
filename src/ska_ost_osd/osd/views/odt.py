"""The ODT view: what ska-oso-services serves to the ODT from GET
/configuration. Its models are the reader models narrowed to the fields it
serves."""

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowBasicCapabilities,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.defaults import SPFRxParameters
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import ConfigurationModel


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


def get_configuration(repository: OSDRepository) -> Configuration:
    """Build the ODT configuration: what ska-oso-services serves from GET
    /configuration.

    :param repository: the OSD repository to read from.
    :return: both telescopes' bands, constraints, defaults and capability
        sets.
    """
    return Configuration(
        ska_mid=MidConfiguration(
            frequency_band=repository.get_basic_capabilities(
                Telescope.MID
            ).frequency_bands,
            constraints=repository.get_constraints(Telescope.MID),
            subarrays=[
                MidConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in repository.get_capability_sets(Telescope.MID)
            ],
            spfrx_defaults=repository.get_defaults(Telescope.MID).spfrx_defaults,
        ),
        ska_low=LowConfiguration(
            frequency_band=repository.get_basic_capabilities(Telescope.LOW),
            constraints=repository.get_constraints(Telescope.LOW),
            quality_attribute_metrics=ConfigurationLowQualityAttributeMetrics.model_validate(
                repository.get_defaults(Telescope.LOW).quality_attribute_metrics,
                from_attributes=True,
            ),
            subarrays=[
                LowConfigurationCapabilitySet.model_validate(
                    capability_set, from_attributes=True
                )
                for capability_set in repository.get_capability_sets(Telescope.LOW)
            ],
        ),
    )
