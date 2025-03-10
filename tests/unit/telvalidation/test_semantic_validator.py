import unittest
from datetime import datetime
from unittest.mock import patch

import pytest
from ska_telmodel.data import TMData
from ska_telmodel.schema import example_by_uri

from ska_ost_osd.telvalidation.oet_tmc_validators import (
    get_matched_rule_constraint_from_osd,
    validate_json,
    validate_target_is_visible,
)
from ska_ost_osd.telvalidation.schematic_validation_exceptions import (
    SchemanticValidationKeyError,
    SchematicValidationError,
)
from ska_ost_osd.telvalidation.semantic_validator import (
    fetch_capabilities_from_osd,
    semantic_validate,
)
from tests.conftest import (
    ARRAY_ASSEMBLY,
    INPUT_COMMAND_CONFIG,
    INVALID_LOW_ASSIGN_JSON,
    INVALID_LOW_CONFIGURE_JSON,
    INVALID_LOW_SBD_JSON,
    INVALID_MID_ASSIGN_JSON,
    INVALID_MID_CONFIGURE_JSON,
    INVALID_MID_SBD_JSON,
    INVALID_MID_VALIDATE_CONSTANT,
    VALID_LOW_ASSIGN_JSON,
    VALID_LOW_CONFIGURE_JSON,
    VALID_LOW_SBD_JSON,
    VALID_MID_ASSIGN_JSON,
    VALID_MID_CONFIGURE_JSON,
    VALID_MID_SBD_JSON,
    capabilities,
    low_configure_expected_result_for_invalid_data,
    low_expected_result_for_invalid_data,
    low_sbd_expected_result_for_invalid_data,
    mid_configure_expected_result_for_invalid_data,
    mid_expected_result_for_invalid_data,
    mid_sbd_expected_result_for_invalid_data,
    sources,
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
        (VALID_LOW_SBD_JSON, "LOW", True, False),
        (INVALID_LOW_SBD_JSON, "LOW", low_sbd_expected_result_for_invalid_data, True),
        # # Add more test cases here
    ],
)
def test_semantic_validate_para(
    mock_fetch_capabilities,
    config,
    telescope,
    expected_result,
    is_exception,
    tm_data_osd,
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
        semantic_validate(config, tm_data_osd)

    config["interface"] = interface

    if not is_exception:
        assert semantic_validate(config, tm_data=tm_data_osd), expected_result
    else:
        try:
            semantic_validate(config, tm_data=tm_data_osd)
        except SchematicValidationError as error:
            assert error.message == expected_result


@patch("ska_ost_osd.telvalidation.semantic_validator.fetch_capabilities_from_osd")
def test_validate_schemantic_json_input_keys(mock6):
    """
    Test if error is raised when invalid key is passed.
    """
    osd_capabilities = capabilities["capabilities"]["mid"]
    mock6.return_value = (
        osd_capabilities[ARRAY_ASSEMBLY],
        osd_capabilities["basic_capabilities"],
    )
    with pytest.raises(
        SchemanticValidationKeyError,
        match="Invalid rule and error key passed",
    ):
        validate_json(
            INVALID_MID_VALIDATE_CONSTANT["AA0.5"]["assign_resource"],
            INPUT_COMMAND_CONFIG,
            parent_path_list=[],
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
