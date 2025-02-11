import json
import os
from importlib.metadata import version
from pathlib import Path
from typing import Dict

import pytest
from ska_telmodel.data import TMData

from ska_ost_osd.osd.osd import osd_tmdata_source
from ska_ost_osd.rest import init_app
from ska_ost_osd.telvalidation.constant import CAR_TELMODEL_SOURCE

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"


def read_json(json_file_location: Path) -> Dict:
    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, "unit/", json_file_location)

    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents


MID_MOCK_DATA = read_json("test_files/mock_mid_capabilities.json")

LOW_MOCK_DATA = read_json("test_files/mock_low_capabilities.json")

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
    "receptor_ids are too many!Current Limit is 4\n"
    "beams are too many! Current limit is 1\n"
    "Invalid function for beams! Currently allowed visibilities\n"
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
    """
    TMData source URL fixture
    """
    return CAR_TELMODEL_SOURCE[0]


@pytest.fixture(scope="module")
def tm_data_osd():
    """This function is used as a fixture for tm_data object

    :returns: tmdata object
    """

    source_uris, _ = osd_tmdata_source(cycle_id=1, source="file")
    return TMData(source_uris=source_uris)


@pytest.fixture(scope="module")
def validate_car_class():
    """This function is used as a fixture for osd_tmdata_source object
        with osd_version as '1.11.0'

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(osd_version="1.11.0")
    return tmdata_source


@pytest.fixture(scope="module")
def validate_gitlab_class():
    """This function is used as a fixture for osd_tmdata_source object
        with parameters.

    :returns: osd_tmdata_source object
    """
    tmdata_source, _ = osd_tmdata_source(
        cycle_id=1,
        gitlab_branch="nak-776-osd-implementation-file-versioning",
        source="gitlab",
    )
    return tmdata_source


@pytest.fixture
def client():
    """This fixture returns a Flask test client that can be used to make requests
        to the application in tests. It handles setting up and tearing down the
        application context.

    :returns FlaskClient: The Flask test client
    """

    app = init_app()
    with app.test_client() as client:  # pylint: disable=W0621
        yield client


@pytest.fixture
def osd_versions():
    """
    This fixture reads a JSON file containing cycle-to-version mappings,
    extracts all unique versions across all cycles, and returns them as a
    sorted list.

    :returns list: A sorted list of unique OSD versions extracted from the JSON file.
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
def open_api_spec():
    """This fixture returns the expected OpenAPI specification
        that is returned from the API. It is used to validate
        the response in tests.

    :returns dict: The OpenAPI specification
    """

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Observatory Static Data API",
            "description": (
                "This OpenAPI document defines the API for the Observatory Static Data"
                " (OSD) REST service"
            ),
            "license": {
                "name": "BSD-3-Clause",
                "url": "https://opensource.org/licenses/BSD-3-Clause",
            },
            "version": "2.0.0",
        },
        "servers": [{"url": "ska-ost-osd/osd/api/v2"}],
        "paths": {
            "/osd": {
                "get": {
                    "summary": "Get OSD data filter by the query parameter",
                    "description": (
                        "Retrieves the OSD cycle_id data which match the query"
                        " parameters. Also requests without parameters will"
                        " take\nexample and default values and return data based on"
                        " that. All query parameters has its own validation\nif user"
                        " provide any invalid value it will return the error message.\n"
                    ),
                    "operationId": "ska_ost_osd.rest.api.resources.get_osd",
                    "parameters": [
                        {
                            "in": "query",
                            "name": "cycle_id",
                            "schema": {"type": "integer"},
                            "required": False,
                            "example": 1,
                        },
                        {
                            "in": "query",
                            "name": "osd_version",
                            "schema": {"type": "string"},
                            "required": False,
                            "example": "1.0.0",
                        },
                        {
                            "in": "query",
                            "name": "source",
                            "schema": {
                                "type": "string",
                                "enum": ["file", "car", "gitlab"],
                                "default": "file",
                            },
                            "required": False,
                        },
                        {
                            "in": "query",
                            "name": "gitlab_branch",
                            "schema": {"type": "string"},
                            "required": False,
                        },
                        {
                            "in": "query",
                            "name": "capabilities",
                            "schema": {"type": "string", "enum": ["mid", "low"]},
                            "required": False,
                        },
                        {
                            "in": "query",
                            "name": "array_assembly",
                            "schema": {"type": "string"},
                            "required": False,
                            "example": "AA0.5",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "object"},
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": (
                                "Bad Request, eg validation of against OpenAPI spec"
                                " failed"
                            ),
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "integer"},
                                            "title": {"type": "string"},
                                            "detail": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "500": {
                            "description": "Internal Server Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "detail": {"type": "string"},
                                            "traceback": {
                                                "type": "object",
                                                "properties": {
                                                    "key": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "full_traceback": {
                                                        "type": "string"
                                                    },
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        },
                    },
                }
            },
            "/semantic_validation": {
                "post": {
                    "summary": "Checks if the Command Input JSON is semantically valid",
                    "description": (
                        "Validate input json Semantically\nSemantic validation checks"
                        " the meaning of the input data and ensures that it is valid in"
                        " the context of the system. It checks whether the input data"
                        " conforms to the business rules and logic of the system.\n"
                    ),
                    "operationId": (
                        "ska_ost_osd.rest.api.resources.semantically_validate_json"
                    ),
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["observing_command_input"],
                                    "properties": {
                                        "observing_command_input": {
                                            "type": "object",
                                            "description": (
                                                "Configuration for semantic validation."
                                            ),
                                            "example": {
                                                "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
                                                "subarray_id": 1,
                                                "dish": {
                                                    "receptor_ids": ["SKA001", "SKA036"]
                                                },
                                                "sdp": {
                                                    "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
                                                    "execution_block": {
                                                        "eb_id": (
                                                            "eb-test-20220916-00000"
                                                        ),
                                                        "max_length": 100.0,
                                                        "context": {},
                                                        "beams": [
                                                            {
                                                                "beam_id": "vis0",
                                                                "function": (
                                                                    "visibilities"
                                                                ),
                                                            }
                                                        ],
                                                        "scan_types": [
                                                            {
                                                                "scan_type_id": (
                                                                    ".default"
                                                                ),
                                                                "beams": {
                                                                    "vis0": {
                                                                        "channels_id": "vis_channels",
                                                                        "polarisations_id": (
                                                                            "all"
                                                                        ),
                                                                    },
                                                                    "pss1": {
                                                                        "field_id": (
                                                                            "field_a"
                                                                        ),
                                                                        "channels_id": "pulsar_channels",
                                                                        "polarisations_id": (
                                                                            "all"
                                                                        ),
                                                                    },
                                                                },
                                                            },
                                                            {
                                                                "scan_type_id": (
                                                                    "target:a"
                                                                ),
                                                                "derive_from": (
                                                                    ".default"
                                                                ),
                                                                "beams": {
                                                                    "vis0": {
                                                                        "field_id": (
                                                                            "field_a"
                                                                        )
                                                                    }
                                                                },
                                                            },
                                                        ],
                                                        "channels": [
                                                            {
                                                                "channels_id": (
                                                                    "vis_channels"
                                                                ),
                                                                "spectral_windows": [
                                                                    {
                                                                        "spectral_window_id": "fsp_1_channels",
                                                                        "count": 14880,
                                                                        "start": 0,
                                                                        "stride": 2,
                                                                        "freq_min": 350000000.0,
                                                                        "freq_max": 368000000.0,
                                                                        "link_map": [
                                                                            [0, 0],
                                                                            [200, 1],
                                                                            [744, 2],
                                                                            [944, 3],
                                                                        ],
                                                                    }
                                                                ],
                                                            }
                                                        ],
                                                        "polarisations": [
                                                            {
                                                                "polarisations_id": (
                                                                    "all"
                                                                ),
                                                                "corr_type": [
                                                                    "XX",
                                                                    "XY",
                                                                    "YY",
                                                                    "YX",
                                                                ],
                                                            }
                                                        ],
                                                        "fields": [
                                                            {
                                                                "field_id": "field_a",
                                                                "phase_dir": {
                                                                    "ra": [123, 0.1],
                                                                    "dec": [80, 0.1],
                                                                    "reference_time": "2023-02-16T01:23:45.678900",
                                                                    "reference_frame": (
                                                                        "ICRF3"
                                                                    ),
                                                                },
                                                                "pointing_fqdn": "low-tmc/telstate/0/pointing",
                                                            }
                                                        ],
                                                    },
                                                    "processing_blocks": [
                                                        {
                                                            "pb_id": "pb-mvp01-20200325-00001",
                                                            "script": {
                                                                "kind": "realtime",
                                                                "name": "vis_receive",
                                                                "version": "0.1.0",
                                                            },
                                                            "parameters": {},
                                                        },
                                                        {
                                                            "pb_id": "pb-mvp01-20200325-00002",
                                                            "script": {
                                                                "kind": "realtime",
                                                                "name": "test_realtime",
                                                                "version": "0.1.0",
                                                            },
                                                            "parameters": {},
                                                        },
                                                        {
                                                            "pb_id": "pb-mvp01-20200325-00003",
                                                            "script": {
                                                                "kind": "batch",
                                                                "name": "ical",
                                                                "version": "0.1.0",
                                                            },
                                                            "parameters": {},
                                                            "dependencies": [
                                                                {
                                                                    "pb_id": "pb-mvp01-20200325-00001",
                                                                    "kind": [
                                                                        "visibilities"
                                                                    ],
                                                                }
                                                            ],
                                                            "sbi_ids": [
                                                                "sbi-mvp01-20200325-00001"
                                                            ],
                                                        },
                                                        {
                                                            "pb_id": "pb-mvp01-20200325-00004",
                                                            "script": {
                                                                "kind": "batch",
                                                                "name": "dpreb",
                                                                "version": "0.1.0",
                                                            },
                                                            "parameters": {},
                                                            "dependencies": [
                                                                {
                                                                    "pb_id": "pb-mvp01-20200325-00003",
                                                                    "kind": [
                                                                        "calibration"
                                                                    ],
                                                                }
                                                            ],
                                                        },
                                                    ],
                                                    "resources": {
                                                        "csp_links": [1, 2, 3, 4],
                                                        "receptors": [
                                                            "SKA001",
                                                            "SKA002",
                                                        ],
                                                    },
                                                },
                                            },
                                        },
                                        "interface": {
                                            "type": "string",
                                            "example": "https://schema.skao.int/ska-tmc-assignresources/2.1",
                                        },
                                        "sources": {
                                            "type": "string",
                                            "example": (
                                                "car:ost/ska-ost-osd?2.0.0#tmdata"
                                            ),
                                        },
                                        "raise_semantic": {
                                            "type": "boolean",
                                            "example": True,
                                        },
                                        "osd_data": {
                                            "type": "object",
                                            "description": (
                                                "Observatory data for validation."
                                            ),
                                            "example": {
                                                "observatory_policy": {
                                                    "cycle_number": 2,
                                                    "cycle_description": (
                                                        "Science Verification"
                                                    ),
                                                    "cycle_information": {
                                                        "cycle_id": "SKAO_2027_1",
                                                        "proposal_open": (
                                                            "2026-03-27T12:00:00.000Z"
                                                        ),
                                                        "proposal_close": (
                                                            "2026-05-12T15:00:00.000Z"
                                                        ),
                                                    },
                                                    "cycle_policies": {
                                                        "normal_max_hours": 100.0
                                                    },
                                                    "telescope_capabilities": {
                                                        "Mid": "AA2",
                                                        "Low": "AA2",
                                                    },
                                                },
                                                "capabilities": {
                                                    "mid": {
                                                        "AA0.5": {
                                                            "available_receivers": [
                                                                "Band_1",
                                                                "Band_2",
                                                            ],
                                                            "number_ska_dishes": 4,
                                                            "number_meerkat_dishes": 0,
                                                            "number_meerkatplus_dishes": 0,
                                                            "max_baseline_km": 1.5,
                                                            "available_bandwidth_hz": 800000.0,
                                                            "cbf_modes": [
                                                                "correlation",
                                                                "pst",
                                                            ],
                                                            "number_zoom_windows": 0,
                                                            "number_zoom_channels": 0,
                                                            "number_pss_beams": 0,
                                                            "number_pst_beams": 1,
                                                            "ps_beam_bandwidth_hz": 400000000.0,
                                                            "number_fsps": 4,
                                                            "allowed_channel_width_values": [
                                                                13440
                                                            ],
                                                            "allowed_channel_count_range_min": [
                                                                1
                                                            ],
                                                            "allowed_channel_count_range_max": [
                                                                58982
                                                            ],
                                                            "number_dish_ids": [
                                                                "SKA001",
                                                                "SKA036",
                                                                "SKA063",
                                                                "SKA100",
                                                            ],
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
                                                    }
                                                },
                                            },
                                        },
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Semantic Validation Successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "integer", "example": 0},
                                            "detail": {
                                                "type": "string",
                                                "example": "JSON is semantically valid",
                                            },
                                            "title": {
                                                "type": "string",
                                                "example": "Semantic validation",
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        "400": {
                            "description": (
                                "Bad Request due to semantic validation errors."
                            ),
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "detail": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "status": {"type": "integer"},
                                            "title": {"type": "string"},
                                        },
                                        "example": {
                                            "detail": [
                                                (
                                                    "receptor_ids are too many!Current"
                                                    " Limit is 4"
                                                ),
                                                (
                                                    "beams are too many! Current limit"
                                                    " is 1"
                                                ),
                                                (
                                                    "Invalid function for beams!"
                                                    " Currently allowed visibilities"
                                                ),
                                                (
                                                    "spectral windows are too many!"
                                                    " Current limit = 1"
                                                ),
                                                "Invalid input for freq_min",
                                                "Invalid input for freq_max",
                                                "freq_min should be less than freq_max",
                                                (
                                                    "length of receptor_ids should be"
                                                    " same as length of receptors"
                                                ),
                                                "receptor_ids did not match receptors",
                                            ],
                                            "status": 0,
                                            "title": "Semantic Validation Error",
                                        },
                                    }
                                }
                            },
                        },
                        "500": {
                            "description": "Internal Server Error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "detail": {"type": "string"},
                                            "traceback": {
                                                "type": "object",
                                                "properties": {
                                                    "key": {"type": "string"},
                                                    "type": {"type": "string"},
                                                    "full_traceback": {
                                                        "type": "string"
                                                    },
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        },
                    },
                }
            },
        },
        "components": {
            "parameters": {
                "cycle_id": {
                    "in": "query",
                    "name": "cycle_id",
                    "schema": {"type": "integer"},
                    "required": False,
                    "example": 1,
                },
                "osd_version": {
                    "in": "query",
                    "name": "osd_version",
                    "schema": {"type": "string"},
                    "required": False,
                    "example": "1.0.0",
                },
                "source": {
                    "in": "query",
                    "name": "source",
                    "schema": {
                        "type": "string",
                        "enum": ["file", "car", "gitlab"],
                        "default": "file",
                    },
                    "required": False,
                },
                "gitlab_branch": {
                    "in": "query",
                    "name": "gitlab_branch",
                    "schema": {"type": "string"},
                    "required": False,
                },
                "capabilities": {
                    "in": "query",
                    "name": "capabilities",
                    "schema": {
                        "type": "string",
                        "enum": ["mid", "low"],
                        "default": "mid",
                    },
                    "required": False,
                },
                "array_assembly": {
                    "in": "query",
                    "name": "array_assembly",
                    "schema": {"type": "string"},
                    "required": False,
                    "example": "AA0.5",
                },
            },
            "responses": {
                "NotFound": {
                    "description": "Not Found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "detail": {"type": "string"},
                                    "traceback": {
                                        "type": "object",
                                        "properties": {
                                            "key": {"type": "string"},
                                            "type": {"type": "string"},
                                            "full_traceback": {"type": "string"},
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "BadRequest": {
                    "description": (
                        "Bad Request, eg validation of against OpenAPI spec failed"
                    ),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "integer"},
                                    "title": {"type": "string"},
                                    "detail": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "InternalServerError": {
                    "description": "Internal Server Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "detail": {"type": "string"},
                                    "traceback": {
                                        "type": "object",
                                        "properties": {
                                            "key": {"type": "string"},
                                            "type": {"type": "string"},
                                            "full_traceback": {"type": "string"},
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
            "schemas": {
                "BadRequestResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "integer"},
                        "title": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "detail": {"type": "string"},
                        "traceback": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string"},
                                "type": {"type": "string"},
                                "full_traceback": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }


@pytest.fixture
def mid_osd_data():
    """This fixture returns the expected OpenAPI specification
        that is returned from the API. It is used to validate
        the response in tests.

    :returns dict: The OpenAPI specification
    """
    return MID_OSD_DATA_JSON


@pytest.fixture(scope="module")
def mock_mid_data():
    """This function is used as a fixture for mid json data

    :returns: mid json data
    """

    return MID_MOCK_DATA


@pytest.fixture(scope="module")
def mock_low_data():
    """This function is used as a fixture for low json data

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
