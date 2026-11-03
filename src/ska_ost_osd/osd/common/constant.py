"""Created file to maintain OSD Model constants."""

from enum import StrEnum

MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
MID_DEFAULTS_JSON_FILE_PATH = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS_JSON_FILE_PATH = "ska1_low/low_defaults.json"
MID_BASIC_CAPABILITIES_JSON_FILE_PATH = "ska1_mid/basic_capabilities.json"
LOW_BASIC_CAPABILITIES_JSON_FILE_PATH = "ska1_low/basic_capabilities.json"
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


class Telescope(StrEnum):
    """Supported telescopes, with the values of the PDM's ``TelescopeType``."""

    SKA_LOW = "ska_low"
    SKA_MID = "ska_mid"


CAPABILITIES_JSON_FILE_PATHS = {
    Telescope.SKA_MID: MID_CONSTANT_JSON_FILE_PATH,
    Telescope.SKA_LOW: LOW_CONSTANT_JSON_FILE_PATH,
}

BASIC_CAPABILITIES_JSON_FILE_PATHS = {
    Telescope.SKA_MID: MID_BASIC_CAPABILITIES_JSON_FILE_PATH,
    Telescope.SKA_LOW: LOW_BASIC_CAPABILITIES_JSON_FILE_PATH,
}

DEFAULTS_JSON_FILE_PATHS = {
    Telescope.SKA_MID: MID_DEFAULTS_JSON_FILE_PATH,
    Telescope.SKA_LOW: LOW_DEFAULTS_JSON_FILE_PATH,
}


ARRAY_ASSEMBLY_PATTERN = r"^AA(\d+|\d+\.\d+)|^Low|^Mid"
