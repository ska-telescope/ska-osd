import pytest

from ska_ost_osd.rest import init_app

# flake8: noqa E501
# pylint: disable=W0621


@pytest.fixture
def tmdata_source():
    """
    TMData source URL fixture
    """
    return "file://tmdata"


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
            "version": "1.0.0",
        },
        "servers": [{"url": "ska-ost-osd/osd/api/v1"}],
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
                            "schema": {
                                "type": "string",
                                "enum": ["mid", "low"],
                                "default": "mid",
                            },
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
                                            "example": "car://gitlab.com/ska-telescope/ska-telmodel?1.14.1#tmdata",
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
    return {
        "capabilities": {
            "mid": {
                "AA0.5": {
                    "available_bandwidth_hz": 800000000.0,
                    "available_receivers": ["Band_1", "Band_2"],
                    "cbf_modes": ["CORR"],
                    "max_baseline_km": 1.5,
                    "number_channels": 14880,
                    "number_fsps": 4,
                    "number_meerkat_dishes": 0,
                    "number_meerkatplus_dishes": 0,
                    "number_pss_beams": 0,
                    "number_pst_beams": 0,
                    "number_ska_dishes": 4,
                    "number_zoom_channels": 0,
                    "number_zoom_windows": 0,
                    "ps_beam_bandwidth_hz": 0.0,
                },
                "basic_capabilities": {
                    "dish_elevation_limit_deg": 15.0,
                    "receiver_information": [
                        {
                            "max_frequency_hz": 1050000000.0,
                            "min_frequency_hz": 350000000.0,
                            "rx_id": "Band_1",
                        },
                        {
                            "max_frequency_hz": 1760000000.0,
                            "min_frequency_hz": 950000000.0,
                            "rx_id": "Band_2",
                        },
                        {
                            "max_frequency_hz": 3050000000.0,
                            "min_frequency_hz": 1650000000.0,
                            "rx_id": "Band_3",
                        },
                        {
                            "max_frequency_hz": 5180000000.0,
                            "min_frequency_hz": 2800000000.0,
                            "rx_id": "Band_4",
                        },
                        {
                            "max_frequency_hz": 8500000000.0,
                            "min_frequency_hz": 4600000000.0,
                            "rx_id": "Band_5a",
                        },
                        {
                            "max_frequency_hz": 15400000000.0,
                            "min_frequency_hz": 8300000000.0,
                            "rx_id": "Band_5b",
                        },
                    ],
                },
            }
        },
        "observatory_policy": {
            "cycle_description": "Science Verification",
            "cycle_information": {
                "cycle_id": "SKAO_2027_1",
                "proposal_close": "20260512T15:00:00.000z",
                "proposal_open": "20260327T12:00:00.000Z",
            },
            "cycle_number": 1,
            "cycle_policies": {"normal_max_hours": 100.0},
            "telescope_capabilities": {"Low": "AA2", "Mid": "AA2"},
        },
    }


