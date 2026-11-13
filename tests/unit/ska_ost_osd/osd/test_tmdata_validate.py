"""Unit tests for the osd-validate-tmdata command.

These use the test copy of the tmdata in tests/tmdata, copied so each test can
break it.
"""

import json
import shutil
from pathlib import Path

import pytest
from pydantic import BaseModel, field_serializer, field_validator, model_validator

from ska_ost_osd.osd.adapters.tmdata.validate import (
    main,
    validate_file,
    validate_tmdata,
)

TESTS_TMDATA = Path(__file__).parents[3] / "tmdata"

LOW_DEFAULTS = "telescopes/ska_low/defaults.json"


class Value(BaseModel):
    value: int


@pytest.fixture(name="tmdata")
def tmdata_fixture(tmp_path: Path) -> Path:
    tmdata = tmp_path / "tmdata"
    shutil.copytree(TESTS_TMDATA, tmdata)
    return tmdata


def write(path: Path, data: object) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_valid_tmdata_has_no_problems(tmdata):
    assert validate_tmdata(tmdata) == []


def test_missing_file_is_reported(tmdata):
    (tmdata / LOW_DEFAULTS).unlink()

    assert validate_tmdata(tmdata) == [f"{LOW_DEFAULTS}: file not found"]


def test_missing_cycle_files_are_reported(tmdata):
    shutil.rmtree(tmdata / "cycles")

    assert validate_tmdata(tmdata) == ["cycles: no cycle files found"]


def test_invalid_json_is_reported(tmdata):
    (tmdata / LOW_DEFAULTS).write_text("{", encoding="utf-8")

    [problem] = validate_tmdata(tmdata)

    assert problem.startswith(f"{LOW_DEFAULTS}: invalid JSON: ")


def test_validation_error_is_reported_with_its_location(tmdata):
    data = json.loads((tmdata / LOW_DEFAULTS).read_text(encoding="utf-8"))
    data["constraints"]["sun_avoidance_angle_deg"] = "high"
    write(tmdata / LOW_DEFAULTS, data)

    [problem] = validate_tmdata(tmdata)

    assert problem.startswith(f"{LOW_DEFAULTS}: constraints.sun_avoidance_angle_deg: ")


def test_validation_error_without_location_is_reported(tmp_path):
    path = tmp_path / "file.json"
    write(path, [])

    assert validate_file(path, Value) == [
        "Input should be a valid dictionary or instance of Value"
    ]


def test_unexpected_error_is_reported(tmp_path):
    class Crashes(BaseModel):
        @model_validator(mode="before")
        @classmethod
        def crash(cls, data):
            raise KeyError("mode")

    path = tmp_path / "file.json"
    write(path, {})

    assert validate_file(path, Crashes) == ["could not be validated: KeyError: 'mode'"]


def test_unreadable_serialisation_is_reported(tmp_path):
    class SerialisesBadly(Value):
        @field_serializer("value")
        def serialise(self, value: int) -> str:
            return "one"

    path = tmp_path / "file.json"
    write(path, {"value": 1})

    [problem] = validate_file(path, SerialisesBadly)

    assert problem.startswith("once serialised, value: ")


def test_different_serialisation_is_reported(tmp_path):
    class Increments(Value):
        @field_validator("value")
        @classmethod
        def increment(cls, value: int) -> int:
            return value + 1

    path = tmp_path / "file.json"
    write(path, {"value": 1})

    assert validate_file(path, Increments) == [
        "once serialised, it reads back as a different model"
    ]


def test_main_passes_valid_tmdata(tmdata, capsys):
    assert main([str(tmdata)]) == 0
    assert capsys.readouterr().out == "17 tmdata files are valid\n"


def test_main_defaults_to_tmdata_where_it_is_run(tmdata, monkeypatch, capsys):
    monkeypatch.chdir(tmdata.parent)

    assert main([]) == 0
    assert capsys.readouterr().out == "17 tmdata files are valid\n"


def test_main_fails_invalid_tmdata(tmdata, capsys):
    (tmdata / LOW_DEFAULTS).unlink()

    assert main([str(tmdata)]) == 1
    assert capsys.readouterr().err == (
        f"{LOW_DEFAULTS}: file not found\n1 problem(s) in the tmdata\n"
    )


def test_main_fails_without_tmdata_directory(tmp_path, capsys):
    missing = tmp_path / "missing"

    assert main([str(missing)]) == 1
    assert capsys.readouterr().err == f"no tmdata directory at {missing}\n"
