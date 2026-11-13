"""The ODT view: what ska-oso-services serves to the ODT from GET
/configuration. Its models are the reader models narrowed to the fields it
serves."""

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowCapabilities,
    MidCapabilities,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.constraints import Constraints
from ska_ost_osd.osd.models.defaults import SPFRxParameters
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import (
    ConfigurationModel,
    LowFrequencyBandWithChannels,
    low_frequency_band,
)


class MidConfigurationCapabilities(ConfigurationModel):
    name: str
    receptors: list[str | int]
    available_bandwidth_hz: float
    number_pst_beams: int
    number_fsps: int
    allowed_channel_width_values_hz: list[int]


class LowConfigurationCapabilities(ConfigurationModel):
    name: str
    receptors: list[str | int]
    available_bandwidth_hz: float
    number_pst_beams: int
    number_fsps: int
    number_substations: int
    number_subarray_beams: int


class ConfigurationLowCBFMetrics(ConfigurationModel):
    processors_ready_percent: float


class ConfigurationLowQualityAttributeMetrics(ConfigurationModel):
    cbf: ConfigurationLowCBFMetrics


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidConfigurationCapabilities]
    spfrx_defaults: SPFRxParameters


class LowConfiguration(ConfigurationModel):
    frequency_band: LowFrequencyBandWithChannels
    constraints: Constraints
    quality_attribute_metrics: ConfigurationLowQualityAttributeMetrics
    subarrays: list[LowConfigurationCapabilities]


class Configuration(ConfigurationModel):
    """The ODT configuration: both telescopes' bands, constraints, defaults
    and capabilities."""

    ska_mid: MidConfiguration
    ska_low: LowConfiguration


def _mid_capabilities(
    capabilities: MidCapabilities,
) -> MidConfigurationCapabilities:
    return MidConfigurationCapabilities(
        name=capabilities.array_assembly,
        receptors=capabilities.receptors.ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.modes.pst.max_beams,
        number_fsps=capabilities.number_fsps,
        allowed_channel_width_values_hz=capabilities.allowed_channel_width_values_hz,
    )


def _low_capabilities(
    capabilities: LowCapabilities,
) -> LowConfigurationCapabilities:
    return LowConfigurationCapabilities(
        name=capabilities.array_assembly,
        receptors=capabilities.receptors.ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.modes.pst.max_beams,
        number_fsps=capabilities.number_fsps,
        number_substations=(
            capabilities.subarray_beams.max_substations_per_subarray_beam
        ),
        number_subarray_beams=capabilities.subarray_beams.max_subarray_beams,
    )


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
                Telescope.SKA_MID
            ).frequency_bands,
            constraints=repository.get_constraints(Telescope.SKA_MID),
            subarrays=[
                _mid_capabilities(capabilities)
                for capabilities in repository.get_array_assembly_capabilities(
                    Telescope.SKA_MID
                )
            ],
            spfrx_defaults=repository.get_defaults(Telescope.SKA_MID).spfrx_defaults,
        ),
        ska_low=LowConfiguration(
            frequency_band=low_frequency_band(repository),
            constraints=repository.get_constraints(Telescope.SKA_LOW),
            quality_attribute_metrics=ConfigurationLowQualityAttributeMetrics.model_validate(
                repository.get_defaults(Telescope.SKA_LOW).quality_attribute_metrics,
                from_attributes=True,
            ),
            subarrays=[
                _low_capabilities(capabilities)
                for capabilities in repository.get_array_assembly_capabilities(
                    Telescope.SKA_LOW
                )
            ],
        ),
    )
