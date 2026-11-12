import logging

import pytest
from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.constant import Telescope, osd_file_mapping
from ska_ost_osd.osd.osd import get_osd_data, get_osd_using_tmdata
from tests.unit.ska_ost_osd.osd.expected import CYCLE_1_LEGACY_OBSERVATORY_POLICY


@pytest.mark.parametrize(
    "telescope, array_assembly, expected_telescopes",
    [
        (None, None, {"mid", "low"}),
        (
            "mid",
            None,
            {"mid"},
        ),
        (
            "mid",
            "AA1",
            {"mid"},
        ),
    ],
)
def test_get_osd_data(
    telescope,
    array_assembly,
    expected_telescopes,
    tests_tmdata,
):
    """Check that get_osd_data returns the expected telescope entries.

    :param telescope: Mid or Low
    :param array_assembly: Array Assembly AA1, AA2
    :param expected_telescopes: telescope entries in the OSD response
    :param tests_tmdata: tmdata fixture
    :returns: assert equals values
    """

    result, _ = get_osd_data(
        telescope, array_assembly, tmdata=tests_tmdata, process_templates=False
    )
    assert set(result["capabilities"]) == expected_telescopes


def test_get_osd_data_without_cycle_returns_complete_catalogue(tests_tmdata):
    """A request without a cycle returns all available capability data."""
    result, error_msgs = get_osd_data(tmdata=tests_tmdata)

    assert error_msgs == []
    assert "observatory_policy" not in result
    assert set(result["capabilities"]) == {"mid", "low"}

    for capability in ("mid", "low"):
        assert set(result["capabilities"][capability]) == {
            "basic_capabilities",
            "AA1",
            "AA2",
        }


def test_invalid_get_osd_data_capability(tests_tmdata):
    """This test case checks if the output of the get_osd_data when
    capabilities is given incorrect with correct array_assembly it should
    return the appropriate error messages.

    :param tests_tmdata: tests_tmdata
    """

    _, error_msgs = get_osd_data(
        telescope="midd",
        array_assembly="AA1",
        tmdata=tests_tmdata,
        process_templates=False,
    )
    assert error_msgs == [
        "Capability midd is invalid. Valid capabilities are low, mid,"
        " observatory_policies."
    ]


def test_get_osd_data_invalid_capability_only(tests_tmdata):
    """This test case checks that the output of the get_osd_data when
    an invalid telescope is provided without an array assembly returns
    the appropriate error messages.

    :param tests_tmdata: tests_tmdata
    """
    _, error_msgs = get_osd_data(
        telescope="invalid",
        array_assembly=None,
        tmdata=tests_tmdata,
        process_templates=False,
    )
    assert error_msgs == [
        "Capability invalid is invalid. Valid capabilities are low, mid,"
        " observatory_policies."
    ]


def test_invalid_get_osd_data_array_assembly(tests_tmdata):
    """This test case checks if the output of the get_osd_data when
    array_assembly is given incorrect with correct capabilities it should
    return the appropriate error messages.

    :param tests_tmdata: tests_tmdata
    """
    aa_value = "AA100000"

    _, error_msgs = get_osd_data(
        telescope="mid",
        array_assembly=aa_value,
        tmdata=tests_tmdata,
        process_templates=False,
    )

    assert len(error_msgs) == 1
    assert (
        error_msgs[0]
        == f"Array assembly {aa_value} is invalid. Valid array assemblies are AA1, AA2."
    )


@pytest.mark.parametrize(
    "invalid_array_assembly", ["constraints", "basic_capabilities"]
)
def test_get_osd_data_array_assembly_rejects_non_array_assembly_keys(
    invalid_array_assembly, tests_tmdata
):
    """ "constraints" and "basic_capabilities" are keys of the capabilities
    document, not named array assemblies, so requesting either as one
    should be rejected rather than returned as if it were a valid
    capability set.

    :param invalid_array_assembly: the non-array-assembly key under test
    :param tests_tmdata: tests_tmdata
    """
    osd_data, error_msgs = get_osd_data(
        telescope="mid",
        array_assembly=invalid_array_assembly,
        tmdata=tests_tmdata,
        process_templates=False,
    )

    assert osd_data is None
    assert error_msgs == [
        f"Array assembly {invalid_array_assembly} is invalid. Valid array assemblies are"
        " AA1, AA2."
    ]


