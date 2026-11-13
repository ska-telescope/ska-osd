"""The PHT views: what ska-oso-services serves to the PHT from GET
/prsls/osd/cycles and GET /prsls/osd/{cycle}: each cycle with the
capabilities each telescope offers and that telescope's basic capabilities. Served
with aliases, the field names are the ones the PHT UI reads."""

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowArrayAssemblyModes,
    LowArrayAssemblyStations,
    LowArrayAssemblySubarrayBeams,
    LowCapabilities,
    LowCBFMode,
    MidArrayAssemblyDishes,
    MidArrayAssemblyModes,
    MidCapabilities,
    MidCBFMode,
    MidFrequencyBand,
)
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.models.defaults import OSDBaseModel
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
    """The capabilities each telescope offers in the cycle, or ``None``.
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


class MidOfferedCapabilities(OSDBaseModel):
    """What the PHT view serves of Mid's capabilities in a cycle: all but the
    basic capabilities, which it serves beside them."""

    name: str
    available_bandwidth_hz: float
    number_fsps: int
    telescope: Literal[Telescope.SKA_MID] = Telescope.SKA_MID
    modes: MidArrayAssemblyModes
    allowed_channel_width_values_hz: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_count_range_max: list[int]
    receivers: list[str]
    cbf_modes: list[MidCBFMode]
    dishes: MidArrayAssemblyDishes


class LowOfferedCapabilities(OSDBaseModel):
    """What the PHT view serves of Low's capabilities in a cycle: all but the
    basic capabilities, which it serves beside them."""

    name: str
    available_bandwidth_hz: float
    number_fsps: int
    telescope: Literal[Telescope.SKA_LOW] = Telescope.SKA_LOW
    subarray_beams: LowArrayAssemblySubarrayBeams
    cbf_modes: list[LowCBFMode]
    modes: LowArrayAssemblyModes
    stations: LowArrayAssemblyStations


class CycleCapabilitiesBase(ConfigurationModel):
    """One telescope's capabilities in a cycle. Served keyed by the name of
    the policy or array assembly, e.g. ``"AA2": {...}``, beside
    ``basic_capabilities``. When the subarray templates are asked for, they
    are served in the capabilities, keyed by name, as
    ``subarray_templates``."""

    capabilities: MidOfferedCapabilities | LowOfferedCapabilities
    subarray_templates: dict[str, CycleSubarrayTemplate] | None = None

    @model_validator(mode="before")
    @classmethod
    def collect_capabilities(cls, data: Any) -> Any:
        """Read the served form back: the one key that isn't
        ``basic_capabilities`` holds the capabilities, and the subarray
        templates if they were served."""
        if not isinstance(data, dict) or "capabilities" in data:
            return data
        data = data.copy()
        names = [key for key in data if key != "basic_capabilities"]
        if len(names) == 1:
            capabilities = dict(data.pop(names[0]))
            if "subarray_templates" in capabilities:
                data["subarray_templates"] = capabilities.pop("subarray_templates")
            if "number_pss_beams" in capabilities:
                modes: dict[str, Any] = {
                    "spectral": {
                        "max_zoom_windows": capabilities.pop("number_zoom_windows"),
                        "max_zoom_channels": capabilities.pop("number_zoom_channels"),
                    },
                    "pss": {
                        "max_beams": capabilities.pop("number_pss_beams"),
                        "beam_bandwidth_hz": capabilities.pop("ps_beam_bandwidth_hz"),
                    },
                    "pst": {"max_beams": capabilities.pop("number_pst_beams")},
                }
                if "allowed_zoom_factors" in capabilities:
                    modes["spectral"]["zoom_factors"] = capabilities.pop(
                        "allowed_zoom_factors"
                    )
                if "number_vlbi_beams" in capabilities:
                    modes["vlbi"] = {"max_beams": capabilities.pop("number_vlbi_beams")}
                capabilities["modes"] = modes
            if "available_receivers" in capabilities:
                capabilities["receivers"] = capabilities.pop("available_receivers")
            if "number_ska_dishes" in capabilities:
                capabilities["dishes"] = {
                    "number_ska_dishes": capabilities.pop("number_ska_dishes"),
                    "number_meerkat_dishes": capabilities.pop("number_meerkat_dishes"),
                    "number_meerkatplus_dishes": capabilities.pop(
                        "number_meerkatplus_dishes"
                    ),
                    "max_baseline_km": capabilities.pop("max_baseline_km"),
                    "ids": capabilities.pop("receptors"),
                }
            if "number_stations" in capabilities:
                capabilities["stations"] = {
                    "number_stations": capabilities.pop("number_stations"),
                    "max_baseline_km": capabilities.pop("max_baseline_km"),
                    "ids": capabilities.pop("receptors"),
                }
            if "number_substations" in capabilities:
                capabilities["subarray_beams"] = {
                    "max_subarray_beams": capabilities.pop("number_subarray_beams"),
                    "max_substations_per_subarray_beam": capabilities.pop(
                        "number_substations"
                    ),
                }
            data["capabilities"] = capabilities
        return data

    @model_serializer(mode="wrap")
    def key_capabilities_by_name(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        data = handler(self)
        capabilities = data.pop("capabilities")
        if "receivers" in capabilities:
            capabilities["available_receivers"] = capabilities.pop("receivers")
        # The PHT UI reads Mid's channel widths without the _hz suffix
        if "allowed_channel_width_values_hz" in capabilities:
            capabilities["allowed_channel_width_values"] = capabilities[
                "allowed_channel_width_values_hz"
            ]
        # The PHT UI reads the modes, the stations or dishes, and Low's
        # subarray beams, flat under their old names
        modes = capabilities.pop("modes")
        capabilities["number_zoom_windows"] = modes["spectral"]["max_zoom_windows"]
        capabilities["number_zoom_channels"] = modes["spectral"]["max_zoom_channels"]
        if "zoom_factors" in modes["spectral"]:
            capabilities["allowed_zoom_factors"] = modes["spectral"]["zoom_factors"]
        capabilities["number_pss_beams"] = modes["pss"]["max_beams"]
        capabilities["ps_beam_bandwidth_hz"] = modes["pss"]["beam_bandwidth_hz"]
        capabilities["number_pst_beams"] = modes["pst"]["max_beams"]
        if "vlbi" in modes:
            capabilities["number_vlbi_beams"] = modes["vlbi"]["max_beams"]
        if "stations" in capabilities:
            stations = capabilities.pop("stations")
            capabilities["receptors"] = stations["ids"]
            capabilities["number_stations"] = stations["number_stations"]
            capabilities["max_baseline_km"] = stations["max_baseline_km"]
        if "dishes" in capabilities:
            dishes = capabilities.pop("dishes")
            capabilities["receptors"] = dishes["ids"]
            capabilities["number_ska_dishes"] = dishes["number_ska_dishes"]
            capabilities["number_meerkat_dishes"] = dishes["number_meerkat_dishes"]
            capabilities["number_meerkatplus_dishes"] = dishes[
                "number_meerkatplus_dishes"
            ]
            capabilities["max_baseline_km"] = dishes["max_baseline_km"]
        if "subarray_beams" in capabilities:
            subarray_beams = capabilities.pop("subarray_beams")
            capabilities["number_substations"] = subarray_beams[
                "max_substations_per_subarray_beam"
            ]
            capabilities["number_subarray_beams"] = subarray_beams["max_subarray_beams"]
        data[self.capabilities.name] = capabilities
        if (subarray_templates := data.pop("subarray_templates")) is not None:
            data[self.capabilities.name]["subarray_templates"] = subarray_templates
        return data


class MidCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: MidCycleBasicCapabilities
    capabilities: MidOfferedCapabilities


class LowCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: LowFrequencyBandWithChannels
    capabilities: LowOfferedCapabilities


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
    array_assembly: str,
    include_subarray_templates: bool,
) -> dict[str, CycleSubarrayTemplate] | None:
    """The array assembly's templates keyed by name, or ``None`` when they
    weren't asked for."""
    if not include_subarray_templates:
        return None
    return {
        template.name: CycleSubarrayTemplate(
            subarray_type=template.subarray_type,
            custom_stations=",".join(template.custom_stations),
            description=template.description,
        )
        for template in repository.get_subarray_templates(telescope, array_assembly)
    }


