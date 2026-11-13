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
    LowCapabilitySetFile,
    LowDefaultsFile,
    MidBasicCapabilitiesFile,
    MidCapabilitySetFile,
    MidDefaultsFile,
    SubarrayTemplateLibraryFile,
)

TMDATA = Path(__file__).parents[4] / "tmdata"


@pytest.mark.parametrize(
    "model, path",
    [
        (MidBasicCapabilitiesFile, "telescopes/ska_mid/basic_capabilities.json"),
        (LowBasicCapabilitiesFile, "telescopes/ska_low/basic_capabilities.json"),
        (MidDefaultsFile, "telescopes/ska_mid/defaults.json"),
        (LowDefaultsFile, "telescopes/ska_low/defaults.json"),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_mid/subarray_templates/AA2.json",
        ),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_mid/subarray_templates/AA4.json",
        ),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_mid/subarray_templates/AASTAR.json",
        ),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_low/subarray_templates/AA2.json",
        ),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_low/subarray_templates/AA4.json",
        ),
        (
            SubarrayTemplateLibraryFile,
            "telescopes/ska_low/subarray_templates/AASTAR.json",
        ),
    ]
    + [
        (model, f"{directory}/{capability_set.name}")
        for model, directory in [
            (MidCapabilitySetFile, "telescopes/ska_mid/array_assemblies"),
            (LowCapabilitySetFile, "telescopes/ska_low/array_assemblies"),
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
