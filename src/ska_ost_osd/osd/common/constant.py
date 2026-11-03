"""Created file to maintain OSD Model constants."""

from enum import Enum

MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
MID_DEFAULTS_JSON_FILE_PATH = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS_JSON_FILE_PATH = "ska1_low/low_defaults.json"
OBSERVING_CYCLES_TMDATA_DIR = "cycles"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"
RELEASE_FILE_PATH_LATEST = "version_mapping/latest_release.txt"
SUBARRAY_TEMPLATES_PATH = "subarray_templates/subarray_template_library.json"

osd_file_mapping = {
    "low": LOW_CONSTANT_JSON_FILE_PATH,
    "mid": MID_CONSTANT_JSON_FILE_PATH,
    "observatory_policies": POLICIES_CONSTANT_JSON_FILE_PATH,
    "subarray_templates": SUBARRAY_TEMPLATES_PATH,
}


class Telescope(str, Enum):
    """Supported telescope names."""

    LOW = "low"
    MID = "mid"

    def __str__(self) -> str:
        """Return the telescope name used in TMData and API responses."""
        return self.value


CAPABILITIES_JSON_FILE_PATHS = {
    Telescope.MID: MID_CONSTANT_JSON_FILE_PATH,
    Telescope.LOW: LOW_CONSTANT_JSON_FILE_PATH,
}

DEFAULTS_JSON_FILE_PATHS = {
    Telescope.MID: MID_DEFAULTS_JSON_FILE_PATH,
    Telescope.LOW: LOW_DEFAULTS_JSON_FILE_PATH,
}


ARRAY_ASSEMBLY_PATTERN = r"^AA(\d+|\d+\.\d+)|^Low|^Mid"
