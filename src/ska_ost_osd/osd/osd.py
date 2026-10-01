import copy
import logging
import re
from typing import Any, Dict, Optional

from ska_telmodel_client import TMData

from ska_ost_osd.common.utils import update_file
from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
)
from ska_ost_osd.osd.template_mapping.template_mapping import process_template_mappings

from .common.constant import (
    ARRAY_ASSEMBLY_PATTERN,
    LOW_CAPABILITIES_JSON_PATH,
    MID_CAPABILITIES_JSON_PATH,
    OBSERVATORY_POLICIES_JSON_PATH,
    OBSERVING_CYCLES_TMDATA_DIR,
    RELEASE_FILE_PATH_LATEST,
    osd_file_mapping,
)

LOGGER = logging.getLogger(__name__)


class OSD:
    """Build OSD responses by joining cycle policies to TMData capabilities."""

    def __init__(
        self,
        capabilities: list,
        array_assembly: str,
        tmdata: TMData,
        cycle_id: int,
        process_templates: bool = False,
    ) -> None:
        """Initialize the OSD class.

        :param capabilities: list, capabilities of the telescope ("mid"
            or "low").
        :param array_assembly: str, for "mid" can be one of "AA0.5",
            "AA2", or "AA1".
        :param tmdata: TMData, TMData class object.
        :param cycle_id: int, cycle identifier.
        :param process_templates: bool, whether to process template mappings.
        :return: None
        """
        self.cycle_id = cycle_id
        self.capabilities = capabilities
        self.array_assembly = array_assembly
        self.tmdata = tmdata
        self.process_templates = process_templates

    def capability_files(self) -> dict[str, str]:
        """Return capability names and TMData paths discovered from TMData."""
        return {
            entry.rsplit("/", maxsplit=1)[-1].removesuffix("_capabilities.json"): entry
            for entry in self.tmdata
            if entry.endswith("_capabilities.json")
        }

    def cycle_files(self):
        """Return the TMData cycle directory or raise when it is absent."""
        if not any(k.startswith(OBSERVING_CYCLES_TMDATA_DIR) for k in self.tmdata):
            raise FileNotFoundError(f"file not found: {OBSERVING_CYCLES_TMDATA_DIR}")
        return self.tmdata[OBSERVING_CYCLES_TMDATA_DIR]

    def get_available_cycles(self) -> list[int]:
        """List available cycle IDs from observing-cycle file names."""
        return [
            int(str(key).removesuffix(".json").removeprefix("cycle_"))
            for key in self.cycle_files()
            if key.startswith("cycle_") and key.endswith(".json")
        ]

    def check_cycle_id(self) -> str | None:
        """Return an error message when the selected cycle file is absent."""
        if self.cycle_id is None:
            return None

        cycle_filename = f"cycle_{self.cycle_id}.json"
        if cycle_filename not in self.cycle_files():
            cycle_numbers = ",".join(
                str(cycle) for cycle in self.get_available_cycles()
            )
            return CYCLE_ID_ERROR_MESSAGE.format(self.cycle_id, cycle_numbers)
        return None

    def validate_query(self) -> str | None:
        """Validate combinations and capability names before reading data."""
        capability_files = self.capability_files()
        if self.capabilities:
            for capability in self.capabilities:
                if capability.lower() not in capability_files:
                    available = ", ".join(list(osd_file_mapping.keys())[:3])
                    return CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                        capability, available
                    )

        if self.array_assembly and not self.capabilities:
            if self.cycle_id is not None:
                return CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE
            return ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE
        return None

    def get_cycle_policy(self) -> tuple[dict[str, Any] | None, str | None]:
        """Load the selected cycle policy after validating its file name."""
        cycle_error = self.check_cycle_id()
        if cycle_error:
            return None, cycle_error
        if self.cycle_id is None:
            return None, None
        return (
            self.tmdata[
                f"{OBSERVING_CYCLES_TMDATA_DIR}/cycle_{self.cycle_id}.json"
            ].get_dict(),
            None,
        )

    def select_capabilities(
        self, cycle_policy: dict[str, Any] | None
    ) -> tuple[dict[str, str | None] | None, str | None]:
        """Join requested capabilities to a cycle policy or the catalogue."""
        if cycle_policy is None:
            capability_names = self.capabilities or sorted(
                self.capability_files(), reverse=True
            )
            return {
                capability.lower(): self.array_assembly
                for capability in capability_names
            }, None

        cycle_capabilities = cycle_policy["telescope_capabilities"]
        requested_capabilities = self.capabilities or cycle_capabilities.keys()
        selected_capabilities = {}

        for capability in requested_capabilities:
            policy_capability = capability.capitalize()
            if policy_capability not in cycle_capabilities:
                available = ", ".join(
                    available_capability.lower()
                    for available_capability in cycle_capabilities
                )
                return None, CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE.format(
                    capability, self.cycle_id, available
                )

            cycle_array_assembly = cycle_capabilities[policy_capability]
            if self.array_assembly:
                if self.array_assembly != cycle_array_assembly:
                    return (
                        None,
                        ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE.format(
                            self.array_assembly,
                            capability,
                            self.cycle_id,
                            cycle_array_assembly,
                        ),
                    )
                LOGGER.warning(
                    "Ignoring redundant array assembly %s for capability %s in cycle %s",
                    self.array_assembly,
                    capability,
                    self.cycle_id,
                )
            selected_capabilities[capability.lower()] = cycle_array_assembly

        return selected_capabilities, None

    def get_data(self, capability: str) -> dict[str, Any]:
        """Load and optionally enrich one capability document."""
        capability_data = self.tmdata[self.capability_files()[capability]].get_dict()
        if not self.process_templates:
            return capability_data

        template_data = self.tmdata[osd_file_mapping["subarray_templates"]].get_dict()
        return process_template_mappings(
            capability_data,
            self.capability_files()[capability],
            template_data,
        )

    def check_array_assembly(
        self, array_assembly: str, capability_data: dict[str, Any]
    ) -> str | None:
        """Return an error when an assembly is absent from capability data."""
        if array_assembly not in capability_data:
            available = ", ".join(
                key for key in capability_data if re.match(ARRAY_ASSEMBLY_PATTERN, key)
            )
            return ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                array_assembly, available
            )
        return None

    def build_osd_data(
        self,
        selected_capabilities: dict[str, str | None],
        cycle_policy: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Materialize the selected capability and assembly data."""
        result_data = {"capabilities": {}}
        errors = []

        for capability, array_assembly in selected_capabilities.items():
            capability_data = self.get_data(capability)
            selected_data = {
                "basic_capabilities": capability_data["basic_capabilities"]
            }

            if array_assembly is None:
                selected_data.update(
                    {
                        key: value
                        for key, value in capability_data.items()
                        if key not in ("telescope", "basic_capabilities")
                    }
                )
            else:
                assembly_error = self.check_array_assembly(
                    array_assembly, capability_data
                )
                if assembly_error:
                    errors.append(assembly_error)
                    continue
                selected_data[array_assembly] = capability_data[array_assembly]

            result_data["capabilities"][capability] = selected_data

        if errors:
            return None, errors
        if cycle_policy is not None:
            result_data = {"observatory_policy": cycle_policy, **result_data}
        return result_data, []

    def get_osd_data(self) -> tuple[dict[str, Any] | None, list[str]]:
        """Return OSD data selected by the query's cycle and capability filters."""
        query_error = self.validate_query()
        if query_error:
            return None, [query_error]

        cycle_policy, cycle_error = self.get_cycle_policy()
        if cycle_error:
            return None, [cycle_error]

        selected_capabilities, selection_error = self.select_capabilities(cycle_policy)
        if selection_error:
            return None, [selection_error]

        return self.build_osd_data(selected_capabilities, cycle_policy)


def get_available_cycles(tmdata: TMData) -> list[int]:
    """List available cycle IDs from observing-cycle file names."""
    return OSD(
        capabilities=None,
        array_assembly=None,
        tmdata=tmdata,
        cycle_id=None,
    ).get_available_cycles()


def get_osd_latest_version(tmdata_version: TMData) -> str:
    """Read the latest_release.txt file and retrieve the latest OSD version.

    :param tmdata_version: TMData, TMData object for gitlab main version files.
    :return: str, the latest OSD release version.
    """
    osd_version = (
        tmdata_version[RELEASE_FILE_PATH_LATEST].get().decode("utf-8").replace('"', "")
    )

    return osd_version


def check_cycle_id(
    cycle_id: int = None,
    tmdata: TMData = None,
) -> str | None:
    """Return an error message when a cycle has no observing-cycle file."""
    return OSD(
        capabilities=None,
        array_assembly=None,
        tmdata=tmdata,
        cycle_id=cycle_id,
    ).check_cycle_id()


def get_osd_data(
    capabilities: list = None,
    array_assembly: str = None,
    tmdata: TMData = None,
    cycle_id: int = None,
    process_templates: bool = False,
) -> dict[dict[str, Any]]:
    """This function creates OSD class object and returns osd_data dictionary
    as json object.

    :param capabilities: mid or low
    :param array_assembly: in mid there are AA0.5, AA2 and AA1 you can
        give any one
    :param tmdata: TMData class object.
    :param cycle_id: cycle id
    :param process_templates: bool, whether to process template mappings
    :return: json object
    """
    osd_data, data_error_msg_list = OSD(
        capabilities=capabilities,
        array_assembly=array_assembly,
        tmdata=tmdata,
        cycle_id=cycle_id,
        process_templates=process_templates,
    ).get_osd_data()

    return osd_data, data_error_msg_list


def get_osd_using_tmdata(
    tm_data: TMData,
    capabilities: Optional[str] = None,
    array_assembly: Optional[str] = None,
    cycle_id: Optional[int] = None,
    process_templates: bool = False,
) -> Dict:
    """Retrieve OSD data using an already constructed TMData object.

    :param tm_data: TMData, pre-resolved TMData source for OSD retrieval.
    :param capabilities: str, optional capabilities.
    :param array_assembly: str, optional array assembly.
    :param cycle_id: int, optional cycle ID.
    :param process_templates: bool, whether to process template mappings.
    :return: Dict[Dict[str, Any]], OSD data.
    :raises ValueError: If any validation or processing errors occur.
    """
    errors = []

    osd_data, osd_errors = get_osd_data(
        capabilities=[capabilities] if capabilities else None,
        tmdata=tm_data,
        array_assembly=array_assembly,
        cycle_id=cycle_id,
        process_templates=process_templates,
    )
    errors.extend(osd_errors)
    if errors:
        raise ValueError(errors)

    return osd_data


def update_osd_file(
    validated_capabilities: Dict,
    observatory_policy: Dict,
    existing_stored_data: Dict,
    telescope: str,
) -> Dict:
    """Process and validate OSD data for insertion into the capabilities file.

    :param validated_capabilities: Dict, dictionary containing the
        validated capabilities.
    :param observatory_policy: Dict, dictionary containing the
        observatory policies.
    :param existing_stored_data: Dict, the existing stored capabilities
        data.
    :param telescope: str, mid or low
    :return: Dict, dictionary with the processed capabilities data.
    :raises OSDModelError: If validation fails.
    :raises ValueError: If required data is missing or invalid.
    """
    # Validate request body against schema

    capabilities = validated_capabilities.capabilities

    telescope = next(iter(capabilities.keys()))
    telescope_data = capabilities[telescope]

    # Create a copy of existing data to avoid modifying it directly
    updated_data = copy.deepcopy(existing_stored_data)

    # Allow new fields while preserving existing data structure
    for key, value in telescope_data.items():
        if key in updated_data:
            # Update existing fields
            if isinstance(value, dict) and isinstance(existing_stored_data[key], dict):
                updated_data[key].update(value)
            else:
                updated_data[key] = value
        else:
            # Add new fields
            updated_data[key] = value

    _get_data(telescope, updated_data)

    if observatory_policy:
        update_file(OBSERVATORY_POLICIES_JSON_PATH, observatory_policy)

    return updated_data


def add_new_data_storage(body: Dict) -> Dict:
    """Process and validate OSD data for insertion into the capabilities file.

    :param body: Dict, dictionary containing the OSD data to insert.
    :return: Dict, dictionary with the processed capabilities data.
    :raises OSDModelError: If validation fails.
    :raises ValueError: If required data is missing or invalid.
    """
    mid_capabilities = {}
    result = {}
    if not body.get("capabilities", {}).get("mid"):
        return mid_capabilities

    capabilities = body["capabilities"]
    telescope = next(iter(capabilities.keys()))
    telescope_data = capabilities[telescope]

    mid_capabilities.update(
        {
            "telescope": telescope,
            "basic_capabilities": telescope_data["basic_capabilities"],
            **{
                key: telescope_data[key]
                for key in telescope_data
                if re.match(ARRAY_ASSEMBLY_PATTERN, key)
            },
        }
    )
    mid_capabilities["telescope"] = mid_capabilities["telescope"].title()
    update_file(MID_CAPABILITIES_JSON_PATH, mid_capabilities)
    if body.get("observatory_policy"):
        update_file(OBSERVATORY_POLICIES_JSON_PATH, body["observatory_policy"])
        result.update(body["observatory_policy"])
    result.update(mid_capabilities)
    return mid_capabilities


def _get_data(telescope: str, data: Dict) -> None:
    """Update capabilities file based on telescope type.

    :param data: Dict, dictionary containing the
        observatory policies.
    :param telescope: str, mid or low
    """

    match telescope:
        case "mid":
            update_file(MID_CAPABILITIES_JSON_PATH, data)

        case "low":
            update_file(LOW_CAPABILITIES_JSON_PATH, data)
