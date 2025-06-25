from unittest.mock import patch

import pytest
from fastapi import status

from ska_ost_osd.osd.routers.api import release_osd_data
from tests.conftest import BASE_API_URL


class TestResources:
    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    def test_release_osd_data_2(
        self, mock_push_to_gitlab, mock_manage_version_release, client_post
    ):
        """Test release_osd_data with valid cycle_id and invalid
        release_type."""

        data = {"cycle_id": 1, "release_type": "invalid_type"}
        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")

        result = client_post(f"{BASE_API_URL}/osd_release", params=data).json()

        assert (
            result["result_data"]
            == "query.release_type: Input should be 'minor' or 'major',"
            " invalid payload: invalid_type"
        )
        assert result["result_status"] == "failed"
        assert result["result_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_manage_version_release.assert_not_called()
        mock_push_to_gitlab.assert_not_called()

    @pytest.mark.parametrize("cycle_id", [False, {}, set()])
    def test_release_osd_data_invalid_cycle_id_types(self, cycle_id, client_post):
        """Test release_osd_data with invalid cycle_id types."""

        data = {"cycle_id": cycle_id, "release_type": "minor"}
        result = client_post(f"{BASE_API_URL}/osd_release", params=data).json()
        assert (
            "query.cycle_id: Input should be a valid integer" in result["result_data"]
        )
        assert result["result_status"] == "failed"
        assert result["result_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_release_osd_data_missing_cycle_id(self, client_post):
        """Test release_osd_data with missing cycle_id."""

        data = {}
        result = client_post(f"{BASE_API_URL}/osd_release", params=data).json()
        assert (
            result["result_data"]
            == "Missing field(s): query.cycle_id, query.release_type"
        )

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_success(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test successful release of OSD data with valid cycle_id and no
        release_type."""

        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")
        mock_push_to_gitlab.return_value = None

        result = release_osd_data(cycle_id=1, release_type="minor").model_dump(
            mode="json"
        )

        assert result == {
            "result_data": [
                {
                    "message": "Released new version 1.0.1",
                    "version": "1.0.1",
                    "cycle_id": "cycle_1",
                }
            ],
            "result_status": "success",
            "result_code": 200,
        }
        mock_manage_version_release.assert_called_once_with("cycle_1", "minor")
        mock_push_to_gitlab.assert_called_once()

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_successful(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test successful release of OSD data with valid cycle_id and no
        release_type."""

        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")
        mock_push_to_gitlab.return_value = None

        result = release_osd_data(cycle_id=1, release_type="minor").model_dump(
            mode="json"
        )

        assert result == {
            "result_data": [
                {
                    "message": "Released new version 1.0.1",
                    "version": "1.0.1",
                    "cycle_id": "cycle_1",
                }
            ],
            "result_status": "success",
            "result_code": 200,
        }
        mock_manage_version_release.assert_called_once_with("cycle_1", "minor")
        mock_push_to_gitlab.assert_called_once()

    @pytest.mark.parametrize("release_type", ["major", "minor"])
    def test_release_osd_data_valid_release_types(self, release_type):
        """Test release_osd_data with valid release types."""
        result = release_osd_data(cycle_id=1, release_type=release_type).model_dump(
            mode="json"
        )
        assert result["result_status"] == "success"

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_with_release_type(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test release_osd_data with valid release_type."""

        mock_manage_version_release.return_value = ("2.0.0", "cycle_2")
        mock_push_to_gitlab.return_value = None

        result = release_osd_data(cycle_id=2, release_type="major").model_dump(
            mode="json"
        )

        assert result == {
            "result_data": [
                {
                    "message": "Released new version 2.0.0",
                    "version": "2.0.0",
                    "cycle_id": "cycle_2",
                }
            ],
            "result_status": "success",
            "result_code": 200,
        }
        mock_manage_version_release.assert_called_once_with("cycle_2", "major")
        mock_push_to_gitlab.assert_called_once()
