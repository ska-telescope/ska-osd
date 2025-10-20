"""Test cases for template_mapping module."""

import json
from unittest.mock import patch

import pytest

from ska_ost_osd.osd.template_mapping.template_mapping import (
    apply_template_mappings_to_osd_data,
    find_matching_templates,
    load_template_file,
    process_template_mappings,
)


class TestLoadTemplateFile:
    """Test cases for load_template_file function."""

    def setUp(self):
        """Clear cache before each test."""
        load_template_file.cache_clear()

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.read_json")
    def test_load_template_file_success(self, mock_read_json):
        """Test successful template file loading."""
        load_template_file.cache_clear()
        mock_data = {"template1": {"data": "value"}}
        mock_read_json.return_value = mock_data

        result = load_template_file("test_file.json")

        assert result == mock_data
        mock_read_json.assert_called_once_with("test_file.json")

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.read_json")
    def test_load_template_file_not_found(self, mock_read_json):
        """Test FileNotFoundError handling."""
        load_template_file.cache_clear()
        mock_read_json.side_effect = FileNotFoundError("File not found")

        with pytest.raises(
            FileNotFoundError, match="Template file not found: test_file_not_found.json"
        ):
            load_template_file("test_file_not_found.json")

    @patch("ska_ost_osd.osd.template_mapping.template_mapping.read_json")
    def test_load_template_file_invalid_json(self, mock_read_json):
        """Test JSON decode error handling."""
        load_template_file.cache_clear()
        mock_read_json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

        with pytest.raises(json.JSONDecodeError):
            load_template_file("test_file_invalid.json")


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

        capabilities_data = {
            "array_assembly": {
                "subarray_templates": ["MID_*"],
                "existing_key": "existing_value",
            }
        }

        result = process_template_mappings(capabilities_data, "tmdata/ska1_mid")

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
    def test_process_template_mappings_file_not_found(self, mock_load_template):
        """Test handling of missing template file."""
        mock_load_template.side_effect = FileNotFoundError("File not found")

        capabilities_data = {"array_assembly": {"subarray_templates": ["*"]}}

        with patch("builtins.print") as mock_print:
            result = process_template_mappings(capabilities_data)

            assert "subarray_templates" not in result["array_assembly"]
            mock_print.assert_called_once()

    def test_process_template_mappings_no_subarray_templates(self):
        """Test processing data without subarray_templates."""
        capabilities_data = {"array_assembly": {"existing_key": "existing_value"}}

        result = process_template_mappings(capabilities_data)

        assert result == capabilities_data


class TestApplyTemplateMappingsToOsdData:
    """Test cases for apply_template_mappings_to_osd_data function."""

    @patch(
        "ska_ost_osd.osd.template_mapping.template_mapping.process_template_mappings"
    )
    def test_apply_template_mappings_success(self, mock_process):
        """Test successful OSD data processing."""
        mock_process.return_value = {"processed": "data"}

        osd_data = {
            "capabilities": {
                "MID": {"subarray_templates": ["*"]},
                "LOW": {"subarray_templates": ["*"]},
            }
        }

        result = apply_template_mappings_to_osd_data(osd_data)

        expected = {
            "capabilities": {"MID": {"processed": "data"}, "LOW": {"processed": "data"}}
        }
        assert result == expected
        assert mock_process.call_count == 2

    def test_apply_template_mappings_no_capabilities(self):
        """Test OSD data without capabilities section."""
        osd_data = {"other_data": "value"}

        result = apply_template_mappings_to_osd_data(osd_data)

        assert result == osd_data

    def test_apply_template_mappings_empty_capabilities(self):
        """Test OSD data with empty capabilities."""
        osd_data = {"capabilities": {}}

        result = apply_template_mappings_to_osd_data(osd_data)

        assert result == osd_data
