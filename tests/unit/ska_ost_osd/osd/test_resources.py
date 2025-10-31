from unittest.mock import patch

import pytest

from ska_ost_osd.osd.models.models import OSDUpdateModel
from ska_ost_osd.osd.routers.api import update_osd_data


class TestResources:
    @pytest.fixture
    def mock_read_file(self):
        with patch("ska_ost_osd.osd.routers.api.read_json") as mock:
            mock.return_value = {
                "cycle_number": 0,
                "telescope_capabilities": {"Mid": "4"},
            }
            yield mock

    @pytest.fixture
    def mock_update_file_storage(self):
        with patch("ska_ost_osd.osd.routers.api.update_file_storage") as mock:
            mock.return_value = {"updated": "data"}
            yield mock

    @patch("ska_ost_osd.common.utils.read_json")
    @patch("ska_ost_osd.osd.routers.api.update_file_storage")
    def test_update_osd_data_2(self, mock_update_file_storage, mock_read_file):
        """Test update_osd_data when cycle_id and array_assembly are valid."""

        mock_read_file.return_value = {"existing": "data"}

        mock_update_file_storage.return_value = {"updated": "data"}

        body = {
            "capabilities": {"mid": {"new_capability": "value"}},
            "observatory_policy": {"new_policy": "value"},
        }
        kwargs = {"cycle_id": 2, "array_assembly": "AA4", "capabilities": "mid"}

        result = update_osd_data(body, OSDUpdateModel(**kwargs))

        assert result.result_data == {"updated": "data"}  # pylint: disable=E1101
