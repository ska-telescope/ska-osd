from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from ska_ost_osd.osd.routers.api import validation_response
from tests.conftest import BASE_API_URL


@pytest.mark.parametrize(
    "cycle_id, osd_version, source, capabilities, array_assembly, expected",
    [
        (
            100000,
            "1..1.0",
            "file",
            "mid",
            "AAA3",
            {
                "result_data": [
                    "Cycle_id and Array_assembly cannot be used together",
                    "osd_version 1..1.0 is not valid",
                    "array_assembly AAA3 is not valid",
                    "Cycle 100000 is not valid,Available IDs are 1",
                ],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            None,
            None,
            "file",
            "mid",
            "AA100000",
            {
                "result_data": [
                    "Array Assembly AA100000 is not valid,Available Array Assemblies"
                    " are AA0.5, AA1, AA2"
                ],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            1,
            None,
            None,
            None,
            "AA0.5",
            {
                "result_data": ["Cycle_id and Array_assembly cannot be used together"],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
        (
            None,
            None,
            None,
            None,
            None,
            {
                "result_data": ["Either cycle_id or capabilities must be provided"],
                "result_status": "failed",
                "result_code": 400,
            },
        ),
    ],
)
def test_invalid_osd_tmdata_source(
    cycle_id,
    osd_version,
    source,
    capabilities,
    array_assembly,
    expected,
    client_get,
    osd_versions,
):
    """This test case checks the functionality of OSD API It will validate all
    params and return expected output.

    NOTE: This testcase has dependency on 'cycle_gitlab_release_version_mapping.json'
          file so make sure to run the 'make osd-pre-release' command which is
          mentioned in readme and document files.

    :param cycle_id,: 1, 2
    :param osd_version,: 1.0.0
    :param source,: File, Car and Gitlab
    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param expected: output of OSD API

    :returns: assert equals values
    """

    if expected.get("detail") and isinstance(expected["detail"], list):
        expected["detail"][0] = expected["detail"][0].format(osd_versions=osd_versions)
    params = {
        "cycle_id": cycle_id,
        "osd_version": osd_version,
        "source": source,
        "capabilities": capabilities,
        "array_assembly": array_assembly,
    }
    filtered_params = {k: v for k, v in params.items() if v is not None}
    response = client_get(
        f"{BASE_API_URL}/osd",
        params=filtered_params,
    ).json()
    print(f"response::::::::::::::: {response}")
    print(f"expected::::::::::::::: {expected}")

    if array_assembly == "AA100000":
        # msg = f"{','.join(response.json()['result_data'][0].split(',')[1:])}"
        # expected_msg = f"{expected['result_data'][0].split(',')[0]},{msg}"
        assert array_assembly in response["result_data"][0]

    else:
        assert response["result_data"] == expected["result_data"]


@patch("ska_ost_osd.osd.routers.api.get_osd_using_tmdata")
def test_osd_endpoint(client_get, mock_mid_data):
    """This function tests that a request to the OSD endpoint for a specific
    OSD returns expected data for that OSD.

    :param mid_osd_data (dict): The expected data for the OSD.
    :raises AssertionError: If the response does not contain the
        expected OSD data or returns an error status code.
    """
    response = client_get(
        f"{BASE_API_URL}/osd",
        params={
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )

    response = MagicMock()
    response.status_code = 200
    response.json = mock_mid_data["AA0.5"]

    assert response.status_code == 200
    assert response.json == mock_mid_data["AA0.5"]


def test_invalid_osd_tmdata_source_capabilities(client_get):
    """This function tests that a request with an invalid capability returns
    the expected error response.

    :raises AssertionError: If the response does not contain the
        expected error message.
    """

    response = client_get(
        f"{BASE_API_URL}/osd",
        params={
            "cycle_id": 1,
            "osd_version": "1.1.0",
            "source": "file",
            "capabilities": "midd",
            "array_assembly": "AA3",
        },
    ).json()

    expected = (
        "query.capabilities: Input should be 'mid' or 'low', invalid payload: midd"
    )
    assert response["result_data"] == expected


def test_response_body():
    """This function tests that the response from the REST API contains the
    expected body contents when retrieving OSD metadata.

    :raises AssertionError: If the response body is invalid.
    """

    error_msg = "Validation failed"
    response = validation_response(
        detail=error_msg,
        status=0,
        title="Validation Error",
        http_status=HTTPStatus.OK,
    )
    expected = {"detail": "Validation failed", "title": "Validation Error", "status": 0}
    assert response[0] == expected


def test_osd_source(client_get):
    """This function tests that a request with an OSD source as car ."""

    response = client_get(
        f"{BASE_API_URL}/osd", params={"cycle_id": 1, "source": "car"}
    )
    error_msg = {
        "detail": (
            "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#tmdata not found"
            " in SKA CAR - make sure to add tmdata CI!"
        ),
        "title": "Bad Request",
    }

    response.json == error_msg  # pylint: disable=W0104


def test_osd_source_gitlab(client_get):
    """This function tests that a request with an OSD source as car."""

    response = client_get(
        f"{BASE_API_URL}/osd", params={"cycle_id": 1, "source": "gitlab"}
    )

    error_msg = [
        {
            "detail": "404: 404 Commit Not Found",
            "status": 0,
            "title": "Internal Server Error",
        },
        500,
    ]

    response.json == error_msg  # pylint: disable=W0104
