"""Functions that read the OSD tmdata and return it as pydantic models.

Each function takes the TMData to read from, so the caller chooses the
source and version and handles any caching.
"""

from fnmatch import fnmatchcase
from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import (
    CAPABILITIES_JSON_FILE_PATHS,
    DEFAULTS_JSON_FILE_PATHS,
    OBSERVING_CYCLES_TMDATA_DIR,
    SUBARRAY_TEMPLATES_PATH,
    Telescope,
)
from ska_ost_osd.osd.exceptions import CapabilitySetNotFoundError, CycleNotFoundError
from ska_ost_osd.osd.models.capabilities import (
    CapabilitySet,
    LowCapabilitiesFile,
    LowCapabilitySet,
    MidCapabilitiesFile,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.configuration import Constraints
from ska_ost_osd.osd.models.cycles import Cycle, CycleFile, CycleID
from ska_ost_osd.osd.models.defaults import (
    LowDefaultsFile,
    MidDefaultsFile,
)
from ska_ost_osd.osd.models.subarray_templates import (
    SubarrayTemplate,
    SubarrayTemplateLibraryFile,
)

_CAPABILITIES_FILE_MODELS = {
    Telescope.MID: MidCapabilitiesFile,
    Telescope.LOW: LowCapabilitiesFile,
}

_DEFAULTS_FILE_MODELS = {
    Telescope.MID: MidDefaultsFile,
    Telescope.LOW: LowDefaultsFile,
}

# The fields of a cycle's telescope_capabilities, by telescope
_CYCLE_TELESCOPE_FIELDS = {
    Telescope.MID: "ska_mid",
    Telescope.LOW: "ska_low",
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


def get_cycle(tmdata: TMData, cycle_id: CycleID) -> Cycle:
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
    return Cycle.model_validate(get_cycle_file(tmdata, cycle_id), from_attributes=True)


def get_cycle_file(tmdata: TMData, cycle_id: CycleID) -> CycleFile:
    """Read one cycle's file, ``cycles/cycle_<N>.json``.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle file, as stored.
    :raises FileNotFoundError: If the file is missing.
    """
    return CycleFile.model_validate(
        _read(tmdata, f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{cycle_id}.json")
    )


@overload
def get_telescope_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> MidCapabilitiesFile: ...


@overload
def get_telescope_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> LowCapabilitiesFile: ...


def get_telescope_capabilities(
    tmdata: TMData, telescope: Telescope
) -> MidCapabilitiesFile | LowCapabilitiesFile:
    """Read one telescope's capabilities file: its elevation constraints,
    frequency bands and capability sets.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's capabilities.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope.
    """
    return _CAPABILITIES_FILE_MODELS[telescope].model_validate(
        _read(tmdata, CAPABILITIES_JSON_FILE_PATHS[telescope])
    )


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.MID]
) -> MidDefaultsFile: ...


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.LOW]
) -> LowDefaultsFile: ...


def get_telescope_defaults(
    tmdata: TMData, telescope: Telescope
) -> MidDefaultsFile | LowDefaultsFile:
    """Read one telescope's defaults file: its avoidance constraints and,
    for Mid, the SPFRx defaults or, for Low, the quality attribute metrics.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's defaults.
    :raises FileNotFoundError: If the tmdata has no defaults file for the
        telescope.
    """
    return _DEFAULTS_FILE_MODELS[telescope].model_validate(
        _read(tmdata, DEFAULTS_JSON_FILE_PATHS[telescope])
    )


def get_constraints(tmdata: TMData, telescope: Telescope) -> Constraints:
    """Read one telescope's observing constraints: the elevation limits from
    its capabilities file and the sun, moon and Jupiter avoidance angles
    from its defaults file.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's constraints.
    :raises FileNotFoundError: If the tmdata has no capabilities or no
        defaults file for the telescope.
    """
    return Constraints.combine(
        get_telescope_capabilities(tmdata, telescope),
        get_telescope_defaults(tmdata, telescope),
    )


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


def get_subarray_template_library(tmdata: TMData) -> SubarrayTemplateLibraryFile:
    """Read the subarray template library file: every template, for both
    telescopes.

    :param tmdata: TMData to read from.
    :return: the template library.
    :raises FileNotFoundError: If the tmdata has no template library file.
    """
    return SubarrayTemplateLibraryFile.model_validate(
        _read(tmdata, SUBARRAY_TEMPLATES_PATH)
    )


def get_subarray_templates(
    tmdata: TMData, telescope: Telescope, capability_set: str
) -> list[SubarrayTemplate]:
    """Read the subarray templates a capability set offers.

    A template belongs to the capability set when its name matches one of
    the set's ``subarray_templates`` patterns (e.g. ``"*_AA2"``) and starts
    with the set's telescope (e.g. ``"MID_"``). A pattern alone is not
    enough: ``"*_AA2"`` matches both telescopes' AA2 templates.

    :param tmdata: TMData to read from.
    :param telescope: the telescope the capability set belongs to.
    :param capability_set: the name of the capability set, e.g. ``"AA2"``.
    :return: the matching templates, in the order the library lists them.
    :raises CapabilitySetNotFoundError: If the telescope has no capability
        set with that name.
    :raises FileNotFoundError: If the tmdata has no capabilities file for
        the telescope, or no template library file.
    """
    patterns = (
        get_capability_set(tmdata, telescope, capability_set).subarray_templates or []
    )
    prefix = f"{telescope.value.upper()}_"
    return [
        template
        for template in get_subarray_template_library(tmdata).templates
        if template.name.startswith(prefix)
        and any(fnmatchcase(template.name, pattern) for pattern in patterns)
    ]


def get_cycle_capability_sets(
    tmdata: TMData, cycle_id: CycleID
) -> dict[Telescope, CapabilitySet]:
    """Read the capability sets a cycle offers: at most one per telescope.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the offered capability set for each telescope the cycle
        offers; telescopes it does not offer are left out.
    :raises CycleNotFoundError: If there is no cycle with that ID.
    :raises CapabilitySetNotFoundError: If the cycle names a capability set
        that does not exist.
    :raises FileNotFoundError: If the tmdata has no cycles directory or no
        capabilities file for an offered telescope.
    """
    offered = get_cycle(tmdata, cycle_id).telescope_capabilities
    return {
        telescope: get_capability_set(tmdata, telescope, name)
        for telescope, field in _CYCLE_TELESCOPE_FIELDS.items()
        if (name := getattr(offered, field)) is not None
    }


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every query reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
