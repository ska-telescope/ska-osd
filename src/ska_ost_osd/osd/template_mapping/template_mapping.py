"""Template mapping functionality for OSD.

This module handles the processing of template_mappings in capabilities data,
finding templates based on patterns and replacing template mappings with
actual template data.
"""

import fnmatch
import json
import logging
from typing import Any, Dict, List

from ska_ser_logging import configure_logging

configure_logging(level="INFO")
LOGGER = logging.getLogger(__name__)


def find_matching_templates(
    template_data: Dict[str, Any], patterns: List[str], base_path: str = ""
) -> Dict[str, Any]:
    """Find templates that match the given patterns and telescope type.

    :param template_data: template data
    :param patterns: List of patterns to match against template keys
    :param base_path: Path to determine telescope type
    :return: Dictionary of matching templates
    """
    matching_templates = {}
    telescope_type = "mid" if "ska1_mid" in base_path else "low"
    excluded_prefix = "low_" if telescope_type == "mid" else "mid_"

    LOGGER.info(
        "Finding templates for telescope type: %s with patterns: %s",
        telescope_type,
        patterns,
    )

    for pattern in patterns:
        for template_key, data in template_data.items():
            if not fnmatch.fnmatch(template_key, pattern):
                continue

            if template_key.lower().startswith(excluded_prefix):
                continue

            matching_templates[template_key] = data
            LOGGER.info("Matched template: %s for pattern: %s", template_key, pattern)

    LOGGER.info("Found %d matching templates", len(matching_templates))
    return matching_templates


def process_template_mappings(
    capabilities_data: Dict[str, Any],
    capability: str = None,
    template_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Process template mappings in capabilities data.

    This function finds subarray_templates in the capabilities data, finds templates
    matching the specified patterns, and replaces the subarray_templates list with
    the actual template data as a dictionary.

    :param capabilities_data: Dictionary containing capabilities data
    :param capability: Capability string to determine base path
    :param template_data: template data
    :return: Updated capabilities data with template mappings resolved
    """
    if not capabilities_data:
        LOGGER.info("No capabilities data provided")
        return capabilities_data

    base_path = (
        f"tmdata/{capability.replace('.json', '')}" if capability else "tmdata/ska1_mid"
    )
    LOGGER.info(
        "Processing template mappings for capability: %s, base_path: %s",
        capability,
        base_path,
    )
    updated_data = json.loads(json.dumps(capabilities_data))

    # Collect all unique patterns to process templates only once
    all_patterns = set()
    values_with_templates = []

    for value in updated_data.values():
        if isinstance(value, dict) and "subarray_templates" in value:
            template_patterns = value["subarray_templates"]
            if isinstance(template_patterns, list):
                all_patterns.update(template_patterns)
                values_with_templates.append((value, template_patterns))

    # Process all templates once if we have patterns
    if all_patterns:
        try:
            all_matching_templates = find_matching_templates(
                template_data, list(all_patterns), base_path
            )

            # Apply matching templates to each value
            for value, patterns in values_with_templates:
                matching_templates = {
                    k: v
                    for k, v in all_matching_templates.items()
                    if any(fnmatch.fnmatch(k, pattern) for pattern in patterns)
                }

                if matching_templates:
                    value["subarray_templates"] = matching_templates
                    LOGGER.info(
                        "Successfully processed %d templates",
                        len(matching_templates),
                    )
                else:
                    del value["subarray_templates"]
                    LOGGER.info(
                        "No matching templates found, removing subarray_templates key"
                    )

        except (KeyError, AttributeError, TypeError, FileNotFoundError) as e:
            LOGGER.error("Failed to process templates: %s", e)
            # Remove subarray_templates from all values on error
            for value, _ in values_with_templates:
                if "subarray_templates" in value:
                    del value["subarray_templates"]

    return updated_data
