
import os
from unittest.mock import patch, MagicMock
import pytest

from ska_oso_osd.rest import get_openapi_spec, init_app



def test_get_open_api_spec(open_api_spec):
    assert get_openapi_spec() == open_api_spec



def test_init_app(open_api_spec):
    with patch('ska_oso_osd.rest.get_openapi_spec', return_value=open_api_spec):
        app = init_app()

        assert  app.url_map._rules_by_endpoint['/ska-oso-osd/api/v1.ska_oso_osd_rest_api_resources_get_osd']



def test_get_openapi_spec(open_api_spec):
    # Patch 'prance.ResolvingParser' to return a mock spec
    with patch('ska_oso_osd.rest.prance.ResolvingParser', autospec=True) as mock_parser:
        instance = mock_parser.return_value
        instance.specification = open_api_spec

        spec = get_openapi_spec()

        assert spec == open_api_spec, "The specification should match the mock specification"
        mock_parser.assert_called_once_with('/home/manish/skao/ska-oso-osd/src/ska_oso_osd/rest/./openapi/osd-openapi-v1.yaml', lazy=True,
                                            strict=True), "ResolvingParser should be called with expected arguments"


def test_init_app(client, open_api_spec):
    with patch('ska_oso_osd.rest.get_openapi_spec', return_value=open_api_spec), \
        patch('ska_oso_osd.rest.App') as mock_connexion_app:
        mock_connexion_instance = mock_connexion_app.return_value
        mock_flask_app = mock_connexion_instance.app
        mock_flask_app.test_client = MagicMock(return_value=client)

        app = init_app(open_api_spec=open_api_spec)

        # Verify that the Connexion app is initialized with the correct parameters
        mock_connexion_app.assert_called_once_with('ska_oso_osd.rest', specification_dir='openapi/')

        # Verify that the API is added with the correct spec and base path
        mock_connexion_instance.add_api.assert_called_once()
        call_args = mock_connexion_instance.add_api.call_args
        assert call_args[0][0] == open_api_spec
        assert call_args[1]['base_path'].startswith('/')



def test_osd_endpoint_for(client,mid_osd_data):

    response = client.get('/ska-oso-osd/api/v1/osd', query_string={
        'cycle_id': 1,
        #'osd_version': 'v1',
        'source': 'file',
        'capabilities': 'mid',
        'array_assembly': 'AA0.5'
    })


    assert response.status_code == 200
    assert response.json == mid_osd_data


# In similar fashion Create the above using parameterise and test scenarios
#
#
# @pytest.mark.parametrize(
#     "cycle_id, osd_version, source, gitlab_branch, capabilities, array_assembly, expected",
#     [
#         (None, None, None, None, None, None, DEFAULT_OSD_RESPONSE_WITH_NO_PARAMETER),
#         (
#             1,
#             "v1",
#             "file",
#             None,
#             "mid",
#             "AA0.5",
#             OSD_RESPONSE_WITH_ONLY_CYCLE_ID_PARAMETER
#         ),
#         (
#             None,
#             "v1",
#             "file",
#             None,
#             "mid",
#             "AA0.5",
#             OSD_RESPONSE_WITH_ONLY_OSD_VERSION_PARAMETER
#         ),
# )
