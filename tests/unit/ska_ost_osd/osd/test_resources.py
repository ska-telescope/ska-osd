from unittest.mock import patch

import pytest

from ska_ost_osd.osd.models.models import OSDUpdateModel
from ska_ost_osd.osd.routers.api import update_osd_data
from tests.conftest import BASE_API_URL


class TestResources:
    @pytest.fixture
    def mock_read_file(self):
        with patch("ska_ost_osd.osd.routers.api.read_json") as mock:
            mock.return_value = {
                "cycle_number": 1,
                "telescope_capabilities": {"Mid": "4"},
            }
            yield mock

    @pytest.fixture
    def mock_update_file_storage(self):
        with patch("ska_ost_osd.osd.routers.api.update_file_storage") as mock:
            mock.return_value = {"updated": "data"}
            yield mock

    @patch("ska_ost_osd.osd.routers.api.read_json")
    @patch("ska_ost_osd.osd.routers.api.update_file_storage")
    def test_update_osd_data_2(self, mock_update_file_storage, mock_read_file):
        """Test update_osd_data when cycle_id and array_assembly are valid."""
        # Mock the read_json function
        mock_read_file.side_effect = [
            {
                "cycle_number": 1,
                "telescope_capabilities": {"Mid": "4"},
            },  # OBSERVATORY_POLICIES_JSON_PATH
            {"existing": "data"},  # MID_CAPABILITIES_JSON_PATH
        ]

        # Mock the update_file_storage function
        mock_update_file_storage.return_value = {"updated": "data"}

        # Prepare test data
        body = {
            "capabilities": {"Mid": {"new_capability": "value"}},
            "observatory_policy": {"new_policy": "value"},
        }
        kwargs = {"cycle_id": 2, "array_assembly": "AA4", "capabilities": "mid"}

        # Call the function
        result = update_osd_data(  # pylint: disable=E1101
            body, OSDUpdateModel(**kwargs)
        ).model_dump(mode="json", exclude_none=True)

        # Assert the result
        assert result["result_data"] == {"updated": "data"}

    @patch("ska_ost_osd.osd.routers.api.read_json")
    def test_update_osd_data_invalid_array_assembly(self, mock_read_file, client_put):
        """Test update_osd_data when array_assembly is invalid for the current
        cycle."""
        mock_read_file.return_value = {
            "cycle_number": 1,
            "telescope_capabilities": {"Mid": "AA5"},
        }
        body = {"capabilities": {"telescope": {"mid": "test"}}}
        params = {"cycle_id": 1, "array_assembly": "AA0", "capabilities": "mid"}

        response = client_put(
            f"{BASE_API_URL}/osd_put_data",
            params=params,
            json=body,
        ).json()

        assert (
            "Array Assembly AA0 does not belongs to cycle 1" == response["result_data"]
        )
