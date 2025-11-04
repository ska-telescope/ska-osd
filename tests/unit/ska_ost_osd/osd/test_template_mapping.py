"""Unit tests for template mapping functionality."""

from unittest.mock import patch

from ska_ost_osd.osd.template_mapping.template_mapping import (
    find_matching_templates,
    process_template_mappings,
)


class TestFindMatchingTemplates:
    """Test cases for find_matching_templates function."""

    def test_find_matching_templates_mid(self):
        """Test finding templates for mid telescope."""
        templates = {
            "mid_template_1": {"data": "mid1"},
            "mid_template_2": {"data": "mid2"},
            "low_template_1": {"data": "low1"},
            "other_template": {"data": "other"},
        }
        patterns = ["mid_*", "other_*"]
        base_path = "tmdata/ska1_mid"

        result = find_matching_templates(templates, patterns, base_path)

        assert "mid_template_1" in result
        assert "mid_template_2" in result
        assert "other_template" in result
        assert "low_template_1" not in result

    def test_find_matching_templates_low(self):
        """Test finding templates for low telescope."""
        templates = {
            "mid_template_1": {"data": "mid1"},
            "low_template_1": {"data": "low1"},
            "low_template_2": {"data": "low2"},
            "other_template": {"data": "other"},
        }
        patterns = ["low_*", "other_*"]
        base_path = "tmdata/ska1_low"

        result = find_matching_templates(templates, patterns, base_path)

        assert "low_template_1" in result
        assert "low_template_2" in result
        assert "other_template" in result
        assert "mid_template_1" not in result

    def test_find_matching_templates_no_matches(self):
        """Test when no templates match the patterns."""
        templates = {"template1": {"data": "test"}}
        patterns = ["nonexistent_*"]
        base_path = "tmdata/ska1_mid"

        result = find_matching_templates(templates, patterns, base_path)

        assert result == {}


class TestProcessTemplateMappings:
    """Test cases for process_template_mappings function."""

    def test_process_template_mappings_success(self):
        """Test successful template mapping processing."""
        capabilities_data = {
            "AA1": {
                "basic_capabilities": {"test": "data"},
                "subarray_templates": ["mid_*"],
            }
        }
        template_data = {
            "mid_template_1": {"config": "test1"},
            "mid_template_2": {"config": "test2"},
        }
        capability = "ska1_mid/mid_capabilities.json"

        result = process_template_mappings(capabilities_data, capability, template_data)

        assert "AA1" in result
        assert "subarray_templates" in result["AA1"]
        assert isinstance(result["AA1"]["subarray_templates"], dict)
        assert "mid_template_1" in result["AA1"]["subarray_templates"]
        assert "mid_template_2" in result["AA1"]["subarray_templates"]

    def test_process_template_mappings_no_matches(self):
        """Test template mapping when no templates match."""
        capabilities_data = {
            "AA1": {
                "basic_capabilities": {"test": "data"},
                "subarray_templates": ["nonexistent_*"],
            }
        }
        template_data = {"mid_template_1": {"config": "test1"}}
        capability = "ska1_mid/mid_capabilities.json"

        result = process_template_mappings(capabilities_data, capability, template_data)

        assert "AA1" in result
        assert "subarray_templates" not in result["AA1"]

    def test_process_template_mappings_no_data(self):
        """Test template mapping with no capabilities data."""
        result = process_template_mappings(None, "test", {})
        assert result is None

        result = process_template_mappings({}, "test", None)
        assert result == {}

    def test_process_template_mappings_no_subarray_templates(self):
        """Test template mapping when no subarray_templates key exists."""
        capabilities_data = {"AA1": {"basic_capabilities": {"test": "data"}}}
        template_data = {"mid_template_1": {"config": "test1"}}
        capability = "ska1_mid/mid_capabilities.json"

        result = process_template_mappings(capabilities_data, capability, template_data)

        assert result == capabilities_data

    def test_process_template_mappings_invalid_patterns(self):
        """Test template mapping with invalid pattern format."""
        capabilities_data = {
            "AA1": {
                "basic_capabilities": {"test": "data"},
                "subarray_templates": "invalid_format",
            }
        }
        template_data = {"mid_template_1": {"config": "test1"}}
        capability = "ska1_mid/mid_capabilities.json"

        result = process_template_mappings(capabilities_data, capability, template_data)

        # Should remove subarray_templates key when format is invalid (not a list)
        assert "AA1" in result
        assert "subarray_templates" not in result["AA1"]

    def test_process_template_mappings_exception_handling(self):
        """Test template mapping exception handling."""
        capabilities_data = {
            "AA1": {
                "basic_capabilities": {"test": "data"},
                "subarray_templates": ["mid_*"],
            }
        }
        template_data = {"mid_template_1": {"config": "test1"}}
        capability = "ska1_mid/mid_capabilities.json"

        with patch(
            "ska_ost_osd.osd.template_mapping.template_mapping.find_matching_templates",
            side_effect=FileNotFoundError("Test error"),
        ):
            # The function should handle the exception gracefully
            result = process_template_mappings(
                capabilities_data, capability, template_data
            )

            assert "AA1" in result
            assert "subarray_templates" not in result["AA1"]
