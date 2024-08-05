import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

import pytest
from ska_telmodel.data import TMData
from ska_telmodel.schema import example_by_uri

from ska_ost_osd.telvalidation.constant import CAR_TELMODEL_SOURCE
from ska_ost_osd.telvalidation.oet_tmc_validators import (
    get_matched_rule_constraint_from_osd,
    validate_json,
    validate_target_is_visible,
)
from ska_ost_osd.telvalidation.schematic_validation_exceptions import (
    SchemanticValdidationKeyError,
    SchematicValidationError,
)
from ska_ost_osd.telvalidation.semantic_validator import (
    fetch_capabilities_from_osd,
    semantic_validate,
)

sources = [
    CAR_TELMODEL_SOURCE[0],
    "car:ska-telmodel-data?main",
]

local_source = ["file://tmdata"]


@pytest.fixture(scope="module")
def git_tm_data():
    return TMData(sources)


# re-defined TMData for local file source
@pytest.fixture(scope="module")
def tm_data():
    return TMData(local_source)


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data


MID_OSD_DATA_JSON = load_string_from_file("test_files/testfile_mid_osd_data.json")

VALID_MID_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_valid_mid_assign.json"
)
INVALID_MID_ASSIGN_JSON = load_string_from_file(
    "test_files/testfile_invalid_mid_assign.json"
)
VALID_MID_CONFIGURE_JSON = load_string_from_file(
    "test_files/testfile_valid_mid_configure.json"
)
VALID_MID_SBD_JSON = load_string_from_file("test_files/testfile_valid_mid_sbd.json")
INVALID_MID_SBD_JSON = load_string_from_file("test_files/testfile_invalid_mid_sbd.json")
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
capabilities = load_string_from_file("test_files/testfile_capabilities.json")

