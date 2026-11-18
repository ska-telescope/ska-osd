"""The PHT views: what ska-oso-services serves to the PHT from GET
/prsls/osd/cycles and GET /prsls/osd/{cycle}: each cycle with the
capabilities each telescope offers and that telescope's basic capabilities. Its
models are its own, named and shaped as ska-oso-services' response models, so
the response doesn't change with the domain models."""

from datetime import datetime, timezone
from typing import Any

from pydantic import (
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import LowCapabilities, MidCapabilities
from ska_ost_osd.osd.models.cycles import Cycle, PolicyType
from ska_ost_osd.osd.repository import OSDRepository
from ska_ost_osd.osd.views.base import (
    NO_CHANNEL_LIMIT,
    ConfigurationModel,
)

# The PHT UI recognises science verification by its name
_TYPE_NAMES = {
    PolicyType.SCIENCE_VERIFICATION: "Science Verification",
    PolicyType.SHARED_RISK: "Shared Risk",
    PolicyType.STANDARD_OPERATIONS: "Proposal",
}


class CycleInformation(ConfigurationModel):
    """The cycle's ID and proposal window, as the PHT UI reads them."""

    cycle_id: str
    proposal_open: str
    proposal_close: str


class CyclePolicies(ConfigurationModel):
    """The cycle's proposal policy, as the PHT UI reads it."""

    normal_max_hours: float
    max_targets: int | None = None
    max_observation_setups: int | None = None
    max_data_products: int | None = None


class TelescopeCapabilities(ConfigurationModel):
    """The name of the capabilities each telescope offers in the cycle, or
    ``None``."""

    Mid: str | None = None
    Low: str | None = None


class ObservatoryPolicy(ConfigurationModel):
    """The cycle, as the PHT UI reads it."""

    cycle_number: int
    cycle_id: str | None = None
    type: str | None = None
    cycle_description: str
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: TelescopeCapabilities


class ReceiverInformation(ConfigurationModel):
    rx_id: str
    min_frequency_hz: float
    max_frequency_hz: float
    sub_bands: list[dict] | None = None


class BasicCapabilitiesMid(ConfigurationModel):
    dish_elevation_limit_deg: float
    receiver_information: list[ReceiverInformation]


class BasicCapabilitiesLow(ConfigurationModel):
    min_frequency_hz: float
    max_frequency_hz: float


class AA2_MID(ConfigurationModel):
    """Any one of Mid's array assemblies, with a policy's applied if one is
    given; ska-oso-services named the model after the first it served."""

    allowed_channel_count_range_max: list[int]
    allowed_channel_count_range_min: list[int]
    allowed_channel_width_values: list[int]
    allowed_channel_width_values_hz: list[int]
    available_receivers: list[str]
    number_ska_dishes: int
    number_meerkat_dishes: int
    number_meerkatplus_dishes: int
    max_baseline_km: float
    available_bandwidth_hz: float
    number_channels: int | None = None
    cbf_modes: list[str]
    number_zoom_windows: int
    number_zoom_channels: int
    number_pss_beams: int
    number_pst_beams: int
    ps_beam_bandwidth_hz: float
    number_fsps: int


class AA2_LOW(ConfigurationModel):
    """Any one of Low's array assemblies, with a policy's applied if one is
    given; ska-oso-services named the model after the first it served."""

    number_stations: int
    number_substations: int
    number_beams: int
    max_baseline_km: float
    available_bandwidth_hz: float
    channel_width_hz: float | None = None
    cbf_modes: list[str]
    number_zoom_windows: int
    number_zoom_channels: int
    number_pss_beams: int
    number_pst_beams: int
    number_vlbi_beams: int
    ps_beam_bandwidth_hz: float
    number_fsps: int


class CycleCapabilitiesBase(ConfigurationModel):
    """One telescope's capabilities in a cycle. Served keyed by the name of
    the policy or array assembly, e.g. ``"AA2": {...}``, beside
    ``basic_capabilities``."""

    name: str = Field(exclude=True)
    capabilities: AA2_MID | AA2_LOW

    @model_serializer(mode="wrap")
    def key_capabilities_by_name(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        data = handler(self)
        data[self.name] = data.pop("capabilities")
        return data


class MidCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: BasicCapabilitiesMid
    capabilities: AA2_MID


class LowCycleCapabilities(CycleCapabilitiesBase):
    basic_capabilities: BasicCapabilitiesLow
    capabilities: AA2_LOW


class CycleCapabilities(ConfigurationModel):
    """The telescopes a cycle offers; ``None`` for one it does not."""

    mid: MidCycleCapabilities | None = None
    low: LowCycleCapabilities | None = None


class CycleConfiguration(ConfigurationModel):
    """One cycle joined with what it offers."""

    observatory_policy: ObservatoryPolicy
    capabilities: CycleCapabilities


def _name(capabilities: MidCapabilities | LowCapabilities) -> str:
    """The name the PHT UI knows capabilities by: the policy's, or the array
    assembly's if no policy applies."""
    return capabilities.policy or capabilities.array_assembly


# Any Mid capabilities, in ska-oso-services' AA2_MID model
def _aa2_mid(capabilities: MidCapabilities) -> AA2_MID:
    observing_modes = capabilities.observing_modes
    receptors = capabilities.receptors
    max_channels = capabilities.cbf.max_channels
    return AA2_MID(
        allowed_channel_count_range_max=[
            NO_CHANNEL_LIMIT if max_channels is None else max_channels
        ],
        allowed_channel_count_range_min=[1],
        allowed_channel_width_values=capabilities.allowed_channel_width_values_hz,
        allowed_channel_width_values_hz=capabilities.allowed_channel_width_values_hz,
        available_receivers=capabilities.receivers,
        number_ska_dishes=receptors.number_ska_dishes,
        number_meerkat_dishes=receptors.number_meerkat_dishes,
        number_meerkatplus_dishes=receptors.number_meerkatplus_dishes,
        max_baseline_km=receptors.max_baseline_km,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        cbf_modes=capabilities.cbf.function_modes,
        number_zoom_windows=observing_modes.spectral.max_zoom_windows,
        number_zoom_channels=observing_modes.spectral.max_zoom_channels,
        number_pss_beams=observing_modes.pss.max_beams,
        number_pst_beams=observing_modes.pst.max_beams,
        ps_beam_bandwidth_hz=observing_modes.pss.beam_bandwidth_hz,
        number_fsps=capabilities.cbf.number_fsps,
    )


# Any Low capabilities, in ska-oso-services' AA2_LOW model
def _aa2_low(capabilities: LowCapabilities) -> AA2_LOW:
    observing_modes = capabilities.observing_modes
    subarray_beams = capabilities.sps.subarray_beams
    return AA2_LOW(
        number_stations=capabilities.receptors.number_stations,
        number_substations=subarray_beams.max_substations_per_subarray_beam,
        number_beams=subarray_beams.max_subarray_beams,
        max_baseline_km=capabilities.receptors.max_baseline_km,
        available_bandwidth_hz=capabilities.available_bandwidth_hz,
        cbf_modes=capabilities.cbf.function_modes,
        number_zoom_windows=observing_modes.spectral.max_zoom_windows,
        number_zoom_channels=observing_modes.spectral.max_zoom_channels,
        number_pss_beams=observing_modes.pss.max_beams,
        number_pst_beams=observing_modes.pst.max_beams,
        number_vlbi_beams=observing_modes.vlbi.max_beams,
        ps_beam_bandwidth_hz=observing_modes.pss.beam_bandwidth_hz,
        number_fsps=capabilities.cbf.number_fsps,
    )


def _basic_capabilities_mid(repository: OSDRepository) -> BasicCapabilitiesMid:
    basic_capabilities = repository.get_basic_capabilities(Telescope.SKA_MID)
    return BasicCapabilitiesMid(
        dish_elevation_limit_deg=basic_capabilities.elevation_limits.min_elevation_deg,
        receiver_information=[
            ReceiverInformation(
                rx_id=band.rx_id,
                min_frequency_hz=band.min_frequency_hz,
                max_frequency_hz=band.max_frequency_hz,
                sub_bands=(
                    None
                    if band.band5b_subbands is None
                    else [sub_band.model_dump() for sub_band in band.band5b_subbands]
                ),
            )
            for band in basic_capabilities.frequency_bands
        ],
    )


def _timestamp(moment: datetime) -> str:
    """A UTC time as the tmdata stores it, e.g. ``"2026-03-27T12:00:00.000Z"``."""
    return (
        moment.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


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
            proposal_open=_timestamp(cycle.proposal_window.opens),
            proposal_close=_timestamp(cycle.proposal_window.closes),
        ),
        cycle_policies=CyclePolicies(
            normal_max_hours=cycle.proposal_policy.max_observing_hours,
            max_targets=cycle.proposal_policy.max_targets,
            max_observation_setups=cycle.proposal_policy.max_observation_setups,
            max_data_products=cycle.proposal_policy.max_data_products,
        ),
        telescope_capabilities=TelescopeCapabilities(
            Mid=_name(mid) if mid is not None else None,
            Low=_name(low) if low is not None else None,
        ),
    )


def get_cycle_configuration(
    repository: OSDRepository, cycle_id: str
) -> CycleConfiguration:
    """Build one cycle's view for the PHT: what ska-oso-services serves from
    GET /prsls/osd/{cycle}.

    :param repository: the OSD repository to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle with, for each telescope it offers, the offered
        capabilities and that telescope's basic capabilities.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises ArrayAssemblyNotFoundError: If the cycle names an array assembly
        that does not exist.
    :raises PolicyNotFoundError: If the cycle names a policy that does not
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
                basic_capabilities=_basic_capabilities_mid(repository),
                name=_name(mid),
                capabilities=_aa2_mid(mid),
            )
            if mid is not None
            else None,
            low=LowCycleCapabilities(
                basic_capabilities=BasicCapabilitiesLow.model_validate(
                    repository.get_basic_capabilities(Telescope.SKA_LOW).frequency_band,
                    from_attributes=True,
                ),
                name=_name(low),
                capabilities=_aa2_low(low),
            )
            if low is not None
            else None,
        ),
    )


def get_cycle_configurations(repository: OSDRepository) -> list[CycleConfiguration]:
    """Build every cycle's view for the PHT, in ascending order of ID: what
    ska-oso-services serves from GET /prsls/osd/cycles.

    :param repository: the OSD repository to read from.
    :return: the cycle views.
    :raises ArrayAssemblyNotFoundError: If a cycle names an array assembly
        that does not exist.
    :raises PolicyNotFoundError: If a cycle names a policy that does not exist.
    :raises ValueError: If a cycle offers more than one policy type.
    """
    return [
        get_cycle_configuration(repository, cycle_id)
        for cycle_id in repository.get_cycle_ids()
    ]
