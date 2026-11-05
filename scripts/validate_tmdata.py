"""Validate the tmdata files against the OSD storage models.

Each file in the repository's ``tmdata`` directory is read into its storage
model, then serialised and read back, which must give the same model. Every
problem is reported, and the script exits with status 1 if there are any.

Usage: ``python scripts/validate_tmdata.py``
"""

import json
import sys
from pathlib import Path

from pydantic import BaseModel, ValidationError

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowCapabilitiesFile,
    LowDefaultsFile,
    MidCapabilitiesFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)

TMDATA_DIR = Path(__file__).resolve().parents[1] / "tmdata"
FILE_MODELS: dict[str, type[BaseModel]] = {
    "ska1_mid/mid_capabilities.json": MidCapabilitiesFile,
    "ska1_low/low_capabilities.json": LowCapabilitiesFile,
    "ska1_mid/mid_defaults.json": MidDefaultsFile,
    "ska1_low/low_defaults.json": LowDefaultsFile,
    "observatory_policies.json": CycleFile,
    "subarray_templates/subarray_template_library.json": SubarrayTemplateLibraryFile,
}
CYCLE_FILES = "cycles/cycle_*.json"


def get_file_models(tmdata_dir: Path) -> dict[str, type[BaseModel]]:
    """Map each file to validate to its storage model.

    :param tmdata_dir: the tmdata directory.
    :return: the storage model of each file, keyed by its path relative to
        ``tmdata_dir``.
    """
    return FILE_MODELS | {
        path.relative_to(tmdata_dir).as_posix(): CycleFile
        for path in sorted(tmdata_dir.glob(CYCLE_FILES))
    }


def validate_file(path: Path, model: type[BaseModel]) -> list[str]:
    """Validate one file, and that it reads back the same once serialised.

    :param path: the file to validate.
    :param model: the storage model of the file.
    :return: the problems found, empty if the file is valid.
    """
    try:
        with open(path, encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        return ["file not found"]
    except json.JSONDecodeError as error:
        return [f"invalid JSON: {error}"]

    try:
        instance = model.model_validate(data)
    except ValidationError as error:
        return describe(error)

    try:
        read_back = model.model_validate_json(instance.model_dump_json(by_alias=True))
    except ValidationError as error:
        return [f"once serialised, {problem}" for problem in describe(error)]
    if read_back != instance:
        return ["once serialised, it reads back as a different model"]
    return []


def validate_tmdata(tmdata_dir: Path) -> list[str]:
    """Validate every tmdata file that has a storage model.

    :param tmdata_dir: the tmdata directory.
    :return: the problems found, each prefixed by its file, empty if the
        tmdata is valid.
    """
    file_models = get_file_models(tmdata_dir)
    problems = []
    if file_models.keys() == FILE_MODELS.keys():
        problems.append(f"{CYCLE_FILES}: no cycle files found")
    for name, model in file_models.items():
        problems.extend(
            f"{name}: {problem}" for problem in validate_file(tmdata_dir / name, model)
        )
    return problems


def describe(error: ValidationError) -> list[str]:
    """Describe each error of a validation, prefixed by its location.

    :param error: the validation error.
    :return: one description per error.
    """
    descriptions = []
    for detail in error.errors():
        location = ".".join(str(part) for part in detail["loc"])
        descriptions.append(
            f"{location}: {detail['msg']}" if location else detail["msg"]
        )
    return descriptions


def main() -> int:
    """Validate the repository's tmdata directory.

    :return: the exit status, 1 if any problem was found.
    """
    problems = validate_tmdata(TMDATA_DIR)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{len(problems)} problem(s) in the tmdata", file=sys.stderr)
        return 1

    print(f"{len(get_file_models(TMDATA_DIR))} tmdata files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
