"""Created file to maintain OSD Model constants."""

from enum import Enum

MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
MID_DEFAULTS_JSON_FILE_PATH = "ska1_mid/mid_defaults.json"
LOW_DEFAULTS_JSON_FILE_PATH = "ska1_low/low_defaults.json"
OBSERVING_CYCLES_TMDATA_DIR = "cycles"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"
RELEASE_FILE = "tmdata/version_mapping/latest_release.txt"
RELEASE_FILE_PATH_LATEST = "version_mapping/latest_release.txt"
VERSION_FILE_PATH = "version_mapping/cycle_gitlab_release_version_mapping.json"
SUBARRAY_TEMPLATES_PATH = "subarray_templates/subarray_template_library.json"

osd_file_mapping = {
    "low": LOW_CONSTANT_JSON_FILE_PATH,
    "mid": MID_CONSTANT_JSON_FILE_PATH,
    "observatory_policies": POLICIES_CONSTANT_JSON_FILE_PATH,
    "cycle_to_version_mapping": VERSION_FILE_PATH,
    "latest_cycle_version_to_release": RELEASE_FILE,
    "subarray_templates": SUBARRAY_TEMPLATES_PATH,
}

BASE_URL = "//gitlab.com/ska-telescope/"
CAR_URL = "ost/ska-ost-osd?"
BASE_FOLDER_NAME = "tmdata"

SOURCES = ("file", "car", "gitlab")
CAPABILITIES = ("mid", "low")


class Telescope(str, Enum):
    """Supported telescope names."""

    LOW = "low"
    MID = "mid"

    def __str__(self) -> str:
        """Return the telescope name used in TMData and API responses."""
        return self.value


OSD_VERSION_PATTERN = r"^\d+\.\d+\.\d+"
ARRAY_ASSEMBLY_PATTERN = r"^AA(\d+|\d+\.\d+)|^Low|^Mid"
QUERY_FIELDS = [
    "cycle_id",
    "osd_version",
    "source",
    "gitlab_branch",
    "capabilities",
    "array_assembly",
]

MID_CAPABILITIES_JSON_PATH = "tmdata/ska1_mid/mid_capabilities.json"
LOW_CAPABILITIES_JSON_PATH = "tmdata/ska1_low/low_capabilities.json"
OBSERVATORY_POLICIES_JSON_PATH = "tmdata/observatory_policies.json"
CYCLE_TO_VERSION_MAPPING = "tmdata/version_mapping/latest_release.txt"
RELEASE_VERSION_MAPPING = (
    "tmdata/version_mapping/cycle_gitlab_release_version_mapping.json"
)
SWAGGER_MID_OSD_DATA_JSON_FILE_PATH = "data/sample_mid_osd_data.json"
