"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import LowFrequencyBand
from ska_ost_osd.osd.models.defaults import OSDBaseModel
from ska_ost_osd.osd.repository import OSDRepository


class ConfigurationModel(OSDBaseModel):
    # serialize_by_alias: a view serialises with the names its consumer
    # reads (e.g. the PHT's Mid and Low) without the caller passing
    # by_alias=True
    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        validate_assignment=True,
        serialize_by_alias=True,
    )


class LowFrequencyBandWithCoarseChannels(LowFrequencyBand):
    """Low's band with its coarse channels, as the ODT and PHT read it."""

    min_coarse_channel: int
    max_coarse_channel: int
    coarse_channel_width_hz: float


def low_frequency_band(repository: OSDRepository) -> LowFrequencyBandWithCoarseChannels:
    """Low's one frequency band, with its coarse channels."""
    basic_capabilities = repository.get_basic_capabilities(Telescope.SKA_LOW)
    (band,) = basic_capabilities.frequency_bands
    coarse_channels = basic_capabilities.coarse_channels
    return LowFrequencyBandWithCoarseChannels(
        **band.model_dump(),
        min_coarse_channel=coarse_channels.min,
        max_coarse_channel=coarse_channels.max,
        coarse_channel_width_hz=coarse_channels.width_hz,
    )
