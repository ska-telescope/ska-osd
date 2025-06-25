"""Created file to maintain OSD Model constants."""

MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"
RELEASE_FILE = "tmdata/version_mapping/latest_release.txt"
VERSION_FILE_PATH = "version_mapping/cycle_gitlab_release_version_mapping.json"

osd_file_mapping = {
    "low": LOW_CONSTANT_JSON_FILE_PATH,
    "mid": MID_CONSTANT_JSON_FILE_PATH,
    "observatory_policies": POLICIES_CONSTANT_JSON_FILE_PATH,
    "cycle_to_version_mapping": VERSION_FILE_PATH,
    "latest_cycle_version_to_release": RELEASE_FILE,
}

osd_response_template = {
    "observatory_policy": {"cycle_number": 0, "telescope_capabilities": []},
    "capabilities": {},
}


BASE_URL = "//gitlab.com/ska-telescope/"
CAR_URL = "ost/ska-ost-osd?"
BASE_FOLDER_NAME = "tmdata"

SOURCES = ("file", "car", "gitlab")
CAPABILITIES = ("mid", "low")
OSD_VERSION_PATTERN = r"^\d+\.\d+\.\d+"
ARRAY_ASSEMBLY_PATTERN = r"^AA(\d+|\d+\.\d+)"
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
# constant define to push gitlab flag.
GITLAB_SOURCE = [f"gitlab:{BASE_URL}{CAR_URL}main#{BASE_FOLDER_NAME}"]
