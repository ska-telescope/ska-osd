import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ska_ost_osd.osd.common.gitlab_helper import (
    check_file_modified,
    get_project_root,
    push_to_gitlab,
    setup_gitlab_access,
)


class TestGitlabHelper:
    @pytest.fixture
    def mock_check_file_modified(self):
        with patch("ska_ost_osd.osd.common.gitlab_helper.check_file_modified") as mock:
            yield mock

    @pytest.fixture
    def mock_git_backend(self):
        with patch("ska_ost_osd.osd.common.gitlab_helper.GitBackend") as mock:
            yield mock

    def test_check_file_modified_empty_file(self, tmp_path):
        """Test check_file_modified function with an empty file.

        Expected to return False.
        """
        empty_file = tmp_path / "empty_file.txt"
        empty_file.touch()
        assert not check_file_modified(empty_file)

    def test_check_file_modified_empty_file_2(self, tmp_path):
        """Test check_file_modified with an empty file."""
        empty_file = tmp_path / "empty_file.txt"
        empty_file.touch()
        assert not check_file_modified(empty_file)

    def test_check_file_modified_existing_empty_file(self, tmp_path):
        """Test check_file_modified with an existing empty file."""
        # Create a temporary empty file
        file_path = tmp_path / "empty_file.txt"
        file_path.touch()

        # Check if the file is considered modified
        result = check_file_modified(file_path)

        # Assert that the file is not considered modified (size == 0)
        assert result is False

    def test_check_file_modified_existing_file_with_content(self, tmp_path):
        """Test check_file_modified with an existing file that has content."""
        # Create a temporary file with some content
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("Some content")

        # Check if the file is considered modified
        result = check_file_modified(file_path)

        # Assert that the file is considered modified (size > 0)
        assert result is True

    def test_check_file_modified_invalid_type(self):
        """Test check_file_modified with an invalid input type."""
        invalid_input = "not_a_path_object"
        with pytest.raises(AttributeError):
            check_file_modified(invalid_input)

    def test_check_file_modified_non_empty_file(self, tmp_path):
        """Test check_file_modified function with a non-empty file.

        Expected to return True.
        """
        non_empty_file = tmp_path / "non_empty_file.txt"
        non_empty_file.write_text("Some content")
        assert check_file_modified(non_empty_file)

    def test_check_file_modified_non_existent_file(self):
        """Test check_file_modified function with a non-existent file.

        Expected to return False.
        """
        non_existent_file = Path("/path/to/non_existent_file.txt")
        assert not check_file_modified(non_existent_file)

    def test_check_file_modified_nonexistent_file(self):
        """Test check_file_modified with a nonexistent file path."""
        non_existent_path = Path("/path/to/nonexistent/file.txt")
        assert not check_file_modified(non_existent_path)

    def test_get_project_root_correct_structure(self):
        """Test that get_project_root returns a path with the expected
        structure."""
        result = get_project_root()
        assert result.name == "ska-ost-osd"
        assert (
            result / "src" / "ska_ost_osd" / "osd" / "common" / "gitlab_helper.py"
        ).exists()

    @patch("ska_ost_osd.osd.common.gitlab_helper.Path")
    def test_get_project_root_file_not_found(self, mock_path):
        """Test get_project_root when __file__ is not found or accessible."""
        mock_path.side_effect = FileNotFoundError("File not found")
        with pytest.raises(FileNotFoundError):
            get_project_root()

    @patch("ska_ost_osd.osd.common.gitlab_helper.Path")
    def test_get_project_root_os_error(self, mock_path):
        """Test get_project_root when there's a general OS error."""
        mock_path.return_value.resolve.side_effect = OSError("OS error")
        with pytest.raises(OSError):
            get_project_root()

    @patch("ska_ost_osd.osd.common.gitlab_helper.Path")
    def test_get_project_root_permission_error(self, mock_path):
        """Test get_project_root when there's a permission error accessing the
        directory."""
        mock_path.return_value.resolve.side_effect = PermissionError(
            "Permission denied"
        )
        with pytest.raises(PermissionError):
            get_project_root()

    def test_get_project_root_returns_existing_directory(self):
        """Test that get_project_root returns an existing directory."""
        result = get_project_root()
        assert result.exists()
        assert result.is_dir()

    def test_get_project_root_returns_path(self):
        """Test that get_project_root returns a Path object."""
        result = get_project_root()
        assert isinstance(result, Path)

    @patch("ska_ost_osd.osd.common.gitlab_helper.setup_gitlab_access")
    def test_push_to_gitlab_git_backend_exception(
        self,
        mock_setup,  # pylint: disable=W0613
        mock_git_backend,
        mock_check_file_modified,
    ):
        """Test push_to_gitlab when GitBackend raises an exception."""
        mock_check_file_modified.return_value = True
        mock_git_backend.return_value.add_data.side_effect = Exception("Git error")

        with pytest.raises(Exception, match="Git error"):
            with patch("pathlib.Path.unlink"):
                push_to_gitlab([(Path("/valid/path"), "target/path")], "Test commit")

    @patch("ska_ost_osd.osd.common.gitlab_helper.setup_gitlab_access")
    @patch("ska_ost_osd.osd.common.gitlab_helper.GitBackend")
    @patch("ska_ost_osd.osd.common.gitlab_helper.check_file_modified")
    def test_push_to_gitlab_no_modified_files(
        self,
        mock_check_file_modified,
        mock_git_backend,
        mock_setup,  # pylint: disable=W0613
    ):
        """Test push_to_gitlab when no files are modified."""

        with patch("pathlib.Path.unlink"):
            # Setup
            mock_check_file_modified.return_value = False
            mock_git_backend_instance = MagicMock()
            mock_git_backend.return_value = mock_git_backend_instance

            # Test data
            files_to_add = [
                (Path("/path/to/file1.txt"), "target/file1.txt"),
                (Path("/path/to/file2.txt"), "target/file2.txt"),
            ]
            commit_msg = "Test commit"

            # Execute
            push_to_gitlab(files_to_add, commit_msg)

            # Assert
            mock_check_file_modified.assert_called()
            mock_git_backend.assert_called_once_with(
                repo="ska-telescope/ost/ska-ost-osd"
            )
            mock_git_backend_instance.add_data.assert_not_called()
            mock_git_backend_instance.commit.assert_not_called()
            mock_git_backend_instance.commit_transaction.assert_not_called()

    @patch("ska_ost_osd.osd.common.gitlab_helper.setup_gitlab_access")
    def test_push_to_gitlab_with_modified_files(
        self, mock_gitlab
    ):  # pylint: disable=W0613
        """Test push_to_gitlab when there are modified files to push."""
        # Mock the GitBackend class
        with patch(
            "ska_ost_osd.osd.common.gitlab_helper.GitBackend"
        ) as mock_git_backend:
            # Create a mock instance of GitBackend
            mock_git_repo = MagicMock()
            mock_git_backend.return_value = mock_git_repo

            # Mock check_file_modified to always return True
            with patch(
                "ska_ost_osd.osd.common.gitlab_helper.check_file_modified",
                return_value=True,
            ):
                with patch("pathlib.Path.unlink"):
                    # Prepare test data
                    files_to_add = [
                        (Path("/path/to/file1.txt"), "target/file1.txt"),
                        (Path("/path/to/file2.txt"), "target/file2.txt"),
                    ]
                    commit_msg = "Test commit"

                    # Call the function
                    push_to_gitlab(files_to_add, commit_msg)

                    # Assert that the correct methods were called on the mock
                    mock_git_repo.add_data.assert_called()
                    assert mock_git_repo.add_data.call_count == 2
                    mock_git_repo.commit.assert_called_once_with(commit_msg)
                    mock_git_repo.commit_transaction.assert_called_once()

    def test_setup_gitlab_access_1(self):
        """Test the setup_gitlab_access function to ensure it creates the .ssh
        directory, adds the GitLab host key, and sets up the SSH key file
        correctly."""

        with (
            patch(
                "ska_ost_osd.osd.common.gitlab_helper.Path.home",
                return_value=Path("/mock/home"),
            ),
            patch("ska_ost_osd.osd.common.gitlab_helper.subprocess.run") as mock_run,
            patch(
                "ska_ost_osd.osd.common.gitlab_helper.os.getenv",
                return_value="mock_ssh_key",
            ),
            patch("pathlib.Path.chmod") as mock_chmod,
            patch("pathlib.Path.open", mock_open()) as mock_file,
        ):
            setup_gitlab_access()

            # Assert ssh-keyscan execution
            mock_run.assert_called_once_with(
                ["ssh-keyscan", "gitlab.com"],
                stdout=mock_file.return_value,
                stderr=subprocess.PIPE,
                check=True,
            )

            # Assert file permissions
            mock_chmod.assert_any_call(0o600)

            # Assert SSH key file creation and permissions
            mock_file.return_value.write.assert_called_once_with("mock_ssh_key")
            mock_chmod.assert_any_call(0o600)
