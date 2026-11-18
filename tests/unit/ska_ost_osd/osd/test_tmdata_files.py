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
    LowArrayAssemblyFile,
    LowBasicCapabilitiesFile,
    LowDefaultsFile,
    LowPolicyFile,
    MidArrayAssemblyFile,
    MidBasicCapabilitiesFile,
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
        (model, f"{directory}/{array_assembly.name}")
        for model, directory in [
            (MidArrayAssemblyFile, "telescopes/ska_mid/array_assemblies"),
            (LowArrayAssemblyFile, "telescopes/ska_low/array_assemblies"),
        ]
        for array_assembly in sorted((TMDATA / directory).glob("*.json"))
    ]
    + [
        (LowPolicyFile, "telescopes/ska_low/policies/AA2.json"),
        (LowPolicyFile, "telescopes/ska_low/policies/AA2_SV.json"),
        (CycleFile, "cycles/TEST_SKAO_2027_Low_AA2_Proposal.json"),
        (CycleFile, "cycles/TEST_SKAO_2027_Low_AA2_SV.json"),
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
