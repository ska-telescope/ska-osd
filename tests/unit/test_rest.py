from unittest.mock import MagicMock, patch

from ska_ost_osd.rest import get_openapi_spec, init_app
from ska_ost_osd.rest.api.resources import validation_response


def test_init_app(open_api_spec):
    with patch("ska_ost_osd.rest.get_openapi_spec", return_value=open_api_spec):
        app = init_app()

        assert app.url_map._rules_by_endpoint[  # pylint: disable=W0212
            "/ska-oso-osd/api/v1.ska_ost_osd_rest_api_resources_get_osd"
        ]


def test_get_openapi_spec(open_api_spec):
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


def test_osd_endpoint_for(client, mid_osd_data):
    response = client.get(
        "/ska-oso-osd/api/v1/osd",
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
    error_msgs = client.get(
        "/ska-oso-osd/api/v1/osd",
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
    error_msgs = client.get(
        "/ska-oso-osd/api/v1/osd",
        query_string={
            "cycle_id": 1,
            "osd_version": "1.1.0",
            "source": "file",
            "capabilities": "midd",
            "array_assembly": "AA3",
        },
    )

    print(error_msgs.json["detail"])
    expected_error_msg = "'midd' is not one of ['mid', 'low']"
    assert error_msgs.json["detail"].startswith(expected_error_msg)


def test_invalid_osd_source(client):
    osd_source_link = client.get(
        "/ska-oso-osd/api/v1/osd", query_string={"cycle_id": 1, "source": "car"}
    )
    print(osd_source_link.json)
    assert osd_source_link == osd_source_link


def test_invalid_get_osd_data_capability(client):
    error_msgs = client.get(
        "/ska-oso-osd/api/v1/osd",
        query_string={"capabilities": "mid", "array_assembly": "AA3"},
    )

    assert (
        error_msgs.json
        == "Array Assembly AA3 doesn't exists. Available are AA0.5, AA1, AA2"
    )


def test_response_body():
    error_msg = "Validation failed"
    response = validation_response(error_msg)

    expected = {"Error": error_msg}
    assert response[0] == expected
