import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

import pytest
from ska_telmodel.data import TMData
from ska_telmodel.schema import example_by_uri

from ska_ost_osd.telvalidation.oet_tmc_validators import (
    validate_json,
    validate_target_is_visible,
)
from ska_ost_osd.telvalidation.schematic_validation_exceptions import (
    SchemanticValdidationKeyError,
    SchematicValidationError,
)
from ska_ost_osd.telvalidation.semantic_validator import (
    fetch_capabilities_from_osd,
    fetch_matched_capabilities_from_basic_capabilities,
    search_and_return_value_from_basic_capabilities,
    semantic_validate,
)

sources = [
    "file://tmdata",
    "car:ska-telmodel-data?main",
]


capabilities = {
    "observatory_policy": {
        "cycle_number": 2,
        "cycle_description": "Science Verification",
        "cycle_information": {
            "cycle_id": "SKAO_2027_1",
            "proposal_open": "20260327T12:00:00.000Z",
            "proposal_close": "20260512T15:00:00.000z",
        },
        "cycle_policies": {"normal_max_hours": 100.0},
        "telescope_capabilities": {"Mid": "AA2", "Low": "AA2"},
    },
    "capabilities": {
        "mid": {
            "AA0.5": {
                "available_receivers": ["Band_1", "Band_2"],
                "number_ska_dishes": 4,
                "number_meerkat_dishes": 0,
                "number_meerkatplus_dishes": 0,
                "max_baseline_km": 1.5,
                "available_bandwidth_hz": 800000.0,
                "number_channels": 14880,
                "number_zoom_windows": 0,
                "number_zoom_channels": 0,
                "number_pss_beams": 0,
                "number_pst_beams": 0,
                "ps_beam_bandwidth_hz": 0.0,
                "number_fsps": 4,
            },
            "basic_capabilities": {
                "dish_elevation_limit_deg": 15.0,
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    },
                    {
                        "rx_id": "Band_2",
                        "min_frequency_hz": 950000000.0,
                        "max_frequency_hz": 1760000000.0,
                    },
                    {
                        "rx_id": "Band_3",
                        "min_frequency_hz": 1650000000.0,
                        "max_frequency_hz": 3050000000.0,
                    },
                    {
                        "rx_id": "Band_4",
                        "min_frequency_hz": 2800000000.0,
                        "max_frequency_hz": 5180000000.0,
                    },
                    {
                        "rx_id": "Band_5a",
                        "min_frequency_hz": 4600000000.0,
                        "max_frequency_hz": 8500000000.0,
                    },
                    {
                        "rx_id": "Band_5b",
                        "min_frequency_hz": 8300000000.0,
                        "max_frequency_hz": 15400000000.0,
                    },
                ],
            },
        },
        "low": {
            "AA0.5": {
                "number_stations": 4,
                "number_substations": 0,
                "number_beams": 1,
                "max_baseline_km": 3.0,
                "available_bandwidth_hz": 75000000.0,
                "channel_width_hz": 5400,
                "cbf_modes": ["vis", "pst"],
                "number_zoom_windows": 0,
                "number_zoom_channels": 0,
                "number_pss_beams": 0,
                "number_pst_beams": 1,
                "number_vlbi_beams": 0,
                "ps_beam_bandwidth_hz": 75000000.0,
                "number_fsps": 6,
            },
            "basic_capabilities": {
                "dish_elevation_limit_deg": 15.0,
                "receiver_information": [
                    {
                        "rx_id": "Band_1",
                        "min_frequency_hz": 350000000.0,
                        "max_frequency_hz": 1050000000.0,
                    },
                    {
                        "rx_id": "Band_2",
                        "min_frequency_hz": 950000000.0,
                        "max_frequency_hz": 1760000000.0,
                    },
                    {
                        "rx_id": "Band_3",
                        "min_frequency_hz": 1650000000.0,
                        "max_frequency_hz": 3050000000.0,
                    },
                    {
                        "rx_id": "Band_4",
                        "min_frequency_hz": 2800000000.0,
                        "max_frequency_hz": 5180000000.0,
                    },
                    {
                        "rx_id": "Band_5a",
                        "min_frequency_hz": 4600000000.0,
                        "max_frequency_hz": 8500000000.0,
                    },
                    {
                        "rx_id": "Band_5b",
                        "min_frequency_hz": 8300000000.0,
                        "max_frequency_hz": 15400000000.0,
                    },
                ],
            },
        },
    },
}