def _name(capabilities: MidCapabilities | LowCapabilities) -> str:
    """The name the PHT UI knows capabilities by: the policy's, or the array
    assembly's if no policy applies."""
    return capabilities.policy or capabilities.array_assembly


def _observatory_policy(
    cycle: Cycle,
    policy_type: PolicyType,
    mid: MidCapabilities | None,
    low: LowCapabilities | None,
) -> ObservatoryPolicy:
    """The cycle, with the field names the PHT UI reads."""
    return ObservatoryPolicy(
        cycle_number=cycle.cycle_number,
        cycle_id=cycle.cycle_id,
        type=_TYPE_NAMES[policy_type],
        cycle_description=cycle.description,
        cycle_information=CycleInformation(
            cycle_id=cycle.cycle_id,
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
            ska_mid=_name(mid) if mid is not None else None,
            ska_low=_name(low) if low is not None else None,
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
    :param include_subarray_templates: whether to serve the subarray
        templates offered with each telescope's capabilities, as
        ``subarray_templates``.
    :return: the cycle with, for each telescope it offers, the offered
        capabilities and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises ArrayAssemblyNotFoundError: If the cycle names an array assembly
        that does not exist.
    :raises FileNotFoundError: If the cycle names a policy that does not
        exist.
    :raises ValueError: If the cycle offers more than one policy type.
    """
    cycle = repository.get_cycle(cycle_id)
    offered = repository.get_cycle_capabilities(cycle_id)
    # The PHT UI handles one policy type per cycle
    types = {policy_type for by_type in offered.values() for policy_type in by_type}
    if len(types) != 1:
        raise ValueError(
            f"Cycle {cycle_id} offers more than one policy type, which the PHT "
            "view can't serve"
        )
    (policy_type,) = types
    mid = offered.get(Telescope.SKA_MID, {}).get(policy_type)
    low = offered.get(Telescope.SKA_LOW, {}).get(policy_type)
    return CycleConfiguration(
        observatory_policy=_observatory_policy(cycle, policy_type, mid, low),
        capabilities=CycleCapabilities(
            mid=MidCycleCapabilities(
                basic_capabilities=MidCycleBasicCapabilities.model_validate(
                    repository.get_basic_capabilities(Telescope.SKA_MID),
                    from_attributes=True,
                ),
                capabilities=MidOfferedCapabilities.model_validate(
                    mid.model_dump() | {"name": _name(mid)}
                ),
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_MID,
                    cycle.capabilities[Telescope.SKA_MID].array_assembly,
                    include_subarray_templates,
                ),
            )
            if mid is not None
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=low_frequency_band(repository),
                capabilities=LowOfferedCapabilities.model_validate(
                    low.model_dump() | {"name": _name(low)}
                ),
                subarray_templates=_subarray_templates(
                    repository,
                    Telescope.SKA_LOW,
                    cycle.capabilities[Telescope.SKA_LOW].array_assembly,
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
    :param include_subarray_templates: whether to serve the subarray
        templates offered with each telescope's capabilities, as
        ``subarray_templates``.
    :return: the cycle views.
    :raises ArrayAssemblyNotFoundError: If a cycle names an array assembly
        that does not exist.
    :raises FileNotFoundError: If a cycle names a policy that does not exist.
    :raises ValueError: If a cycle offers more than one policy type.
    """
    return [
        get_cycle_configuration(repository, cycle_id, include_subarray_templates)
        for cycle_id in repository.get_cycle_ids()
    ]
