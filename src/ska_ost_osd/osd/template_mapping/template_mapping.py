"""Template mapping functionality for OSD.

This module handles the processing of template_mappings in capabilities data,
finding templates based on patterns and replacing template mappings with
actual template data.
"""

import fnmatch
import json
from functools import lru_cache
from typing import Any, Dict

from ska_ost_osd.common.utils import read_json


@lru_cache(maxsize=32)
def load_template_file(file_path: str) -> Dict[str, Any]:
    """Load template data from a JSON file with caching.

    :param file_path: Path to the template file
    :return: Dictionary containing template data
    :raises FileNotFoundError: If the template file doesn't exist
    :raises json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        return read_json(file_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Template file not found: {file_path}") from exc
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in template file {file_path}: {e}", e.doc, e.pos
        ) from e


def find_matching_templates(
    templates: Dict[str, Any], patterns: list, base_path: str = ""
) -> Dict[str, Any]:
    """Find templates that match the given patterns and telescope type.

    :param templates: Dictionary of all available templates
    :param patterns: List of patterns to match against template keys
    :param base_path: Base path to determine telescope type
    :return: Dictionary of matching templates
    """
    matching_templates = {}
    telescope_type = "mid" if "ska1_mid" in base_path else "low"

    for pattern in patterns:
        for template_key, template_data in templates.items():
            if fnmatch.fnmatch(template_key, pattern):
                # Filter out templates that don't match telescope type
                template_lower = template_key.lower()
                if telescope_type == "mid" and not template_lower.startswith("low_"):
                    matching_templates[template_key] = template_data
                elif telescope_type == "low" and not template_lower.startswith("mid_"):
                    matching_templates[template_key] = template_data

    return matching_templates


def process_template_mappings(
    capabilities_data: Dict[str, Any], base_path: str = "tmdata/ska1_mid"
) -> Dict[str, Any]:
    """Process template mappings in capabilities data.

    This function finds template_mappings in the capabilities data, loads the referenced
    template files, finds templates matching the specified patterns, and replaces the
    template_mappings key with the actual template data as individual keys.

    :param capabilities_data: Dictionary containing capabilities data
    :param base_path: Base path for template files
    :return: Updated capabilities data with template mappings resolved
    """
    # Create a deep copy to avoid modifying the original data
    updated_data = json.loads(json.dumps(capabilities_data))

    # Process each array assembly in the capabilities data
    for value in updated_data.values():
        if isinstance(value, dict) and "template_mappings" in value:
            template_mappings = value["template_mappings"]

            # Process each template mapping
            for mapping_key, mapping_config in template_mappings.items():
                if isinstance(mapping_config, dict) and "file" in mapping_config:
                    template_file = mapping_config["file"]
                    template_patterns = mapping_config.get("template_patterns", [])

                    # Use the file path as specified in the mapping config
                    template_file_path = (
                        template_file
                        if template_file.startswith("tmdata/")
                        else f"{base_path}/{template_file}"
                    )

                    try:
                        # Load template data from file
                        template_data = load_template_file(template_file_path)

                        # Find templates matching the patterns
                        matching_templates = find_matching_templates(
                            template_data, template_patterns, base_path
                        )

                        # Add matching templates directly with lowercase keys
                        for template_key, template_value in matching_templates.items():
                            value[template_key.lower()] = template_value

                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        # Log error but continue processing
                        print(
                            "Warning: Could not process template mapping"
                            f" {mapping_key}: {e}"
                        )

            # Remove the template_mappings key entirely
            del value["template_mappings"]

    return updated_data


def apply_template_mappings_to_osd_data(osd_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply template mapping processing to OSD data.

    This function processes the capabilities section of OSD data and applies
    template mapping resolution to each telescope's capabilities.

    :param osd_data: Complete OSD data dictionary
    :return: Updated OSD data with template mappings resolved
    """
    if "capabilities" not in osd_data:
        return osd_data

    updated_osd_data = json.loads(json.dumps(osd_data))

    # Process each telescope's capabilities
    for telescope, telescope_data in updated_osd_data["capabilities"].items():
        if isinstance(telescope_data, dict):
            # Determine base path based on telescope type
            base_path = f"tmdata/ska1_{telescope.lower()}"

            # Process template mappings for this telescope's data
            updated_osd_data["capabilities"][telescope] = process_template_mappings(
                telescope_data, base_path
            )

    return updated_osd_data
