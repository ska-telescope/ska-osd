"""Test cases for template_mapping module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from ska_ost_osd.osd.template_mapping.template_mapping import (
    find_matching_templates,
    load_template_file,
    process_template_mappings,
)


class TestLoadTemplateFile:
    """Test cases for load_template_file function."""

    def test_load_template_file_success(self):
        """Test successful template file loading."""
        mock_data = {"template1": {"data": "value"}}
        mock_item = Mock()
        mock_item.get_dict.return_value = mock_data
        mock_tmdata = MagicMock()
        mock_tmdata.__getitem__.return_value = mock_item

        result = load_template_file("test_file.json", mock_tmdata)
        assert result == mock_data

    def test_load_template_file_not_found(self):
        """Test FileNotFoundError handling."""
        mock_tmdata = MagicMock()
        mock_tmdata.__getitem__.side_effect = KeyError("File not found")

        with pytest.raises(
            FileNotFoundError, match="Template file not found: test_file_not_found.json"
        ):
            load_template_file("test_file_not_found.json", mock_tmdata)

    def test_load_template_file_attribute_error(self):
        """Test AttributeError handling."""
        mock_item = Mock()
        mock_item.get_dict.side_effect = AttributeError("Invalid access")
        mock_tmdata = MagicMock()
        mock_tmdata.__getitem__.return_value = mock_item

        with pytest.raises(FileNotFoundError):
            load_template_file("test_file_invalid.json", mock_tmdata)


class TestFindMatchingTemplates:
    """Test cases for find_matching_templates function."""

    def test_find_matching_templates_mid_telescope(self):
        """Test template matching for mid telescope."""
        templates = {
            "mid_template1": {"data": "mid1"},
            "mid_template2": {"data": "mid2"},
            "low_template1": {"data": "low1"},
            "other_template": {"data": "other"},
        }
        patterns = ["mid_*", "other_*"]
        base_path = "tmdata/ska1_mid"

        result = find_matching_templates(templates, patterns, base_path)

        expected = {
            "mid_template1": {"data": "mid1"},
            "mid_template2": {"data": "mid2"},
            "other_template": {"data": "other"},
        }
        assert result == expected

    def test_find_matching_templates_low_telescope(self):
        """Test template matching for low telescope."""
        templates = {
            "mid_template1": {"data": "mid1"},
            "low_template1": {"data": "low1"},
            "low_template2": {"data": "low2"},
            "other_template": {"data": "other"},
        }
        patterns = ["low_*", "other_*"]
        base_path = "tmdata/ska1_low"

        result = find_matching_templates(templates, patterns, base_path)

        expected = {
            "low_template1": {"data": "low1"},
            "low_template2": {"data": "low2"},
            "other_template": {"data": "other"},
        }
        assert result == expected

    def test_find_matching_templates_no_matches(self):
        """Test when no templates match patterns."""
        templates = {"template1": {"data": "value"}}
        patterns = ["nonexistent_*"]

        result = find_matching_templates(templates, patterns)

        assert result == {}


class TestProcessTemplateMappings:
    """Test cases for process_template_mappings function."""

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.load_template_file")
    def test_process_template_mappings_success(self, mock_load_template):
        """Test successful template mapping processing."""
        mock_load_template.return_value = {
            "MID_Template1": {"config": "mid1"},
            "MID_Template2": {"config": "mid2"},
        }
        mock_tmdata = Mock()

        capabilities_data = {
            "array_assembly": {
                "subarray_templates": ["MID_*"],
                "existing_key": "existing_value",
            }
        }

        result = process_template_mappings(
            capabilities_data, "ska1_mid.json", mock_tmdata
        )

        expected = {
            "array_assembly": {
                "existing_key": "existing_value",
                "subarray_templates": {
                    "MID_Template1": {"config": "mid1"},
                    "MID_Template2": {"config": "mid2"},
                },
            }
        }
        assert result == expected

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.load_template_file")
    @patch("ska_ost_osd.osd.template_mapping.template_mapping.LOGGER")
    def test_process_template_mappings_file_not_found(self, mock_logger, mock_load_template):
        """Test handling of missing template file."""
        mock_load_template.side_effect = FileNotFoundError("File not found")
        mock_tmdata = Mock()

        capabilities_data = {"array_assembly": {"subarray_templates": ["*"]}}

        result = process_template_mappings(
            capabilities_data, "ska1_mid.json", mock_tmdata
        )

        assert "subarray_templates" not in result["array_assembly"]
        mock_logger.error.assert_called()

    def test_process_template_mappings_no_subarray_templates(self):
        """Test processing data without subarray_templates."""
        capabilities_data = {"array_assembly": {"existing_key": "existing_value"}}
        mock_tmdata = Mock()

        result = process_template_mappings(capabilities_data, tmdata=mock_tmdata)

        assert result == capabilities_data

    def test_process_template_mappings_empty_data(self):
        """Test processing empty data."""
        capabilities_data = {}
        mock_tmdata = Mock()

        result = process_template_mappings(capabilities_data, tmdata=mock_tmdata)

        assert result == capabilities_data

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.load_template_file")
    def test_process_template_mappings_no_matching_templates(self, mock_load_template):
        """Test when no templates match patterns."""
        mock_load_template.return_value = {"OTHER_Template": {"config": "other"}}
        mock_tmdata = Mock()

        capabilities_data = {
            "array_assembly": {
                "subarray_templates": ["MID_*"],
                "existing_key": "existing_value",
            }
        }

        result = process_template_mappings(
            capabilities_data, "ska1_mid.json", mock_tmdata
        )

        expected = {
            "array_assembly": {
                "existing_key": "existing_value",
            }
        }
        assert result == expected
        assert "subarray_templates" not in result["array_assembly"]
