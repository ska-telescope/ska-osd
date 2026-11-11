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
    LowCapabilitySet,
    LowFrequencyBand,
    MidCapabilitySet,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.cycles import CycleInformation, CyclePolicies
from ska_ost_osd.osd.models.subarray_templates import SubarrayType
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import ConfigurationModel


class CycleTelescopeCapabilities(ConfigurationModel):
    """The capability set each telescope offers in the cycle, or ``None``.
    Served as ``Mid`` and ``Low``, the names the PHT UI reads."""

    ska_mid: str | None = Field(validation_alias="Mid", serialization_alias="Mid")
    ska_low: str | None = Field(validation_alias="Low", serialization_alias="Low")


class ObservatoryPolicy(ConfigurationModel):
    """The cycle, as the PHT UI reads it: read from a ``Cycle``'s ``number``,
    ``id`` and ``description``, and served as ``cycle_number``, ``cycle_id``
    and ``cycle_description``."""

    cycle_number: int = Field(validation_alias="number")
    cycle_id: str = Field(validation_alias="id")
    type: str | None
    cycle_description: str = Field(validation_alias="description")
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: CycleTelescopeCapabilities


class MidCycleBasicCapabilities(ConfigurationModel):
    """Mid's receiver bands, served as ``receiver_information``, the name the
    PHT UI reads."""

    frequency_bands: list[MidFrequencyBand] = Field(
        validation_alias="receiver_information",
        serialization_alias="receiver_information",
    )


class CycleSubarrayTemplate(ConfigurationModel):
    """One subarray template, as the legacy OSD API serves it: keyed by its
    name, with its stations as one comma-separated string."""

    subarray_type: SubarrayType
    custom_stations: str
    description: str


class CycleCapabilitiesBase(ConfigurationModel):
    """One telescope's capabilities in a cycle. Served with the capability
    set keyed by its name, e.g. ``"AA2": {...}``, beside
    ``basic_capabilities``. When the subarray templates are asked for, they
    are served in the capability set, keyed by name, as
    ``subarray_templates``."""

    capability_set: CapabilitySet
    subarray_templates: dict[str, CycleSubarrayTemplate] | None = None

    @model_validator(mode="before")
    @classmethod
    def collect_capability_set(cls, data: Any) -> Any:
        """Read the served form back: the one key that isn't
        ``basic_capabilities`` is the capability set, which holds the
        subarray templates if they were served."""
        if not isinstance(data, dict) or "capability_set" in data:
            return data
        data = data.copy()
        names = [key for key in data if key != "basic_capabilities"]
        if len(names) == 1:
            capability_set = dict(data.pop(names[0]))
            if "subarray_templates" in capability_set:
                data["subarray_templates"] = capability_set.pop("subarray_templates")
            data["capability_set"] = capability_set
        return data

    @model_serializer(mode="wrap")
    def key_capability_set_by_name(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        data = handler(self)
        data[self.capability_set.name] = data.pop("capability_set")
        if (subarray_templates := data.pop("subarray_templates")) is not None:
            data[self.capability_set.name]["subarray_templates"] = subarray_templates
        return data


class MidCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: MidCycleBasicCapabilities
    capability_set: MidCapabilitySet


class LowCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: LowFrequencyBand
    capability_set: LowCapabilitySet


class CycleCapabilities(ConfigurationModel):
    """The telescopes a cycle offers; ``None`` for one it does not."""

    mid: MidCycleCapabilities | None = None
    low: LowCycleCapabilities | None = None


class CycleConfiguration(ConfigurationModel):
    """One cycle joined with what it offers."""

    observatory_policy: ObservatoryPolicy
    capabilities: CycleCapabilities


def _subarray_templates(
    repository: OSDRepository,
    telescope: Telescope,
    capability_set: str,
    include_subarray_templates: bool,
) -> dict[str, CycleSubarrayTemplate] | None:
    """The capability set's templates keyed by name, or ``None`` when they
    weren't asked for."""
    if not include_subarray_templates:
        return None
    return {
        template.name: CycleSubarrayTemplate(
            subarray_type=template.subarray_type,
            custom_stations=",".join(template.custom_stations),
            description=template.description,
        )
        for template in repository.get_subarray_templates(telescope, capability_set)
    }


def _low_frequency_band(repository: OSDRepository) -> LowFrequencyBand:
    """Low's one frequency band, which the PHT reads as Low's basic
    capabilities."""
    (band,) = repository.get_basic_capabilities(Telescope.SKA_LOW).frequency_bands
    return band


def get_cycle_configuration(
    repository: OSDRepository,
    cycle_id: str,
    include_subarray_templates: bool = False,
) -> CycleConfiguration:
    """Build one cycle's view for the PHT: what ska-oso-services serves from
    GET /prsls/osd/{cycle}.

    :param repository: the OSD repository to read from.
    :param cycle_id: the ID of the cycle.
    :param include_subarray_templates: whether to serve each offered
        capability set's subarray templates, as ``subarray_templates``.
    :return: the cycle with, for each telescope it offers, the offered
        capability set and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises CapabilitySetNotFoundError: If the cycle names a capability set
        that does not exist.
    """
    cycle = repository.get_cycle(cycle_id)
    offered = cycle.telescope_capabilities
    return CycleConfiguration(
        observatory_policy=ObservatoryPolicy.model_validate(
            cycle, from_attributes=True
        ),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=MidCycleBasicCapabilities.model_validate(
                    repository.get_basic_capabilities(Telescope.SKA_MID),
                    from_attributes=True,
                ),
                capability_set=repository.get_capability_set(
                    Telescope.SKA_MID, offered.ska_mid
                ),
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_MID,
                    offered.ska_mid,
                    include_subarray_templates,
                ),
            )
            if offered.ska_mid is not None
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=_low_frequency_band(repository),
                capability_set=repository.get_capability_set(
                    Telescope.SKA_LOW, offered.ska_low
                ),
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_LOW,
                    offered.ska_low,
                    include_subarray_templates,
                ),
            )
            if offered.ska_low is not None
            else None,
        ),
    )


def get_cycle_configurations(
    repository: OSDRepository, include_subarray_templates: bool = False
) -> list[CycleConfiguration]:
    """Build every cycle's view for the PHT, in ascending order of ID: what
    ska-oso-services serves from GET /prsls/osd/cycles.

    :param repository: the OSD repository to read from.
    :param include_subarray_templates: whether to serve each offered
        capability set's subarray templates, as ``subarray_templates``.
    :return: the cycle views.
    :raises CapabilitySetNotFoundError: If a cycle names a capability set
        that does not exist.
    """
    return [
        get_cycle_configuration(repository, cycle_id, include_subarray_templates)
        for cycle_id in repository.get_cycle_ids()
    ]
