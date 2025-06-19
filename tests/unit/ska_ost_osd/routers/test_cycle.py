from unittest import mock

import pytest
from fastapi import status

from tests.conftest import BASE_API_URL


class TestCycleAPI:
    """This class contains unit tests for the Cycle GET API, which is
    responsible for fetching Dictionary containing list of cycle numbers."""

    @mock.patch("ska_ost_osd.routers.osd_api.read_file")
    def test_cycle_endpoint(self, mock_read_file, client_get):
        """This function tests that a request to the GET /cycle endpoint.

        :returns: cycle list
        """

        mock_read_file.return_value = {
            "cycle_1": ["1.0.0", "1.0.1", "1.0.2"],
            "cycle_2": ["1.0.0", "1.0.1", "1.0.2"],
        }
        response = client_get(f"{BASE_API_URL}/cycle")

        expected_json = {
            "result_data": [{"cycles": [1, 2]}],
            "result_status": "success",
            "result_code": 200,
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_json

    @mock.patch("ska_ost_osd.routers.osd_api.read_file")
    def test_cycle_endpoint_file_not_found(self, mock_read_file, client_get):
        """Test that GET /cycle returns 500 or appropriate error when read_file
        returns invalid data structure."""

        mock_read_file.side_effect = Exception("file not found")

        response = client_get(f"{BASE_API_URL}/cycle")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["result_status"] == "failed"
        assert "file not found" in response.json()["result_data"]
