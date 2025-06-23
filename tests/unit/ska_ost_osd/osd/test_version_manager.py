import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from ska_ost_osd.osd.version_mapping.version_manager import (
    increment_version,
    manage_version_release,
)


class TestVersionManager:
    @pytest.fixture
    def mock_latest_release(self, tmp_path):
        file_path = tmp_path / "latest_release.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('"1.0.1"')
        return file_path

    @pytest.fixture
    def mock_version_mapping(self, tmp_path):
        mapping = {"cycle1": ["1.0.0", "1.0.1"], "cycle2": ["2.0.0"]}
        file_path = tmp_path / "cycle_gitlab_release_version_mapping.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f)
        return file_path

    def test_increment_major_version(self):
        """Test increment_version function for major release type."""
        current_version = "1.2.3"
        release_type = "major"
        expected_version = "2.0.0"

        result = increment_version(current_version, release_type)

        assert (
            result == expected_version
        ), f"Expected {expected_version}, but got {result}"

    def test_increment_minor_version(self):
        """Test incrementing the minor version number."""
        current_version = "1.2.3"
        release_type = "minor"
        expected_version = "1.3.0"

        result = increment_version(current_version, release_type)

        assert (
            result == expected_version
        ), f"Expected {expected_version}, but got {result}"

    def test_increment_patch_version(self):
        """Test incrementing patch version when release_type is None and patch
        is less than 9."""
        current_version = "1.2.3"
        result = increment_version(current_version)
        assert result == "1.2.4"

    def test_increment_version_2(self):
        """Test incrementing the minor version number when the current version
        has a non-zero patch."""
        current_version = "2.4.5"
        release_type = "minor"
        expected_version = "2.5.0"

        result = increment_version(current_version, release_type)

        assert (
            result == expected_version
        ), f"Expected {expected_version}, but got {result}"

    def test_increment_version_3(self):
        """Test increment_version when patch and minor exceed 9, resulting in a
        major version increment."""
        current_version = "1.9.9"
        result = increment_version(current_version)
        assert result == "2.0.0"

    def test_increment_version_4(self):
        """Test increment_version when patch > 9 and minor <= 9."""
        current_version = "1.2.9"
        expected_version = "1.3.0"
        result = increment_version(current_version)
        assert (
            result == expected_version
        ), f"Expected {expected_version}, but got {result}"

    def test_increment_version_5(self):
        """Test incrementing patch version when release_type is None and patch
        is less than 9."""
        current_version = "2.5.8"
        result = increment_version(current_version)
        assert result == "2.5.9"

    def test_increment_version_empty_input(self):
        """Test increment_version with empty input."""
        with pytest.raises(ValueError):
            increment_version("")

    def test_increment_version_extra_whitespace(self):
        """Test increment_version with extra whitespace."""
        result = increment_version("  1.2.3  ")
        assert result == "1.2.4"

    def test_increment_version_incorrect_type(self):
        """Test increment_version with incorrect input type."""
        with pytest.raises(AttributeError):
            increment_version(123)

    def test_increment_version_invalid_format(self):
        """Test increment_version with invalid version format."""
        with pytest.raises(ValueError):
            increment_version("1.2")

    def test_increment_version_major(self):
        assert increment_version("1.2.3", "major") == "2.0.0"

    def test_increment_version_minor(self):
        assert increment_version("1.2.3", "minor") == "1.3.0"

    def test_increment_version_non_numeric(self):
        """Test increment_version with non-numeric version components."""
        with pytest.raises(ValueError):
            increment_version("1.a.3")

    def test_increment_version_overflow(self):
        """Test increment_version with version number overflow."""
        result = increment_version("9.9.9")
        assert result == "10.0.0"

    def test_increment_version_patch(self):
        assert increment_version("1.2.3") == "1.2.4"

    def test_increment_version_patch_rollover(self):
        assert increment_version("1.9.9") == "2.0.0"

    def test_increment_version_patch_rollover_2(self):
        assert increment_version("1.2.9") == "1.3.0"

    def test_increment_version_quoted_input(self):
        """Test increment_version with quoted input."""
        result = increment_version('"1.2.3"')
        assert result == "1.2.4"

    @pytest.mark.parametrize(
        "version,expected",
        [
            ("0.0.0", "0.0.1"),
            ("1.2.3", "1.2.4"),
            ("9.9.9", "10.0.0"),
        ],
    )
    def test_increment_version_various(self, version, expected):
        assert increment_version(version) == expected

    def test_manage_version_release_corrupted_json(
        self, monkeypatch, mock_version_mapping, mock_latest_release
    ):
        """Test manage_version_release with corrupted JSON in version mapping
        file."""
        monkeypatch.setattr(Path, "resolve", lambda self: mock_version_mapping.parent)
        monkeypatch.setattr(
            Path,
            "__truediv__",
            lambda self, other: (
                mock_version_mapping if "mapping" in str(other) else mock_latest_release
            ),
        )

        with open(mock_version_mapping, "w", encoding="utf-8") as f:
            f.write("This is not valid JSON")

        with pytest.raises(json.JSONDecodeError):
            manage_version_release("cycle1")

    def test_manage_version_release_duplicate_version(self):
        """Test manage_version_release when the new version already exists in
        another cycle."""
        mock_version_mapping = {"test_cycle1": ["1.0.0"], "test_cycle2": ["1.1.0"]}
        mock_file_content = json.dumps(mock_version_mapping)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("json.load", return_value=mock_version_mapping):
                with patch("json.dump") as mock_json_dump:
                    with patch("pathlib.Path.resolve", return_value=Path("/fake/path")):
                        new_version, cycle_id = manage_version_release(
                            "test_cycle1", "minor"
                        )

        assert new_version == "1.2.0"
        assert cycle_id == "test_cycle1"
        mock_json_dump.assert_called_once()

    def test_manage_version_release_empty_versions_2(
        self, monkeypatch, mock_version_mapping, mock_latest_release
    ):
        """Test manage_version_release with a cycle_id that has no versions."""
        monkeypatch.setattr(Path, "resolve", lambda self: mock_version_mapping.parent)
        monkeypatch.setattr(
            Path,
            "__truediv__",
            lambda self, other: (
                mock_version_mapping if "mapping" in str(other) else mock_latest_release
            ),
        )

        with open(mock_version_mapping, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["empty_cycle"] = []
        with open(mock_version_mapping, "w", encoding="utf-8") as f:
            json.dump(data, f)

        with pytest.raises(ValueError, match="No versions found for cycle empty_cycle"):
            manage_version_release("empty_cycle")

    def test_manage_version_release_file_not_found(self, monkeypatch):
        """Test manage_version_release when version mapping file is not
        found."""

        def mock_open(*args, **kwargs):  # pylint: disable=W0621
            raise FileNotFoundError("File not found")

        monkeypatch.setattr("builtins.open", mock_open)

        with pytest.raises(FileNotFoundError):
            manage_version_release("cycle1")

    def test_manage_version_release_invalid_cycle_id_2(self):
        """Test manage_version_release with an invalid cycle_id."""
        mock_version_mapping = {"valid_cycle": ["1.0.0"]}
        mock_file_content = json.dumps(mock_version_mapping)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("json.load", return_value=mock_version_mapping):
                with pytest.raises(ValueError, match="Invalid cycle_id: invalid_cycle"):
                    manage_version_release("invalid_cycle")

    def test_manage_version_release_invalid_cycle_id_5(
        self, monkeypatch, mock_version_mapping, mock_latest_release
    ):
        """Test manage_version_release with an invalid cycle_id."""
        monkeypatch.setattr(Path, "resolve", lambda self: mock_version_mapping.parent)
        monkeypatch.setattr(
            Path,
            "__truediv__",
            lambda self, other: (
                mock_version_mapping if "mapping" in str(other) else mock_latest_release
            ),
        )

        with pytest.raises(ValueError, match="Invalid cycle_id: invalid_cycle"):
            manage_version_release("invalid_cycle")

    def test_manage_version_release_invalid_release_type(
        self, monkeypatch, mock_version_mapping, mock_latest_release
    ):
        """Test manage_version_release with an invalid release_type."""
        monkeypatch.setattr(Path, "resolve", lambda self: mock_version_mapping.parent)
        monkeypatch.setattr(
            Path,
            "__truediv__",
            lambda self, other: (
                mock_version_mapping if "mapping" in str(other) else mock_latest_release
            ),
        )

        new_version, cycle_id = manage_version_release("cycle1", release_type="invalid")
        assert new_version == "1.0.2"  # Should default to patch release
        assert cycle_id == "cycle1"

    def test_manage_version_release_new_version(self):
        """Test manage_version_release with a valid cycle_id and
        release_type."""
        mock_version_mapping = {"test_cycle": ["1.0.0"]}
        mock_file_content = json.dumps(mock_version_mapping)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch("json.load", return_value=mock_version_mapping):
                with patch("json.dump") as mock_json_dump:
                    with patch("pathlib.Path.resolve", return_value=Path("/fake/path")):
                        new_version, cycle_id = manage_version_release(
                            "test_cycle", "minor"
                        )

        assert new_version == "1.1.0"
        assert cycle_id == "test_cycle"
        mock_json_dump.assert_called_once()
