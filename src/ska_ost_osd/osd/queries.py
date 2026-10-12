"""Functions that read the OSD tmdata and return it as pydantic models.

Each function takes the TMData to read from, so the caller chooses the
source and version and handles any caching.
"""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    CAPABILITIES_JSON_FILE_PATHS,
    DEFAULTS_JSON_FILE_PATHS,
    OBSERVING_CYCLES_TMDATA_DIR,
    Telescope,
)
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowBasicCapabilities,
    LowCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilities,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.observatory_policies import CycleID, ObservatoryPolicy

_CAPABILITIES_MODELS = {
    Telescope.MID: MidCapabilities,
    Telescope.LOW: LowCapabilities,
}

_DEFAULTS_MODELS = {
    Telescope.MID: MidDefaults,
    Telescope.LOW: LowDefaults,
}


def get_cycle_ids(tmdata: TMData) -> list[CycleID]:
    """List the cycle IDs, from the ``cycles/cycle_<N>.json`` file names.

    :param tmdata: TMData to read from.
    :return: the cycle IDs in ascending order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    if not any(key.startswith(OBSERVING_CYCLES_TMDATA_DIR) for key in tmdata):
        raise FileNotFoundError(f"file not found: {OBSERVING_CYCLES_TMDATA_DIR}")
    return sorted(
        CycleID(int(key.removeprefix("cycle_").removesuffix(".json")))
        for key in tmdata[OBSERVING_CYCLES_TMDATA_DIR]
        if key.startswith("cycle_") and key.endswith(".json")
    )


def get_cycle(tmdata: TMData, cycle_id: CycleID) -> ObservatoryPolicy:
    """Read one cycle, from ``cycles/cycle_<N>.json``: its metadata,
    policies and the capability set each telescope offers.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    cycle_ids = get_cycle_ids(tmdata)
    if cycle_id not in cycle_ids:
        raise CycleNotFoundError(cycle_id, cycle_ids)
    return _read_cycle(tmdata, cycle_id)


def get_cycles(tmdata: TMData) -> list[ObservatoryPolicy]:
    """Read every cycle, in ascending order of ID.

    :param tmdata: TMData to read from.
    :return: the cycles.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    return [_read_cycle(tmdata, cycle_id) for cycle_id in get_cycle_ids(tmdata)]


@overload
def get_telescope_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> MidCapabilities: ...


@overload
def get_telescope_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> LowCapabilities: ...


def get_telescope_capabilities(
    tmdata: TMData, telescope: Telescope
) -> MidCapabilities | LowCapabilities:
    """Read one telescope's capabilities file: its elevation constraints,
    frequency bands and capability sets.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's capabilities.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope.
    """
    return _CAPABILITIES_MODELS[telescope].model_validate(
        _read(tmdata, CAPABILITIES_JSON_FILE_PATHS[telescope])
    )


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> MidDefaults: ...


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> LowDefaults: ...


def get_telescope_defaults(
    tmdata: TMData, telescope: Telescope
) -> MidDefaults | LowDefaults:
    """Read one telescope's defaults file: its avoidance constraints and,
    for Mid, the SPFRx defaults or, for Low, the quality attribute metrics.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's defaults.
    :raises FileNotFoundError: If the tmdata has no defaults file for the
        telescope.
    """
    return _DEFAULTS_MODELS[telescope].model_validate(
        _read(tmdata, DEFAULTS_JSON_FILE_PATHS[telescope])
    )


@overload
def get_basic_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> MidBasicCapabilities: ...


@overload
def get_basic_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> LowBasicCapabilities: ...


def get_basic_capabilities(
    tmdata: TMData, telescope: Telescope
) -> MidBasicCapabilities | LowBasicCapabilities:
    """Read one telescope's basic capabilities: Mid's receiver bands, or
    Low's frequency band and how it is divided into channels.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's basic capabilities.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope.
    """
    return get_telescope_capabilities(tmdata, telescope).basic_capabilities


@overload
def get_capability_sets(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> list[MidCapabilitySet]: ...


@overload
def get_capability_sets(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> list[LowCapabilitySet]: ...


def get_capability_sets(tmdata: TMData, telescope: Telescope) -> list[CapabilitySet]:
    """Read all of one telescope's capability sets, in the order the tmdata
    lists them.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's capability sets.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope.
    """
    return get_telescope_capabilities(tmdata, telescope).subarrays


@overload
def get_capability_set(
    tmdata: TMData, telescope: Literal[Telescope.MID], name: str
) -> MidCapabilitySet: ...


@overload
def get_capability_set(
    tmdata: TMData, telescope: Literal[Telescope.LOW], name: str
) -> LowCapabilitySet: ...


def get_capability_set(
    tmdata: TMData, telescope: Telescope, name: str
) -> CapabilitySet:
    """Read one capability set, identified by its telescope and name.

    :param tmdata: TMData to read from.
    :param telescope: the telescope the capability set belongs to.
    :param name: the name of the capability set, e.g. ``"AA0.5"``.
    :return: the capability set.
    :raises CapabilitySetNotFoundError: If the telescope has no capability
        set with that name.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope.
    """
    capability_sets = get_capability_sets(tmdata, telescope)
    for capability_set in capability_sets:
        if capability_set.name == name:
            return capability_set
    raise CapabilitySetNotFoundError(
        telescope, name, [capability_set.name for capability_set in capability_sets]
    )


def _read_cycle(tmdata: TMData, cycle_id: CycleID) -> ObservatoryPolicy:
    return ObservatoryPolicy.model_validate(
        _read(tmdata, f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{cycle_id}.json")
    )


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every query reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
