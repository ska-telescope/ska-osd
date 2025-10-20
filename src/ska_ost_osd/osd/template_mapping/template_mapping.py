"""Template mapping functionality for OSD.

This module handles the processing of template_mappings in capabilities data,
finding templates based on patterns and replacing template mappings with
actual template data.
"""

import fnmatch
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from ska_ost_osd.common.utils import read_json

# Constants
SUBARRAY_TEMPLATES_PATH = "tmdata/subarray_templates/subarray_template_library.json"


@lru_cache(maxsize=32)
def load_template_file(file_path: Path) -> Dict[str, Any]:
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
    templates: Dict[str, Any], patterns: list, base_path: Path = ""
) -> Dict[str, Any]:
    """Find templates that match the given patterns and telescope type.

    :param templates: Dictionary of all available templates
    :param patterns: List of patterns to match against template keys
    :param base_path: Path to determine telescope type
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
    capabilities_data: Dict[str, Any], base_path: Path = "tmdata/ska1_mid"
) -> Dict[str, Any]:
    """Process template mappings in capabilities data.

    This function finds template_mappings in the capabilities data, loads the referenced
    template files, finds templates matching the specified patterns, and replaces the
    template_mappings key with the actual template data as individual keys.

    :param capabilities_data: Dictionary containing capabilities data
    :param base_path: Path for template files
    :return: Updated capabilities data with template mappings resolved
    """
    # Create a deep copy to avoid modifying the original data
    updated_data = json.loads(json.dumps(capabilities_data))

    # Process each array assembly in the capabilities data
    for value in updated_data.values():
        if isinstance(value, dict) and "subarray_templates" in value:
            template_patterns = value["subarray_templates"]

            if isinstance(template_patterns, list):
                try:
                    # Load subarray template data from constant path
                    template_data = load_template_file(SUBARRAY_TEMPLATES_PATH)

                    # Find templates matching the patterns
                    matching_templates = find_matching_templates(
                        template_data, template_patterns, base_path
                    )

                    # Replace the patterns list with the actual template data
                    if matching_templates:
                        value["subarray_templates"] = matching_templates
                    else:
                        # Remove the key if no templates match
                        del value["subarray_templates"]

                except (FileNotFoundError, json.JSONDecodeError) as e:
                    # Log error and remove the key
                    print(f"Warning: Could not process subarray templates: {e}")
                    del value["subarray_templates"]

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
