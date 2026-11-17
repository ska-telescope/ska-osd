from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import AliasChoices, Field, computed_field, model_validator

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


class MidBasicCBF(OSDBaseModel):
    """What Mid's correlator-beamformer (CBF) is designed to provide.
    tmdata: ``basic_capabilities.cbf``."""

    frequency_slice_bandwidth_hz: int = Field(gt=0, examples=[198180864])
    fine_channel_width_hz: int = Field(gt=0, examples=[13440])


class MidBasicCapabilities(OSDBaseModel):
    """Mid's receiver bands, elevation limits and the bandwidth of the
    frequency slices its FSPs each process. tmdata: ``basic_capabilities``."""

    telescope: Literal[Telescope.SKA_MID]
    frequency_bands: list[MidFrequencyBand]
    elevation_limits: ElevationLimits
    cbf: MidBasicCBF

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


class MidArrayAssemblyContinuumMode(OSDBaseModel):
    """What a Mid array assembly offers for continuum observations: the
    factors it can average its unzoomed fine channels by."""

    channel_averaging_factors: list[Annotated[int, Field(ge=1)]] = Field(
        examples=[[1, 2, 3, 4]]
    )


class MidArrayAssemblySpectralMode(OSDBaseModel):
    """The zoom windows a Mid array assembly offers for spectral line
    observations. ``max_zoom_channels`` is the most channels in one window,
    and zoom factor *z* divides the fine channel width by 2**z."""

    max_zoom_windows: int = Field(ge=0, examples=[16])
    max_zoom_channels: int = Field(ge=0, examples=[14880])
    zoom_factors: list[int] = Field(examples=[[1, 2, 3, 4, 5, 6]])


class MidArrayAssemblyPSSMode(OSDBaseModel):
    """The pulsar search beams a Mid array assembly offers."""

    max_beams: int = Field(ge=0, examples=[384])
    beam_bandwidth_hz: float = Field(ge=0, examples=[400e6])


class MidArrayAssemblyPSTMode(OSDBaseModel):
    """The pulsar timing beams a Mid array assembly offers."""

    max_beams: int = Field(ge=0, examples=[6])


class MidArrayAssemblyObservingModes(OSDBaseModel):
    """What a Mid array assembly offers in each observing mode."""

    continuum: MidArrayAssemblyContinuumMode
    spectral: MidArrayAssemblySpectralMode
    pss: MidArrayAssemblyPSSMode
    pst: MidArrayAssemblyPSTMode


class MidArrayAssemblyCBF(OSDBaseModel):
    """What a Mid array assembly's correlator-beamformer (CBF) offers.
    ``max_channels`` is the most correlated channels over all spectral
    windows, or ``None`` if the OSD sets no limit."""

    number_fsps: int = Field(ge=0, examples=[26])
    function_modes: list[MidCBFMode]
    max_channels: Annotated[int, Field(ge=1)] | None = Field(examples=[58982])


class MidCBF(OSDBaseModel):
    """Mid's correlator-beamformer (CBF): the bandwidth of each frequency
    slice, the width of the fine channels the FSPs divide them into, how many
    frequency slice processors (FSPs) there are, the function modes it runs,
    and the most correlated channels over all spectral windows (``None`` if
    the OSD sets no limit)."""

    frequency_slice_bandwidth_hz: int = Field(gt=0, examples=[198180864])
    fine_channel_width_hz: int = Field(gt=0, examples=[13440])
    number_fsps: int = Field(ge=0, examples=[26])
    function_modes: list[MidCBFMode]
    max_channels: Annotated[int, Field(ge=1)] | None = Field(examples=[58982])


class MidArrayAssemblyReceptors(OSDBaseModel):
    """The dishes a Mid array assembly is made of, by ID: SKA dishes
    (``SKA…``) and MeerKAT dishes (``MKT…``)."""

    number_ska_dishes: int = Field(ge=0, examples=[64])
    number_meerkat_dishes: int = Field(ge=0, examples=[4])
    number_meerkatplus_dishes: int = Field(ge=0, examples=[0])
    max_baseline_km: float = Field(gt=0, examples=[110.0])
    receptor_ids: list[str] = Field(examples=[["SKA001", "SKA036"]])

    @model_validator(mode="after")
    def check_number_ska_dishes(self) -> Self:
        ska_ids = [dish for dish in self.receptor_ids if dish.startswith("SKA")]
        if self.number_ska_dishes != len(ska_ids):
            raise ValueError(
                f"number_ska_dishes ({self.number_ska_dishes}) does not match the "
                f"number of SKA dishes in receptor_ids ({len(ska_ids)})"
            )
        return self


