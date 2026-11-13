"""Created file to maintain OSD Model constants."""

from dataclasses import dataclass
from enum import StrEnum

# Legacy files, kept for older releases and for consumers that read them
# directly; the current code does not read them
MID_CONSTANT_JSON_FILE_PATH = "ska1_mid/mid_capabilities.json"
LOW_CONSTANT_JSON_FILE_PATH = "ska1_low/low_capabilities.json"
POLICIES_CONSTANT_JSON_FILE_PATH = "observatory_policies.json"

# Each telescope's files are in its own directory under telescopes
TELESCOPES_TMDATA_DIR = "telescopes"
SUBARRAY_TEMPLATES_DIRNAME = "subarray_templates"

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


@dataclass(frozen=True)
class TelescopeFiles:
    """Paths of one telescope's tmdata files, relative to the tmdata root.

    Every telescope's files have the same names; only the directory differs.
    """

    directory: str

    @property
    def basic_capabilities(self) -> str:
        return f"{self.directory}/basic_capabilities.json"

    @property
    def defaults(self) -> str:
        return f"{self.directory}/defaults.json"

    @property
    def capability_sets(self) -> str:
        return f"{self.directory}/array_assemblies"

    @property
    def subarray_templates(self) -> str:
        return f"{self.directory}/{SUBARRAY_TEMPLATES_DIRNAME}"

    def capability_set(self, name: str) -> str:
        return f"{self.capability_sets}/{name}.json"

    def subarray_template_library(self, array_assembly: str) -> str:
        return f"{self.subarray_templates}/{array_assembly}.json"


# Each telescope's directory is named by its Telescope value, so a new
# telescope needs only a new Telescope member
TELESCOPE_FILES = {
    telescope: TelescopeFiles(f"{TELESCOPES_TMDATA_DIR}/{telescope}")
    for telescope in Telescope
}
