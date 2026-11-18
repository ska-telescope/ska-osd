"""The ODT view: what ska-oso-services serves to the ODT from GET
/configuration. Its models are its own, named and shaped as ska-oso-services'
response models, so the response doesn't change with the domain models."""

from enum import StrEnum

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import LowCapabilities, MidCapabilities
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import ConfigurationModel


class Band5bSubband(ConfigurationModel):
    sub_band: int
    max_frequency_hz: float
    min_frequency_hz: float
    lo_frequency_hz: float
    sideband: str


class FrequencyBand(ConfigurationModel):
    max_frequency_hz: float
    min_frequency_hz: float


class MidFrequencyBand(FrequencyBand):
    rx_id: str
    band5b_subbands: list[Band5bSubband] | None = None


class LowFrequencyBand(FrequencyBand):
    """Low's band with its coarse channels and the channels each mode divides
    them into."""

    min_coarse_channel: int
    max_coarse_channel: int
    coarse_channel_width_hz: float
    number_continuum_channels_per_coarse_channel: int
    number_zoom_channels_per_coarse_channel: int
    number_pst_channels_per_coarse_channel: int
    number_pss_channels_per_coarse_channel: int


class Constraints(ConfigurationModel):
    sun_avoidance_angle_deg: float
    moon_avoidance_angle_deg: float
    jupiter_avoidance_angle_deg: float
    min_elevation_deg: float
    max_elevation_deg: float


class Subarray(ConfigurationModel):
    name: str
    receptors: list[str | int]
    available_bandwidth_hz: float
    number_pst_beams: int
    number_fsps: int


class MidSubarray(Subarray):
    allowed_channel_width_values_hz: list[int]


class LowSubarray(Subarray):
    number_substations: int
    number_subarray_beams: int


class PeriodicNoiseDiode(ConfigurationModel):
    mode: str = "periodic"
    period_ms: float
    duty_cycle_ms: float
    phase_shift_ms: float


class PseudoRandomNoiseDiode(ConfigurationModel):
    mode: str = "pseudo_random"
    binary_polynomial: int
    seed: int
    dwell_ms: float


class TargetSPFRx(ConfigurationModel):
    attenuation_1_x: float | None = None
    attenuation_1_y: float | None = None
    attenuation_2_x: float | None = None
    attenuation_2_y: float | None = None
    noise_diode_options: list[PeriodicNoiseDiode | PseudoRandomNoiseDiode]
    default_noise_diode_mode: str


class SyncPPS(StrEnum):
    UNSET = "unset"
    ON = "on"
    OFF = "off"


class CSPSPFRx(ConfigurationModel):
    sync_pps: SyncPPS
    saturation_threshold: float


class SPFRxParameters(ConfigurationModel):
    target_spfrx: TargetSPFRx
    csp_spfrx: CSPSPFRx


class LowCBFMetrics(ConfigurationModel):
    processors_ready_percent: float


class LowQualityAttributeMetrics(ConfigurationModel):
    cbf: LowCBFMetrics


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidSubarray]
    spfrx_defaults: SPFRxParameters


class LowConfiguration(ConfigurationModel):
    frequency_band: LowFrequencyBand
    constraints: Constraints
    quality_attribute_metrics: LowQualityAttributeMetrics
    subarrays: list[LowSubarray]


class Configuration(ConfigurationModel):
    """The ODT configuration: both telescopes' bands, constraints, defaults
    and capabilities."""

    ska_mid: MidConfiguration
    ska_low: LowConfiguration


def _low_frequency_band(repository: OSDRepository) -> LowFrequencyBand:
    """Low's one frequency band, with its channels."""
    basic_capabilities = repository.get_basic_capabilities(Telescope.SKA_LOW)
    coarse_channels = basic_capabilities.sps.coarse_channels
    observing_modes = basic_capabilities.observing_modes
    return LowFrequencyBand(
        max_frequency_hz=basic_capabilities.frequency_band.max_frequency_hz,
        min_frequency_hz=basic_capabilities.frequency_band.min_frequency_hz,
        min_coarse_channel=coarse_channels.min,
        max_coarse_channel=coarse_channels.max,
        coarse_channel_width_hz=coarse_channels.width_hz,
        number_continuum_channels_per_coarse_channel=(
            observing_modes.continuum.channels_per_coarse_channel
        ),
        number_zoom_channels_per_coarse_channel=observing_modes.spectral.channels_per_coarse_channel,
        number_pst_channels_per_coarse_channel=observing_modes.pst.channels_per_coarse_channel,
        number_pss_channels_per_coarse_channel=observing_modes.pss.channels_per_coarse_channel,
    )


def _mid_capabilities(
    capabilities: MidCapabilities,
) -> MidSubarray:
    return MidSubarray(
        name=capabilities.array_assembly,
        receptors=capabilities.receptors.receptor_ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.observing_modes.pst.max_beams,
        number_fsps=capabilities.cbf.number_fsps,
        allowed_channel_width_values_hz=capabilities.allowed_channel_width_values_hz,
    )


def _low_capabilities(
    capabilities: LowCapabilities,
) -> LowSubarray:
    return LowSubarray(
        name=capabilities.array_assembly,
        receptors=capabilities.receptors.receptor_ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.observing_modes.pst.max_beams,
        number_fsps=capabilities.cbf.number_fsps,
        number_substations=(
            capabilities.sps.subarray_beams.max_substations_per_subarray_beam
        ),
        number_subarray_beams=capabilities.sps.subarray_beams.max_subarray_beams,
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
            frequency_band=[
                MidFrequencyBand.model_validate(band, from_attributes=True)
                for band in repository.get_basic_capabilities(
                    Telescope.SKA_MID
                ).frequency_bands
            ],
            constraints=Constraints.model_validate(
                repository.get_constraints(Telescope.SKA_MID), from_attributes=True
            ),
            subarrays=[
                _mid_capabilities(capabilities)
                for capabilities in repository.get_array_assembly_capabilities(
                    Telescope.SKA_MID
                )
            ],
            spfrx_defaults=SPFRxParameters.model_validate(
                repository.get_defaults(Telescope.SKA_MID).spfrx_defaults,
                from_attributes=True,
            ),
        ),
        ska_low=LowConfiguration(
            frequency_band=_low_frequency_band(repository),
            constraints=Constraints.model_validate(
                repository.get_constraints(Telescope.SKA_LOW), from_attributes=True
            ),
            quality_attribute_metrics=LowQualityAttributeMetrics.model_validate(
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
