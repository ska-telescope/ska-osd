from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AliasChoices, Field, model_validator

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    Band5bSubbandNotFoundError,
    FrequencyBandNotFoundError,
)
from ska_ost_osd.osd.models.constraints import ElevationLimits
from ska_ost_osd.osd.models.defaults import OSDBaseModel


class FrequencyBand(OSDBaseModel):
    max_frequency_hz: float = Field(gt=0)
    min_frequency_hz: float = Field(gt=0)

    @model_validator(mode="after")
    def check_frequency_range(self) -> Self:
        if self.min_frequency_hz > self.max_frequency_hz:
            raise ValueError("min_frequency_hz must not exceed max_frequency_hz")
        return self


class CapabilitySetBase(OSDBaseModel):
    name: str = Field(examples=["AA0.5"])
    receptors: list[str | int] = Field(
        validation_alias=AliasChoices(
            "receptors", "stations", "dishes", "number_dish_ids", "number_station_ids"
        ),
        examples=[["SKA001", "SKA036"], [345, 350]],
    )
    available_bandwidth_hz: float = Field(gt=0)
    number_fsps: int = Field(ge=0)
    max_baseline_km: float = Field(gt=0)
    ps_beam_bandwidth_hz: float = Field(ge=0)


class MidCBFMode(StrEnum):
    CORRELATION = "correlation"
    PST = "pst"
    PSS = "pss"


class Band5bSubband(FrequencyBand):
    sub_band: int = Field(ge=1, examples=[1])
    lo_frequency_hz: float = Field(gt=0, examples=[11.1e9])
    sideband: Literal["high", "low"]


class MidFrequencyBand(FrequencyBand):
    """One receiver band. tmdata: ``basic_capabilities.frequency_bands[]``."""

    rx_id: str = Field(examples=["Band_1"])
    band5b_subbands: list[Band5bSubband] | None = Field(
        default=None,
        validation_alias=AliasChoices("band5b_subbands", "sub_bands"),
    )

    def get_band5b_subband(self, sub_band: int) -> Band5bSubband:
        """Look up one of this band's Band 5b sub-bands by number.

        :param sub_band: the sub-band number, e.g. ``2``.
        :return: the sub-band.
        :raises Band5bSubbandNotFoundError: If this band has no sub-band
            with that number, including when it has no sub-bands at all.
        """
        subbands = self.band5b_subbands or []
        for subband in subbands:
            if subband.sub_band == sub_band:
                return subband
        raise Band5bSubbandNotFoundError(
            self.rx_id, sub_band, [subband.sub_band for subband in subbands]
        )


class MidBasicCapabilities(OSDBaseModel):
    """Mid's receiver bands and elevation limits. tmdata:
    ``basic_capabilities``."""

    frequency_bands: list[MidFrequencyBand]
    elevation_limits: ElevationLimits

    def get_frequency_band(self, rx_id: str) -> MidFrequencyBand:
        """Look up one receiver band by its ID.

        :param rx_id: the band ID, e.g. ``"Band_2"``.
        :return: the band.
        :raises FrequencyBandNotFoundError: If there is no band with that ID.
        """
        for band in self.frequency_bands:
            if band.rx_id == rx_id:
                return band
        raise FrequencyBandNotFoundError(
            rx_id, [band.rx_id for band in self.frequency_bands]
        )


class MidCapabilitySet(CapabilitySetBase):
    telescope: Literal[Telescope.SKA_MID] = Telescope.SKA_MID
    number_pst_beams: int = Field(ge=0)
    number_pss_beams: int = Field(ge=0)
    number_zoom_windows: int = Field(ge=0)
    number_zoom_channels: int = Field(ge=0)
    allowed_channel_width_values_hz: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_count_range_max: list[int]
    available_receivers: list[str] = Field(examples=[["Band_1", "Band_2"]])
    cbf_modes: list[MidCBFMode]
    number_ska_dishes: int = Field(ge=0)
    number_meerkat_dishes: int = Field(ge=0)
    number_meerkatplus_dishes: int = Field(ge=0)

    @model_validator(mode="after")
    def check_dish_count(self) -> Self:
        ska_dishes = [dish for dish in self.receptors if str(dish).startswith("SKA")]
        if self.number_ska_dishes != len(ska_dishes):
            raise ValueError(
                f"{self.name}: number_ska_dishes ({self.number_ska_dishes}) does "
                f"not match the number of SKA dishes ({len(ska_dishes)})"
            )
        return self


