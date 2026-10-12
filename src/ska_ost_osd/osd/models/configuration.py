from typing import Any, Self

from pydantic import (
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    ElevationConstraints,
    LowBasicCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilitySet,
    MidFrequencyBand,
    TelescopeCapabilitiesFileBase,
)
from ska_ost_osd.osd.models.defaults import (
    AvoidanceConstraints,
    OSDBaseModel,
    SPFRxParameters,
    TelescopeDefaultsFileBase,
)
from ska_ost_osd.osd.models.observatory_policies import ObservatoryPolicy


class ConfigurationModel(OSDBaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, validate_assignment=True
    )


class Constraints(ElevationConstraints, AvoidanceConstraints):
    """A telescope's observing constraints, which tmdata stores in two
    files."""

    @classmethod
    def combine(
        cls,
        capabilities: TelescopeCapabilitiesFileBase,
        defaults: TelescopeDefaultsFileBase,
    ) -> Self:
        """The elevation limits from the capabilities file with the sun,
        moon and Jupiter avoidance angles from the defaults file."""
        return cls(
            **capabilities.constraints.model_dump(),
            **defaults.constraints.model_dump(),
        )


# The view models below are what ska-oso-services serves to the ODT from
# GET /configuration: the reader models narrowed to the fields it serves.


class ConfigurationCapabilitySetBase(ConfigurationModel):
    """The fields of a capability set the configuration serves for both
    telescopes."""

    name: str
    receptors: list[str | int]
    available_bandwidth_hz: float
    number_pst_beams: int
    number_fsps: int


class MidConfigurationCapabilitySet(ConfigurationCapabilitySetBase):
    allowed_channel_width_values_hz: list[int]


class LowConfigurationCapabilitySet(ConfigurationCapabilitySetBase):
    number_substations: int
    number_subarray_beams: int


class ConfigurationLowCBFMetrics(ConfigurationModel):
    processors_ready_percent: float


class ConfigurationLowQualityAttributeMetrics(ConfigurationModel):
    cbf: ConfigurationLowCBFMetrics


class MidConfiguration(ConfigurationModel):
    frequency_band: list[MidFrequencyBand]
    constraints: Constraints
    subarrays: list[MidConfigurationCapabilitySet]
    spfrx_defaults: SPFRxParameters


class LowConfiguration(ConfigurationModel):
    frequency_band: LowBasicCapabilities
    constraints: Constraints
    quality_attribute_metrics: ConfigurationLowQualityAttributeMetrics
    subarrays: list[LowConfigurationCapabilitySet]


class Configuration(ConfigurationModel):
    """The ODT configuration: both telescopes' bands, constraints, defaults
    and capability sets."""

    ska_mid: MidConfiguration
    ska_low: LowConfiguration


# The view models below are what ska-oso-services serves to the PHT from
# GET /prsls/osd/cycles and GET /prsls/osd/{cycle}: each cycle with the
# capability set each telescope offers and that telescope's basic
# capabilities. Served with aliases, the field names are the ones the PHT UI
# reads.


class CycleCapabilitiesBase(ConfigurationModel):
    """One telescope's capabilities in a cycle. Served with the capability
    set keyed by its name, e.g. ``"AA2": {...}``, beside
    ``basic_capabilities``."""

    capability_set: CapabilitySet

    @model_validator(mode="before")
    @classmethod
    def collect_capability_set(cls, data: Any) -> Any:
        """Read the served form back: the one key that isn't
        ``basic_capabilities`` is the capability set."""
        if not isinstance(data, dict) or "capability_set" in data:
            return data
        data = data.copy()
        names = [key for key in data if key != "basic_capabilities"]
        if len(names) == 1:
            data["capability_set"] = data.pop(names[0])
        return data

    @model_serializer(mode="wrap")
    def key_capability_set_by_name(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        data = handler(self)
        data[self.capability_set.name] = data.pop("capability_set")
        return data


class MidCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: MidBasicCapabilities
    capability_set: MidCapabilitySet


class LowCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: LowBasicCapabilities
    capability_set: LowCapabilitySet


class CycleCapabilities(ConfigurationModel):
    """The telescopes a cycle offers; ``None`` for one it does not."""

    mid: MidCycleCapabilities | None = None
    low: LowCycleCapabilities | None = None


class CycleConfiguration(ConfigurationModel):
    """One cycle joined with what it offers."""

    observatory_policy: ObservatoryPolicy
    capabilities: CycleCapabilities
