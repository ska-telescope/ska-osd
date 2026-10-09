"""Checks that the real tmdata files validate against their models.

This is the only test that reads the real tmdata. The other model tests use
the test copy in tests/tmdata, so changing the tmdata doesn't need them
updating.
"""

import json
from pathlib import Path

import pytest

from ska_ost_osd.osd.models.capabilities import LowCapabilities, MidCapabilities
from ska_ost_osd.osd.models.defaults import LowDefaults, MidDefaults
from ska_ost_osd.osd.models.observatory_policies import ObservatoryPolicy
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplateLibrary

TMDATA = Path(__file__).parents[4] / "tmdata"


@pytest.mark.parametrize(
    "model, path",
    [
        (MidCapabilities, "ska1_mid/mid_capabilities.json"),
        (LowCapabilities, "ska1_low/low_capabilities.json"),
        (MidDefaults, "ska1_mid/mid_defaults.json"),
        (LowDefaults, "ska1_low/low_defaults.json"),
        (ObservatoryPolicy, "observatory_policies.json"),
        (
            SubarrayTemplateLibrary,
            "subarray_templates/subarray_template_library.json",
        ),
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
