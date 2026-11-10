"""Created file to maintain OSD Model constants."""

from enum import StrEnum

# Legacy files, kept for older releases and for consumers that read them
# directly; the current code does not read them
MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"

# Each telescope's files are in its own directory under telescopes
TELESCOPES_TMDATA_DIR = "telescopes"
MID_TMDATA_DIR = f"{TELESCOPES_TMDATA_DIR}/ska_mid"
LOW_TMDATA_DIR = f"{TELESCOPES_TMDATA_DIR}/ska_low"
MID_DEFAULTS_JSON_FILE_PATH = f"{MID_TMDATA_DIR}/defaults.json"
LOW_DEFAULTS_JSON_FILE_PATH = f"{LOW_TMDATA_DIR}/defaults.json"
MID_BASIC_CAPABILITIES_JSON_FILE_PATH = f"{MID_TMDATA_DIR}/basic_capabilities.json"
LOW_BASIC_CAPABILITIES_JSON_FILE_PATH = f"{LOW_TMDATA_DIR}/basic_capabilities.json"
MID_CAPABILITY_SETS_TMDATA_DIR = f"{MID_TMDATA_DIR}/capabilities"
LOW_CAPABILITY_SETS_TMDATA_DIR = f"{LOW_TMDATA_DIR}/capabilities"
SUBARRAY_TEMPLATES_DIRNAME = "subarray_templates"
MID_SUBARRAY_TEMPLATES_TMDATA_DIR = f"{MID_TMDATA_DIR}/{SUBARRAY_TEMPLATES_DIRNAME}"
LOW_SUBARRAY_TEMPLATES_TMDATA_DIR = f"{LOW_TMDATA_DIR}/{SUBARRAY_TEMPLATES_DIRNAME}"

OBSERVING_CYCLES_TMDATA_DIR = "cycles"
RELEASE_FILE_PATH_LATEST = "version_mapping/latest_release.txt"

osd_file_mapping = {
    "low": LOW_CONSTANT_JSON_FILE_PATH,
    "mid": MID_CONSTANT_JSON_FILE_PATH,
    "observatory_policies": POLICIES_CONSTANT_JSON_FILE_PATH,
    "subarray_templates": SUBARRAY_TEMPLATES_DIRNAME,
}


class Telescope(StrEnum):
    """Supported telescopes, with the values of the PDM's ``TelescopeType``."""

    SKA_LOW = "ska_low"
    SKA_MID = "ska_mid"


BASIC_CAPABILITIES_JSON_FILE_PATHS = {
    Telescope.SKA_MID: MID_BASIC_CAPABILITIES_JSON_FILE_PATH,
    Telescope.SKA_LOW: LOW_BASIC_CAPABILITIES_JSON_FILE_PATH,
}

CAPABILITY_SETS_TMDATA_DIRS = {
    Telescope.SKA_MID: MID_CAPABILITY_SETS_TMDATA_DIR,
    Telescope.SKA_LOW: LOW_CAPABILITY_SETS_TMDATA_DIR,
}

SUBARRAY_TEMPLATES_TMDATA_DIRS = {
    Telescope.SKA_MID: MID_SUBARRAY_TEMPLATES_TMDATA_DIR,
    Telescope.SKA_LOW: LOW_SUBARRAY_TEMPLATES_TMDATA_DIR,
}

DEFAULTS_JSON_FILE_PATHS = {
    Telescope.SKA_MID: MID_DEFAULTS_JSON_FILE_PATH,
    Telescope.SKA_LOW: LOW_DEFAULTS_JSON_FILE_PATH,
}
