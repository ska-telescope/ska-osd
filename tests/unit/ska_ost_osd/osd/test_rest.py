from http import HTTPStatus

from fastapi.testclient import TestClient

from ska_ost_osd.app import create_app
from ska_ost_osd.common.utils import remove_none_params
from ska_ost_osd.osd.routers.dependencies import get_tmdata_for_osd_query
from tests.conftest import BASE_API_URL


def test_osd_endpoint(test_client):
    """This function tests that a request to the OSD endpoint for a specific
    OSD returns expected data for that OSD.

    :param mid_osd_data (dict): The expected data for the OSD.
    :raises AssertionError: If the response does not contain the
        expected OSD data or returns an error status code.
    """

    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    ).json()

    assert response["result_code"] == 200
    assert "AA0.5" in response["result_data"]["capabilities"]["mid"].keys()


def test_osd_sub_bands_endpoint(test_client):
    """This function checks that the sub_bands are defined for band 5b.

    :param mid_osd_data (dict): The expected data for the OSD.
    :raises AssertionError: If the response does not contain the
        expected OSD data or returns an error status code.
    """
    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )
    assert response.status_code == 200

    result_data = response.json()["result_data"]
    b5_info = result_data["capabilities"]["mid"]["basic_capabilities"][
        "receiver_information"
    ][5]
    assert "sub_bands" in b5_info
    assert len(b5_info["sub_bands"]) == 3


def test_invalid_osd_tmdata_source_capabilities(test_client):
    """This function tests that a request with an invalid capability returns
    the expected error response.

    :raises AssertionError: If the response does not contain the
        expected error message.
    """

    response = test_client.get(
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


def test_osd_source_reports_backend_resolution_error():
    """OSD endpoint should surface CAR TMData read errors.

    get_tmdata_for_osd_query should still resolve successfully; the
    returned TMData object fails when OSD retrieval reads from it.
    Uses dependency override so the test is deterministic and does not
    connect to CAR.
    """
    app = create_app()

    class FailingTMData:
        def __getitem__(self, _):
            raise ValueError(
                "car://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#tmdata "
                "not found in SKA CAR - make sure to add tmdata CI!"
            )

    app.dependency_overrides[get_tmdata_for_osd_query] = lambda: FailingTMData()
    client = TestClient(app)

    response = client.get(
        f"{BASE_API_URL}/osd", params={"cycle_id": 1, "source": "car"}
    )
    body = response.json()

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert body["result_code"] == HTTPStatus.BAD_REQUEST
    assert body["result_status"] == "failed"
    assert "not found in SKA CAR" in body["result_data"]


def test_mid_low_response(
    mid_low_response_input,
    test_client,
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

    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params=remove_none_params(params),
    ).json()

    result_data = response["result_data"]["capabilities"]

    assert capabilities in result_data.keys()
    assert array_assembly in result_data[capabilities].keys()


def test_invalid_cycle_id(
    sad_path_client,
):
    """Client smoke test for dependency-resolution errors in /osd.

    Resolver logic is exercised through get_tmdata_for_osd_query by not
    overriding that dependency on sad_path_client.
    """
    response = sad_path_client.get(
        f"{BASE_API_URL}/osd",
        params={"cycle_id": 3, "source": "file", "capabilities": "mid"},
    ).json()

    assert "Cycle 3 is not valid" in response["result_data"][0]
    assert response["result_code"] == HTTPStatus.BAD_REQUEST
