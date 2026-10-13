"""The PHT views: what ska-oso-services serves to the PHT from GET
/prsls/osd/cycles and GET /prsls/osd/{cycle}: each cycle with the capability
set each telescope offers and that telescope's basic capabilities. Served
with aliases, the field names are the ones the PHT UI reads."""

from typing import Any

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowBasicCapabilities,
    LowCapabilitySet,
    MidCapabilitySet,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.cycles import CycleID, CycleInformation, CyclePolicies
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import ConfigurationModel


class CycleTelescopeCapabilities(ConfigurationModel):
    """The capability set each telescope offers in the cycle, or ``None``.
    Served as ``Mid`` and ``Low``, the names the PHT UI reads."""

    ska_mid: str | None = Field(alias="Mid")
    ska_low: str | None = Field(alias="Low")


class ObservatoryPolicy(ConfigurationModel):
    """The cycle, as the PHT UI reads it."""

    cycle_number: CycleID
    cycle_id: str | None
    type: str | None
    cycle_description: str
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: CycleTelescopeCapabilities


class MidCycleBasicCapabilities(ConfigurationModel):
    """Mid's receiver bands, served as ``receiver_information``, the name the
    PHT UI reads."""

    frequency_bands: list[MidFrequencyBand] = Field(alias="receiver_information")


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
    basic_capabilities: MidCycleBasicCapabilities
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


def get_cycle_configuration(
    repository: OSDRepository, cycle_id: CycleID
) -> CycleConfiguration:
    """Build one cycle's view for the PHT: what ska-oso-services serves from
    GET /prsls/osd/{cycle}.

    :param repository: the OSD repository to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle with, for each telescope it offers, the offered
        capability set and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises CapabilitySetNotFoundError: If the cycle names a capability set
        that does not exist.
    """
    capability_sets = repository.get_cycle_capability_sets(cycle_id)
    mid = capability_sets.get(Telescope.MID)
    low = capability_sets.get(Telescope.LOW)
    return CycleConfiguration(
        observatory_policy=ObservatoryPolicy.model_validate(
            repository.get_cycle(cycle_id), from_attributes=True
        ),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=MidCycleBasicCapabilities.model_validate(
                    repository.get_basic_capabilities(Telescope.MID),
                    from_attributes=True,
                ),
                capability_set=mid,
            )
            if mid
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=repository.get_basic_capabilities(Telescope.LOW),
                capability_set=low,
            )
            if low
            else None,
        ),
    )


def get_cycle_configurations(repository: OSDRepository) -> list[CycleConfiguration]:
    """Build every cycle's view for the PHT, in ascending order of ID: what
    ska-oso-services serves from GET /prsls/osd/cycles.

    :param repository: the OSD repository to read from.
    :return: the cycle views.
    :raises CapabilitySetNotFoundError: If a cycle names a capability set
        that does not exist.
    """
    return [
        get_cycle_configuration(repository, cycle_id)
        for cycle_id in repository.get_cycle_ids()
    ]
