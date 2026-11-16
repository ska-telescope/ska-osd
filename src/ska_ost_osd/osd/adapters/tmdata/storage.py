"""The storage layer of the TMData repository: functions that read each
tmdata file into its storage model. ``TMDataRepository`` maps these to the
reader models.

Each function takes the TMData to read from, so the caller chooses the
source and version and handles any caching.
"""

from collections.abc import Iterator
from typing import Literal, overload

from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowArrayAssemblyFile,
    LowBasicCapabilitiesFile,
    LowDefaultsFile,
    LowPolicyFile,
    MidArrayAssemblyFile,
    MidBasicCapabilitiesFile,
    MidDefaultsFile,
    MidPolicyFile,
    SubarrayTemplateLibraryFile,
)
from ska_ost_osd.osd.common.constant import (
    OBSERVING_CYCLES_TMDATA_DIR,
    TELESCOPE_FILES,
    Telescope,
)

_ARRAY_ASSEMBLY_FILE_MODELS = {
    Telescope.SKA_MID: MidArrayAssemblyFile,
    Telescope.SKA_LOW: LowArrayAssemblyFile,
}

_POLICY_FILE_MODELS = {
    Telescope.SKA_MID: MidPolicyFile,
    Telescope.SKA_LOW: LowPolicyFile,
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
    any name: the cycle's ID is the ``cycle_id`` in the file.

    :param tmdata: TMData to read from.
    :return: the path of each cycle's file, keyed by cycle ID in ascending
        order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    :raises ValueError: If two cycle files have the same ``cycle_id``.
    """
    return _paths_by_id(tmdata, OBSERVING_CYCLES_TMDATA_DIR, "cycle_id")


def get_cycle_ids(tmdata: TMData) -> list[str]:
    """List the cycle IDs, from the ``cycle_id`` in each cycle file.

    :param tmdata: TMData to read from.
    :return: the cycle IDs in ascending order.
    :raises FileNotFoundError: If the tmdata has no cycles directory.
    :raises ValueError: If two cycle files have the same ``cycle_id``.
    """
    return list(get_cycle_paths(tmdata))


def get_cycle_file(tmdata: TMData, cycle_id: str) -> CycleFile:
    """Read one cycle's file: the one whose ``cycle_id`` is the ID.

    :param tmdata: TMData to read from.
    :param cycle_id: the ID of the cycle.
    :return: the cycle file, as stored.
    :raises FileNotFoundError: If the tmdata has no cycles directory, or no
        cycle file has the ID.
    :raises ValueError: If two cycle files have the same ``cycle_id``.
    """
    return CycleFile.model_validate(
        _contents_with_id(tmdata, OBSERVING_CYCLES_TMDATA_DIR, "cycle_id", cycle_id)
    )


def get_policy_paths(tmdata: TMData, telescope: Telescope) -> dict[str, str]:
    """Find each of one telescope's policy files,
    ``telescopes/<telescope>/policies/<name>.json``. A policy file may have
    any name: the policy's ID is the ``policy`` in the file.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the path of each policy's file, keyed by policy ID in ascending
        order.
    :raises FileNotFoundError: If the tmdata has no policies directory for
        the telescope.
    :raises ValueError: If two policy files have the same ``policy``.
    """
    return _paths_by_id(tmdata, TELESCOPE_FILES[telescope].policies, "policy")


@overload
def get_policy_file(
    tmdata: TMData, telescope: Literal[Telescope.SKA_MID], policy_id: str
) -> MidPolicyFile: ...


@overload
def get_policy_file(
    tmdata: TMData, telescope: Literal[Telescope.SKA_LOW], policy_id: str
) -> LowPolicyFile: ...


def get_policy_file(
    tmdata: TMData, telescope: Telescope, policy_id: str
) -> MidPolicyFile | LowPolicyFile:
    """Read one of a telescope's policy files: the one whose ``policy`` is the
    ID.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :param policy_id: the ID of the policy.
    :return: the policy file, as stored.
    :raises FileNotFoundError: If the tmdata has no policies directory for
        the telescope, or no policy file has the ID.
    :raises ValueError: If two policy files have the same ``policy``.
    """
    return _POLICY_FILE_MODELS[telescope].model_validate(
        _contents_with_id(
            tmdata, TELESCOPE_FILES[telescope].policies, "policy", policy_id
        )
    )


@overload
def get_array_assembly_files(
    tmdata: TMData, telescope: Literal[Telescope.SKA_MID]
) -> dict[str, MidArrayAssemblyFile]: ...


@overload
def get_array_assembly_files(
    tmdata: TMData, telescope: Literal[Telescope.SKA_LOW]
) -> dict[str, LowArrayAssemblyFile]: ...


def get_array_assembly_files(
    tmdata: TMData, telescope: Telescope
) -> dict[str, MidArrayAssemblyFile] | dict[str, LowArrayAssemblyFile]:
    """Read each of one telescope's array assembly files,
    ``telescopes/<telescope>/array_assemblies/<name>.json``. A file may have
    any name: the array assembly is the ``array_assembly`` in the file.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :return: the telescope's array assembly files keyed by array assembly, in
        ascending order.
    :raises FileNotFoundError: If the tmdata has no array_assemblies
        directory for the telescope.
    :raises ValueError: If two files have the same ``array_assembly``.
    """
    contents = _contents_by_id(
        tmdata, TELESCOPE_FILES[telescope].array_assemblies, "array_assembly"
    )
    return {
        array_assembly: _ARRAY_ASSEMBLY_FILE_MODELS[telescope].model_validate(data)
        for array_assembly, data in contents.items()
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
    """Read one array assembly's subarray template library file: the one
    whose ``array_assembly`` is the array assembly.

    :param tmdata: TMData to read from.
    :param telescope: the telescope.
    :param array_assembly: the array assembly, e.g. ``"AA2"`` or ``"AA*"``.
    :return: the array assembly's template library.
    :raises FileNotFoundError: If the tmdata has no subarray_templates
        directory for the telescope, or no library file for the array
        assembly.
    :raises ValueError: If two library files have the same ``array_assembly``.
    """
    return SubarrayTemplateLibraryFile.model_validate(
        _contents_with_id(
            tmdata,
            TELESCOPE_FILES[telescope].subarray_templates,
            "array_assembly",
            array_assembly,
        )
    )


def _iterate_files_by_id(
    tmdata: TMData, directory: str, field: str
) -> Iterator[tuple[str, str, dict]]:
    """Read each file in a directory, whatever its name, with the ID it has in
    the field that names what it describes.

    :return: an iterator of each file's ID, path and contents.
    :raises FileNotFoundError: If the tmdata has no such directory.
    :raises ValueError: If two files have the same ID.
    """
    if not any(key.startswith(f"{directory}/") for key in tmdata):
        raise FileNotFoundError(f"file not found: {directory}")
    paths = {}
    for name in tmdata[directory]:
        if not name.endswith(".json"):
            continue
        path = f"{directory}/{name}"
        contents = _read(tmdata, path)
        file_id = contents[field]
        if file_id in paths:
            raise ValueError(
                f"{field} {file_id} is in both {paths[file_id]} and {path}"
            )
        paths[file_id] = path
        yield file_id, path, contents


def _paths_by_id(tmdata: TMData, directory: str, field: str) -> dict[str, str]:
    """Each file's path in a directory, by ID in ascending order."""
    return dict(
        sorted(
            (file_id, path)
            for file_id, path, _ in _iterate_files_by_id(tmdata, directory, field)
        )
    )


def _contents_by_id(tmdata: TMData, directory: str, field: str) -> dict[str, dict]:
    """Each file's contents in a directory, by ID in ascending order."""
    return dict(
        sorted(
            (file_id, contents)
            for file_id, _, contents in _iterate_files_by_id(tmdata, directory, field)
        )
    )


def _contents_with_id(tmdata: TMData, directory: str, field: str, file_id: str) -> dict:
    """The contents of the file in a directory with the ID.

    :raises FileNotFoundError: If the tmdata has no such directory, or no
        file has the ID.
    """
    contents = _contents_by_id(tmdata, directory, field)
    if file_id not in contents:
        raise FileNotFoundError(
            f"file not found: no file in {directory} has {field} {file_id}"
        )
    return contents[file_id]


def _read(tmdata: TMData, path: str) -> dict:
    """Read one tmdata file. Every storage reader reads tmdata through here."""
    try:
        return tmdata[path].get_dict()
    except KeyError as error:
        raise FileNotFoundError(f"file not found: {path}") from error
