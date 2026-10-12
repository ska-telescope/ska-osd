"""Checks that the real tmdata files validate against their models.

This is the only test that reads the real tmdata. The other model tests use
the test copy in tests/tmdata, so changing the tmdata doesn't need them
updating.
"""

import json
from pathlib import Path

import pytest

from ska_ost_osd.osd.models.capabilities import LowCapabilitiesFile, MidCapabilitiesFile
from ska_ost_osd.osd.models.cycles import CycleFile
from ska_ost_osd.osd.models.defaults import LowDefaultsFile, MidDefaultsFile
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplateLibraryFile

TMDATA = Path(__file__).parents[4] / "tmdata"


@pytest.mark.parametrize(
    "model, path",
    [
        (MidCapabilitiesFile, "ska1_mid/mid_capabilities.json"),
        (LowCapabilitiesFile, "ska1_low/low_capabilities.json"),
        (MidDefaultsFile, "ska1_mid/mid_defaults.json"),
        (LowDefaultsFile, "ska1_low/low_defaults.json"),
        (CycleFile, "observatory_policies.json"),
        (
            SubarrayTemplateLibraryFile,
            "subarray_templates/subarray_template_library.json",
        ),
    ]
    + [
        (CycleFile, f"cycles/{cycle.name}")
        for cycle in sorted((TMDATA / "cycles").glob("cycle_*.json"))
    ],
)
def test_tmdata_file_serialises(model, path):
    """Each tmdata file validates against its model, and the model's JSON
    reads back to the same model."""
    with open(TMDATA / path, encoding="utf-8") as json_file:
        instance = model.model_validate(json.load(json_file))

    assert (
        model.model_validate_json(instance.model_dump_json(by_alias=True)) == instance
    )
