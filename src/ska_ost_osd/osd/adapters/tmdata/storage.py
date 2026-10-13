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
    LowCapabilitiesFile,
    LowDefaultsFile,
    MidCapabilitiesFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.common.constant import (
    CAPABILITIES_JSON_FILE_PATHS,
    DEFAULTS_JSON_FILE_PATHS,
    OBSERVING_CYCLES_TMDATA_DIR,
    SUBARRAY_TEMPLATES_PATH,
    Telescope,
)
from ska_ost_osd.osd.models.cycles import CycleID

_CAPABILITIES_FILE_MODELS = {
    Telescope.MID: MidCapabilitiesFile,
    Telescope.LOW: LowCapabilitiesFile,
}

_DEFAULTS_FILE_MODELS = {
    Telescope.MID: MidDefaultsFile,
    Telescope.LOW: LowDefaultsFile,
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


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every storage reader reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
