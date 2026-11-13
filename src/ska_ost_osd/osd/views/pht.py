"""The PHT views: what ska-oso-services serves to the PHT from GET
/prsls/osd/cycles and GET /prsls/osd/{cycle}: each cycle with the capability
set each telescope offers and that telescope's basic capabilities. Served
with aliases, the field names are the ones the PHT UI reads."""

from datetime import datetime
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
    MidCapabilitySet,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.subarray_templates import SubarrayType
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import (
    ConfigurationModel,
    LowFrequencyBandWithChannels,
    low_frequency_band,
)

# The PHT UI recognises science verification by its name
_TYPE_NAMES = {
    PolicyType.SCIENCE_VERIFICATION: "Science Verification",
    PolicyType.SHARED_RISK: "Shared Risk",
    PolicyType.STANDARD_OPERATIONS: "Proposal",
}


class CycleTelescopeCapabilities(ConfigurationModel):
    """The capability set each telescope offers in the cycle, or ``None``.
    Served as ``Mid`` and ``Low``, the names the PHT UI reads."""

    ska_mid: str | None = Field(validation_alias="Mid", serialization_alias="Mid")
    ska_low: str | None = Field(validation_alias="Low", serialization_alias="Low")


class CycleInformation(ConfigurationModel):
    """The cycle's ID and proposal window, as the PHT UI reads them."""

    cycle_id: str
    proposal_open: datetime
    proposal_close: datetime


class CyclePolicies(ConfigurationModel):
    """The cycle's proposal policy, as the PHT UI reads it."""

    normal_max_hours: float
    max_targets: int | None
    max_observation_setups: int | None
    max_data_products: int | None


