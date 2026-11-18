"""The ODT view: what ska-oso-services serves to the ODT from GET
/configuration. Its models are its own, named and shaped as ska-oso-services'
response models, so the response doesn't change with the domain models."""

from enum import StrEnum
from typing import Literal, overload

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowCapabilities,
    MidBasicCapabilities,
    MidCapabilities,
)
from ska_ost_osd.osd.models.defaults import MidDefaults
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


def _mid_capabilities(capabilities: MidCapabilities) -> MidSubarray:
    return MidSubarray(
        name=capabilities.policy or capabilities.array_assembly,
        receptors=capabilities.receptors.receptor_ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.observing_modes.pst.max_beams,
        number_fsps=capabilities.cbf.number_fsps,
        allowed_channel_width_values_hz=capabilities.allowed_channel_width_values_hz,
    )


def _low_capabilities(capabilities: LowCapabilities) -> LowSubarray:
    return LowSubarray(
        name=capabilities.policy or capabilities.array_assembly,
        receptors=capabilities.receptors.receptor_ids,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        number_pst_beams=capabilities.observing_modes.pst.max_beams,
        number_fsps=capabilities.cbf.number_fsps,
        number_substations=(
            capabilities.sps.subarray_beams.max_substations_per_subarray_beam
        ),
        number_subarray_beams=capabilities.sps.subarray_beams.max_subarray_beams,
    )


@overload
def get_basic_capabilities(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_MID]
) -> list[MidFrequencyBand]: ...


@overload
def get_basic_capabilities(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_LOW]
) -> LowFrequencyBand: ...


def get_basic_capabilities(
    repository: OSDRepository, telescope: Telescope
) -> list[MidFrequencyBand] | LowFrequencyBand:
    """A telescope's basic capabilities, as the ODT reads them: Mid's receiver
    bands, or Low's band with its coarse channels and the channels each mode
    divides them into.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :return: Mid's frequency bands, or Low's frequency band.
    """
    basic_capabilities = repository.get_basic_capabilities(telescope)
    if isinstance(basic_capabilities, MidBasicCapabilities):
        return [
            MidFrequencyBand.model_validate(band, from_attributes=True)
            for band in basic_capabilities.frequency_bands
        ]
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


def get_constraints(repository: OSDRepository, telescope: Telescope) -> Constraints:
    """A telescope's elevation limits and sun, moon and Jupiter avoidance
    angles.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :return: the telescope's constraints.
    """
    return Constraints.model_validate(
        repository.get_constraints(telescope), from_attributes=True
    )


@overload
def get_defaults(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_MID]
) -> SPFRxParameters: ...


@overload
def get_defaults(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_LOW]
) -> LowQualityAttributeMetrics: ...


def get_defaults(
    repository: OSDRepository, telescope: Telescope
) -> SPFRxParameters | LowQualityAttributeMetrics:
    """A telescope's defaults, as the ODT reads them.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :return: Mid's SPFRx defaults, or Low's quality attribute metrics.
    """
    defaults = repository.get_defaults(telescope)
    if isinstance(defaults, MidDefaults):
        return SPFRxParameters.model_validate(
            defaults.spfrx_defaults, from_attributes=True
        )
    return LowQualityAttributeMetrics.model_validate(
        defaults.quality_attribute_metrics, from_attributes=True
    )


@overload
def get_capabilities(
    repository: OSDRepository,
    telescope: Literal[Telescope.SKA_MID],
    array_assembly: str,
    policy_id: str | None = None,
) -> MidSubarray: ...


@overload
def get_capabilities(
    repository: OSDRepository,
    telescope: Literal[Telescope.SKA_LOW],
    array_assembly: str,
    policy_id: str | None = None,
) -> LowSubarray: ...


def get_capabilities(
    repository: OSDRepository,
    telescope: Telescope,
    array_assembly: str,
    policy_id: str | None = None,
) -> MidSubarray | LowSubarray:
    """An array assembly's capabilities, with a policy's applied if one is
    given, as the ODT reads them.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :param array_assembly: the array assembly, e.g. ``"AA2"``.
    :param policy_id: the ID of a policy to apply, e.g. ``"AA2_SV"``.
    :return: the capabilities, named after the policy, or else the array
        assembly.
    :raises ArrayAssemblyNotFoundError: If there is no such array assembly.
    :raises PolicyNotFoundError: If there is no such policy.
    """
    capabilities = repository.get_capabilities(telescope, array_assembly, policy_id)
    if isinstance(capabilities, MidCapabilities):
        return _mid_capabilities(capabilities)
    return _low_capabilities(capabilities)
