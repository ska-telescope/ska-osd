"""The PHT view: the parts of what ska-oso-services serves to the PHT from GET
/prsls/osd/cycles and GET /prsls/osd/{cycle}. ska-oso-services chooses which
array assemblies and policies to serve, and assembles its response. The models
are the view's own, named and shaped as ska-oso-services' response models, so
the response doesn't change with the domain models."""

from datetime import datetime, timezone
from typing import Literal, overload

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.capabilities import (
    LowCapabilities,
    MidBasicCapabilities,
    MidCapabilities,
)
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


def _timestamp(moment: datetime) -> str:
    """A UTC time as the tmdata stores it, e.g. ``"2026-03-27T12:00:00.000Z"``."""
    return (
        moment.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _policy_type(cycle: Cycle) -> PolicyType:
    """The one policy type the cycle offers; the PHT UI handles one per
    cycle."""
    types = {
        policy_type
        for offered in cycle.telescopes.values()
        for policy_type in offered.policies
    }
    if len(types) != 1:
        raise ValueError(
            f"Cycle {cycle.cycle_id} offers more than one policy type, which the "
            "PHT view can't serve"
        )
    (policy_type,) = types
    return policy_type


def get_observatory_policy(
    repository: OSDRepository, cycle_id: str
) -> ObservatoryPolicy:
    """A cycle, as the PHT reads it. Its telescope_capabilities name the
    policy each telescope offers, which ska-oso-services serves the
    capabilities under.

    :param repository: the OSD repository to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises ValueError: If the cycle offers more than one policy type.
    """
    cycle = repository.get_cycle(cycle_id)
    policy_type = _policy_type(cycle)
    names = {
        telescope: offered.policies.get(policy_type)
        for telescope, offered in cycle.telescopes.items()
    }
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
            Mid=names.get(Telescope.SKA_MID), Low=names.get(Telescope.SKA_LOW)
        ),
    )


@overload
def get_basic_capabilities(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_MID]
) -> BasicCapabilitiesMid: ...


@overload
def get_basic_capabilities(
    repository: OSDRepository, telescope: Literal[Telescope.SKA_LOW]
) -> BasicCapabilitiesLow: ...


def get_basic_capabilities(
    repository: OSDRepository, telescope: Telescope
) -> BasicCapabilitiesMid | BasicCapabilitiesLow:
    """A telescope's basic capabilities, as the PHT reads them: Mid's dish
    elevation limit and receiver bands, or Low's frequency range.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :return: the telescope's basic capabilities.
    """
    basic_capabilities = repository.get_basic_capabilities(telescope)
    if isinstance(basic_capabilities, MidBasicCapabilities):
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
                        else [
                            sub_band.model_dump() for sub_band in band.band5b_subbands
                        ]
                    ),
                )
                for band in basic_capabilities.frequency_bands
            ],
        )
    return BasicCapabilitiesLow.model_validate(
        basic_capabilities.frequency_band, from_attributes=True
    )


@overload
def get_capabilities(
    repository: OSDRepository,
    telescope: Literal[Telescope.SKA_MID],
    array_assembly: str,
    policy_id: str | None = None,
) -> AA2_MID: ...


@overload
def get_capabilities(
    repository: OSDRepository,
    telescope: Literal[Telescope.SKA_LOW],
    array_assembly: str,
    policy_id: str | None = None,
) -> AA2_LOW: ...


def get_capabilities(
    repository: OSDRepository,
    telescope: Telescope,
    array_assembly: str,
    policy_id: str | None = None,
) -> AA2_MID | AA2_LOW:
    """An array assembly's capabilities, with a policy's applied if one is
    given, as the PHT reads them.

    :param repository: the OSD repository to read from.
    :param telescope: the telescope.
    :param array_assembly: the array assembly, e.g. ``"AA2"``.
    :param policy_id: the ID of a policy to apply, e.g. ``"AA2_SV"``.
    :return: the capabilities.
    :raises ArrayAssemblyNotFoundError: If there is no such array assembly.
    :raises PolicyNotFoundError: If there is no such policy.
    """
    capabilities = repository.get_capabilities(telescope, array_assembly, policy_id)
    if isinstance(capabilities, MidCapabilities):
        return _aa2_mid(capabilities)
    return _aa2_low(capabilities)