@pytest.fixture(scope="module")
def tm_data():
    return TMData(sources)


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data


VALID_MID_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_valid_mid_assign.json"
)
INVALID_MID_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_invalid_mid_assign.json"
)
VALID_MID_CONFIGURE_JSON = load_string_from_file(
    "test_files/testfile_valid_mid_configure.json"
)
INVALID_MID_CONFIGURE_JSON = load_string_from_file(
    "test_files/testfile_invalid_mid_configure.json"
)
VALID_LOW_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_valid_low_assign.json"
)
INVALID_LOW_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_invalid_low_assign.json"
)
VALID_LOW_CONFIGURE_JSON = load_string_from_file(
    "test_files/testfile_valid_low_configure.json"
)
INVALID_LOW_CONFIGURE_JSON = load_string_from_file(
    "test_files/testfile_invalid_low_configure.json"
)


INVALID_MID_VALIDATE_CONSTANT = {
    "AA0.5": {
        "assign_resource": {
            "dish": {
                "receptor_ids": [
                    {
                        "rules": "(0 < len(receptor_ids) <= 0)",
                        "error": (
                            "receptor_ids are                             too"
                            " many!Current Limit is 4"
                        ),
                    }
                ]
            }
        }
    }
}

INPUT_COMMAND_CONFIG = {
    "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["0001"]},
}