class MidContinuumMode(OSDBaseModel):
    """What Mid offers for continuum observations: the factors it can average
    its unzoomed fine channels by."""

    channel_averaging_factors: list[Annotated[int, Field(ge=1)]] = Field(
        examples=[[1, 2, 3, 4]]
    )


class MidSpectralMode(OSDBaseModel):
    """What Mid offers for spectral line observations: its zoom windows.
    ``max_zoom_channels`` is the most channels in one window, and zoom factor
    *z* divides the fine channel width by 2**z."""

    max_zoom_windows: int = Field(ge=0, examples=[16])
    max_zoom_channels: int = Field(ge=0, examples=[14880])
    zoom_factors: list[int] = Field(examples=[[1, 2, 3, 4, 5, 6]])


class MidPSSMode(OSDBaseModel):
    """What Mid offers for pulsar search: its beams."""

    max_beams: int = Field(ge=0, examples=[384])
    beam_bandwidth_hz: float = Field(ge=0, examples=[400e6])


class MidPSTMode(OSDBaseModel):
    """What Mid offers for pulsar timing: its beams."""

    max_beams: int = Field(ge=0, examples=[6])


class MidObservingModes(OSDBaseModel):
    """What Mid offers in each observing mode."""

    continuum: MidContinuumMode
    spectral: MidSpectralMode
    pss: MidPSSMode
    pst: MidPSTMode


