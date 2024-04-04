"""
  created file to maintain OSD Model constants
"""

MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"
FILE_NAME = "cycle_gitlab_release_version_mapping.json"
VERSIONS_JSON_FILE_PATH = f"version_mapping/{FILE_NAME}"

osd_file_mapping = {
    "low": LOW_CONSTANT_JSON_FILE_PATH,
    "mid": MID_CONSTANT_JSON_FILE_PATH,
    "observatory_policies": POLICIES_CONSTANT_JSON_FILE_PATH,
    "cycle_to_version_mapping": VERSIONS_JSON_FILE_PATH,
}

osd_response_template = {
    "observatory_policy": {"cycle_number": 0, "telescope_capabilities": []},
    "capabilities": {},
}


BASE_URL = "//gitlab.com/ska-telescope/ost/ska-ost-osd?"
BASE_FOLDER_NAME = "tm_data"

source_list = ["file", "car", "gitlab"]
array_assembly_pattern = r"^AA(\d+|\d+\.\d+)"
error_msg_list = []
