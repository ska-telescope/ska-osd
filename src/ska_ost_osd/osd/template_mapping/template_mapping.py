"""Template mapping functionality for OSD.

This module handles the processing of template_mappings in capabilities data,
finding templates based on patterns and replacing template mappings with
actual template data.
"""

import fnmatch
import json
from typing import Any, Dict, List

from ska_telmodel.data import TMData

# Constants
SUBARRAY_TEMPLATES_PATH = "subarray_templates/subarray_template_library.json"


def load_template_file(file_path: str, tmdata: TMData) -> Dict[str, Any]:
    """Load template data from TMData.

    :param file_path: Path to the template file
    :param tmdata: TMData instance for remote sources
    :return: Dictionary containing template data
    :raises FileNotFoundError: If the template file doesn't exist
    """
    try:
        return tmdata[file_path].get_dict()
    except (KeyError, AttributeError) as e:
        raise FileNotFoundError(f"Template file not found: {file_path}") from e


def find_matching_templates(
    templates: Dict[str, Any], patterns: List[str], base_path: str = ""
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
    capabilities_data: Dict[str, Any],
    capability: str = None,
    tmdata: TMData = None,
) -> Dict[str, Any]:
    """Process template mappings in capabilities data.

    This function finds template_mappings in the capabilities data, loads the referenced
    template files, finds templates matching the specified patterns, and replaces the
    template_mappings key with the actual template data as individual keys.

    :param capabilities_data: Dictionary containing capabilities data
    :param capability: Capability string to determine base path
    :param tmdata: TMData instance
    :return: Updated capabilities data with template mappings resolved
    """
    if not capabilities_data:
        return capabilities_data

    # Calculate base_path from capability
    base_path = (
        f"tmdata/{capability.replace('.json', '')}" if capability else "tmdata/ska1_mid"
    )
    # Create a deep copy to avoid modifying the original data
    updated_data = json.loads(json.dumps(capabilities_data))

    # Process each array assembly in the capabilities data
    for value in updated_data.values():
        if isinstance(value, dict) and "subarray_templates" in value:
            template_patterns = value["subarray_templates"]

            if isinstance(template_patterns, list):
                try:
                    # Load subarray template data using TMData
                    template_data = load_template_file(SUBARRAY_TEMPLATES_PATH, tmdata)

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

                except FileNotFoundError as e:
                    # Log error and remove the key
                    print(f"Warning: Could not process subarray templates: {e}")
                    if "subarray_templates" in value:
                        del value["subarray_templates"]

    return updated_data