class ObservatoryPolicy(ConfigurationModel):
    """The cycle, as the PHT UI reads it."""

    cycle_number: int | None
    cycle_id: str
    type: str
    cycle_description: str
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
            if "number_pss_beams" in capability_set:
                modes: dict[str, Any] = {
                    "spectral": {
                        "max_zoom_windows": capability_set.pop("number_zoom_windows"),
                        "max_zoom_channels": capability_set.pop("number_zoom_channels"),
                    },
                    "pss": {
                        "max_beams": capability_set.pop("number_pss_beams"),
                        "beam_bandwidth_hz": capability_set.pop("ps_beam_bandwidth_hz"),
                    },
                    "pst": {"max_beams": capability_set.pop("number_pst_beams")},
                }
                if "allowed_zoom_factors" in capability_set:
                    modes["spectral"]["zoom_factors"] = capability_set.pop(
                        "allowed_zoom_factors"
                    )
                if "number_vlbi_beams" in capability_set:
                    modes["vlbi"] = {
                        "max_beams": capability_set.pop("number_vlbi_beams")
                    }
                capability_set["modes"] = modes
            if "available_receivers" in capability_set:
                capability_set["receivers"] = capability_set.pop("available_receivers")
            if "number_ska_dishes" in capability_set:
                capability_set["dishes"] = {
                    "number_ska_dishes": capability_set.pop("number_ska_dishes"),
                    "number_meerkat_dishes": capability_set.pop(
                        "number_meerkat_dishes"
                    ),
                    "number_meerkatplus_dishes": capability_set.pop(
                        "number_meerkatplus_dishes"
                    ),
                    "max_baseline_km": capability_set.pop("max_baseline_km"),
                    "ids": capability_set.pop("receptors"),
                }
            if "number_stations" in capability_set:
                capability_set["stations"] = {
                    "number_stations": capability_set.pop("number_stations"),
                    "max_baseline_km": capability_set.pop("max_baseline_km"),
                    "ids": capability_set.pop("receptors"),
                }
            if "number_substations" in capability_set:
                capability_set["subarray_beams"] = {
                    "max_subarray_beams": capability_set.pop("number_subarray_beams"),
                    "max_substations_per_subarray_beam": capability_set.pop(
                        "number_substations"
                    ),
                }
            data["capability_set"] = capability_set
        return data

    @model_serializer(mode="wrap")
    def key_capability_set_by_name(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        data = handler(self)
        capability_set = data.pop("capability_set")
        if "receivers" in capability_set:
            capability_set["available_receivers"] = capability_set.pop("receivers")
        # The PHT UI reads Mid's channel widths without the _hz suffix
        if "allowed_channel_width_values_hz" in capability_set:
            capability_set["allowed_channel_width_values"] = capability_set[
                "allowed_channel_width_values_hz"
            ]
        # The PHT UI reads the modes, the stations or dishes, and Low's
        # subarray beams, flat under their old names
        modes = capability_set.pop("modes")
        capability_set["number_zoom_windows"] = modes["spectral"]["max_zoom_windows"]
        capability_set["number_zoom_channels"] = modes["spectral"]["max_zoom_channels"]
        if "zoom_factors" in modes["spectral"]:
            capability_set["allowed_zoom_factors"] = modes["spectral"]["zoom_factors"]
        capability_set["number_pss_beams"] = modes["pss"]["max_beams"]
        capability_set["ps_beam_bandwidth_hz"] = modes["pss"]["beam_bandwidth_hz"]
        capability_set["number_pst_beams"] = modes["pst"]["max_beams"]
        if "vlbi" in modes:
            capability_set["number_vlbi_beams"] = modes["vlbi"]["max_beams"]
        if "stations" in capability_set:
            stations = capability_set.pop("stations")
            capability_set["receptors"] = stations["ids"]
            capability_set["number_stations"] = stations["number_stations"]
            capability_set["max_baseline_km"] = stations["max_baseline_km"]
        if "dishes" in capability_set:
            dishes = capability_set.pop("dishes")
            capability_set["receptors"] = dishes["ids"]
            capability_set["number_ska_dishes"] = dishes["number_ska_dishes"]
            capability_set["number_meerkat_dishes"] = dishes["number_meerkat_dishes"]
            capability_set["number_meerkatplus_dishes"] = dishes[
                "number_meerkatplus_dishes"
            ]
            capability_set["max_baseline_km"] = dishes["max_baseline_km"]
        if "subarray_beams" in capability_set:
            subarray_beams = capability_set.pop("subarray_beams")
            capability_set["number_substations"] = subarray_beams[
                "max_substations_per_subarray_beam"
            ]
            capability_set["number_subarray_beams"] = subarray_beams[
                "max_subarray_beams"
            ]
        data[self.capability_set.name] = capability_set
        if (subarray_templates := data.pop("subarray_templates")) is not None:
            data[self.capability_set.name]["subarray_templates"] = subarray_templates
        return data


class MidCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: MidCycleBasicCapabilities
    capability_set: MidCapabilitySet


class LowCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: LowFrequencyBandWithChannels
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


def _observatory_policy(
    cycle: Cycle,
    policy_type: PolicyType,
    mid: MidCapabilitySet | None,
    low: LowCapabilitySet | None,
) -> ObservatoryPolicy:
    """The cycle, with the field names the PHT UI reads."""
    return ObservatoryPolicy(
        cycle_number=cycle.number,
        cycle_id=cycle.id,
        type=_TYPE_NAMES[policy_type],
        cycle_description=cycle.description,
        cycle_information=CycleInformation(
            cycle_id=cycle.id,
            proposal_open=cycle.proposal_window.opens,
            proposal_close=cycle.proposal_window.closes,
        ),
        cycle_policies=CyclePolicies(
            normal_max_hours=cycle.proposal_policy.max_observing_hours,
            max_targets=cycle.proposal_policy.max_targets,
            max_observation_setups=cycle.proposal_policy.max_observation_setups,
            max_data_products=cycle.proposal_policy.max_data_products,
        ),
        telescope_capabilities=CycleTelescopeCapabilities(
            ska_mid=mid.name if mid is not None else None,
            ska_low=low.name if low is not None else None,
        ),
    )


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
    :raises ValueError: If the cycle offers more than one policy type.
    """
    cycle = repository.get_cycle(cycle_id)
    capability_sets = repository.get_cycle_capability_sets(cycle_id)
    # The PHT UI handles one policy type per cycle
    types = {
        policy_type for by_type in capability_sets.values() for policy_type in by_type
    }
    if len(types) != 1:
        raise ValueError(
            f"Cycle {cycle_id} offers more than one policy type, which the PHT "
            "view can't serve"
        )
    (policy_type,) = types
    mid = capability_sets.get(Telescope.SKA_MID, {}).get(policy_type)
    low = capability_sets.get(Telescope.SKA_LOW, {}).get(policy_type)
    return CycleConfiguration(
        observatory_policy=_observatory_policy(cycle, policy_type, mid, low),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=MidCycleBasicCapabilities.model_validate(
                    repository.get_basic_capabilities(Telescope.SKA_MID),
                    from_attributes=True,
                ),
                capability_set=mid,
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_MID,
                    mid.name,
                    include_subarray_templates,
                ),
            )
            if mid is not None
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=low_frequency_band(repository),
                capability_set=low,
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_LOW,
                    low.name,
                    include_subarray_templates,
                ),
            )
            if low is not None
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
    :raises ValueError: If a cycle offers more than one policy type.
    """
    return [
        get_cycle_configuration(repository, cycle_id, include_subarray_templates)
        for cycle_id in repository.get_cycle_ids()
    ]