def mid_channel_width_values_hz(
    fine_channel_width_hz: int,
    zoom_factors: list[int],
    channel_averaging_factors: list[int],
) -> list[int]:
    """The channel widths a Mid spectral window can have, in ascending order.

    :param fine_channel_width_hz: the width of Mid's unzoomed fine channels.
    :param zoom_factors: the zoom factors offered; zoom factor *z* divides the
        fine channel width by 2**z.
    :param channel_averaging_factors: the factors the unzoomed fine channels
        can be averaged by.
    :return: the widths, each once.
    """
    return sorted(
        {fine_channel_width_hz // 2**zoom for zoom in zoom_factors}
        | {fine_channel_width_hz * factor for factor in channel_averaging_factors}
    )


class MidCapabilities(OSDBaseModel):
    """Everything Mid offers: its basic capabilities, an array assembly's
    capabilities, and a policy's changes to them if one applies."""

    telescope: Literal[Telescope.SKA_MID]
    array_assembly: str = Field(examples=["AA2"])
    policy: str | None = Field(default=None, examples=["AA2_SV"])
    frequency_bands: list[MidFrequencyBand]
    elevation_limits: ElevationLimits
    cbf: MidCBF
    available_bandwidth_hz: float = Field(gt=0)
    observing_modes: MidObservingModes
    receivers: list[str] = Field(examples=[["Band_1", "Band_2"]])
    receptors: MidArrayAssemblyReceptors

    @computed_field
    @property
    def allowed_channel_width_values_hz(self) -> list[int]:
        """Every channel width a spectral window can have, in ascending
        order: the fine channel width divided by 2**z for each zoom factor,
        or multiplied by each averaging factor. Averaging only applies to
        unzoomed channels."""
        return mid_channel_width_values_hz(
            self.cbf.fine_channel_width_hz,
            self.observing_modes.spectral.zoom_factors,
            self.observing_modes.continuum.channel_averaging_factors,
        )

    @model_validator(mode="after")
    def check_function_modes(self) -> Self:
        for cbf_mode, mode in (
            (MidCBFMode.PSS, self.observing_modes.pss),
            (MidCBFMode.PST, self.observing_modes.pst),
        ):
            if (cbf_mode in self.cbf.function_modes) != (mode.max_beams > 0):
                raise ValueError(
                    f"{self.policy or self.array_assembly}: "
                    f"cbf.function_modes must list {cbf_mode} exactly when "
                    f"observing_modes.{cbf_mode}.max_beams is above 0"
                )
        return self

    @model_validator(mode="after")
    def check_receivers(self) -> Self:
        unknown = set(self.receivers) - {band.rx_id for band in self.frequency_bands}
        if unknown:
            raise ValueError(
                f"{self.policy or self.array_assembly}: "
                f"receivers {sorted(unknown)} not found in frequency_bands"
            )
        return self


class LowCBFMode(StrEnum):
    VIS = "vis"
    PST = "pst"
    PSS = "pss"


class CoarseChannels(OSDBaseModel):
    """The coarse channels Low's stations divide the band into. ``min`` and
    ``max`` are the lowest and highest coarse channel numbers, not counts.
    tmdata: ``basic_capabilities.sps.coarse_channels``."""

    min: int = Field(ge=0, examples=[64])
    max: int = Field(ge=0, examples=[447])
    width_hz: float = Field(gt=0, examples=[781.25e3])


class LowBasicSPS(OSDBaseModel):
    """What Low's station signal processing (SPS) is designed to provide.
    tmdata: ``basic_capabilities.sps``."""

    coarse_channels: CoarseChannels


class LowBasicContinuumMode(OSDBaseModel):
    """How Low's continuum mode divides each coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[144])


class LowBasicSpectralMode(OSDBaseModel):
    """How Low's spectral line mode divides each coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[432])


class LowBasicPSSMode(OSDBaseModel):
    """How Low's pulsar search mode divides each coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[54])


class LowBasicPSTMode(OSDBaseModel):
    """How Low's pulsar timing mode divides each coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[216])


class LowBasicObservingModes(OSDBaseModel):
    """Low's observing modes. tmdata: ``basic_capabilities.observing_modes``."""

    continuum: LowBasicContinuumMode
    spectral: LowBasicSpectralMode
    pss: LowBasicPSSMode
    pst: LowBasicPSTMode


class LowBasicCapabilities(OSDBaseModel):
    """Low's frequency band, elevation limits, coarse channels and observing modes.
    tmdata: ``basic_capabilities``."""

    telescope: Literal[Telescope.SKA_LOW]
    frequency_band: FrequencyBand
    elevation_limits: ElevationLimits
    sps: LowBasicSPS
    observing_modes: LowBasicObservingModes


class LowArrayAssemblySpectralMode(OSDBaseModel):
    """The zoom windows a Low array assembly offers for spectral line
    observations. ``max_zoom_channels`` is the most channels in one window."""

    max_zoom_windows: int = Field(ge=0, examples=[16])
    max_zoom_channels: int = Field(ge=0, examples=[1800])
    zoom_factors: list[int] = Field(examples=[[1, 2, 4, 8]])


class LowArrayAssemblyPSSMode(OSDBaseModel):
    """The pulsar search beams a Low array assembly offers."""

    max_beams: int = Field(ge=0, examples=[30])
    beam_bandwidth_hz: float = Field(ge=0, examples=[118e6])


class LowArrayAssemblyPSTMode(OSDBaseModel):
    """The pulsar timing beams a Low array assembly offers."""

    max_beams: int = Field(ge=0, examples=[4])


class LowArrayAssemblyVLBIMode(OSDBaseModel):
    """The VLBI beams a Low array assembly offers."""

    max_beams: int = Field(ge=0, examples=[0])


class LowArrayAssemblyObservingModes(OSDBaseModel):
    """What a Low array assembly offers in each observing mode."""

    spectral: LowArrayAssemblySpectralMode
    pss: LowArrayAssemblyPSSMode
    pst: LowArrayAssemblyPSTMode
    vlbi: LowArrayAssemblyVLBIMode


class LowArrayAssemblySubarrayBeams(OSDBaseModel):
    """The subarray beams a Low array assembly offers. Each subarray beam is
    formed from substations: whole stations (substation 0) or parts of
    stations."""

    max_subarray_beams: int = Field(ge=0, examples=[8])
    max_substations_per_subarray_beam: int = Field(ge=0, examples=[720])


class LowArrayAssemblyCBF(OSDBaseModel):
    """What a Low array assembly's correlator-beamformer (CBF) offers."""

    number_fsps: int = Field(ge=0, examples=[10])
    function_modes: list[LowCBFMode]


class LowArrayAssemblySPS(OSDBaseModel):
    """What a Low array assembly's station signal processing (SPS) offers."""

    subarray_beams: LowArrayAssemblySubarrayBeams


class LowSPS(OSDBaseModel):
    """Low's station signal processing (SPS): the coarse channels its
    stations make, and the subarray beams they form. MCCS configures it."""

    coarse_channels: CoarseChannels
    subarray_beams: LowArrayAssemblySubarrayBeams


class LowArrayAssemblyReceptors(OSDBaseModel):
    """The stations a Low array assembly is made of, by ID."""

    number_stations: int = Field(ge=0, examples=[68])
    max_baseline_km: float = Field(gt=0, examples=[40.0])
    receptor_ids: list[int] = Field(examples=[[345, 350]])

    @model_validator(mode="after")
    def check_number_stations(self) -> Self:
        if self.number_stations != len(self.receptor_ids):
            raise ValueError(
                f"number_stations ({self.number_stations}) does not match the "
                f"number of receptor_ids ({len(self.receptor_ids)})"
            )
        return self


class LowContinuumMode(OSDBaseModel):
    """What Low offers for continuum observations: how it divides each
    coarse channel."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[144])


class LowSpectralMode(OSDBaseModel):
    """What Low offers for spectral line observations: how it divides each
    coarse channel, and its zoom windows. ``max_zoom_channels`` is the most
    channels in one window."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[432])
    max_zoom_windows: int = Field(ge=0, examples=[16])
    max_zoom_channels: int = Field(ge=0, examples=[1800])
    zoom_factors: list[int] = Field(examples=[[1, 2, 4, 8]])


class LowPSSMode(OSDBaseModel):
    """What Low offers for pulsar search: how it divides each coarse
    channel, and its beams."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[54])
    max_beams: int = Field(ge=0, examples=[30])
    beam_bandwidth_hz: float = Field(ge=0, examples=[118e6])


class LowPSTMode(OSDBaseModel):
    """What Low offers for pulsar timing: how it divides each coarse
    channel, and its beams."""

    channels_per_coarse_channel: int = Field(ge=0, examples=[216])
    max_beams: int = Field(ge=0, examples=[4])


class LowVLBIMode(OSDBaseModel):
    """What Low offers for VLBI: its beams."""

    max_beams: int = Field(ge=0, examples=[0])


class LowObservingModes(OSDBaseModel):
    """What Low offers in each observing mode."""

    continuum: LowContinuumMode
    spectral: LowSpectralMode
    pss: LowPSSMode
    pst: LowPSTMode
    vlbi: LowVLBIMode


class LowCapabilities(OSDBaseModel):
    """Everything Low offers: its basic capabilities, an array assembly's
    capabilities, and a policy's changes to them if one applies."""

    telescope: Literal[Telescope.SKA_LOW]
    array_assembly: str = Field(examples=["AA2"])
    policy: str | None = Field(default=None, examples=["AA2_SV"])
    frequency_band: FrequencyBand
    elevation_limits: ElevationLimits
    sps: LowSPS
    available_bandwidth_hz: float = Field(gt=0)
    cbf: LowArrayAssemblyCBF
    observing_modes: LowObservingModes
    receptors: LowArrayAssemblyReceptors

    @model_validator(mode="after")
    def check_function_modes(self) -> Self:
        # vis isn't checked against observing_modes.spectral: some array assemblies list
        # vis but offer no zoom windows
        for cbf_mode, mode in (
            (LowCBFMode.PSS, self.observing_modes.pss),
            (LowCBFMode.PST, self.observing_modes.pst),
        ):
            if (cbf_mode in self.cbf.function_modes) != (mode.max_beams > 0):
                raise ValueError(
                    f"{self.policy or self.array_assembly}: cbf.function_modes must list "
                    f"{cbf_mode} exactly "
                    f"when observing_modes.{cbf_mode}.max_beams is above 0"
                )
        return self


def merge_capabilities(
    basic: dict[str, Any],
    array_assembly: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything a telescope offers: the array assembly's capabilities with
    the policy's changes applied, combined with the basic capabilities.

    :raises ValueError: If the basic capabilities and the array assembly, or
        the policy, set the same field. Basic capabilities can't be changed.
    """
    return _combine(basic, _apply(array_assembly, policy or {}))


def _apply(capabilities: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    """The capabilities with each field the changes set replaced, groups field
    by field."""
    applied = dict(capabilities)
    for field, value in changes.items():
        applied[field] = (
            _apply(applied[field], value)
            if isinstance(value, dict) and isinstance(applied.get(field), dict)
            else value
        )
    return applied


def _combine(
    basic: dict[str, Any], offered: dict[str, Any], path: str = ""
) -> dict[str, Any]:
    """The basic capabilities with the offered ones added. A group in both
    is combined field by field; any other field in both is an error."""
    combined = dict(basic)
    for field, value in offered.items():
        if field not in combined:
            combined[field] = value
        elif isinstance(value, dict) and isinstance(combined[field], dict):
            combined[field] = _combine(combined[field], value, f"{path}{field}.")
        else:
            raise ValueError(
                f"{path}{field} is set by both the basic capabilities and the "
                "array assembly or policy"
            )
    return combined


# Either telescope's capabilities; the telescope field picks the model when
# they are read back.
Capabilities = Annotated[
    MidCapabilities | LowCapabilities, Field(discriminator="telescope")
]