class LowCBFMode(StrEnum):
    VIS = "vis"
    PST = "pst"
    PSS = "pss"


class CoarseChannels(OSDBaseModel):
    """The coarse channels Low's station beamformer divides its band into.
    tmdata: ``basic_capabilities.coarse_channels``."""

    min: int = Field(ge=0, examples=[64])
    max: int = Field(ge=0, examples=[447])
    width_hz: float = Field(gt=0, examples=[781.25e3])


class LowMode(OSDBaseModel):
    """How one observing mode divides each coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[144])


class LowModes(OSDBaseModel):
    """Low's observing modes. tmdata: ``basic_capabilities.modes``."""

    continuum: LowMode
    spectral: LowMode
    pss: LowMode
    pst: LowMode


class LowBasicCapabilities(OSDBaseModel):
    """Low's frequency band, elevation limits, coarse channels and modes.
    tmdata: ``basic_capabilities``."""

    frequency_band: FrequencyBand
    elevation_limits: ElevationLimits
    coarse_channels: CoarseChannels
    modes: LowModes


class LowCapabilitySetSpectralMode(OSDBaseModel):
    """The zoom windows a Low capability set offers for spectral line
    observations. ``max_zoom_channels`` is the most channels in one window."""

    max_zoom_windows: int = Field(ge=0, examples=[16])
    max_zoom_channels: int = Field(ge=0, examples=[1800])
    zoom_factors: list[int] = Field(examples=[[1, 2, 4, 8]])


class LowCapabilitySetBeamformedMode(OSDBaseModel):
    """The beams a Low capability set offers in one beamformed mode."""

    max_beams: int = Field(ge=0, examples=[4])


class LowCapabilitySetModes(OSDBaseModel):
    """What a Low capability set offers in each observing mode."""

    spectral: LowCapabilitySetSpectralMode
    pss: LowCapabilitySetBeamformedMode
    pst: LowCapabilitySetBeamformedMode
    vlbi: LowCapabilitySetBeamformedMode


class LowStationBeamforming(OSDBaseModel):
    """The subarray beams a Low capability set offers. Each subarray beam is
    formed from substations: whole stations (substation 0) or parts of
    stations."""

    max_subarray_beams: int = Field(ge=0, examples=[8])
    max_substations_per_subarray_beam: int = Field(ge=0, examples=[720])


class LowCapabilitySet(CapabilitySetBase):
    telescope: Literal[Telescope.SKA_LOW] = Telescope.SKA_LOW
    station_beamforming: LowStationBeamforming
    number_stations: int = Field(ge=0)
    cbf_modes: list[LowCBFMode]
    modes: LowCapabilitySetModes

    @model_validator(mode="after")
    def check_station_count(self) -> Self:
        if self.number_stations != len(self.receptors):
            raise ValueError(
                f"{self.name}: number_stations ({self.number_stations}) does not "
                f"match the number of receptors ({len(self.receptors)})"
            )
        return self

    @model_validator(mode="after")
    def check_cbf_modes(self) -> Self:
        # vis isn't checked against modes.spectral: some capability sets list
        # vis but offer no zoom windows
        for cbf_mode, mode in (
            (LowCBFMode.PSS, self.modes.pss),
            (LowCBFMode.PST, self.modes.pst),
        ):
            if (cbf_mode in self.cbf_modes) != (mode.max_beams > 0):
                raise ValueError(
                    f"{self.name}: cbf_modes must list {cbf_mode} exactly "
                    f"when modes.{cbf_mode}.max_beams is above 0"
                )
        return self


# A capability set is one array assembly of either telescope; the
# telescope field picks the model when one is read back.
CapabilitySet = Annotated[
    MidCapabilitySet | LowCapabilitySet, Field(discriminator="telescope")
]