ARRAY_ASSEMBLY = "AA0.5"


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_assignresources_valid_inputs(mock1, tm_data):  # pylint: disable=W0621
    """
    Test semantic validate assign resource command with valid inputs.
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock1.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = VALID_MID_ASSIGN_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    assert semantic_validate(config, tm_data=tm_data), True


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_assignresources_invalid_inputs(mock2, tm_data):  # pylint: disable=W0621
    """
    Test semantic validate assign resource command with invalid inputs.
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock2.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = INVALID_MID_ASSIGN_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    try:
        semantic_validate(config, tm_data=tm_data)

    except SchematicValidationError as error:
        assert (
            error.message
            == "receptor_ids are too many!Current Limit is 4\n"
            "beams are too many! Current limit is 1\n"
            "Invalid function for beams! Currently allowed visibilities\n"
            "spectral windows are too many! Current limit = 1\n"
            "Invalid input for channel_count! Currently allowed 14880\n"
            "Invalid input for freq_min\n"
            "Invalid input for freq_max\n"
            "freq_min should be less than freq_max\n"
            "length of receptor_ids should be same as length of receptors\n"
            "receptor_ids did not match receptors"
        )


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_configure_valid_inputs(cnf_mock, tm_data):  # pylint: disable=W0621
    """Test validations by modifying appropriately
    the fields from default example
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    cnf_mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = VALID_MID_CONFIGURE_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    assert semantic_validate(config, tm_data=tm_data)


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_configure_invalid_inputs(mock, tm_data):  # pylint: disable=W0621
    """Test validations by modifying appropriately
    the fields from default example
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = INVALID_MID_CONFIGURE_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    try:
        semantic_validate(config, tm_data=tm_data)

    except SchematicValidationError as error:
        assert (
            error.message
            == "Invalid input for receiver_band! Currently allowed [1,2]\n"
            "FSPs are too many!Current Limit = 4\n"
            "Invalid input for fsp_id!\n"
            "Invalid input for function_mode\n"
            "Invalid input for zoom_factor\n"
            "frequency_slice_id did not match fsp_id\n"
            "frequency_band did not match receiver_band"
        )


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_validate_scemantic_json_input_keys(mock6):
    """
    Test if error is raised when invalid key is passed.
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock6.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    with pytest.raises(
        SchemanticValdidationKeyError,
        match="Invalid rule and error key passed",
    ):
        validate_json(
            INVALID_MID_VALIDATE_CONSTANT,
            INPUT_COMMAND_CONFIG,
            error_msg_list=[],
            parent_key=None,
            capabilities=capabilities,
        )


def test_tmc_configure_ra_dec():
    """
    Test if error is raised only when target is not
    possible to be observed at given time
    """
    # check for a src which is always below 15 degrees for mid telescope
    config = INVALID_MID_CONFIGURE_JSON
    configure_ver = config["interface"]
    config = example_by_uri(configure_ver)
    # check no error is raised for a src which
    # is always above 15 degrees for mid telescope
    assert config["pointing"]["target"]["ra"] == "21:08:47.92"
    assert config["pointing"]["target"]["dec"] == "-88:57:22.9"


class TestTargetVisibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tm_data = TMData(sources)

    def test_target_is_visible_mid(self):
        ra_str = "21:08:47.92"
        dec_str = "-88:57:22.9"
        telescope = "mid"
        observing_time = datetime(2023, 5, 8, 20, 30)

        expected_output = True

        self.assertEqual(
            validate_target_is_visible(
                ra_str,
                dec_str,
                telescope,
                "target_mid",
                tm_data=self.tm_data,
                observing_time=observing_time,
            ),
            expected_output,
        )

    def test_target_is_visible_low(self):
        ra = "21:08:47.92"
        dec = "-88:57:22.9"
        telescope = "low"
        observing_time = datetime(2023, 5, 8, 20, 30)

        expected_output = True
        self.assertEqual(
            validate_target_is_visible(
                ra, dec, telescope, "target_low", self.tm_data, observing_time
            ),
            expected_output,
        )

    def test_target_is_visible_unknown_name(self):
        ra = "21:08:47.92"
        dec = "-88:57:22.9"
        telescope = "asd"
        observing_time = datetime(2023, 5, 8, 20, 30)

        with pytest.raises(
            SchematicValidationError,
            match="Invalid telescope name",
        ):
            validate_target_is_visible(
                ra, dec, telescope, "asd", self.tm_data, observing_time
            )

    @patch("ska_ost_osd.telvalidation.oet_tmc_validators.ra_dec_to_az_el")
    def test_temp_list_length_less_than_3(self, mock_ra_dec_to_az_el):
        # Mock ra_dec_to_az_el to return temp_list with length < 3
        mock_ra_dec_to_az_el.return_value = [180, 60]

        ra = "21:08:47.92"
        dec = "-88:57:22.9"
        telescope = "low"
        observing_time = datetime(2023, 5, 8, 20, 30)
        expected_result = (
            "Telescope: low target observing during 2023-05-08T12:30:00 is not visible"
        )

        with self.assertRaises(SchematicValidationError) as context:
            validate_target_is_visible(
                ra, dec, telescope, "target_low", self.tm_data, observing_time
            )

        # Assert that the exception was raised
        self.assertIsInstance(context.exception, SchematicValidationError)
        # Assert that the error message matches the expected result
        self.assertEqual(str(context.exception), expected_result)

    def test_target_is_visible_low_with_utc(self):
        ra = "21:08:47.92"
        dec = "-88:57:22.9"
        telescope = "low"

        expected_output = True
        self.assertEqual(
            validate_target_is_visible(ra, dec, telescope, "target_low", self.tm_data),
            expected_output,
        )


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_low_assignresources_valid_inputs(mock, tm_data):  # pylint: disable=W0621
    """
    Test to verify valid inputs for low assign resource command
    """
    osd_capabilities = capabilities["capabilities"]["low"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = VALID_LOW_ASSIGN_JSON
    interface = config["interface"]
    # sample values that pass semantic only
    del config["interface"]  # to test use of interface key
    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    assert semantic_validate(config, tm_data=tm_data), True


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_low_assignresources_invalid_inputs(mock, tm_data):  # pylint: disable=W0621
    """
    Test to verify spectral window value in assign resource
    command value for semantic validation
    """
    osd_capabilities = capabilities["capabilities"]["low"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = INVALID_LOW_ASSIGN_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    try:
        semantic_validate(config, tm_data=tm_data)

    except SchematicValidationError as error:
        assert (
            error.message
            == "beams are too many! Current limit is 1\n"
            "Invalid function for beams! Currently allowed visibilities\n"
            "spectral windows are too many! Current limit = 1"
        )


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_low_configure_valid_inputs(mock, tm_data):  # pylint: disable=W0621
    """
    Test to verify function_mode  value in configure
    command input for semantic validation
    """
    osd_capabilities = capabilities["capabilities"]["low"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = VALID_LOW_CONFIGURE_JSON
    # sample values that pass semantic only
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)
    config["interface"] = interface

    assert semantic_validate(config, tm_data)


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_tmc_low_configure_invalid_inputs(mock, tm_data):  # pylint: disable=W0621
    """
    Test to verify fsp_ids value in assign resource
    command input for semantic validation
    """
    osd_capabilities = capabilities["capabilities"]["low"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    config = INVALID_LOW_CONFIGURE_JSON
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match="""interface is missing from observing_command_input.
        Please provide interface='...' explicitly""",
    ):
        semantic_validate(config, tm_data)
    config["interface"] = interface

    try:
        semantic_validate(config, tm_data=tm_data)

    except SchematicValidationError as error:
        assert (
            error.message
            == "stations are too many! Current limit is 4\n"
            "Invalid input for function mode! Currently allowed vis\n"
            "The fsp_ids should all be distinct\n"
            "fsp_ids are too many!Current Limit is 6"
        )


@pytest.fixture
def sbd_valid_request_json_path():
    """
    Pytest fixture to return path to resource allocation JSON file
    for SBD
    """
    config = load_string_from_file("test_files/testfile_valid_mid_sbd.json")
    return config


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_sbd_valid_inputs(
    mock, sbd_valid_request_json_path, tm_data
):  # pylint: disable=W0621
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    assert semantic_validate(sbd_valid_request_json_path, tm_data=tm_data), True


@pytest.fixture
def sbd_invalid_request_json_path():
    """
    Pytest fixture to return path to resource allocation JSON file
    for SBD
    """
    config = load_string_from_file("test_files/testfile_invalid_mid_sbd.json")
    return config


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_sbd_invalid_inputs(
    mock, sbd_invalid_request_json_path, tm_data
):  # pylint: disable=W0621
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )

    try:
        semantic_validate(sbd_invalid_request_json_path, tm_data=tm_data)

    except SchematicValidationError as error:
        assert (
            error.message
            == "receptor_ids are too many!Current Limit is 4\n"
            "beams are too many! Current limit is 1\n"
            "Invalid function for beams! Currently allowed visibilities\n"
            "spectral windows are too many! Current limit = 1\n"
            "Invalid input for channel_count! Currently allowed 14880\n"
            "Invalid input for freq_min\n"
            "Invalid input for freq_max\n"
            "length of receptor_ids should be same as length of receptors\n"
            "receptor_ids did not match receptors\n"
            "FSPs are too many!Current Limit = 4\n"
            "Invalid input for fsp_id!\n"
            "Invalid input for function_mode\n"
            "Invalid input for zoom_factor\n"
            "frequency_slice_id did not match fsp_id\n"
            "Invalid input for receiver_band! Currently allowed [1,2]"
        )


def test_fetch_matched_capabilities_from_basic_capabilities():
    """
    test case to verify whether we can replace band values or not
    which are present in dictionary within list
    """
    expected = [
        {
            "Band_1": {
                "rx_id": "Band_1",
                "min_frequency_hz": 350000000.0,
                "max_frequency_hz": 1050000000.0,
            }
        },
        {
            "Band_2": {
                "rx_id": "Band_2",
                "min_frequency_hz": 950000000.0,
                "max_frequency_hz": 1760000000.0,
            }
        },
    ]
    osd_capabilities = capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY][
        "available_receivers"
    ] = {
        "Band_1": {"test": "Band_1"},
        "Band_2": "test",
    }
    basic_capabilities = capabilities["capabilities"]["mid"]["basic_capabilities"]
    basic_capabilities["receiver_information"] = {
        "rx_id": {"Band_1": {"min_frequency_hz": 350000000.0}},
        "min_frequency_hz": 350000000.0,
        "max_frequency_hz": 1050000000.0,
    }
    assert fetch_matched_capabilities_from_basic_capabilities(
        osd_capabilities, basic_capabilities, matched_capabilities_list=[]
    ), expected

    osd_capabilities = capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY][
        "available_receivers"
    ] = {
        "Band_1": [{"test": "Band_1"}],
        "Band_2": "Band_1",
    }
    basic_capabilities = capabilities["capabilities"]["mid"]["basic_capabilities"]

    assert fetch_matched_capabilities_from_basic_capabilities(
        osd_capabilities, basic_capabilities, matched_capabilities_list=[]
    ), expected


def test_search_and_return_value_from_basic_capabilities():
    """
    test case to verify whether we can fetch frequency values or not
    which are present in dictionary within list
    """
    capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY]["basic_capabilities"] = {
        "min_frequency_hz": {"test": "test"},
    }
    expected = [{"test": "test"}]
    assert expected, search_and_return_value_from_basic_capabilities(
        capabilities, "test", rule=None, result=[]
    )

    osd_capabilities = capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY][
        "available_receivers"
    ] = {"min_frequency_hz": ["test"]}
    result = search_and_return_value_from_basic_capabilities(
        osd_capabilities, "test", rule=None, result=[]
    )
    assert [{"min_frequency_hz": ["test"]}], result


@patch("ska_ost_osd.osd.osd.get_osd_data")
def test_fetch_capabilities_from_osd_based_on_client_based_osd_data(mock1):
    """
    test case to verify if client passed osd data from semantic_validate method
    """
    result = fetch_capabilities_from_osd(
        telescope="mid", array_assembly=ARRAY_ASSEMBLY, osd_data=capabilities
    )
    expected_1 = (
        {
            "available_receivers": {"min_frequency_hz": ["test"]},
            "number_ska_dishes": 4,
            "number_meerkat_dishes": 0,
            "number_meerkatplus_dishes": 0,
            "max_baseline_km": 1.5,
            "available_bandwidth_hz": 800000.0,
            "number_channels": 14880,
            "number_zoom_windows": 0,
            "number_zoom_channels": 0,
            "number_pss_beams": 0,
            "number_pst_beams": 0,
            "ps_beam_bandwidth_hz": 0.0,
            "number_fsps": 4,
            "basic_capabilities": {"min_frequency_hz": {"test": "test"}},
        },
        {
            "dish_elevation_limit_deg": 15.0,
            "receiver_information": {
                "rx_id": {"Band_1": {"min_frequency_hz": 350000000.0}},
                "min_frequency_hz": 350000000.0,
                "max_frequency_hz": 1050000000.0,
            },
        },
    )
    assert result == expected_1

    mock1.return_value = {}, []
    result = fetch_capabilities_from_osd(telescope="mid", array_assembly=ARRAY_ASSEMBLY)
    assert result == ({}, {})
