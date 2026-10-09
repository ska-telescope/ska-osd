from enum import StrEnum
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class OSDBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class AvoidanceConstraints(OSDBaseModel):
    """
    Sun, moon and Jupiter avoidance angles.
    """

    sun_avoidance_angle_deg: float = Field(examples=[30.0])
    moon_avoidance_angle_deg: float = Field(examples=[10.0])
    jupiter_avoidance_angle_deg: float = Field(examples=[10.0])


class TelescopeDefaults(OSDBaseModel):
    """
    Base for the top-level Mid and Low defaults models. Subclasses
    narrow ``telescope`` to their own value.
    """

    telescope: str
    constraints: AvoidanceConstraints


class NoiseDiodeMode(StrEnum):
    PERIODIC = "periodic"
    PSEUDO_RANDOM = "pseudo_random"


class DefaultNoiseDiodeMode(StrEnum):
    PERIODIC = "periodic"
    PSEUDO_RANDOM = "pseudo_random"
    OFF = "off"


class PeriodicNoiseDiode(OSDBaseModel):
    mode: Literal[NoiseDiodeMode.PERIODIC] = NoiseDiodeMode.PERIODIC
    period_ms: float = Field(ge=0, examples=[1000.0])
    duty_cycle_ms: float = Field(ge=0, examples=[500.0])
    phase_shift_ms: float = Field(ge=0, examples=[0.0])


class PseudoRandomNoiseDiode(OSDBaseModel):
    mode: Literal[NoiseDiodeMode.PSEUDO_RANDOM] = NoiseDiodeMode.PSEUDO_RANDOM
    binary_polynomial: int = Field(ge=0)
    seed: int = Field(ge=0)
    dwell_ms: float = Field(ge=0)


NoiseDiode = Annotated[
    Union[PeriodicNoiseDiode, PseudoRandomNoiseDiode], Field(discriminator="mode")
]

Attenuation = Annotated[Optional[float], Field(default=None, ge=0.0, le=31.75)]


class TargetSPFRx(OSDBaseModel):
    attenuation_1_x: Attenuation
    attenuation_1_y: Attenuation
    attenuation_2_x: Attenuation
    attenuation_2_y: Attenuation
    noise_diode_options: List[NoiseDiode]
    default_noise_diode_mode: DefaultNoiseDiodeMode

    @model_validator(mode="before")
    @classmethod
    def from_tmdata_noise_diode(cls, data: Any) -> Any:
        """tmdata nests the options and the default mode under
        ``noise_diode``, keyed by mode; flatten them into
        ``noise_diode_options`` and ``default_noise_diode_mode``."""
        if not isinstance(data, dict) or "noise_diode" not in data:
            return data
        data = dict(data)
        noise_diode = dict(data.pop("noise_diode"))
        data["default_noise_diode_mode"] = noise_diode.pop("mode")
        data["noise_diode_options"] = [
            {"mode": mode, **option} for mode, option in noise_diode.items()
        ]
        return data

    @model_validator(mode="after")
    def check_default_mode_has_option(self):
        if self.default_noise_diode_mode == DefaultNoiseDiodeMode.OFF:
            return self
        modes = {option.mode for option in self.noise_diode_options}
        if self.default_noise_diode_mode not in modes:
            raise ValueError(
                f"default_noise_diode_mode '{self.default_noise_diode_mode}' "
                "has no matching entry in noise_diode_options"
            )
        return self


class SyncPPS(StrEnum):
    UNSET = "unset"
    ON = "on"
    OFF = "off"


class CSPSPFRx(OSDBaseModel):
    """tmdata: ``defaults.csp_configuration.spfrx``."""

    sync_pps: SyncPPS
    saturation_threshold: float = Field(examples=[0.2])

    @field_validator("sync_pps", mode="before")
    @classmethod
    def from_boolean(cls, value: Any) -> Any:
        """Releases up to 6.0.9 used a boolean rather than the three-way
        mode; true and false mean on and off."""
        if isinstance(value, bool):
            return SyncPPS.ON if value else SyncPPS.OFF
        return value


class SPFRxParameters(OSDBaseModel):
    """tmdata: ``defaults``."""

    target_spfrx: TargetSPFRx = Field(
        validation_alias=AliasChoices(
            "target_spfrx", AliasPath("target", "dish_spfrx_params")
        )
    )
    csp_spfrx: CSPSPFRx = Field(
        validation_alias=AliasChoices(
            "csp_spfrx", AliasPath("csp_configuration", "spfrx")
        )
    )


class MidDefaults(TelescopeDefaults):
    """Top-level model for mid_defaults.json."""

    telescope: Literal["Mid"] = "Mid"
    spfrx_defaults: SPFRxParameters = Field(
        validation_alias=AliasChoices("spfrx_defaults", "defaults")
    )


class LowCBFMetrics(OSDBaseModel):
    processors_ready_percent: float = Field(ge=0, le=100)
    alveo_configured_percent: float = Field(ge=0, le=100)


class LowQualityAttributeMetrics(OSDBaseModel):
    cbf: LowCBFMetrics


class LowDefaults(TelescopeDefaults):
    """Top-level model for low_defaults.json."""

    telescope: Literal["Low"] = "Low"
    quality_attribute_metrics: LowQualityAttributeMetrics
