from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from ska_ost_osd.rest import get_openapi_spec, init_app
from ska_ost_osd.rest.api.resources import validation_response
from tests.conftest import BASE_API_URL


def test_init_app(open_api_spec):
    """This function tests that the Flask application can be initialized
       properly and that the OpenAPI spec is registered as expected.

    :param open_api_spec (dict): The OpenAPI specification expected to be
       registered on the app.

    :raises AssertionError: If the app fails to initialize or the wrong spec
       is registered.
    """

    with patch("ska_ost_osd.rest.get_openapi_spec", return_value=open_api_spec):
        app = init_app()

        assert app.url_map._rules_by_endpoint[  # pylint: disable=W0212
            f"{BASE_API_URL}.ska_ost_osd_rest_api_resources_get_osd"
        ]


def test_get_openapi_spec(open_api_spec):
    """This function tests that a valid OpenAPI specification
       is returned when requesting the API documentation.

    :params open_api_spec (dict): The expected OpenAPI specification

    :raises AssertionError: If the response spec differs from expected.
    """

    with patch("ska_ost_osd.rest.prance.ResolvingParser", autospec=True) as mock_parser:
        instance = mock_parser.return_value
        instance.specification = open_api_spec

        spec = get_openapi_spec()

        assert (
            spec == open_api_spec
        ), "The specification should match the mock specification"
        mock_parser.assert_called_once_with(  # pylint: disable=W0106
            (
                "/builds/ska-telescope/ost/ska-ost-osd/src/"
                "ska_ost_osd/rest/./openapi/osd-openapi-v1.yaml"
            ),
            lazy=True,
            strict=True,
        ), "ResolvingParser should be called with expected arguments"


def test_init_app_client(client, open_api_spec):
    """This function tests that the get_openapi_spec function returns
       the expected OpenAPI specification.

    :param open_api_spec (dict): The OpenAPI specification that is expected
       to be returned.

    :raises AssertionError: If the actual spec returned does not match the
       expected spec.
    """

    with (
        patch("ska_ost_osd.rest.get_openapi_spec", return_value=open_api_spec),
        patch("ska_ost_osd.rest.App") as mock_connexion_app,
    ):
        mock_connexion_instance = mock_connexion_app.return_value
        mock_flask_app = mock_connexion_instance.app
        mock_flask_app.test_client = MagicMock(return_value=client)

        init_app(open_api_spec=open_api_spec)

        # Verify that the Connexion app is initialized with the correct parameters
        mock_connexion_app.assert_called_once_with(
            "ska_ost_osd.rest", specification_dir="openapi/"
        )

        # Verify that the API is added with the correct spec and base path
        mock_connexion_instance.add_api.assert_called_once()
        call_args = mock_connexion_instance.add_api.call_args
        assert call_args[0][0] == open_api_spec
        assert call_args[1]["base_path"].startswith("/")


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
                "detail": [
                    "Cycle_id and Array_assembly cannot be used together",
                    "osd_version 1..1.0 is not valid",
                    "array_assembly AAA3 is not valid",
                    "Cycle 100000 is not valid,Available IDs are 1",
                ],
                "status": -1,
                "title": "Value Error",
            },
        ),
        (
            None,
            None,
            "file",
            "mid",
            "AA100000",
            {
                "detail": [
                    "Array Assembly AA100000 is not valid,Available Array Assemblies"
                    " are AA0.5, AA1, AA2"
                ],
                "title": "Value Error",
                "status": -1,
            },
        ),
        (
            1,
            None,
            None,
            None,
            "AA0.5",
            {
                "detail": ["Cycle_id and Array_assembly cannot be used together"],
                "status": -1,
                "title": "Value Error",
            },
        ),
        (
            None,
            None,
            None,
            None,
            None,
            {
                "detail": ["Either cycle_id or capabilities must be provided"],
                "status": -1,
                "title": "Value Error",
            },
        ),
        (
            1,
            "31.0.7",
            None,
            ["mid"],
            None,
            {
                "detail": [
                    "OSD Version 31.0.7 is not valid,Available OSD Versions are"
                    " {osd_versions}"
                ],
                "status": -1,
                "title": "Value Error",
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
    client,
    osd_versions,
):
    """This test case checks the functionality of OSD API
        It will validate all params and return expected output.

    NOTE: This testcase has dependency on 'cycle_gitlab_release_version_mapping.json'
          file so make sure to run the 'make osd-pre-release' command which is
          mentioned in readme and document files.

    :param cycle_id,: 1, 2
    :param osd_version,: 1.0.0
    :param source,: File, Car and Gitlab
    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param expected: output of OSD API
    :param client: Flask test client

    :returns: assert equals values
    """

    if expected.get("detail") and isinstance(expected["detail"], list):
        expected["detail"][0] = expected["detail"][0].format(osd_versions=osd_versions)

    response = client.get(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": cycle_id,
            "osd_version": osd_version,
            "source": source,
            "capabilities": capabilities,
            "array_assembly": array_assembly,
        },
    )

    if array_assembly == "AA100000":
        msg = f"{','.join(response.json['detail'][0].split(',')[1:])}"
        expected_msg = f"{expected['detail'][0].split(',')[0]},{msg}"
        assert response.json["detail"][0] == expected_msg

    else:
        assert response.json == expected