@pytest.fixture
def mid_osd_data_for_cycle_id_1():
    """This fixture returns the expected OpenAPI specification
        that is returned from the API. It is used to validate
        the response in tests.

    :returns dict: The OpenAPI specification
    """
    return {
        "capabilities": {
            "mid": {
                "AA2": {
                    "available_bandwidth_hz": 800000.0,
                    "available_receivers": ["Band_1", "Band_2", "Band_5a", "Band_5b"],
                    "cbf_modes": ["CORR", "PST_BF", "PSS_BF"],
                    "max_baseline_km": 110.0,
                    "number_channels": 14880,
                    "number_fsps": 4,
                    "number_meerkat_dishes": 4,
                    "number_meerkatplus_dishes": 0,
                    "number_pss_beams": 384,
                    "number_pst_beams": 6,
                    "number_ska_dishes": 64,
                    "number_zoom_channels": 14880,
                    "number_zoom_windows": 16,
                    "ps_beam_bandwidth_hz": 800000.0,
                },
                "basic_capabilities": {
                    "dish_elevation_limit_deg": 15.0,
                    "receiver_information": [
                        {
                            "max_frequency_hz": 1050000000.0,
                            "min_frequency_hz": 350000000.0,
                            "rx_id": "Band_1",
                        },
                        {
                            "max_frequency_hz": 1760000000.0,
                            "min_frequency_hz": 950000000.0,
                            "rx_id": "Band_2",
                        },
                        {
                            "max_frequency_hz": 3050000000.0,
                            "min_frequency_hz": 1650000000.0,
                            "rx_id": "Band_3",
                        },
                        {
                            "max_frequency_hz": 5180000000.0,
                            "min_frequency_hz": 2800000000.0,
                            "rx_id": "Band_4",
                        },
                        {
                            "max_frequency_hz": 8500000000.0,
                            "min_frequency_hz": 4600000000.0,
                            "rx_id": "Band_5a",
                        },
                        {
                            "max_frequency_hz": 15400000000.0,
                            "min_frequency_hz": 8300000000.0,
                            "rx_id": "Band_5b",
                        },
                    ],
                },
            }
        },
        "observatory_policy": {
            "cycle_description": "Science Verification",
            "cycle_information": {
                "cycle_id": "SKAO_2027_1",
                "proposal_close": "20260512T15:00:00.000z",
                "proposal_open": "20260327T12:00:00.000Z",
            },
            "cycle_number": 1,
            "cycle_policies": {"normal_max_hours": 100.0},
            "telescope_capabilities": {"Low": "AA2", "Mid": "AA2"},
        },
    }


