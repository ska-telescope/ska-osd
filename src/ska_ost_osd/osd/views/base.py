"""The base of the view models."""

from pydantic import ConfigDict

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import FrequencyBand
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


class LowFrequencyBandWithChannels(FrequencyBand):
    """Low's band with its coarse channels and the channels each mode divides
    them into, as the ODT and PHT read it."""

    min_coarse_channel: int
    max_coarse_channel: int
    coarse_channel_width_hz: float
    number_continuum_channels_per_coarse_channel: int
    number_zoom_channels_per_coarse_channel: int
    number_pst_channels_per_coarse_channel: int
    number_pss_channels_per_coarse_channel: int


def low_frequency_band(repository: OSDRepository) -> LowFrequencyBandWithChannels:
    """Low's one frequency band, with its channels."""
    basic_capabilities = repository.get_basic_capabilities(Telescope.SKA_LOW)
    (band,) = basic_capabilities.frequency_bands
    coarse_channels = basic_capabilities.coarse_channels
    modes = basic_capabilities.modes
    return LowFrequencyBandWithChannels(
        **band.model_dump(),
        min_coarse_channel=coarse_channels.min,
        max_coarse_channel=coarse_channels.max,
        coarse_channel_width_hz=coarse_channels.width_hz,
        number_continuum_channels_per_coarse_channel=(
            modes.continuum.channels_per_coarse_channel
        ),
        number_zoom_channels_per_coarse_channel=modes.zoom.channels_per_coarse_channel,
        number_pst_channels_per_coarse_channel=modes.pst.channels_per_coarse_channel,
        number_pss_channels_per_coarse_channel=modes.pss.channels_per_coarse_channel,
    )
