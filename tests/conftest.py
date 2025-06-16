import json
import os
import pathlib
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Dict

import pytest
from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import osd_tmdata_source
from ska_ost_osd.telvalidation.constant import CAR_TELMODEL_SOURCE

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"


def read_json(json_file_location: Path) -> Dict:
    """This function returns json file object from local file system.

    :param json_file_location: json file.
    :returns: file content as json object
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, "unit/", json_file_location)

    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents


def create_mock_json_files(json_file_location: Path, json_data: Dict) -> None:
    """This function create json file for mocking TMData object.

    :param json_file_location: json file.
    :param json_data: json data to be saved.
    :returns: None
    """
    with open(json_file_location, "w") as f:  # pylint: disable=W1514
        json.dump(json_data, f)


MID_MOCK_DATA = read_json("test_files/mock_mid_capabilities.json")

LOW_MOCK_DATA = read_json("test_files/mock_low_capabilities.json")

OBSERVATORY_MOCK_DATA = read_json("test_files/mock_observatory_policies.json")

MID_VALIDATION_MOCK_DATA = read_json("test_files/mock-mid-validation-constants.json")

LOW_VALIDATION_MOCK_DATA = read_json("test_files/mock-low-validation-constants.json")

MID_SBD_VALIDATION_MOCK_DATA = read_json(
    "test_files/mock_mid_sbd-validation-constants.json"
)

LOW_SBD_VALIDATION_MOCK_DATA = read_json(
    "test_files/mock_low_sbd-validation-constants.json"
)

MID_OSD_DATA_JSON = read_json("test_files/testfile_mid_osd_data.json")

VALID_MID_ASSIGN_JSON = read_json("test_files/testfile_valid_mid_assign.json")
INVALID_MID_ASSIGN_JSON = read_json("test_files/testfile_invalid_mid_assign.json")
VALID_MID_CONFIGURE_JSON = read_json("test_files/testfile_valid_mid_configure.json")
VALID_MID_SBD_JSON = read_json("test_files/testfile_valid_mid_sbd.json")
INVALID_MID_SBD_JSON = read_json("test_files/testfile_invalid_mid_sbd.json")
VALID_LOW_SBD_JSON = read_json("test_files/testfile_valid_low_sbd.json")
INVALID_LOW_SBD_JSON = read_json("test_files/testfile_invalid_low_sbd.json")
INVALID_MID_CONFIGURE_JSON = read_json("test_files/testfile_invalid_mid_configure.json")
VALID_LOW_ASSIGN_JSON = read_json("test_files/testfile_valid_low_assign.json")
INVALID_LOW_ASSIGN_JSON = read_json("test_files/testfile_invalid_low_assign.json")
VALID_LOW_CONFIGURE_JSON = read_json("test_files/testfile_valid_low_configure.json")
INVALID_LOW_CONFIGURE_JSON = read_json("test_files/testfile_invalid_low_configure.json")
capabilities = read_json("test_files/testfile_capabilities.json")

DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER = read_json(
    "test_files/default_osd_response.json"
)
OSD_RESPONSE_WITH_ONLY_CAPABILITIES_PARAMETER = read_json(
    "test_files/osd_response_with_capabilities.json"
)

file_name = "osd_response_with_capabilities_and_array_assembly.json"
OSD_RESPONSE_WITH_CAPABILITIES_ARRAY_ASSEMBLY_PARAMETER = read_json(
    f"test_files/{file_name}"
)

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


@pytest.fixture(scope="module")
def git_tm_data():
    return TMData(sources)


# re-defined TMData for local file source
@pytest.fixture(scope="module")
def tm_data():
    return TMData(local_source)


@pytest.fixture
def tmdata_source():
    """TMData source URL fixture."""
    return CAR_TELMODEL_SOURCE[0]


@pytest.fixture(scope="module")
def tm_data_osd():
    with tempfile.TemporaryDirectory("tmdata") as dirname:
        mid_parent = pathlib.Path(dirname, "ska1_mid")
        mid_parent.mkdir(parents=True)
        create_mock_json_files(mid_parent / "mid_capabilities.json", MID_MOCK_DATA)

        low_parent = pathlib.Path(dirname, "ska1_low")
        low_parent.mkdir(parents=True)
        create_mock_json_files(low_parent / "low_capabilities.json", LOW_MOCK_DATA)

        create_mock_json_files(
            f"{dirname}/observatory_policies.json", OBSERVATORY_MOCK_DATA
        )

        mid_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_mid", "validation"
        )
        mid_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_validation_parent / "mid-validation-constants.json",
            MID_VALIDATION_MOCK_DATA,
        )

        low_validation_parent = pathlib.Path(
            dirname, "instrument", "ska1_low", "validation"
        )
        low_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            low_validation_parent / "low-validation-constants.json",
            LOW_VALIDATION_MOCK_DATA,
        )

        mid_sbd_validation_parent = pathlib.Path(
            dirname, "instrument", "scheduling-block", "validation"
        )
        mid_sbd_validation_parent.mkdir(parents=True)
        create_mock_json_files(
            mid_sbd_validation_parent / "mid_sbd-validation-constants.json",
            MID_SBD_VALIDATION_MOCK_DATA,
        )

        create_mock_json_files(
            mid_sbd_validation_parent / "low_sbd-validation-constants.json",
            LOW_SBD_VALIDATION_MOCK_DATA,
        )

        print(f"Dirname: {dirname} {mid_parent} {os.listdir(dirname)}")
        yield TMData([f"file://{dirname}"])


@pytest.fixture(scope="module")
def validate_car_class():
    """This function is used as a fixture for osd_tmdata_source object with
    osd_version as '1.11.0'.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(osd_version="1.11.0")
    return tmdata_source


