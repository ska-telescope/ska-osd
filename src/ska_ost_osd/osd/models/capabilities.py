import re
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import AliasChoices, Field, model_validator

from ska_ost_osd.osd.common.constant import ARRAY_ASSEMBLY_PATTERN, Telescope
from ska_ost_osd.osd.exceptions import (
    Band5bSubbandNotFoundError,
    FrequencyBandNotFoundError,
)
from ska_ost_osd.osd.models.defaults import OSDBaseModel


class ElevationConstraints(OSDBaseModel):
    min_elevation_deg: float = Field(ge=0, le=90, examples=[45.0])
    max_elevation_deg: float = Field(ge=0, le=90, examples=[90.0])

    @model_validator(mode="after")
    def check_elevation_range(self) -> Self:
        if self.min_elevation_deg > self.max_elevation_deg:
            raise ValueError("min_elevation_deg must not exceed max_elevation_deg")
        return self


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
            "receptors", "number_dish_ids", "number_station_ids"
        ),
        examples=[["SKA001", "SKA036"], [345, 350]],
    )
    available_bandwidth_hz: float = Field(gt=0)
    number_pst_beams: int = Field(ge=0)
    number_fsps: int = Field(ge=0)
    max_baseline_km: float = Field(gt=0)
    number_zoom_windows: int = Field(ge=0)
    number_zoom_channels: int = Field(ge=0)
    number_pss_beams: int = Field(ge=0)
    ps_beam_bandwidth_hz: float = Field(ge=0)
    # Name patterns in tmdata, e.g. ["*_AA2"]; when the OSD processes
    # templates, the matching templates keyed by name. The *_ITF assemblies
    # have none.
    subarray_templates: list[str] | dict[str, Any] | None = None


class TelescopeCapabilitiesFileBase(OSDBaseModel):
    """Base for the Mid and Low capabilities file models."""

    constraints: ElevationConstraints

    @model_validator(mode="before")
    @classmethod
    def collect_subarrays(cls, data: Any) -> Any:
        """
        In the tmdata file each array assembly is a top-level key;
        gather the keys matching ``ARRAY_ASSEMBLY_PATTERN`` into
        ``subarrays``, using the key as the subarray name.

        The pattern separates the array assemblies from the file's other
        top-level keys.
        """
        if not isinstance(data, dict) or "subarrays" in data:
            return data
        data = data.copy()
        data["subarrays"] = [
            {"name": key, **data.pop(key)}
            for key in list(data)
            if re.match(ARRAY_ASSEMBLY_PATTERN, key)
        ]
        return data


class MidCBFMode(StrEnum):
    CORRELATION = "correlation"
    PST = "pst"
    PSS = "pss"


class Band5bSubband(FrequencyBand):
    sub_band: int = Field(ge=1, examples=[1])
    lo_frequency_hz: float = Field(gt=0, examples=[11.1e9])
    sideband: Literal["high", "low"]


class MidFrequencyBand(FrequencyBand):
    """One receiver band. tmdata: ``basic_capabilities.receiver_information[]``."""

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
    """Mid's receiver bands. tmdata: ``basic_capabilities``."""

    # Served as receiver_information, the tmdata name, which the PHT UI reads
    frequency_bands: list[MidFrequencyBand] = Field(
        validation_alias=AliasChoices("frequency_bands", "receiver_information"),
        serialization_alias="receiver_information",
    )

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
    telescope: Literal[Telescope.MID] = Telescope.MID
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
        # receptors lists SKA dish IDs only; MeerKAT dishes are counted separately
        if self.number_ska_dishes != len(self.receptors):
            raise ValueError(
                f"{self.name}: number_ska_dishes ({self.number_ska_dishes}) does "
                f"not match the number of receptors ({len(self.receptors)})"
            )
        return self


class MidCapabilitiesFile(TelescopeCapabilitiesFileBase):
    """Top-level model for mid_capabilities.json."""

    telescope: Literal["Mid"] = "Mid"
    basic_capabilities: MidBasicCapabilities
    subarrays: list[MidCapabilitySet]

    @model_validator(mode="after")
    def check_available_receivers(self) -> Self:
        rx_ids = {band.rx_id for band in self.basic_capabilities.frequency_bands}
        for subarray in self.subarrays:
            unknown = set(subarray.available_receivers) - rx_ids
            if unknown:
                raise ValueError(
                    f"{subarray.name}: available_receivers {sorted(unknown)} "
                    "not found in frequency_bands"
                )
        return self


class LowCBFMode(StrEnum):
    VIS = "vis"
    PST = "pst"
    PSS = "pss"


class LowBasicCapabilities(FrequencyBand):
    """Low's frequency band and how it is divided into channels.
    tmdata: ``basic_capabilities``."""

    min_coarse_channel: int = Field(ge=0, examples=[64])
    max_coarse_channel: int = Field(ge=0, examples=[447])
    coarse_channel_width_hz: float = Field(gt=0, examples=[781.25e3])
    number_continuum_channels_per_coarse_channel: int = Field(ge=0, examples=[144])
    number_zoom_channels_per_coarse_channel: int = Field(ge=0, examples=[432])
    number_pst_channels_per_coarse_channel: int = Field(ge=0, examples=[216])
    number_pss_channels_per_coarse_channel: int = Field(ge=0, examples=[54])


class LowCapabilitySet(CapabilitySetBase):
    telescope: Literal[Telescope.LOW] = Telescope.LOW
    number_substations: int = Field(ge=0)
    number_subarray_beams: int = Field(ge=0)
    number_stations: int = Field(ge=0)
    cbf_modes: list[LowCBFMode]
    number_vlbi_beams: int = Field(ge=0)
    allowed_zoom_factors: list[int]

    @model_validator(mode="after")
    def check_station_count(self) -> Self:
        if self.number_stations != len(self.receptors):
            raise ValueError(
                f"{self.name}: number_stations ({self.number_stations}) does not "
                f"match the number of receptors ({len(self.receptors)})"
            )
        return self


# A capability set is one array assembly of either telescope; the
# telescope field picks the model when one is read back.
CapabilitySet = Annotated[
    MidCapabilitySet | LowCapabilitySet, Field(discriminator="telescope")
]


class LowCapabilitiesFile(TelescopeCapabilitiesFileBase):
    """Top-level model for low_capabilities.json."""

    telescope: Literal["Low"] = "Low"
    basic_capabilities: LowBasicCapabilities
    subarrays: list[LowCapabilitySet]