def test_get_osd_data_missing_subarray_templates_falls_back_to_empty(
    tests_tmdata, monkeypatch
):
    """When process_templates is requested but the TMData source has no
    subarray_templates file, get_osd_data should fall back to treating the
    template data as empty rather than raising.

    :param tests_tmdata: tests_tmdata
    :param monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setitem(osd_file_mapping, "subarray_templates", "missing")

    osd_data, error_msgs = get_osd_data(
        telescope="mid",
        array_assembly="AA1",
        tmdata=tests_tmdata,
        process_templates=True,
    )

    assert error_msgs == []
    assert "AA1" in osd_data["capabilities"]["mid"]


def test_get_osd_data_with_process_templates(tests_tmdata):
    """Test that process_templates parameter is properly passed through."""
    # Test with process_templates=False (default)
    result_false, _ = get_osd_data(
        telescope="mid",
        array_assembly="AA1",
        tmdata=tests_tmdata,
        process_templates=False,
    )

    # Test with process_templates=True
    result_true, _ = get_osd_data(
        telescope="mid",
        array_assembly="AA1",
        tmdata=tests_tmdata,
        process_templates=True,
    )

    # Both should return valid data structures
    assert "capabilities" in result_false
    assert "capabilities" in result_true
    assert "mid" in result_false["capabilities"]
    assert "mid" in result_true["capabilities"]


def test_get_osd_data_processes_templates(tests_tmdata):
    """With process_templates=True, a capability set's template pattern is
    replaced by its array assembly's templates."""
    result, _ = get_osd_data(
        telescope="mid",
        array_assembly="AA2",
        tmdata=tests_tmdata,
        process_templates=True,
    )

    assert "subarray_templates" in result["capabilities"]["mid"]["AA2"]
    assert (
        "SKA_MID_FULL_AA2" in result["capabilities"]["mid"]["AA2"]["subarray_templates"]
    )


@pytest.fixture
def failing_tmdata(tests_tmdata_source, monkeypatch):
    """TMData fixture that fails on item access to simulate CAR backend errors."""
    tmdata = TMData(source_uris=[tests_tmdata_source])

    def raise_car_backend_error(_, __):
        raise ValueError(
            "car://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#tmdata "
            "not found in SKA CAR - make sure to add tmdata CI!"
        )

    monkeypatch.setattr(TMData, "__getitem__", raise_car_backend_error)
    return tmdata


def test_get_osd_using_tmdata_cycle_uses_selected_cycle_file(tests_tmdata):
    """A cycle-specific query includes its selected cycle-file policy."""
    osd_data = get_osd_using_tmdata(tests_tmdata, cycle_id=2)

    assert osd_data["observatory_policy"]["cycle_number"] == 2
    assert osd_data["observatory_policy"]["cycle_id"] == "TEST_SKAO_2027_AA2_Proposal"
    assert set(osd_data["capabilities"]) == {"mid", "low"}


def test_get_osd_using_tmdata_cycle_observatory_policy(tests_tmdata):
    """The legacy response serves the cycle as observatory_policy, with the
    telescopes keyed Mid and Low."""
    osd_data = get_osd_using_tmdata(tests_tmdata, cycle_id=1)

    assert osd_data["observatory_policy"] == CYCLE_1_LEGACY_OBSERVATORY_POLICY


def test_get_osd_using_tmdata_cycle_capability_uses_cycle_array_assembly(
    tests_tmdata,
):
    """A cycle and capability query uses the array assembly from the cycle."""
    osd_data = get_osd_using_tmdata(
        tests_tmdata, telescope=Telescope.SKA_MID, cycle_id=2
    )

    assert list(osd_data["capabilities"]) == ["mid"]
    assert set(osd_data["capabilities"]["mid"]) == {"basic_capabilities", "AA2"}


def test_get_osd_using_tmdata_capability_only_returns_complete_catalogue(
    tests_tmdata,
):
    """A capability-only query returns all of that capability's assemblies."""
    osd_data = get_osd_using_tmdata(tests_tmdata, telescope=Telescope.SKA_MID)

    assert "observatory_policy" not in osd_data
    assert set(osd_data["capabilities"]) == {"mid"}
    assert set(osd_data["capabilities"]["mid"]) == {"basic_capabilities", "AA1", "AA2"}


@pytest.mark.parametrize(
    "telescope, key, array_assembly",
    [
        (Telescope.SKA_MID, "mid", "AA1"),
        (Telescope.SKA_MID, "mid", "AA2"),
        (Telescope.SKA_LOW, "low", "AA1"),
        (Telescope.SKA_LOW, "low", "AA2"),
        ("mid", "mid", "AA1"),
        ("low", "low", "AA1"),
    ],
)
def test_get_osd_using_tmdata_catalogue_filter(
    telescope, key, array_assembly, tests_tmdata
):
    """A non-cycle filter selects catalogue data without a cycle policy."""
    osd_data = get_osd_using_tmdata(
        tests_tmdata, telescope=telescope, array_assembly=array_assembly
    )

    assert "observatory_policy" not in osd_data
    assert list(osd_data["capabilities"]) == [key]
    assert array_assembly in osd_data["capabilities"][key]


