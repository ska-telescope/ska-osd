import logging
import posixpath
from functools import cached_property
from typing import Any, Dict, Optional

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
)

from .adapters.tmdata.storage import get_cycle_paths
from .common.constant import (
    RELEASE_FILE_PATH_LATEST,
    Telescope,
    osd_file_mapping,
)

LOGGER = logging.getLogger(__name__)

# The telescope names the capability documents and responses use
_LEGACY_TELESCOPE_NAMES = {
    Telescope.SKA_MID: "mid",
    Telescope.SKA_LOW: "low",
}


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

        :param telescope: requested telescope, ``Telescope.SKA_MID`` or
            ``Telescope.SKA_LOW``. The legacy names ``"mid"`` and ``"low"``
            are still accepted.
        :param array_assembly: requested capability-set name, such as ``"AA2"``.
        :param tmdata: TMData, TMData class object.
        :param cycle_id: int, cycle identifier.
        :param process_templates: bool, whether to process template mappings.
        :return: None
        """
        self.cycle_id = cycle_id
        self.requested_telescope = _LEGACY_TELESCOPE_NAMES.get(telescope, telescope)
        self.requested_capability_set = array_assembly
        self.tmdata = tmdata
        self.process_templates = process_templates

    @cached_property
    def capability_filepaths(self) -> dict[str, str]:
        """Return telescope-keyed TMData basic capabilities paths, e.g.
        ``{"mid": "telescopes/ska_mid/basic_capabilities.json"}``."""
        return {
            posixpath.basename(posixpath.dirname(entry)).removeprefix("ska_"): entry
            for entry in self.tmdata
            if entry.endswith("/basic_capabilities.json")
        }

    def cycle_filepaths(self) -> dict[int, str]:
        """Return the TMData cycle file paths keyed by the ``cycle_number``
        in each file; a cycle file may have any name."""
        return get_cycle_paths(self.tmdata)

    def get_available_cycles(self) -> list[int]:
        """List available cycle IDs from the observing-cycle files."""
        return list(self.cycle_filepaths())

    def check_cycle_id(self) -> str | None:
        """Return an error message when the selected cycle file is absent."""
        if self.cycle_id is None:
            return None

        if self.cycle_id not in self.cycle_filepaths():
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
        """Load the selected cycle definition after checking it exists."""
        cycle_error = self.check_cycle_id()
        if cycle_error:
            return None, cycle_error
        if self.cycle_id is None:
            return None, None
        cycle_definition = self.tmdata[self.cycle_filepaths()[self.cycle_id]].get_dict()
        # The cycle files name the telescopes by Telescope value; the legacy
        # response names them Mid and Low
        cycle_definition["telescope_capabilities"] = {
            _LEGACY_TELESCOPE_NAMES[Telescope(telescope)].capitalize(): capability_set
            for telescope, capability_set in cycle_definition[
                "telescope_capabilities"
            ].items()
        }
        return cycle_definition, None

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
        """Load one telescope capability document and optional template mappings.

        The document is rebuilt in its legacy shape: the basic capabilities,
        without the elevation limits, as Mid's ``receiver_information`` or
        Low's one band, and each capability set."""
        capability_filepath = self.capability_filepaths[telescope]
        telescope_dir = posixpath.dirname(capability_filepath)
        bands = self.tmdata[capability_filepath].get_dict()["frequency_bands"]
        basic_capabilities = (
            {"receiver_information": bands} if telescope == "mid" else bands[0]
        )
        return {
            "basic_capabilities": basic_capabilities,
            **{
                name.removesuffix(".json"): self._legacy_capability_set(
                    telescope_dir, name
                )
                for name in sorted(self.tmdata[f"{telescope_dir}/capabilities"])
            },
        }

    def _legacy_capability_set(self, telescope_dir: str, name: str) -> dict[str, Any]:
        """A capability set in its legacy shape: its array assembly as a template
        pattern, or as that array assembly's templates when they are processed."""
        capability_set = self.tmdata[f"{telescope_dir}/capabilities/{name}"].get_dict()
        array_assembly = capability_set.pop("array_assembly", None)
        if array_assembly is None:
            return capability_set
        if not self.process_templates:
            capability_set["subarray_templates"] = [f"*_{array_assembly}"]
            return capability_set
        templates_dir = f"{telescope_dir}/{osd_file_mapping['subarray_templates']}"
        try:
            templates = self.tmdata[f"{templates_dir}/{array_assembly}.json"].get_dict()
        except KeyError:
            return capability_set
        # Keyed by name, with the stations as one comma-separated string
        capability_set["subarray_templates"] = {
            template.pop("name"): {
                **template,
                "custom_stations": ",".join(template["custom_stations"]),
            }
            for template in templates["templates"]
        }
        return capability_set

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
