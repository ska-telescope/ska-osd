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
            "/ska-ost-osd/osd/api/v1.ska_ost_osd_rest_api_resources_get_osd"
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

    with patch("ska_ost_osd.rest.get_openapi_spec", return_value=open_api_spec), patch(
        "ska_ost_osd.rest.App"
    ) as mock_connexion_app:
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
            3,
            "1..1.0",
            "file",
            "mid",
            "AAA3",
            {
                "detail": (
                    "osd_version 1..1.0 is not valid, array_assembly AAA3 is not valid,"
                    " Cycle id 3 is not valid,Available IDs are 1,2"
                ),
                "title": "Bad Request",
            },
        ),
        (
            None,
            None,
            None,
            "mid",
            "AA3",
            {
                "detail": (
                    "Array Assembly AA3 doesn't exists. Available are AA0.5, AA1, AA2"
                ),
                "title": "Bad Request",
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
):
    """This test case checks the functionality of OSD API
        It will validate all params and retunr expected output.

    :param cycle_id,: 1, 2
    :param osd_version,: 1.0.0
    :param source,: File, Car and Gitlab
    :param capabilities: Mid or Low
    :param array_assembly: Array Assembly AA0.5, AA1
    :param expected: output of OSD API
    :param client: Flask test client

    :returns: assert equals values
    """

    response = client.get(
        "/ska-ost-osd/osd/api/v1/osd",
        query_string={
            "cycle_id": cycle_id,
            "osd_version": osd_version,
            "source": source,
            "capabilities": capabilities,
            "array_assembly": array_assembly,
        },
    )
    assert response.json == expected


def test_osd_endpoint(client, mid_osd_data):
    """This function tests that a request to the OSD endpoint for a
        specific OSD returns expected data for that OSD.

    :param client (FlaskClient): The Flask test client.
    :param mid_osd_data (dict): The expected data for the OSD.

    :raises AssertionError: If the response does not contain the expected
         OSD data or returns an error status code.
    """

    response = client.get(
        "/ska-ost-osd/osd/api/v1/osd",
        query_string={
            "cycle_id": 1,
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )

    assert response.status_code == 200
    assert response.json == mid_osd_data


def test_invalid_osd_tmdata_source_capabilities(client):
    """This function tests that a request with an invalid capability
       returns the expected error response.

    :param client (FlaskClient): The Flask test client.

    :raises AssertionError: If the response does not contain the
       expected error message.
    """

    error_msgs = client.get(  # pylint: disable=W0621
        "/ska-ost-osd/osd/api/v1/osd",
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


def test_response_body(client):
    """This function tests that the response from the REST API contains
       the expected body contents when retrieving OSD metadata.

    :raises AssertionError: If the response body is invalid.
    """

    response = client.get(
        "/ska-ost-osd/osd/api/v1/osd",
        query_string={
            "cycle_id": 3,
            "source": "file",
            "capabilities": "mid",
            "array_assembly": "AA0.5",
        },
    )

    error_msg = response.json
    expected_response = validation_response(error_msg)

    assert expected_response[0] == {"Error": error_msg}


def test_osd_source(client):
    """This function tests that a request with an OSD source as car .

    :param client (FlaskClient): The Flask test client.
    """

    response = client.get(
        "/ska-ost-osd/osd/api/v1/osd", query_string={"cycle_id": 1, "source": "car"}
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
        "/ska-ost-osd/osd/api/v1/osd", query_string={"cycle_id": 1, "source": "gitlab"}
    )

    error_msg = [{"Error": "404: 404 Commit Not Found"}, 422]

    response.json == error_msg  # pylint: disable=W0104