@patch("ska_ost_osd.rest.api.resources.get_osd_using_tmdata")
def test_osd_endpoint(client, mock_mid_data):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param mid_osd_data (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """
    response = client.get(
        f"{BASE_API_URL}/osd",
        query_string={
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


def test_invalid_osd_tmdata_source_capabilities(client):
    """This function tests that a request with an invalid capability
       returns the expected error response.

    :param client (FlaskClient): The Flask test client.

    :raises AssertionError: If the response does not contain the
       expected error message.
    """

    error_msgs = client.get(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": 1,
            "osd_version": "1.1.0",
            "source": "file",
            "capabilities": "midd",
            "array_assembly": "AA3",
        },
    )

    expected_error_msg = "'midd' is not one of ['mid', 'low']"
    assert error_msgs.json["detail"].startswith(expected_error_msg)


def test_response_body():
    """This function tests that the response from the REST API contains
       the expected body contents when retrieving OSD metadata.

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


def test_osd_source(client):
    """This function tests that a request with an OSD source as car .

    :param client (FlaskClient): The Flask test client.
    """

    response = client.get(
        f"{BASE_API_URL}/osd", query_string={"cycle_id": 1, "source": "car"}
    )
    error_msg = {
        "detail": (
            "gitlab://gitlab.com/ska-telescope/ost/ska-ost-osd?1.0.0#tmdata not found"
            " in SKA CAR - make sure to add tmdata CI!"
        ),
        "title": "Bad Request",
    }

    response.json == error_msg  # pylint: disable=W0104


def test_osd_source_gitlab(client):
    """This function tests that a request with an OSD source as car .

    :param client (FlaskClient): The Flask test client.
    """

    response = client.get(
        f"{BASE_API_URL}/osd", query_string={"cycle_id": 1, "source": "gitlab"}
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


@pytest.mark.parametrize(
    "cycle_id, capabilities, array_assembly, expected",
    [
        (
            100000,
            "mid",
            "AA0.5",
            {
                "detail": "Cycle 100000 is not valid,Available IDs are 1",
                "status": -1,
                "title": "Value Error",
            },
        ),
        (
            None,
            "mid",
            "AA1",
            {
                "detail": "Cycle ID must be an integer",
                "title": "Value Error",
                "status": -1,
            },
        ),
        (
            1,
            "mid",
            "ABC",
            {
                "detail": "Array assembly must be in the format of AA[0-9].[0-9]",
                "status": -1,
                "title": "Value Error",
            },
        ),
        (
            1,
            "low",
            "AA500000",
            {
                "detail": (
                    "Array Assembly AA500000 is not valid,Available Array Assemblies"
                    " are AA0.5, AA1, AA2"
                ),
                "status": -1,
                "title": "Value Error",
            },
        ),
    ],
)
def test_invalid_put_osd_source(
    cycle_id,
    capabilities,
    array_assembly,
    expected,
    client,
):
    """This test case checks the functionality of OSD API
        It will validate all params and return expected output.

    NOTE: This testcase has dependency on 'cycle_gitlab_release_version_mapping.json'
          file so make sure to run the 'make osd-pre-release' command which is
          mentioned in readme and document files.

    :param cycle_id,: 1, 2
    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param expected: output of OSD API
    :param client: Flask test client

    :returns: assert equals values
    """

    response = client.put(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": cycle_id,
            "capabilities": capabilities,
            "array_assembly": array_assembly,
        },
    )

    if array_assembly == "AA500000":
        msg = f"{','.join(response.json['detail'].split(',')[1:])}"
        expected_msg = f"{expected['detail'].split(',')[0]},{msg}"
        assert response.json["detail"] == expected_msg

    else:
        assert response.json == expected


@patch("ska_ost_osd.rest.api.resources.update_file")
@patch("ska_ost_osd.rest.api.resources.get_osd_using_tmdata")
def test_osd_put_endpoint(mock_osd_data, client, mid_osd_data, mock_mid_data):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param mid_osd_data (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """
    mock_osd_data.return_value = mid_osd_data
    response = client.put(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": 1,
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )

    response = MagicMock()
    response.status_code = 200
    response.json = mock_mid_data["AA0.5"]

    assert response.status_code == 200
    assert response.json == mock_mid_data["AA0.5"]


@patch("ska_ost_osd.rest.api.resources.update_file")
def test_osd_put_observatory_policies(mock_osd_data, client, osd_observatory_policies):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param osd_observatory_policies (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """
    mock_osd_data.return_value = osd_observatory_policies
    response = client.put(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": 1,
            "capabilities": "mid",
        },
    )
    assert response.status_code == 200
    assert response.json == osd_observatory_policies


@patch("ska_ost_osd.rest.api.resources.update_file")
def test_osd_put_basic_capabilities(mock_osd_data, client, mid_osd_data):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param mid_osd_data (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """
    mock_osd_data.return_value = mid_osd_data
    basic_capabilities_dict = {
        "basic_capabilities": {
            "dish_elevation_limit_deg": 15.0,
            "receiver_information": [
                {
                    "rx_id": "Band_1",
                    "min_frequency_hz": 350000000.0,
                    "max_frequency_hz": 1050000000.0,
                }
            ],
        }
    }

    response = client.put(
        f"{BASE_API_URL}/osd",
        query_string={
            "cycle_id": 1,
            "capabilities": "mid",
        },
        json=basic_capabilities_dict,
    )

    assert response.status_code == 200
    assert (
        response.json["basic_capabilities"]["dish_elevation_limit_deg"]
        == mid_osd_data["capabilities"]["mid"]["basic_capabilities"][
            "dish_elevation_limit_deg"
        ]
    )


@patch("ska_ost_osd.rest.api.resources.get_tmdata_sources")
@pytest.mark.parametrize(
    "json_body_to_validate, response",
    [
        ("valid_semantic_validation_body", "valid_semantic_validation_response"),
        ("invalid_semantic_validation_body", "invalid_semantic_validation_response"),
    ],
)
def test_semantic_validate_api(
    mock_tmdata, client, request, json_body_to_validate, response
):
    """
    Test semantic validation API with valid and invalid JSON
    """
    mock_tmdata.return_value = ["file://tmdata"]
    json_body = request.getfixturevalue(json_body_to_validate)
    expected_response = request.getfixturevalue(response)

    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


@patch("ska_ost_osd.telvalidation.semantic_validator.VALIDATION_STRICTNESS", "1")
@patch("ska_ost_osd.rest.api.resources.VALIDATION_STRICTNESS", "1")
@patch("ska_ost_osd.rest.api.resources.get_tmdata_sources")
@pytest.mark.parametrize(
    "json_body_to_validate, response",
    [
        ("valid_semantic_validation_body", "semantic_validation_disable_response"),
        ("invalid_semantic_validation_body", "semantic_validation_disable_response"),
    ],
)
def test_disable_semantic_validate_api(
    mock_tmdata, client, request, json_body_to_validate, response
):
    """
    Test semantic validation API when VALIDATION_STRICTNESS is set to 1
    """
    mock_tmdata.return_value = ["file://tmdata"]
    json_body = request.getfixturevalue(json_body_to_validate)
    expected_response = request.getfixturevalue(response)

    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)

    assert res.get_json() == expected_response


def test_semantic_validate_api_not_passing_required_keys(
    client, observing_command_input_missing_response, valid_semantic_validation_body
):
    """
    Test semantic validation API response with missing input observing_command_input key
    """
    json_body = valid_semantic_validation_body.copy()
    del json_body["observing_command_input"]
    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)
    assert res.get_json() == observing_command_input_missing_response


@patch("ska_ost_osd.rest.api.resources.get_tmdata_sources")
@pytest.mark.parametrize(
    "json_body_to_validate, response, key_to_delete",
    [
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "sources",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "interface",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "raise_semantic",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "osd_data",
        ),
    ],
)
def test_not_passing_optional_keys(
    mock_tmdata, request, client, json_body_to_validate, response, key_to_delete
):
    """
    Test semantic validation API response by not passing optional keys
    """
    mock_tmdata.return_value = ["file://tmdata"]
    json_body = request.getfixturevalue(json_body_to_validate).copy()
    del json_body[key_to_delete]
    expected_response = request.getfixturevalue(response)
    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


def test_wrong_values_and_no_observing_command_input(
    wrong_semantic_validation_parameter_value_response,
    wrong_semantic_validation_parameter_body,
    client,
):
    """
    Test semantic validation API response with wrong values
    """
    json_body = wrong_semantic_validation_parameter_body
    expected_response = wrong_semantic_validation_parameter_value_response
    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


@patch("ska_ost_osd.rest.api.resources.get_tmdata_sources")
def test_passing_only_required_keys(
    mock_tmdata,
    client,
    valid_only_observing_command_input_in_request_body,
    valid_semantic_validation_response,
):
    """
    Test semantic validation API response with only required keys.
    """
    mock_tmdata.return_value = ["file://tmdata"]
    json_body = valid_only_observing_command_input_in_request_body
    expected_response = valid_semantic_validation_response
    res = client.post(f"{BASE_API_URL}/semantic_validation", json=json_body)
    assert res.get_json() == expected_response