INVALID_MID_VALIDATE_CONSTANT = {
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

INPUT_COMMAND_CONFIG = {
    "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
    "transaction_id": "txn-....-00001",
    "subarray_id": 1,
    "dish": {"receptor_ids": ["0001"]},
}

ARRAY_ASSEMBLY = "AA0.5"

mid_expected_result_for_invalid_data = (
    "receptor_ids are too many!Current Limit is 4\n"
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

low_expected_result_for_invalid_data = (
    "subarray_beam_id must be between 1 and 48\n"
    "number_of_channels must be between 8 and 384\n"
    "Invalid input for station_id! Currently allowed [345, 350, 352, 431]\n"
    "Initials of aperture_id should be AP\n"
    "station_id in aperture_id should be same as station_id\n"
    "beams are too many! Current limit is 1\n"
    "Invalid function for beams! Currently allowed visibilities\n"
    "spectral windows are too many! Current limit = 1"
)

mid_configure_expected_result_for_invalid_data = (
    "Invalid input for receiver_band! Currently allowed [1,2]\n"
    "FSPs are too many!Current Limit = 4\n"
    "Invalid input for fsp_id!\n"
    "Invalid input for function_mode\n"
    "Invalid input for zoom_factor\n"
    "frequency_slice_id did not match fsp_id\n"
    "frequency_band did not match receiver_band"
)

low_configure_expected_result_for_invalid_data = (
    "subarray_beam_id must be between 1 and 48\n"
    "update_rate must be greater than or equal to 0.0\n"
    "start_channel must be greater than 2 and less than 504\n"
    "number_of_channels must be greater than or equal to 8 and less"
    " than or equal to 384\n"
    "Initials of aperture_id should be AP\n"
    "Invalid reference frame! Currently allowed  [“topocentric”, “ICRS”, “galactic”]\n"
    "c1 must be between 0.0 and 360.0\n"
    "c2 must be between -90.0 and 90.0\n"
    "stations are too many! Current limit is 4\n"
    "Invalid input for firmware! Currently allowed vis\n"
    "The fsp_ids should all be distinct\n"
    "fsp_ids are too many!Current Limit is 6\n"
    "beams are too many!Current Limit is 1\n"
    "Invalid input for firmware! Currently allowed pst\n"
    "beams are too many! Current limit is 1"
)


mid_sbd_expected_result_for_invalid_data = (
    "receptor_ids are too many!Current Limit is 4\n"
    "beams are too many! Current limit is 1\n"
    "Invalid function for beams! Currently allowed visibilities\n"
    "spectral windows are too many! Current limit = 1\n"
    "Invalid input for channel_count! Currently allowed 14880\n"
    "Invalid input for freq_min\n"
    "Invalid input for freq_max\n"
    "freq_min should be less than freq_max\n"
    "length of receptor_ids should be same as length of receptors\n"
    "receptor_ids did not match receptors\n"
    "FSPs are too many!Current Limit = 4\n"
    "Invalid input for fsp_id!\n"
    "Invalid input for function_mode\n"
    "Invalid input for zoom_factor\n"
    "frequency_slice_id did not match fsp_id\n"
    "Invalid input for receiver_band! Currently allowed [1,2]"
)


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
@pytest.mark.parametrize(
    "config, telescope, expected_result, is_exception",
    [
        (VALID_MID_ASSIGN_JSON, "MID", True, False),
        (INVALID_MID_ASSIGN_JSON, "MID", mid_expected_result_for_invalid_data, True),
        (VALID_LOW_ASSIGN_JSON, "LOW", True, False),
        (INVALID_LOW_ASSIGN_JSON, "LOW", low_expected_result_for_invalid_data, True),
        (VALID_MID_CONFIGURE_JSON, "MID", True, False),
        (
            INVALID_MID_CONFIGURE_JSON,
            "MID",
            mid_configure_expected_result_for_invalid_data,
            True,
        ),
        (VALID_LOW_CONFIGURE_JSON, "LOW", True, False),
        (
            INVALID_LOW_CONFIGURE_JSON,
            "LOW",
            low_configure_expected_result_for_invalid_data,
            True,
        ),
        (VALID_MID_SBD_JSON, "MID", True, False),
        (INVALID_MID_SBD_JSON, "MID", mid_sbd_expected_result_for_invalid_data, True),
        # Add more test cases here
    ],
)
def test_semantic_validate_para(
    mock_fetch_capabilities,
    config,
    telescope,
    expected_result,
    is_exception,
    tm_data,  # pylint: disable=W0621
):
    """
    Parameterized test case to verify semantic validation for different inputs.
    Test semantic validate assign resource command with valid inputs.
    """
    if telescope == "MID":
        osd_capabilities = capabilities["capabilities"]["mid"]
    else:
        osd_capabilities = capabilities["capabilities"]["low"]
    mock_fetch_capabilities.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    interface = config["interface"]
    del config["interface"]  # to test use of interface key
    # sample values that pass semantic only

    with pytest.raises(
        SchematicValidationError,
        match=(
            "Interface is missing from observing_command_input. Please provide"
            " interface='...' explicitly."
        ),
    ):
        semantic_validate(config, tm_data)

    config["interface"] = interface

    if not is_exception:
        assert semantic_validate(config, tm_data=tm_data), expected_result
    else:
        try:
            semantic_validate(config, tm_data=tm_data)
        except SchematicValidationError as error:
            assert error.message == expected_result


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
            parent_path=[],
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


@pytest.fixture
def sbd_invalid_request_json_path():
    """
    Pytest fixture to return path to resource allocation JSON file
    for SBD
    """
    config = load_string_from_file("test_files/testfile_invalid_mid_sbd.json")
    return config


def test_get_matched_rule_constraint_from_osd():
    """
    test case to verify whether we can fetch frequency values or not
    which are present in dictionary within list
    """
    capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY]["basic_capabilities"] = {
        "min_frequency_hz": {"test": "test"},
    }
    expected = [{"test": "test"}]
    assert expected, get_matched_rule_constraint_from_osd(
        capabilities, "test", rule=None
    )

    osd_capabilities = capabilities["capabilities"]["mid"][ARRAY_ASSEMBLY][
        "available_receivers"
    ] = {"min_frequency_hz": ["test"]}
    result = get_matched_rule_constraint_from_osd(osd_capabilities, "test", rule=None)
    assert [{"min_frequency_hz": ["test"]}], result


@patch("ska_ost_osd.osd.osd.get_osd_data")
def test_fetch_capabilities_from_osd_based_on_client_based_osd_data(mock1):
    """
    test case to verify if client passed osd data from semantic_validate method
    """
    fetch_capabilities_from_osd(
        telescope="mid", array_assembly=ARRAY_ASSEMBLY, osd_data=capabilities
    )
    mock1.return_value = {}, []
    result = fetch_capabilities_from_osd(telescope="mid", array_assembly=ARRAY_ASSEMBLY)
    assert result == ({}, {})
