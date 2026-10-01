from http import HTTPStatus

from ska_ost_osd.common.utils import remove_none_params
from tests.conftest import BASE_API_URL


def test_osd_legacy_query_parameters_are_noops(test_client):
    """Legacy source and version parameters do not alter OSD selection."""
    baseline = test_client.get(f"{BASE_API_URL}/osd", params={"cycle_id": 2})
    legacy_parameters = test_client.get(
        f"{BASE_API_URL}/osd",
        params={
            "cycle_id": 2,
            "source": "gitlab",
            "osd_version": "999.999.999",
            "gitlab_branch": "legacy-client-branch",
        },
    )

    assert baseline.status_code == HTTPStatus.OK
    assert legacy_parameters.status_code == HTTPStatus.OK
    assert legacy_parameters.json()["result_data"] == baseline.json()["result_data"]


def test_cycle_osd_uses_selected_cycle_file(test_client):
    """A cycle-specific request includes its selected cycle-file policy."""
    response = test_client.get(f"{BASE_API_URL}/osd", params={"cycle_id": 2})
    body = response.json()

    assert response.status_code == HTTPStatus.OK
    assert body["result_data"]["observatory_policy"]["cycle_number"] == 2
    assert body["result_data"]["observatory_policy"]["cycle_id"] == (
        "TEST_SKAO_2027_Low_AA2_Proposal"
    )
    assert set(body["result_data"]["capabilities"]) == {"mid", "low"}


def test_cycle_capability_uses_cycle_selected_array_assembly(test_client):
    """A valid cycle capability request uses the assembly from its policy."""
    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={"cycle_id": 2, "capabilities": "mid"},
    )
    body = response.json()

    assert response.status_code == HTTPStatus.OK
    assert list(body["result_data"]["capabilities"]) == ["mid"]
    assert set(body["result_data"]["capabilities"]["mid"]) == {
        "basic_capabilities",
        "AA2",
    }


def test_catalogue_filter_does_not_include_observatory_policy(test_client):
    """A non-cycle filter selects catalogue data without a cycle policy."""
    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={"capabilities": "mid", "array_assembly": "AA0.5"},
    )
    body = response.json()

    assert response.status_code == HTTPStatus.OK
    assert "observatory_policy" not in body["result_data"]
    assert list(body["result_data"]["capabilities"]) == ["mid"]
    assert "AA0.5" in body["result_data"]["capabilities"]["mid"]


def test_cycle_id_and_array_assembly_are_incompatible(test_client):
    """A cycle policy, rather than an explicit array filter, selects assemblies."""
    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={"cycle_id": 2, "array_assembly": "AA0.5"},
    )
    body = response.json()

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Cycle_id and Array_assembly cannot be used together" in str(
        body["result_data"]
    )


def test_cycle_rejects_capability_not_in_policy(test_client):
    """An explicit capability must be available in the selected cycle."""
    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={"cycle_id": 1, "capabilities": "mid"},
    )
    body = response.json()

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert body["result_data"] == [
        "Capability mid is not available for cycle 1,Available Capabilities are low"
    ]


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


def test_osd_source_reports_backend_resolution_error(car_source_failure_client):
    """OSD endpoint should surface CAR TMData read errors.

    Uses dependency override so the test is deterministic and does not
    connect to CAR.
    """
    response = car_source_failure_client.get(
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
    test_client,
):
    """Test that an invalid cycle_id returns the expected error response.

    :raises AssertionError: If the respone is not as expected.
    """

    response = test_client.get(
        f"{BASE_API_URL}/osd",
        params={"cycle_id": 3, "source": "file", "capabilities": "mid"},
    ).json()

    assert "Cycle 3 is not valid" in response["result_data"][0]
    assert response["result_code"] == HTTPStatus.BAD_REQUEST
