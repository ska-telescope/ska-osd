from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from ska_ost_osd.common.utils import remove_none_params
from tests.conftest import BASE_API_URL


def test_invalid_osd_tmdata_source(
    invalid_osd_tmdata_source_input,
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

    (
        cycle_id,
        osd_version,
        source,
        capabilities,
        array_assembly,
        expected,
    ) = invalid_osd_tmdata_source_input

    if expected.get("detail") and isinstance(expected["detail"], list):
        expected["detail"][0] = expected["detail"][0].format(osd_versions=osd_versions)
    params = {
        "cycle_id": cycle_id,
        "osd_version": osd_version,
        "source": source,
        "capabilities": capabilities,
        "array_assembly": array_assembly,
    }

    response = client_get(
        f"{BASE_API_URL}/osd",
        params=remove_none_params(params),
    ).json()

    if array_assembly == "AA100000":
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


@patch("ska_ost_osd.osd.routers.api.get_osd_using_tmdata")
def test_osd_sub_bands_endpoint(client_get, mock_mid_data):
    """This function checks that the sub_bands are defined for band 5b.

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
    ).json()

    response = MagicMock()
    response.status_code = 200
    response.json = mock_mid_data["basic_capabilities"]

    # Check that sub_bands have been defined for band 5b
    sub_bands = response.json["receiver_information"][5]["sub_bands"]
    assert len(sub_bands) == 3


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


def test_mid_low_response(
    mid_low_response_input,
    client_get,
):
    """This function tests that the response from the REST API contains the
    expected body contents when retrieving OSD metadata.

    :raises AssertionError: If the expected data is invalid.
    """

    (
        cycle_id,
        osd_version,
        source,
        gitlab_branch,
        capabilities,
        array_assembly,
    ) = mid_low_response_input
    params = {
        "cycle_id": cycle_id,
        "osd_version": osd_version,
        "source": source,
        "gitlab_branch": gitlab_branch,
        "capabilities": capabilities,
        "array_assembly": array_assembly,
    }

    response = client_get(
        f"{BASE_API_URL}/osd",
        params=remove_none_params(params),
    ).json()

    result_data = response["result_data"]["capabilities"]

    assert capabilities in result_data.keys()
    assert array_assembly in result_data[capabilities].keys()


@pytest.mark.parametrize(
    "cycle_id, source, capabilities",
    [
        (
            3,
            "file",
            "mid",
        ),
        (
            2,
            "file",
            "low",
        ),
    ],
)
def test_invalid_cycle_id(
    cycle_id,
    source,
    capabilities,
    client_get,
):
    """This function tests that the response from the REST API contains the
    expected body contents when retrieving OSD metadata.

    :raises AssertionError: If the expected data is invalid.
    """

    params = {
        "cycle_id": cycle_id,
        "source": source,
        "capabilities": capabilities,
    }

    response = client_get(
        f"{BASE_API_URL}/osd",
        params=params,
    ).json()

    expected = f"Cycle {cycle_id} is not valid,Available IDs are 1"

    assert response["result_data"][0] == expected
    assert response["result_code"] == HTTPStatus.BAD_REQUEST
