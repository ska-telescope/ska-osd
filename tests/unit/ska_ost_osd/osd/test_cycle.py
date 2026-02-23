from unittest import mock

from fastapi import status

from tests.conftest import BASE_API_URL


class TestCycleAPI:
    """This class contains unit tests for the Cycle GET API, which is
    responsible for fetching Dictionary containing list of cycle numbers."""

    @mock.patch("ska_ost_osd.osd.osd.TMData")
    def test_cycle_endpoint(self, mock_tmdata, client_get):
        """Test that GET /cycle returns appropriate json response after
        fetching cycle data from TMData."""

        # Mock TMData instance and its methods
        mock_tmdata_instance = mock.MagicMock()
        mock_tmdata.return_value = mock_tmdata_instance
        mock_tmdata_instance.__getitem__.return_value.get_dict.return_value = {
            "cycle_1": ["1.0.0", "1.0.1", "1.0.2"],
            "cycle_2": ["1.0.0", "1.0.1", "1.0.2"],
        }

        response = client_get(f"{BASE_API_URL}/cycle")

        expected_json = {
            "result_data": {"cycles": [1, 2]},
            "result_status": "success",
            "result_code": 200,
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_json

    @mock.patch("ska_ost_osd.osd.osd.TMData")
    def test_cycle_endpoint_file_not_found(self, mock_tmdata, client_get):
        """Test that GET /cycle returns 500 or appropriate error when TMData
        raises an exception."""

        mock_tmdata.side_effect = FileNotFoundError("file not found")

        response = client_get(f"{BASE_API_URL}/cycle")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["result_status"] == "failed"
        assert "file not found" in response.json()["result_data"]
