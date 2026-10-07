import copy
import logging
import re
from functools import cached_property
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
    Telescope,
    osd_file_mapping,
)

LOGGER = logging.getLogger(__name__)


class OSD:
    """Build OSD responses from telescope capability documents and cycle definitions."""

    def __init__(
        self,
        telescope: Telescope | None,
        array_assembly: str,
        tmdata: TMData,
        cycle_id: int,
        process_templates: bool = False,
    ) -> None:
        """Initialize the OSD class.

        :param telescope: requested telescope name (``"mid"`` or ``"low"``).
        :param array_assembly: requested capability-set name, such as ``"AA2"`` or ``"AA2_SV"``.
        :param tmdata: TMData, TMData class object.
        :param cycle_id: int, cycle identifier.
        :param process_templates: bool, whether to process template mappings.
        :return: None
        """
        self.cycle_id = cycle_id
        self.requested_telescope = telescope
        self.requested_capability_set = array_assembly
        self.tmdata = tmdata
        self.process_templates = process_templates

    @cached_property
    def capability_filepaths(self) -> dict[str, str]:
        """Return telescope-keyed TMData capability document paths."""
        capability_filepaths = {}
        for entry in self.tmdata:
            if entry.endswith("_capabilities.json"):
                telescope = self.tmdata[entry].get_dict()["telescope"]
                capability_filepaths[telescope.lower()] = entry
        return capability_filepaths

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
        """Validate the query before reading TMData files."""
        capability_filepaths = self.capability_filepaths
        if self.requested_telescope:
            # A queried telescope must have a corresponding capability document.
            if self.requested_telescope.lower() not in capability_filepaths:
                available = ", ".join(list(osd_file_mapping.keys())[:3])
                return CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                    self.requested_telescope, available
                )

        # A named capability set can only be queried with a telescope.
        if self.requested_capability_set and not self.requested_telescope:
            if self.cycle_id is not None:
                return CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE
            return ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE
        return None

    def get_cycle_definition(self) -> tuple[dict[str, Any] | None, str | None]:
        """Load the selected cycle definition after validating its file name."""
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

    def select_telescope_capability_sets(
        self, cycle_definition: dict[str, Any] | None
    ) -> tuple[dict[str, str | None] | None, str | None]:
        """Select a named capability set for each included telescope."""
        if cycle_definition is None:
            # Catalogue mode: select each requested telescope and optionally one
            # named capability set. No capability-set filter is expanded to all
            # named sets later in build_osd_data().
            if self.requested_telescope:
                return {
                    self.requested_telescope.lower(): self.requested_capability_set
                }, None
            return {
                telescope.lower(): self.requested_capability_set
                for telescope in self.capability_filepaths
            }, None

        # Cycle mode: each telescope maps to one prescribed capability set.
        cycle_telescope_capability_sets = cycle_definition["telescope_capabilities"]
        if self.requested_telescope is None:
            return {
                telescope.lower(): capability_set
                for telescope, capability_set in cycle_telescope_capability_sets.items()
            }, None

        telescope_key = self.requested_telescope.capitalize()
        # A requested telescope must be specified in the requested cycle.
        if telescope_key not in cycle_telescope_capability_sets:
            available = ", ".join(
                available_telescope.lower()
                for available_telescope in cycle_telescope_capability_sets
            )
            return None, CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE.format(
                self.requested_telescope, self.cycle_id, available
            )

        cycle_capability_set = cycle_telescope_capability_sets[telescope_key]
        if self.requested_capability_set:
            # A cycle already specifies a capability set for each telescope.
            # Requesting a capability set is valid only when it matches the cycle.
            if self.requested_capability_set != cycle_capability_set:
                return (
                    None,
                    ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE.format(
                        self.requested_capability_set,
                        self.requested_telescope,
                        self.cycle_id,
                        cycle_capability_set,
                    ),
                )
            LOGGER.warning(
                "Ignoring redundant array assembly %s for capability %s in cycle %s",
                self.requested_capability_set,
                self.requested_telescope,
                self.cycle_id,
            )

        # Join the telescope to the capability set specified in the cycle.
        return {self.requested_telescope.lower(): cycle_capability_set}, None

    def get_telescope_capability_data(self, telescope: str) -> dict[str, Any]:
        """Load one telescope capability document and optional template mappings."""
        telescope_capability_data = self.tmdata[
            self.capability_filepaths[telescope]
        ].get_dict()
        if not self.process_templates:
            return telescope_capability_data

        try:
            template_data = self.tmdata[
                osd_file_mapping["subarray_templates"]
            ].get_dict()
        except (KeyError, AttributeError):
            template_data = {}
        return process_template_mappings(
            telescope_capability_data,
            self.capability_filepaths[telescope],
            template_data,
        )

    def check_capability_set(
        self, capability_set: str, telescope_capability_data: dict[str, Any]
    ) -> str | None:
        """Return an error when a named capability set is absent from a telescope."""
        if (
            capability_set in ("constraints", "basic_capabilities")
            or capability_set not in telescope_capability_data
        ):
            available = ", ".join(
                key
                for key in telescope_capability_data
                if key not in ("telescope", "basic_capabilities", "constraints")
            )
            return ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                capability_set, available
            )
        return None

    def build_osd_data(
        self,
        selected_telescope_capability_sets: dict[str, str | None],
        cycle_definition: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Materialize the selected telescope capability sets."""
        result_data = {"capabilities": {}}
        errors = []

        for (
            telescope,
            capability_set,
        ) in selected_telescope_capability_sets.items():
            telescope_capability_data = self.get_telescope_capability_data(telescope)
            selected_data = {
                "basic_capabilities": telescope_capability_data["basic_capabilities"]
            }

            if capability_set is None:
                # An unfiltered catalogue response contains all named capability sets.
                selected_data.update(
                    {
                        key: value
                        for key, value in telescope_capability_data.items()
                        if key not in ("telescope", "basic_capabilities", "constraints")
                    }
                )
            else:
                capability_set_error = self.check_capability_set(
                    capability_set, telescope_capability_data
                )
                if capability_set_error:
                    errors.append(capability_set_error)
                    continue
                selected_data[capability_set] = telescope_capability_data[
                    capability_set
                ]

            result_data["capabilities"][telescope] = selected_data

        if errors:
            return None, errors
        if cycle_definition is not None:
            result_data = {"observatory_policy": cycle_definition, **result_data}
        return result_data, []

    def get_osd_data(self) -> tuple[dict[str, Any] | None, list[str]]:
        """Return OSD data selected by the query's cycle and telescope filters."""
        query_error = self.validate_query()
        if query_error:
            return None, [query_error]

        cycle_definition, cycle_error = self.get_cycle_definition()
        if cycle_error:
            return None, [cycle_error]

        selected_telescope_capability_sets, selection_error = (
            self.select_telescope_capability_sets(cycle_definition)
        )
        if selection_error:
            return None, [selection_error]

        return self.build_osd_data(selected_telescope_capability_sets, cycle_definition)


def get_available_cycles(tmdata: TMData) -> list[int]:
    """List available cycle IDs from observing-cycle file names."""
    return OSD(
        telescope=None,
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


def get_osd_data(
    telescope: Telescope | None = None,
    array_assembly: str = None,
    tmdata: TMData = None,
    cycle_id: int = None,
    process_templates: bool = False,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Build OSD data for telescope and named-capability-set query filters.

    :param telescope: optional telescope name.
    :param array_assembly: optional name of a capability set.
    :param tmdata: TMData object containing the OSD documents.
    :param cycle_id: optional observing-cycle ID.
    :param process_templates: whether to process template mappings.
    :return: OSD data and any validation errors.
    """
    osd_data, data_error_msg_list = OSD(
        telescope=telescope,
        array_assembly=array_assembly,
        tmdata=tmdata,
        cycle_id=cycle_id,
        process_templates=process_templates,
    ).get_osd_data()

    return osd_data, data_error_msg_list


def get_osd_using_tmdata(
    tm_data: TMData,
    telescope: Telescope | None = None,
    array_assembly: Optional[str] = None,
    cycle_id: Optional[int] = None,
    process_templates: bool = False,
) -> Dict:
    """Retrieve OSD data using an already constructed TMData object.

    :param tm_data: TMData, pre-resolved TMData source for OSD retrieval.
    :param telescope: optional telescope name.
    :param array_assembly: optional name of a capability set.
    :param cycle_id: int, optional cycle ID.
    :param process_templates: bool, whether to process template mappings.
    :return: Dict[Dict[str, Any]], OSD data.
    :raises ValueError: If any validation or processing errors occur.
    """
    errors = []

    osd_data, osd_errors = get_osd_data(
        telescope=telescope,
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
