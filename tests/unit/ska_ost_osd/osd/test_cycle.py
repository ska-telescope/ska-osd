from fastapi import status

from tests.conftest import BASE_API_URL


class TestCycleAPI:
    """This class contains unit tests for the Cycle GET API, which is
    responsible for fetching Dictionary containing list of cycle numbers."""

    def test_cycle_endpoint(self, test_client):
        """Test that GET /cycle returns appropriate json response after
        fetching cycle data from TMData."""

        response = test_client.get(f"{BASE_API_URL}/cycle")

        expected_json = {
            "result_data": {"cycles": [1, 10000]},
            "result_status": "success",
            "result_code": 200,
        }

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_json

    def test_cycle_endpoint_file_not_found(self, empty_client):
        """Test that GET /cycle returns 500 or appropriate error when TMData
        raises an exception."""

        response = empty_client.get(f"{BASE_API_URL}/cycle")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["result_status"] == "failed"
        assert "file not found" in response.json()["result_data"]
