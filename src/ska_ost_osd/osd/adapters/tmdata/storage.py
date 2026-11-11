"""The storage layer of the TMData repository: functions that read each
tmdata file into its storage model. ``TMDataRepository`` maps these to the
reader models.

Each function takes the TMData to read from, so the caller chooses the
source and version and handles any caching.
"""

from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowBasicCapabilitiesFile,
    LowCapabilitySetFile,
    LowDefaultsFile,
    MidBasicCapabilitiesFile,
    MidCapabilitySetFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.common.constant import (
    OBSERVING_CYCLES_TMDATA_DIR,
    TELESCOPE_FILES,
    Telescope,
)

_CAPABILITY_SET_FILE_MODELS = {
    Telescope.SKA_MID: MidCapabilitySetFile,
    Telescope.SKA_LOW: LowCapabilitySetFile,
}

_BASIC_CAPABILITIES_FILE_MODELS = {
    Telescope.SKA_MID: MidBasicCapabilitiesFile,
    Telescope.SKA_LOW: LowBasicCapabilitiesFile,
}

_DEFAULTS_FILE_MODELS = {
    Telescope.SKA_MID: MidDefaultsFile,
    Telescope.SKA_LOW: LowDefaultsFile,
}


def get_cycle_paths(tmdata: TMData) -> dict[str, str]:
    """Find each cycle's file, ``cycles/<name>.json``. A cycle file may have
    any name: the cycle's ID is the ``id`` in the file.

    :param tmdata: TMData to read from.
    :return: the path of each cycle's file, keyed by cycle ID in ascending
        order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    :raises ValueError: If two cycle files have the same ``id`` or the same
        ``number``.
    """
    if not any(key.startswith(OBSERVING_CYCLES_TMDATA_DIR) for key in tmdata):
        raise FileNotFoundError(f"file not found: {OBSERVING_CYCLES_TMDATA_DIR}")
    paths = {}
    paths_by_number = {}
    for name in tmdata[OBSERVING_CYCLES_TMDATA_DIR]:
        if not name.endswith(".json"):
            continue
        path = f"{OBSERVING_CYCLES_TMDATA_DIR}/{name}"
        cycle = _read(tmdata, path)
        cycle_id, cycle_number = cycle["id"], cycle.get("number")
        # The ID identifies the cycle, so no two files may share one; nor may
        # two cycles with numbers share one, as the legacy OSD API looks cycles
        # up by number
        if cycle_id in paths:
            raise ValueError(f"id {cycle_id} is in both {paths[cycle_id]} and {path}")
        if cycle_number is not None:
            if cycle_number in paths_by_number:
                raise ValueError(
                    f"number {cycle_number} is in both "
                    f"{paths_by_number[cycle_number]} and {path}"
                )
            paths_by_number[cycle_number] = path
        paths[cycle_id] = path
    return dict(sorted(paths.items()))


def get_cycle_ids(tmdata: TMData) -> list[str]:
    """List the cycle IDs, from the ``id`` in each cycle file.

    :param tmdata: TMData to read from.
    :return: the cycle IDs in ascending order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    :raises ValueError: If two cycle files have the same ``id`` or the same
        ``number``.
    """
    return list(get_cycle_paths(tmdata))


def get_cycle_file(tmdata: TMData, cycle_id: str) -> CycleFile:
    """Read one cycle's file: the one whose ``id`` is the ID.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle file, as stored.
    :raises FileNotFoundError: If the tmdata has no cycles directory, or no
        cycle file has the ID.
    :raises ValueError: If two cycle files have the same ``id`` or the same
        ``number``.
    """
    paths = get_cycle_paths(tmdata)
    if cycle_id not in paths:
        raise FileNotFoundError(
            f"file not found: no cycle file in {OBSERVING_CYCLES_TMDATA_DIR} "
            f"has id {cycle_id}"
        )
    return CycleFile.model_validate(_read(tmdata, paths[cycle_id]))


@overload
def get_capability_set_files(
    tmdata: TMData, telescope: Literal[Telescope.SKA_MID]
) -> dict[str, MidCapabilitySetFile]: ...


@overload
def get_capability_set_files(
    tmdata: TMData, telescope: Literal[Telescope.SKA_LOW]
) -> dict[str, LowCapabilitySetFile]: ...


def get_capability_set_files(
    tmdata: TMData, telescope: Telescope
) -> dict[str, MidCapabilitySetFile] | dict[str, LowCapabilitySetFile]:
    """Read each of one telescope's capability set files,
    ``telescopes/<telescope>/capabilities/<name>.json``.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's capability set files keyed by name, the file
        name without ``.json``, in name order.
    :raises FileNotFoundError: If the tmdata has no capabilities directory
        for the telescope.
    """
    files = TELESCOPE_FILES[telescope]
    directory = files.capability_sets
    if not any(key.startswith(f"{directory}/") for key in tmdata):
        raise FileNotFoundError(f"file not found: {directory}")
    names = sorted(
        key.removesuffix(".json") for key in tmdata[directory] if key.endswith(".json")
    )
    return {
        name: _CAPABILITY_SET_FILE_MODELS[telescope].model_validate(
            _read(tmdata, files.capability_set(name))
        )
        for name in names
    }


@overload
def get_telescope_basic_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.SKA_MID]
) -> MidBasicCapabilitiesFile: ...


@overload
def get_telescope_basic_capabilities(
    tmdata: TMData, telescope: Literal[Telescope.SKA_LOW]
) -> LowBasicCapabilitiesFile: ...


def get_telescope_basic_capabilities(
    tmdata: TMData, telescope: Telescope
) -> MidBasicCapabilitiesFile | LowBasicCapabilitiesFile:
    """Read one telescope's basic capabilities file: Mid's receiver bands,
    or Low's frequency band and how it is divided into channels.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's basic capabilities.
    :raises FileNotFoundError: If the tmdata has no basic capabilities file
        for the telescope.
    """
    return _BASIC_CAPABILITIES_FILE_MODELS[telescope].model_validate(
        _read(tmdata, TELESCOPE_FILES[telescope].basic_capabilities)
    )


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.SKA_MID]
) -> MidDefaultsFile: ...


@overload
def get_telescope_defaults(
    tmdata: TMData, telescope: Literal[Telescope.SKA_LOW]
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
        _read(tmdata, TELESCOPE_FILES[telescope].defaults)
    )


def get_subarray_template_library(
    tmdata: TMData, telescope: Telescope, array_assembly: str
) -> SubarrayTemplateLibraryFile:
    """Read one array assembly's subarray template library file,
    ``telescopes/<telescope>/subarray_templates/<array_assembly>.json``.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :param array_assembly: the array assembly, e.g. ``"AA2"``.
    :return: the array assembly's template library.
    :raises FileNotFoundError: If the tmdata has no template library file
        for the array assembly.
    """
    return SubarrayTemplateLibraryFile.model_validate(
        _read(
            tmdata, TELESCOPE_FILES[telescope].subarray_template_library(array_assembly)
        )
    )


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every storage reader reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
