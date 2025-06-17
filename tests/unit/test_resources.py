from unittest.mock import patch

import pytest

from ska_ost_osd.routers.osd_api import update_osd_data


class TestResources:
    @pytest.fixture
    def mock_read_file(self):
        with patch("ska_ost_osd.routers.osd_api.read_file") as mock:
            mock.return_value = {
                "cycle_number": 1,
                "telescope_capabilities": {"Mid": "4"},
            }
            yield mock

    @pytest.fixture
    def mock_update_file_storage(self):
        with patch("ska_ost_osd.routers.osd_api.update_file_storage") as mock:
            mock.return_value = {"updated": "data"}
            yield mock

    @patch("ska_ost_osd.routers.osd_api.read_file")
    @patch("ska_ost_osd.routers.osd_api.update_file_storage")
    def test_update_osd_data_2(self, mock_update_file_storage, mock_read_file):
        """Test update_osd_data when cycle_id and array_assembly are valid."""
        # Mock the read_file function
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
        result = update_osd_data(body, **kwargs)
        # Assert the result
        assert result == {"updated": "data"}

    @patch("ska_ost_osd.routers.osd_api.read_file")
    def test_update_osd_data_invalid_array_assembly(self, mock_read_file):
        """Test update_osd_data when array_assembly is invalid for the current
        cycle."""
        mock_read_file.return_value = {
            "cycle_number": 1,
            "telescope_capabilities": {"Mid": "AA5"},
        }

        body = {"capabilities": {"telescope": {"mid": "test"}}}
        kwargs = {"cycle_id": 1, "array_assembly": "AA0", "capabilities": "mid"}
        result = update_osd_data(body, **kwargs)
        assert "Array Assembly AA0 does not belongs to cycle 1" == result[0]["detail"]
