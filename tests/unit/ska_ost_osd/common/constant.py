from ska_ost_osd.telvalidation.common.constant import CAR_TELMODEL_SOURCE
from tests.unit.ska_ost_osd.utils import read_json

DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER = "test_files/default_osd_response.json"

MID_CAPABILITIES_MOCK_DATA = "test_files/mock_mid_capabilities.json"

LOW_CAPABILITIES_MOCK_DATA = "test_files/mock_low_capabilities.json"

OBSERVATORY_POLICIES_MOCK_DATA = DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER

MID_VALIDATION_MOCK_DATA = read_json("test_files/mock-validation-constants.json").get(
    "mid_validation"
)

LOW_VALIDATION_MOCK_DATA = read_json("test_files/mock-validation-constants.json").get(
    "low_validation"
)

MID_SBD_VALIDATION_MOCK_DATA = "test_files/mock_mid_sbd-validation-constants.json"

LOW_SBD_VALIDATION_MOCK_DATA = "test_files/mock_low_sbd-validation-constants.json"

MID_OSD_DATA_JSON = read_json("test_files/testfile_mid_osd_data.json")

VALID_MID_ASSIGN_JSON = read_json("test_files/testfile_mid_assign.json").get("valid")
INVALID_MID_ASSIGN_JSON = read_json("test_files/testfile_mid_assign.json").get(
    "invalid"
)
VALID_MID_CONFIGURE_JSON = read_json("test_files/testfile_mid_configure.json").get(
    "valid"
)
VALID_MID_SBD_JSON = read_json("test_files/testfile_mid_sbd.json").get("valid")
INVALID_MID_SBD_JSON = read_json("test_files/testfile_mid_sbd.json").get("invalid")
VALID_LOW_SBD_JSON = read_json("test_files/testfile_low_sbd.json").get("valid")
INVALID_LOW_SBD_JSON = read_json("test_files/testfile_low_sbd.json").get("invalid")
INVALID_MID_CONFIGURE_JSON = read_json("test_files/testfile_mid_configure.json").get(
    "invalid"
)
VALID_LOW_ASSIGN_JSON = read_json("test_files/testfile_low_assign.json").get("valid")
INVALID_LOW_ASSIGN_JSON = read_json("test_files/testfile_low_assign.json").get(
    "invalid"
)
VALID_LOW_CONFIGURE_JSON = read_json("test_files/testfile_low_configure.json").get(
    "valid"
)
INVALID_LOW_CONFIGURE_JSON = read_json("test_files/testfile_low_configure.json").get(
    "invalid"
)
capabilities = read_json("test_files/testfile_capabilities.json")

OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER = (
    "test_files/osd_response_with_capabilities.json"
)

file_name = "osd_response_with_capabilities_and_array_assembly.json"
OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER = f"test_files/{file_name}"

# This is dummy constant json for testing "Invalid rule and error key passed" scenario.
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
    "dish": {"receptor_ids": ["SKA001"]},
}

ARRAY_ASSEMBLY = "AA0.5"

mid_expected_result_for_invalid_data = (
    "receptor_ids are too many!Current Limit is 4\nInvalid input for receptor_ids!"
    " Currently allowed ['SKA001', 'SKA036', 'SKA063', 'SKA100']\nbeams are too many!"
    " Current limit is 1\nInvalid function for beams! Currently allowed"
    " visibilities\nInvalid input for freq_min\nInvalid input for freq_max\nfreq_min"
    " should be less than freq_max\nlength of receptor_ids should be same as length of"
    " receptors\nreceptor_ids did not match receptors"
)

low_expected_result_for_invalid_data = (
    "subarray_beam_id must be between 1 and 48\n"
    "number_of_channels must be between 8 and 384\n"
    "Invalid input for station_id! Currently allowed [345, 350, 352, 431]\n"
    "Initials of aperture_id should be AP\n"
    "station_id in aperture_id should be same as station_id\n"
    "beams are too many! Current limit is 1\n"
    "Invalid function for beams! Currently allowed visibilities"
)

mid_configure_expected_result_for_invalid_data = (
    "Invalid input for receiver_band! Currently allowed [1,2]\n"
    "The fsp_ids should all be distinct\n"
    "fsp_ids are too many!Current Limit is 4\n"
    "Invalid fsp_ids! The range should not greater than 4\n"
    "Invalid input for channel_width! Currently allowed [13440]\n"
    "channel_count must be between 1 to 58982\n"
    "channel_count must be a multiple of 20\n"
    "Invalid input for start_freq\n"
    "Invalid input for start_freq\n"
    "sdp_start_channel_id must be between 0 to 2147483647\n"
    "integration_factor must be between 1 to 10\n"
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
    "Invalid fsp_ids! The range should not greater than 6\n"
    "beams are too many!Current Limit is 1\n"
    "Invalid input for firmware! Currently allowed pst\n"
    "beams are too many! Current limit is 1"
)

mid_sbd_expected_result_for_invalid_data = (
    "receptor_ids are too many!Current Limit is 4\nInvalid input for receptor_ids!"
    " Currently allowed ['SKA001', 'SKA036', 'SKA063', 'SKA100']\nbeams are too many!"
    " Current limit is 1\nInvalid function for beams! Currently allowed"
    " visibilities\nInvalid input for freq_min\nInvalid input for freq_max\nfreq_min"
    " should be less than freq_max\nlength of receptor_ids should be same as length of"
    " receptors\nreceptor_ids did not match receptors\nFSPs are too many!Current Limit"
    " = 4\nInvalid input for fsp_id!\nInvalid input for function_mode\nInvalid input"
    " for zoom_factor\nfrequency_slice_id did not match fsp_id\nInvalid input for"
    " receiver_band! Currently allowed [1,2]"
)

low_sbd_expected_result_for_invalid_data = (
    "subarray_beam_id must be between 1 and 48\n"
    "number_of_channels must be between 8 and 384\n"
    "Invalid input for station_id! Currently allowed [345, 350, 352, 431]\n"
    "The logical_fsp_ids should all be distinct\n"
    "logical_fsp_ids are too many!Current Limit is 6\n"
    "Invalid input for zoom_factor"
)

sources = [
    CAR_TELMODEL_SOURCE[0],
    "car:ska-telmodel-data?main",
]

local_source = ["file://tmdata"]
