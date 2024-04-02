import pytest

from ska_ost_osd.rest import init_app


@pytest.fixture
def client():
    app = init_app()
    with app.test_client() as client:  # pylint: disable=W0621
        yield client


@pytest.fixture
def open_api_spec():
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
        "servers": [{"url": "/ska-ost-osd/api/v1/"}],
        "paths": {
            "/osd": {
                "get": {
                    "summary": "Get OSD data filter by the query parameter",
                    "description": (
                        "Retrieves the OSD data which match the query parameters.\n"
                    ),
                    "operationId": "ska_ost_osd.rest.api.resources.get_osd",
                    "parameters": [
                        {
                            "in": "query",
                            "name": "cycle_id",
                            "schema": {"type": "integer"},
                            "required": False,
                        },
                        {
                            "in": "query",
                            "name": "osd_version",
                            "schema": {"type": "string"},
                            "required": False,
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
            }
        },
        "components": {
            "parameters": {
                "cycle_id": {
                    "in": "query",
                    "name": "cycle_id",
                    "schema": {"type": "integer"},
                    "required": False,
                },
                "osd_version": {
                    "in": "query",
                    "name": "osd_version",
                    "schema": {"type": "string"},
                    "required": False,
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
                    "schema": {"type": "string", "enum": ["mid", "low"]},
                    "required": False,
                },
                "array_assembly": {
                    "in": "query",
                    "name": "array_assembly",
                    "schema": {"type": "string"},
                    "required": False,
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
                "UnprocessableEntity": {
                    "description": (
                        "Unprocessable Entity, semantic error in request eg"
                        " mismatched IDs"
                    ),
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
    return {
        "capabilities": {
            "mid": {
                "AA0.5": {
                    "available_bandwidth_hz": 800000.0,
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