@pytest.fixture(scope="module")
def validate_gitlab_class():
    """This function is used as a fixture for osd_tmdata_source object with
    parameters.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )
    return tmdata_source


@pytest.fixture
def osd_versions():
    """This fixture reads a JSON file containing cycle-to-version mappings,
    extracts all unique versions across all cycles, and returns them as a
    sorted list.

    :returns list: A sorted list of unique OSD versions extracted from
        the JSON file.
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    json_path = os.path.join(
        parent_dir,
        "src",
        "ska_ost_osd",
        "osd",
        "version_mapping",
        "cycle_gitlab_release_version_mapping.json",
    )

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    all_versions = set()
    for cycle_versions in data.values():
        all_versions.update(cycle_versions)

    return sorted(list(all_versions))


@pytest.fixture
def mid_osd_data():
    """This fixture returns data in MID_OSD_DATA_JSON file

    :returns dict: MID_OSD_DATA_JSON file data
    """
    return MID_OSD_DATA_JSON


@pytest.fixture
def osd_observatory_policies():
    """This fixture returns data in OBSERVATORY_MOCK_DATA file

    :returns dict: OBSERVATORY_MOCK_DATA file data
    """
    return OBSERVATORY_MOCK_DATA


@pytest.fixture(scope="module")
def mock_mid_data():
    """This function is used as a fixture for mid json data.

    :returns: mid json data
    """

    return MID_MOCK_DATA


@pytest.fixture(scope="module")
def mock_low_data():
    """This function is used as a fixture for low json data.

    :returns: low json data
    """

    return LOW_MOCK_DATA


@pytest.fixture
def valid_observing_command_input():
    return VALID_MID_ASSIGN_JSON


@pytest.fixture
def invalid_observing_command_input():
    return INVALID_MID_ASSIGN_JSON


@pytest.fixture
def valid_semantic_validation_body(
    tmdata_source, mid_osd_data, valid_observing_command_input
):
    return {
        "observing_command_input": valid_observing_command_input,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data,
    }


@pytest.fixture
def valid_semantic_validation_response():
    return {
        "status": 0,
        "detail": "JSON is semantically valid",
        "title": "Semantic validation",
    }


@pytest.fixture
def semantic_validation_disable_response():
    return {
        "status": 0,
        "detail": "Semantic Validation is currently disable",
        "title": "Semantic validation",
    }


@pytest.fixture
def invalid_semantic_validation_body(
    tmdata_source, mid_osd_data, invalid_observing_command_input
):
    return {
        "observing_command_input": invalid_observing_command_input,
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "sources": tmdata_source,
        "raise_semantic": True,
        "osd_data": mid_osd_data,
    }


@pytest.fixture
def invalid_semantic_validation_response():
    return {
        "detail": [
            "receptor_ids are too many!Current Limit is 4",
            (
                "Invalid input for receptor_ids! Currently allowed ['SKA001', 'SKA036',"
                " 'SKA063', 'SKA100']"
            ),
            "beams are too many! Current limit is 1",
            "Invalid function for beams! Currently allowed visibilities",
            "Invalid input for freq_min",
            "Invalid input for freq_max",
            "freq_min should be less than freq_max",
            "length of receptor_ids should be same as length of receptors",
            "receptor_ids did not match receptors",
        ],
        "status": 0,
        "title": "Semantic Validation Error",
    }


@pytest.fixture
def observing_command_input_missing_response():
    return {
        "detail": [
            "Value error, [{'field': 'observing_command_input', 'msg': 'This field is"
            " required'}]"
        ],
        "status": -1,
        "title": "Value Error",
    }


@pytest.fixture
def wrong_semantic_validation_parameter_body():
    return {
        "interface": "https://schemka-tmc-assignresources/2.1",
        "raise_semantic": "123",
        "sources": "car://gitlab.com/ska-telescope14.1#tmdata",
    }


@pytest.fixture
def wrong_semantic_validation_parameter_value_response():
    return {
        "detail": [
            (
                "gitlab://gitlab.com/ska-telescope14.1?~default~#tmdata not found"
                " in SKA CAR - make sure to add tmdata CI!"
            ),
        ],
        "status": -1,
        "title": "Value Error",
    }


@pytest.fixture
def valid_only_observing_command_input_in_request_body(valid_observing_command_input):
    return {"observing_command_input": valid_observing_command_input}
