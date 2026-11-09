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
    BASIC_CAPABILITIES_JSON_FILE_PATHS,
    CAPABILITY_SETS_TMDATA_DIRS,
    DEFAULTS_JSON_FILE_PATHS,
    OBSERVING_CYCLES_TMDATA_DIR,
    SUBARRAY_TEMPLATES_TMDATA_DIRS,
    Telescope,
)
from ska_ost_osd.osd.models.cycles import CycleID

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


def get_cycle_ids(tmdata: TMData) -> list[CycleID]:
    """List the cycle IDs, from the ``cycles/cycle_<N>.json`` file names.

    :param tmdata: TMData to read from.
    :return: the cycle IDs in ascending order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    """
    if not any(key.startswith(OBSERVING_CYCLES_TMDATA_DIR) for key in tmdata):
        raise FileNotFoundError(f"file not found: {OBSERVING_CYCLES_TMDATA_DIR}")
    return sorted(
        CycleID(key.removeprefix("cycle_").removesuffix(".json"))
        for key in tmdata[OBSERVING_CYCLES_TMDATA_DIR]
        if key.startswith("cycle_") and key.endswith(".json")
    )


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
    ``telescopes/ska1_<telescope>/capabilities/<name>.json``.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's capability set files keyed by name, the file
        name without ``.json``, in name order.
    :raises FileNotFoundError: If the tmdata has no capabilities directory
        for the telescope.
    """
    directory = CAPABILITY_SETS_TMDATA_DIRS[telescope]
    if not any(key.startswith(f"{directory}/") for key in tmdata):
        raise FileNotFoundError(f"file not found: {directory}")
    names = sorted(
        key.removesuffix(".json") for key in tmdata[directory] if key.endswith(".json")
    )
    return {
        name: _CAPABILITY_SET_FILE_MODELS[telescope].model_validate(
            _read(tmdata, f"{directory}/{name}.json")
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
        _read(tmdata, BASIC_CAPABILITIES_JSON_FILE_PATHS[telescope])
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
        _read(tmdata, DEFAULTS_JSON_FILE_PATHS[telescope])
    )


def get_subarray_template_library(
    tmdata: TMData, telescope: Telescope, array_assembly: str
) -> SubarrayTemplateLibraryFile:
    """Read one array assembly's subarray template library file,
    ``telescopes/ska1_<telescope>/subarray_templates/<array_assembly>.json``.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :param array_assembly: the array assembly, e.g. ``"AA2"``.
    :return: the array assembly's template library.
    :raises FileNotFoundError: If the tmdata has no template library file
        for the array assembly.
    """
    return SubarrayTemplateLibraryFile.model_validate(
        _read(
            tmdata, f"{SUBARRAY_TEMPLATES_TMDATA_DIRS[telescope]}/{array_assembly}.json"
        )
    )


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every storage reader reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
