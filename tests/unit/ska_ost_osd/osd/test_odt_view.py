"""Unit tests for the ODT view's functions, using the test copy of the tmdata
in tests/tmdata."""

import pytest

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.exceptions import ArrayAssemblyNotFoundError, PolicyNotFoundError
from ska_ost_osd.osd.views import odt
from tests.unit.ska_ost_osd.osd.expected import (
    ODT_LOW_AA1,
    ODT_LOW_AA2,
    ODT_LOW_AA2_SV,
    ODT_LOW_CONSTRAINTS,
    ODT_LOW_FREQUENCY_BAND,
    ODT_LOW_QUALITY_ATTRIBUTE_METRICS,
    ODT_MID_AA1,
    ODT_MID_AA2,
    ODT_MID_CONSTRAINTS,
    ODT_MID_FREQUENCY_BANDS,
    ODT_MID_SPFRX_DEFAULTS,
)


@pytest.mark.parametrize(
    "telescope, expected",
    [
        (Telescope.SKA_MID, ODT_MID_FREQUENCY_BANDS),
        (Telescope.SKA_LOW, ODT_LOW_FREQUENCY_BAND),
    ],
    ids=["mid", "low"],
)
def test_get_basic_capabilities(test_tmdata_repository, telescope, expected):
    assert odt.get_basic_capabilities(test_tmdata_repository, telescope) == expected


def test_get_basic_capabilities_raises_when_files_missing(empty_tmdata_repository):
    with pytest.raises(FileNotFoundError):
        odt.get_basic_capabilities(empty_tmdata_repository, Telescope.SKA_MID)


@pytest.mark.parametrize(
    "telescope, expected",
    [
        (Telescope.SKA_MID, ODT_MID_CONSTRAINTS),
        (Telescope.SKA_LOW, ODT_LOW_CONSTRAINTS),
    ],
    ids=["mid", "low"],
)
def test_get_constraints(test_tmdata_repository, telescope, expected):
    assert odt.get_constraints(test_tmdata_repository, telescope) == expected


@pytest.mark.parametrize(
    "telescope, expected",
    [
        (Telescope.SKA_MID, ODT_MID_SPFRX_DEFAULTS),
        (Telescope.SKA_LOW, ODT_LOW_QUALITY_ATTRIBUTE_METRICS),
    ],
    ids=["mid", "low"],
)
def test_get_defaults(test_tmdata_repository, telescope, expected):
    assert odt.get_defaults(test_tmdata_repository, telescope) == expected


@pytest.mark.parametrize(
    "telescope, array_assembly, policy_id, expected",
    [
        (Telescope.SKA_MID, "AA1", None, ODT_MID_AA1),
        (Telescope.SKA_MID, "AA2", None, ODT_MID_AA2),
        (Telescope.SKA_MID, "AA2", "AA2", ODT_MID_AA2),
        (Telescope.SKA_LOW, "AA1", None, ODT_LOW_AA1),
        (Telescope.SKA_LOW, "AA2", None, ODT_LOW_AA2),
        (Telescope.SKA_LOW, "AA2", "AA2_SV", ODT_LOW_AA2_SV),
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
        odt.get_capabilities(
            test_tmdata_repository, telescope, array_assembly, policy_id
        )
        == expected
    )


def test_get_capabilities_raises_for_unknown_array_assembly(test_tmdata_repository):
    with pytest.raises(ArrayAssemblyNotFoundError):
        odt.get_capabilities(test_tmdata_repository, Telescope.SKA_LOW, "AA3")


def test_get_capabilities_raises_for_unknown_policy(test_tmdata_repository):
    with pytest.raises(PolicyNotFoundError):
        odt.get_capabilities(
            test_tmdata_repository, Telescope.SKA_LOW, "AA2", "NO_SUCH_POLICY"
        )