@pytest.fixture
def valid_observing_command_input():
    return {
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "subarray_id": 1,
        "dish": {"receptor_ids": ["SKA001", "SKA002"]},
        "sdp": {
            "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
            "execution_block": {
                "eb_id": "eb-test-20220916-00000",
                "max_length": 100.0,
                "context": {},
                "beams": [{"beam_id": "vis0", "function": "visibilities"}],
                "scan_types": [
                    {
                        "scan_type_id": ".default",
                        "beams": {
                            "vis0": {
                                "channels_id": "vis_channels",
                                "polarisations_id": "all",
                            },
                            "pss1": {
                                "field_id": "field_a",
                                "channels_id": "pulsar_channels",
                                "polarisations_id": "all",
                            },
                        },
                    },
                    {
                        "scan_type_id": "target:a",
                        "derive_from": ".default",
                        "beams": {"vis0": {"field_id": "field_a"}},
                    },
                ],
                "channels": [
                    {
                        "channels_id": "vis_channels",
                        "spectral_windows": [
                            {
                                "spectral_window_id": "fsp_1_channels",
                                "count": 14880,
                                "start": 0,
                                "stride": 2,
                                "freq_min": 350000000.0,
                                "freq_max": 368000000.0,
                                "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]],
                            }
                        ],
                    }
                ],
                "polarisations": [
                    {
                        "polarisations_id": "all",
                        "corr_type": ["XX", "XY", "YY", "YX"],
                    }
                ],
                "fields": [
                    {
                        "field_id": "field_a",
                        "phase_dir": {
                            "ra": [123, 0.1],
                            "dec": [80, 0.1],
                            "reference_time": "2023-02-16T01:23:45.678900",
                            "reference_frame": "ICRF3",
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
                    "script": {"kind": "batch", "name": "ical", "version": "0.1.0"},
                    "parameters": {},
                    "dependencies": [
                        {
                            "pb_id": "pb-mvp01-20200325-00001",
                            "kind": ["visibilities"],
                        }
                    ],
                    "sbi_ids": ["sbi-mvp01-20200325-00001"],
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
                            "kind": ["calibration"],
                        }
                    ],
                },
            ],
            "resources": {
                "csp_links": [1, 2, 3, 4],
                "receptors": ["SKA001", "SKA002"],
            },
        },
    }


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
def invalid_semantic_validation_body():
    return {
        "observing_command_input": {
            "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
            "subarray_id": 1,
            "dish": {
                "receptor_ids": [
                    "SKA001",
                    "SKA002",
                    "SKA003",
                    "SKA004",
                    "SKA005",
                    "SKA006",
                ]
            },
            "sdp": {
                "interface": "https://schema.skao.int/ska-sdp-assignres/0.4",
                "execution_block": {
                    "eb_id": "eb-test-20220916-00000",
                    "max_length": 100.0,
                    "context": {},
                    "beams": [
                        {"beam_id": "vis0", "function": "pulsar timing"},
                        {
                            "beam_id": "pss1",
                            "search_beam_id": 1,
                            "function": "pulsar search",
                        },
                    ],
                    "scan_types": [
                        {
                            "scan_type_id": ".default",
                            "beams": {
                                "vis0": {
                                    "channels_id": "vis_channels",
                                    "polarisations_id": "all",
                                },
                                "pss1": {
                                    "field_id": "field_a",
                                    "channels_id": "pulsar_channels",
                                    "polarisations_id": "all",
                                },
                            },
                        },
                        {
                            "scan_type_id": "target:a",
                            "derive_from": ".default",
                            "beams": {"vis0": {"field_id": "field_a"}},
                        },
                    ],
                    "channels": [
                        {
                            "channels_id": "vis_channels",
                            "spectral_windows": [
                                {
                                    "spectral_window_id": "fsp_1_channels",
                                    "count": 744,
                                    "start": 0,
                                    "stride": 2,
                                    "freq_min": 50000000000000.0,
                                    "freq_max": 49880000000000.0,
                                    "link_map": [[0, 0], [200, 1], [744, 2], [944, 3]],
                                },
                                {
                                    "spectral_window_id": "fsp_2_channels",
                                    "count": 744,
                                    "start": 2000,
                                    "stride": 1,
                                    "freq_min": 36000000.0,
                                    "freq_max": 49880000000000.0,
                                    "link_map": [[2000, 4], [2200, 5]],
                                },
                            ],
                        },
                        {
                            "channels_id": "pulsar_channels",
                            "spectral_windows": [
                                {
                                    "spectral_window_id": "pulsar_fsp_channels",
                                    "count": 744,
                                    "start": 0,
                                    "freq_min": 35000000.0,
                                    "freq_max": 3680049880000000000.0,
                                }
                            ],
                        },
                    ],
                    "polarisations": [
                        {
                            "polarisations_id": "all",
                            "corr_type": ["XX", "XY", "YY", "YX"],
                        }
                    ],
                    "fields": [
                        {
                            "field_id": "field_a",
                            "phase_dir": {
                                "ra": [123, 0.1],
                                "dec": [80, 0.1],
                                "reference_time": "2023-02-16T01:23:45.678900",
                                "reference_frame": "ICRF3",
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
                        "script": {"kind": "batch", "name": "ical", "version": "0.1.0"},
                        "parameters": {},
                        "dependencies": [
                            {
                                "pb_id": "pb-mvp01-20200325-00001",
                                "kind": ["visibilities"],
                            }
                        ],
                        "sbi_ids": ["sbi-mvp01-20200325-00001"],
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
                                "kind": ["calibration"],
                            }
                        ],
                    },
                ],
                "resources": {
                    "csp_links": [1, 2, 3, 4],
                    "receptors": ["FS4", "FS8", "FS16", "FS17", "FS22"],
                    "receive_nodes": 10,
                },
            },
        },
        "interface": "https://schema.skao.int/ska-tmc-assignresources/2.1",
        "raise_semantic": True,
        "osd_data": {
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
                }
            },
        },
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
        "detail": {
            "missing_required_fields": (
                "Missing required fields: observing_command_input"
            )
        },
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
        "detail": {
            "interface": (
                "value https://schemka-tmc-assignresources/2.1 for interface is not"
                " valid"
            ),
            "missing_required_fields": (
                "Missing required fields: observing_command_input"
            ),
            "raise_semantic": "value 123 for raise_semantic is not a boolean value ",
        },
        "status": -1,
        "title": "Value Error",
    }


@pytest.fixture
def valid_only_observing_command_input_in_request_body(valid_observing_command_input):
    return {"observing_command_input": valid_observing_command_input}