def test_get_osd_using_tmdata_serves_low_modes_flat(tests_tmdata):
    """Low's modes, stations and station beamforming are served under their
    legacy names."""
    osd_data = get_osd_using_tmdata(tests_tmdata, telescope=Telescope.SKA_LOW)

    capability_set = osd_data["capabilities"]["low"]["AA2"]
    assert "modes" not in capability_set
    assert capability_set["number_zoom_windows"] == 0
    assert capability_set["number_zoom_channels"] == 0
    assert capability_set["allowed_zoom_factors"] == [1, 2, 4, 8]
    assert capability_set["number_pss_beams"] == 0
    assert capability_set["ps_beam_bandwidth_hz"] == 75_000_000.0
    assert capability_set["number_pst_beams"] == 1
    assert capability_set["number_vlbi_beams"] == 0
    assert "station_beamforming" not in capability_set
    assert capability_set["number_subarray_beams"] == 8
    assert capability_set["number_substations"] == 512
    assert "stations" not in capability_set
    assert capability_set["number_stations"] == 8
    assert capability_set["max_baseline_km"] == 6.0
    assert capability_set["number_station_ids"] == [
        345,
        346,
        347,
        348,
        349,
        350,
        351,
        352,
    ]


def test_get_osd_using_tmdata_serves_mid_modes_flat(tests_tmdata):
    """Mid's modes are served under their legacy names, and its capability
    sets with templates processed have no constraints."""
    osd_data = get_osd_using_tmdata(
        tests_tmdata, telescope=Telescope.SKA_MID, process_templates=True
    )

    assert "constraints" not in osd_data["capabilities"]["mid"]
    capability_set = osd_data["capabilities"]["mid"]["AA2"]
    assert "modes" not in capability_set
    assert capability_set["number_pss_beams"] == 0
    assert capability_set["ps_beam_bandwidth_hz"] == 400_000_000
    assert capability_set["number_pst_beams"] == 1
    assert "dishes" not in capability_set
    assert capability_set["number_ska_dishes"] == 8
    assert capability_set["number_meerkat_dishes"] == 0
    assert capability_set["max_baseline_km"] == 1.5
    assert capability_set["number_dish_ids"][0] == "SKA001"
    assert capability_set["number_zoom_windows"] == 0
    assert capability_set["number_zoom_channels"] == 0
    assert "allowed_zoom_factors" not in capability_set


def test_get_osd_using_tmdata_band_5b_has_sub_bands(tests_tmdata):
    """Band 5b of the Mid basic capabilities is split into sub-bands."""
    osd_data = get_osd_using_tmdata(
        tests_tmdata, telescope=Telescope.SKA_MID, array_assembly="AA1"
    )
    band_5b = osd_data["capabilities"]["mid"]["basic_capabilities"][
        "receiver_information"
    ][5]

    assert len(band_5b["sub_bands"]) == 3


def test_get_osd_using_tmdata_matching_array_assembly_is_redundant(
    tests_tmdata, caplog
):
    """A matching explicit assembly does not override the cycle policy."""
    with caplog.at_level(logging.WARNING):
        osd_data = get_osd_using_tmdata(
            tests_tmdata, telescope=Telescope.SKA_MID, array_assembly="AA2", cycle_id=2
        )

    assert list(osd_data["capabilities"]) == ["mid"]
    assert "AA2" in osd_data["capabilities"]["mid"]
    assert (
        "Ignoring redundant array assembly AA2 for capability mid in cycle 2"
        in caplog.messages
    )


@pytest.mark.parametrize(
    "query, expected_errors",
    [
        (
            {"array_assembly": "AA1"},
            ["Array assembly requires a capability."],
        ),
        (
            {"cycle_id": 2, "array_assembly": "AA1"},
            ["Cycle_id and Array_assembly cannot be used together."],
        ),
        (
            {"telescope": Telescope.SKA_MID, "cycle_id": 2, "array_assembly": "AA1"},
            [
                "Array assembly AA1 does not match capability mid in cycle 2."
                " Expected AA2."
            ],
        ),
        (
            {"telescope": Telescope.SKA_MID, "cycle_id": 1},
            ["Capability mid is invalid for cycle 1. Valid capabilities are low."],
        ),
    ],
)
def test_get_osd_using_tmdata_invalid_query(query, expected_errors, tests_tmdata):
    """An invalid combination of query filters raises a ValueError listing the
    errors."""
    with pytest.raises(ValueError) as error:
        get_osd_using_tmdata(tests_tmdata, **query)

    assert error.value.args[0] == expected_errors


def test_get_osd_using_tmdata_invalid_cycle_id(tests_tmdata):
    """A cycle with no cycle file raises a ValueError naming the cycle."""
    with pytest.raises(ValueError) as error:
        get_osd_using_tmdata(tests_tmdata, telescope=Telescope.SKA_MID, cycle_id=3)

    assert "Cycle 3 is invalid" in error.value.args[0][0]


def test_get_osd_using_tmdata_surfaces_tmdata_read_errors(failing_tmdata):
    """An error reading the TMData source is raised to the caller."""
    with pytest.raises(ValueError, match="not found in SKA CAR"):
        get_osd_using_tmdata(failing_tmdata, cycle_id=1)
