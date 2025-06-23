from unittest.mock import patch

import pytest

from ska_ost_osd.osd.routers.api import release_osd_data


@pytest.mark.skip
class TestResources:
    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    def test_release_osd_data_2(self, mock_push_to_gitlab, mock_manage_version_release):
        """Test release_osd_data with valid cycle_id and invalid
        release_type."""
        # Arrange
        cycle_id = 1
        release_type = "invalid_type"
        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")

        # Act
        # with pytest.raises(ValueError) as exc_info:
        result = release_osd_data(cycle_id=cycle_id, release_type=release_type)

        # Assert
        assert (
            result[0]["detail"]
            == "release_type must be either 'major' or 'minor' if provided"
        )
        mock_manage_version_release.assert_not_called()
        mock_push_to_gitlab.assert_not_called()

    def test_release_osd_data_empty_release_type(self):
        """Test release_osd_data with empty release_type."""
        result = release_osd_data(cycle_id=1, release_type="")
        assert result["status"] == "success"

    @pytest.mark.parametrize("cycle_id", [False, [], {}, set()])
    def test_release_osd_data_invalid_cycle_id_types(self, cycle_id):
        """Test release_osd_data with invalid cycle_id types."""
        result = release_osd_data(cycle_id=cycle_id)
        assert result[0]["title"] == "Value Error"

    def test_release_osd_data_missing_cycle_id(self):
        """Test release_osd_data with missing cycle_id."""
        # Act & Assert
        result = release_osd_data()
        assert result[0]["detail"] == "cycle_id is required"

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_success(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test successful release of OSD data with valid cycle_id and no
        release_type."""
        # Arrange
        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")
        mock_push_to_gitlab.return_value = None

        # Act
        result = release_osd_data(cycle_id=1)

        # Assert
        assert result == {
            "status": "success",
            "message": "Released new version 1.0.1",
            "version": "1.0.1",
            "cycle_id": "cycle_1",
        }
        mock_manage_version_release.assert_called_once_with("cycle_1", None)
        mock_push_to_gitlab.assert_called_once()

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_successful(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test successful release of OSD data with valid cycle_id and no
        release_type."""
        # Arrange
        mock_manage_version_release.return_value = ("1.0.1", "cycle_1")
        mock_push_to_gitlab.return_value = None

        # Act
        result = release_osd_data(cycle_id=1)

        # Assert
        assert result == {
            "status": "success",
            "message": "Released new version 1.0.1",
            "version": "1.0.1",
            "cycle_id": "cycle_1",
        }
        mock_manage_version_release.assert_called_once_with("cycle_1", None)
        mock_push_to_gitlab.assert_called_once()

    @pytest.mark.parametrize("release_type", [None, "major", "minor"])
    def test_release_osd_data_valid_release_types(self, release_type):
        """Test release_osd_data with valid release types."""
        result = release_osd_data(cycle_id=1, release_type=release_type)
        assert result["status"] == "success"

    @patch("ska_ost_osd.osd.routers.api.manage_version_release")
    @patch("ska_ost_osd.osd.routers.api.push_to_gitlab")
    @patch("ska_ost_osd.osd.routers.api.PUSH_TO_GITLAB", "1")
    def test_release_osd_data_with_release_type(
        self, mock_push_to_gitlab, mock_manage_version_release
    ):
        """Test release_osd_data with valid release_type."""
        # Arrange
        mock_manage_version_release.return_value = ("2.0.0", "cycle_2")
        mock_push_to_gitlab.return_value = None

        # Act
        result = release_osd_data(cycle_id=2, release_type="major")

        # Assert
        assert result == {
            "status": "success",
            "message": "Released new version 2.0.0",
            "version": "2.0.0",
            "cycle_id": "cycle_2",
        }
        mock_manage_version_release.assert_called_once_with("cycle_2", "major")
        mock_push_to_gitlab.assert_called_once()
