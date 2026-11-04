"""Checks that the real tmdata files validate against their models.

This is the only test that reads the real tmdata. The other model tests use
the test copy in tests/tmdata, so changing the tmdata doesn't need them
updating.
"""

import json
from pathlib import Path

import pytest

from ska_ost_osd.osd.adapters.tmdata.models import (
    CycleFile,
    LowBasicCapabilitiesFile,
    LowCapabilitiesFile,
    LowCapabilitySetFile,
    LowDefaultsFile,
    MidBasicCapabilitiesFile,
    MidCapabilitiesFile,
    MidCapabilitySetFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)

TMDATA = Path(__file__).parents[4] / "tmdata"


@pytest.mark.parametrize(
    "model, path",
    [
        (MidCapabilitiesFile, "ska1_mid/mid_capabilities.json"),
        (LowCapabilitiesFile, "ska1_low/low_capabilities.json"),
        (MidBasicCapabilitiesFile, "ska1_mid/basic_capabilities.json"),
        (LowBasicCapabilitiesFile, "ska1_low/basic_capabilities.json"),
        (MidDefaultsFile, "ska1_mid/mid_defaults.json"),
        (LowDefaultsFile, "ska1_low/low_defaults.json"),
        (CycleFile, "observatory_policies.json"),
        (SubarrayTemplateLibraryFile, "ska1_mid/subarray_templates/AA2.json"),
        (SubarrayTemplateLibraryFile, "ska1_mid/subarray_templates/AA4.json"),
        (SubarrayTemplateLibraryFile, "ska1_mid/subarray_templates/AASTAR.json"),
        (SubarrayTemplateLibraryFile, "ska1_low/subarray_templates/AA2.json"),
        (SubarrayTemplateLibraryFile, "ska1_low/subarray_templates/AA4.json"),
        (SubarrayTemplateLibraryFile, "ska1_low/subarray_templates/AASTAR.json"),
    ]
    + [
        (model, f"{directory}/{capability_set.name}")
        for model, directory in [
            (MidCapabilitySetFile, "ska1_mid/capabilities"),
            (LowCapabilitySetFile, "ska1_low/capabilities"),
        ]
        for capability_set in sorted((TMDATA / directory).glob("*.json"))
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
