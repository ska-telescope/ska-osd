import json
import os
from importlib.metadata import version

import pytest

from ska_ost_osd.rest import init_app
from ska_ost_osd.telvalidation.constant import CAR_TELMODEL_SOURCE
from tests.unit.telvalidation.test_semantic_validator import (
    INVALID_MID_ASSIGN_JSON,
    MID_OSD_DATA_JSON,
    VALID_MID_ASSIGN_JSON,
)

# flake8: noqa E501
# pylint: disable=W0621
OSD_MAJOR_VERSION = version("ska-ost-osd").split(".")[0]
BASE_API_URL = f"/ska-ost-osd/osd/api/v{OSD_MAJOR_VERSION}"


@pytest.fixture
def tmdata_source():
    """
    TMData source URL fixture
    """
    return CAR_TELMODEL_SOURCE[0]


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
                                                    "receptor_ids": ["SKA001", "SKA002"]
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
                                                            "number_channels": 14880,
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
                                                            "allowed_channel_count_range_min": 1,
                                                            "allowed_channel_count_range_max": 58982,
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
                                                (
                                                    "Invalid input for channel_count!"
                                                    " Currently allowed 14880"
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
            "beams are too many! Current limit is 1",
            "Invalid function for beams! Currently allowed visibilities",
            "spectral windows are too many! Current limit = 1",
            "Invalid input for channel_count! Currently allowed 14880",
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
        "detail": ["Input should be a valid dictionary"],
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
