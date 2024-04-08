from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from ska_ost_osd.rest import get_openapi_spec, init_app
from ska_ost_osd.rest.api.resources import validation_response


def test_get_open_api_spec(open_api_spec):
    """Test the get_open_api_spec function.

    :param open_api_spec (dict): The OpenAPI specification this test expects
        to be returned.
    """
    assert get_openapi_spec() == open_api_spec


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
            "/ska-ost-osd/api/v1.ska_ost_osd_rest_api_resources_get_osd"
        ]


def test_get_openapi_spec(open_api_spec):
    """This function tests that a valid OpenAPI specification
       is returned when requesting the API documentation.

    :params open_api_spec (dict): The expected OpenAPI specification

    :raises AssertionError: If the response spec differs from expected.
    """

    # Patch 'prance.ResolvingParser' to return a mock spec
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

    with patch("ska_ost_osd.rest.get_openapi_spec", return_value=open_api_spec), patch(
        "ska_ost_osd.rest.App"
    ) as mock_connexion_app:
        mock_connexion_instance = mock_connexion_app.return_value
        mock_flask_app = mock_connexion_instance.app
        mock_flask_app.test_client = MagicMock(return_value=client)

        app = init_app(open_api_spec=open_api_spec)  # noqa: F841, pylint: disable=W0612

        # Verify that the Connexion app is initialized with the correct parameters
        mock_connexion_app.assert_called_once_with(
            "ska_ost_osd.rest", specification_dir="openapi/"
        )

        # Verify that the API is added with the correct spec and base path
        mock_connexion_instance.add_api.assert_called_once()
        call_args = mock_connexion_instance.add_api.call_args
        assert call_args[0][0] == open_api_spec
        assert call_args[1]["base_path"].startswith("/")


def test_osd_endpoint(client, mid_osd_data):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param mid_osd_data (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """

    response = client.get(
        "/ska-ost-osd/api/v1/osd",
        query_string={
            "cycle_id": 1,
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )

    assert response.status_code == 200
    assert response.json == mid_osd_data


def test_invalid_osd_tmdata_source(client):
    """This function tests that a request with an invalid OSD TM data
       source ID returns the expected error response.

    :param client (FlaskClient): The Flask test client.

    :raises AssertionError: If the response does not contain the expected
       error message.
    """
    error_msgs = client.get(
        "/ska-ost-osd/api/v1/osd",
        query_string={
            "cycle_id": 3,
            "osd_version": "1..1.0",
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AAA3",
        },
    )

    expected_error_msg_1 = "osd_version 1..1.0 is not valid"
    expected_error_msg_2 = "array_assembly AAA3 is not valid"
    expected_error_msg_3 = "Cycle id 3 is not valid,Available IDs are 1,2"

    assert (
        error_msgs.json
        == f"{expected_error_msg_1}, {expected_error_msg_2}, {expected_error_msg_3}"
    )


def test_invalid_osd_tmdata_source_capabilities(client):
    """This function tests that a request with an invalid capability
       returns the expected error response.

    :param client (FlaskClient): The Flask test client.

    :raises AssertionError: If the response does not contain the
       expected error message.
    """

    error_msgs = client.get(
        "/ska-ost-osd/api/v1/osd",
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


def test_osd_source(client):
    """This function tests that a request with an OSD source as car .

    :param client (FlaskClient): The Flask test client.
    """
    osd_source_link = client.get(
        "/ska-oso-osd/api/v1/osd", query_string={"cycle_id": 1, "source": "car"}
    )
    assert osd_source_link == osd_source_link


def test_invalid_array_assembly(client):
    """Test invalid array_assembly
    :param client (FlaskClient): The Flask test client.
    """
    error_msgs = client.get(
        "/ska-ost-osd/api/v1/osd",
        query_string={"capabilities": "mid", "array_assembly": "AA3"},
    )

    assert (
        error_msgs.json
        == "Array Assembly AA3 doesn't exists. Available are AA0.5, AA1, AA2"
    )


def test_response_body():
    """This function tests that the response from the REST API contains
       the expected body contents when retrieving OSD metadata.

    :raises AssertionError: If the response body is invalid.
    """
    error_msg = "Validation failed"
    response = validation_response(
        error_msg=error_msg,
        status=0,
        title="Validation Error",
        http_status=HTTPStatus.OK,
    )
    expected = {"detail": "Validation failed", "title": "Validation Error", "status": 0}
    assert response[0] == expected


@pytest.mark.parametrize(
    "json_body_to_validate, response",
    [
        ("valid_semantic_validation_body", "valid_semantic_validation_response"),
        ("invalid_semantic_validation_body", "invalid_semantic_validation_response"),
    ],
)
def test_semantic_validate_api(client, request, json_body_to_validate, response):
    """
    Test semantic validation API with valid and invalid JSON
    """
    json_body = request.getfixturevalue(json_body_to_validate)
    expected_response = request.getfixturevalue(response)
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


def test_semantic_validate_api_not_passing_required_keys(
    client, observing_command_input_missing_response, valid_semantic_validation_body
):
    """
    Test semantic validation API response with missing input observing_command_input key
    """
    json_body = valid_semantic_validation_body.copy()
    del json_body["observing_command_input"]
    expected_response = observing_command_input_missing_response
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


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
    request, client, json_body_to_validate, response, key_to_delete
):
    """
    Test semantic validation API response by not passing optional keys
    """
    json_body = request.getfixturevalue(json_body_to_validate).copy()
    del json_body[key_to_delete]
    expected_response = request.getfixturevalue(response)
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response
