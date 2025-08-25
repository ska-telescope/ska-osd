"""Version management module for OSD.

This module handles version increments according to semantic versioning
rules.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def increment_version(current_version: str, release_type: Optional[str] = None) -> str:
    """Increment the version number based on semantic versioning rules.

    :param current_version: str, current version string in format
        "X.Y.Z".
    :param release_type: Optional[str], type of release ("major",
        "minor", or None for patch).
    :return: str, new version string following semantic versioning
        rules.
    """
    major, minor, patch = map(int, current_version.strip('"').split("."))

    if release_type == "major":
        return f"{major + 1}.0.0"

    if release_type == "minor":
        return f"{major}.{minor + 1}.0"

    # Default patch release
    patch += 1
    if patch > 9:
        minor += 1
        patch = 0
        if minor > 9:
            major += 1
            minor = 0

    return f"{major}.{minor}.{patch}"


def manage_version_release(
    cycle_id: str, release_type: Optional[str] = None
) -> Tuple[str, str]:
    """Manage version release for a given cycle ID.

    :param cycle_id: str, the cycle ID for version mapping.
    :param release_type: Optional[str], type of release ("major",
        "minor", defaults to patch).
    :return: Tuple[str, str], tuple containing (new_version, cycle_id).
    :raises ValueError: If cycle_id is invalid or no versions are found
        for the cycle.
    """
    # Get the project root directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent

    # Read version mapping file
    version_mapping_path = (
        project_root
        / "tmdata/version_mapping/cycle_gitlab_release_version_mapping.json"
    )
    with open(version_mapping_path, "r", encoding="utf-8") as f:
        version_mapping = json.load(f)

    # Validate cycle_id exists in mapping
    if cycle_id not in version_mapping:
        raise ValueError(f"Invalid cycle_id: {cycle_id}")

    # Get versions list for the cycle
    versions = version_mapping[cycle_id]
    if not versions:
        raise ValueError(f"No versions found for cycle {cycle_id}")

    # Get latest version
    latest_version = versions[-1]

    # Increment version
    new_version = increment_version(latest_version, release_type)

    # Keep incrementing version until we find one that doesn't exist in any cycle
    while any(
        new_version in cycle_versions for cycle_versions in version_mapping.values()
    ):
        new_version = increment_version(new_version, release_type)

    # Update version mapping with new version
    version_mapping[cycle_id].append(new_version)

    # Save updated mapping
    with open(version_mapping_path, "w", encoding="utf-8") as f:
        json.dump(version_mapping, f, indent=2)

    # Write new version to latest_release.txt
    latest_release_path = project_root / "tmdata/version_mapping/latest_release.txt"
    with open(latest_release_path, "w", encoding="utf-8") as f:
        f.write(f'"{new_version}"')
    return new_version, cycle_id
