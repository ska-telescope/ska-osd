"""Unit tests for the PHT view's functions, using the test copy of the tmdata
in tests/tmdata."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import (
    ArrayAssemblyNotFoundError,
    CycleNotFoundError,
    PolicyNotFoundError,
)
from ska_ost_osd.osd.views import pht
from ska_ost_osd.osd.views.pht import CyclePolicies
from tests.unit.ska_ost_osd.osd.expected import (
    CYCLE_1_FILE,
    PHT_CYCLE_1_OBSERVATORY_POLICY,
    PHT_CYCLE_2_OBSERVATORY_POLICY,
    PHT_LOW_AA1,
    PHT_LOW_AA2,
    PHT_LOW_AA2_SV,
    PHT_LOW_BASIC_CAPABILITIES,
    PHT_MID_AA1,
    PHT_MID_AA2,
    PHT_MID_BASIC_CAPABILITIES,
)


@pytest.mark.parametrize(
    "cycle_id, expected",
    [
        ("TEST_SKAO_2027_Low_AA1_SV", PHT_CYCLE_1_OBSERVATORY_POLICY),
        ("TEST_SKAO_2027_AA2_Proposal", PHT_CYCLE_2_OBSERVATORY_POLICY),
    ],
    ids=["low only", "mid and low"],
)
def test_get_observatory_policy(test_tmdata_repository, cycle_id, expected):
    assert pht.get_observatory_policy(test_tmdata_repository, cycle_id) == expected


def test_get_observatory_policy_without_cycle_number_or_optional_limits(
    tmdata_repository_with,
):
    """A cycle's number and its proposal policy's limits are optional."""
    cycle = CYCLE_1_FILE.model_dump(mode="json", by_alias=True)
    del cycle["cycle_number"]
    cycle["proposal_policy"] = {"max_observing_hours": 100.0}
    repository = tmdata_repository_with(
        {"cycles/TEST_SKAO_2027_Low_AA1_SV.json": cycle}
    )

    assert pht.get_observatory_policy(
        repository, "TEST_SKAO_2027_Low_AA1_SV"
    ) == PHT_CYCLE_1_OBSERVATORY_POLICY.model_copy(
        update={
            "cycle_number": None,
            "cycle_policies": CyclePolicies(normal_max_hours=100.0),
        }
    )


def test_get_observatory_policy_raises_for_unknown_cycle(test_tmdata_repository):
    with pytest.raises(CycleNotFoundError):
        pht.get_observatory_policy(test_tmdata_repository, "NO_SUCH_CYCLE")


def test_get_observatory_policy_raises_when_cycle_offers_more_than_one_type(
    tmdata_repository_with,
):
    """The PHT UI handles one policy type per cycle."""
    repository = tmdata_repository_with(
        {
            "cycles/TEST_SKAO_2027_Low_AA1_SV.json": {
                **CYCLE_1_FILE.model_dump(mode="json", by_alias=True),
                "telescopes": {
                    "ska_low": {
                        "array_assembly": "AA1",
                        "policies": {
                            "science_verification": "AA1",
                            "shared_risk": "AA1",
                        },
                    }
                },
            }
        }
    )

    with pytest.raises(ValueError, match="more than one policy type"):
        pht.get_observatory_policy(repository, "TEST_SKAO_2027_Low_AA1_SV")


@pytest.mark.parametrize(
    "telescope, expected",
    [
        (Telescope.SKA_MID, PHT_MID_BASIC_CAPABILITIES),
        (Telescope.SKA_LOW, PHT_LOW_BASIC_CAPABILITIES),
    ],
    ids=["mid", "low"],
)
def test_get_basic_capabilities(test_tmdata_repository, telescope, expected):
    assert pht.get_basic_capabilities(test_tmdata_repository, telescope) == expected


def test_get_basic_capabilities_raises_when_files_missing(empty_tmdata_repository):
    with pytest.raises(FileNotFoundError):
        pht.get_basic_capabilities(empty_tmdata_repository, Telescope.SKA_MID)


@pytest.mark.parametrize(
    "telescope, array_assembly, policy_id, expected",
    [
        (Telescope.SKA_MID, "AA1", None, PHT_MID_AA1),
        (Telescope.SKA_MID, "AA2", None, PHT_MID_AA2),
        (Telescope.SKA_MID, "AA2", "AA2", PHT_MID_AA2),
        (Telescope.SKA_LOW, "AA1", None, PHT_LOW_AA1),
        (Telescope.SKA_LOW, "AA2", None, PHT_LOW_AA2),
        (Telescope.SKA_LOW, "AA2", "AA2_SV", PHT_LOW_AA2_SV),
    ],
    ids=[
        "mid AA1",
        "mid AA2",
        "mid AA2 with an empty policy",
        "low AA1",
        "low AA2",
        "low AA2 with the AA2_SV policy",
    ],
)
def test_get_capabilities(
    test_tmdata_repository, telescope, array_assembly, policy_id, expected
):
    assert (
        pht.get_capabilities(
            test_tmdata_repository, telescope, array_assembly, policy_id
        )
        == expected
    )


def test_get_capabilities_raises_for_unknown_array_assembly(test_tmdata_repository):
    with pytest.raises(ArrayAssemblyNotFoundError):
        pht.get_capabilities(test_tmdata_repository, Telescope.SKA_LOW, "AA3")


def test_get_capabilities_raises_for_unknown_policy(test_tmdata_repository):
    with pytest.raises(PolicyNotFoundError):
        pht.get_capabilities(
            test_tmdata_repository, Telescope.SKA_LOW, "AA2", "NO_SUCH_POLICY"
        )
