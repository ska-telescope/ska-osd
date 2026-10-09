import re
from enum import StrEnum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import AliasChoices, AliasPath, Field, model_validator

from ska_ost_osd.osd.common.constant import ARRAY_ASSEMBLY_PATTERN
from ska_ost_osd.osd.models.defaults import OSDBaseModel


class ElevationConstraints(OSDBaseModel):
    min_elevation_deg: float = Field(ge=0, le=90, examples=[45.0])
    max_elevation_deg: float = Field(ge=0, le=90, examples=[90.0])

    @model_validator(mode="after")
    def check_elevation_range(self):
        if self.min_elevation_deg > self.max_elevation_deg:
            raise ValueError("min_elevation_deg must not exceed max_elevation_deg")
        return self


class FrequencyBand(OSDBaseModel):
    max_frequency_hz: float = Field(gt=0)
    min_frequency_hz: float = Field(gt=0)

    @model_validator(mode="after")
    def check_frequency_range(self):
        if self.min_frequency_hz > self.max_frequency_hz:
            raise ValueError("min_frequency_hz must not exceed max_frequency_hz")
        return self


class Subarray(OSDBaseModel):
    name: str = Field(examples=["AA0.5"])
    receptors: List[Union[str, int]] = Field(
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
    subarray_templates: Optional[Union[List[str], Dict[str, Any]]] = None


class TelescopeCapabilitiesBase(OSDBaseModel):
    constraints: ElevationConstraints

    @model_validator(mode="before")
    @classmethod
    def collect_subarrays(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "subarrays" in data:
            return data
        data = dict(data)
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
    band5b_subbands: Optional[List[Band5bSubband]] = Field(
        default=None,
        validation_alias=AliasChoices("band5b_subbands", "sub_bands"),
    )


class MidSubarray(Subarray):
    allowed_channel_width_values_hz: List[int]
    allowed_channel_count_range_min: List[int]
    allowed_channel_count_range_max: List[int]
    available_receivers: List[str] = Field(examples=[["Band_1", "Band_2"]])
    cbf_modes: List[MidCBFMode]
    number_ska_dishes: int = Field(ge=0)
    number_meerkat_dishes: int = Field(ge=0)
    number_meerkatplus_dishes: int = Field(ge=0)

    @model_validator(mode="after")
    def check_dish_count(self):
        # receptors lists SKA dish IDs only; MeerKAT dishes are counted separately
        if self.number_ska_dishes != len(self.receptors):
            raise ValueError(
                f"{self.name}: number_ska_dishes ({self.number_ska_dishes}) does "
                f"not match the number of receptors ({len(self.receptors)})"
            )
        return self


class MidCapabilities(TelescopeCapabilitiesBase):
    telescope: Literal["Mid"] = "Mid"
    frequency_band: List[MidFrequencyBand] = Field(
        validation_alias=AliasChoices(
            "frequency_band", AliasPath("basic_capabilities", "receiver_information")
        )
    )
    subarrays: List[MidSubarray]

    @model_validator(mode="after")
    def check_available_receivers(self):
        rx_ids = {band.rx_id for band in self.frequency_band}
        for subarray in self.subarrays:
            unknown = set(subarray.available_receivers) - rx_ids
            if unknown:
                raise ValueError(
                    f"{subarray.name}: available_receivers {sorted(unknown)} "
                    "not found in frequency_band"
                )
        return self


class LowCBFMode(StrEnum):
    VIS = "vis"
    PST = "pst"
    PSS = "pss"


class LowFrequencyBand(FrequencyBand):
    min_coarse_channel: int = Field(ge=0, examples=[64])
    max_coarse_channel: int = Field(ge=0, examples=[447])
    coarse_channel_width_hz: float = Field(gt=0, examples=[781.25e3])
    number_continuum_channels_per_coarse_channel: int = Field(ge=0, examples=[144])
    number_zoom_channels_per_coarse_channel: int = Field(ge=0, examples=[432])
    number_pst_channels_per_coarse_channel: int = Field(ge=0, examples=[216])
    number_pss_channels_per_coarse_channel: int = Field(ge=0, examples=[54])


class LowSubarray(Subarray):
    number_substations: int = Field(ge=0)
    number_subarray_beams: int = Field(ge=0)
    number_stations: int = Field(ge=0)
    cbf_modes: List[LowCBFMode]
    number_vlbi_beams: int = Field(ge=0)
    allowed_zoom_factors: List[int]

    @model_validator(mode="after")
    def check_station_count(self):
        if self.number_stations != len(self.receptors):
            raise ValueError(
                f"{self.name}: number_stations ({self.number_stations}) does not "
                f"match the number of receptors ({len(self.receptors)})"
            )
        return self


class LowCapabilities(TelescopeCapabilitiesBase):
    telescope: Literal["Low"] = "Low"
    frequency_band: LowFrequencyBand = Field(
        validation_alias=AliasChoices("frequency_band", "basic_capabilities")
    )
    subarrays: List[LowSubarray]
